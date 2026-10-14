# =====================================================================
#  LIMPIEZA Y EXPLORACIÓN DEL RNDC 2015
#  Proyecto Teoría de Grafos — Vulnerabilidad de la red vial de carga
#
#  Salidas (en data/final/):
#    matriz_od.csv          -> matriz origen-destino para el grafo (Python)
#    costo_por_config.csv   -> costo por tonelada-km según tipo de vehículo
#    rndc_limpio.rds        -> base completa limpia (para seguir en R)
# =====================================================================

library(here)
library(dplyr)
library(readr)
library(stringr)

# ---------------------------------------------------------------------
# 0. PARÁMETROS — decisiones que el grupo debe discutir y justificar
# ---------------------------------------------------------------------

# Conversión de galones a kg para la carga líquida.
# Supuesto: densidad del ACPM/diésel ~0,84 kg/L x 3,785 L/galón ~ 3,2 kg/galón
FACTOR_KG_POR_GALON <- 3.2

# Rangos físicamente plausibles POR VIAJE para estimar costos.
# Se aplican antes de los cuantiles para sacar errores de digitación.
TON_VIAJE_MIN   <- 0.5     # menos: paquetería o kilos mal digitados (ej. "1" kg)
TON_VIAJE_MAX   <- 40      # carga útil máx. aprox. de un tractocamión 3S3 (peso bruto 52 t)
KM_VIAJE_MIN    <- 5
KM_VIAJE_MAX    <- 2000    # más largo que cualquier ruta nacional por carretera
FLETE_VIAJE_MIN <- 50000   # COP de 2015; fletes de 3 o 4 pesos son errores

# Cuantiles para marcar costos por ton-km atípicos (después de los filtros físicos)
CUANTIL_INF <- 0.01
CUANTIL_SUP <- 0.99

# Columna de código municipal en divipola.csv
COL_COD_DIVIPOLA <- "Codigo.Municipio"

# Función auxiliar para imprimir números con formato colombiano
fmt <- function(x, dec = 0) {
  format(round(x, dec), big.mark = ".", decimal.mark = ",", nsmall = dec)
}

# ---------------------------------------------------------------------
# 1. LECTURA — todo como texto para no perder ceros ni romper comas
# ---------------------------------------------------------------------

leer_texto <- function(archivo) {
  read.csv(here("data", "raw", archivo), colClasses = "character")
}

base1    <- leer_texto("base1.csv")
base2    <- leer_texto("base2.csv")
divipola <- leer_texto("divipola.csv")

rndc <- bind_rows(base1, base2)
stopifnot(nrow(rndc) == nrow(base1) + nrow(base2))
cat("\n== 1. LECTURA ==\n")
cat("Filas totales:", fmt(nrow(rndc)), "(esperado: 1.048.001)\n")
rm(base1, base2)

# ---------------------------------------------------------------------
# 2. CHEQUEOS ANTES DE BORRAR COLUMNAS
# ---------------------------------------------------------------------
cat("\n== 2. CHEQUEOS DE COLUMNAS ==\n")

# La columna de año es la primera (se ubica por posición para evitar
# problemas de codificación con la Ñ)
col_anio <- names(rndc)[1]
cat("Columna de año detectada:", col_anio, "\n")
print(count(rndc, .data[[col_anio]]))

# ¿'codigo' es igual al código de origen?
dif_codigo <- sum(rndc$codigo != rndc$CODMUNICIPIOORIGEN, na.rm = TRUE)
cat("Filas donde 'codigo' difiere del origen:", fmt(dif_codigo), "\n")

# ¿Las columnas de contenedor tienen algún dato?
con_dato <- function(x) sum(!is.na(x) & str_trim(x) != "")
cat("Filas con CODTIPOCONTENEDOR:", fmt(con_dato(rndc$CODTIPOCONTENEDOR)), "\n")
cat("Filas con TIPOCONTENEDOR:   ", fmt(con_dato(rndc$TIPOCONTENEDOR)), "\n")

# Solo se borran si los chequeos lo permiten
cols_borrar <- col_anio
if (dif_codigo == 0) cols_borrar <- c(cols_borrar, "codigo")
if (con_dato(rndc$CODTIPOCONTENEDOR) == 0 && con_dato(rndc$TIPOCONTENEDOR) == 0) {
  cols_borrar <- c(cols_borrar, "CODTIPOCONTENEDOR", "TIPOCONTENEDOR")
}
if (n_distinct(rndc[[col_anio]]) > 1) {
  warning("Hay más de un año: NO se borra la columna de año.")
  cols_borrar <- setdiff(cols_borrar, col_anio)
}
rndc <- select(rndc, -all_of(cols_borrar))
cat("Columnas eliminadas:", paste(cols_borrar, collapse = ", "), "\n")

# ---------------------------------------------------------------------
# 3. CONVERSIÓN NUMÉRICA CON CONTROL DE NA
#    parse_number entiende "5,000" como 5000 (coma = separador de miles)
# ---------------------------------------------------------------------
cat("\n== 3. CONVERSIÓN NUMÉRICA ==\n")

cols_num <- c("VIAJESTOTALES", "KILOGRAMOS", "GALONES", "VIAJESLIQUIDOS",
              "VIAJESVALORCERO", "KILOMETROS", "VALORESPAGADOS")

crudos   <- rndc[cols_num]                       # copia para diagnosticar
vacio    <- function(x) is.na(x) | str_trim(x) == ""
na_antes <- sapply(crudos, function(x) sum(vacio(x)))

rndc <- rndc %>%
  mutate(across(all_of(cols_num), ~ suppressWarnings(parse_number(.x))))

na_despues <- sapply(rndc[cols_num], function(x) sum(is.na(x)))
negativos  <- sapply(rndc[cols_num], function(x) sum(x < 0, na.rm = TRUE))

chequeo_na <- data.frame(
  columna   = cols_num,
  na_antes  = na_antes,
  na_despues = na_despues,
  nuevos_na = na_despues - na_antes,
  negativos = negativos,
  row.names = NULL
)
print(chequeo_na)

# Si la conversión creó NA, muestra ejemplos de los valores que fallaron
for (col in cols_num) {
  fallo <- !vacio(crudos[[col]]) & is.na(rndc[[col]])
  if (any(fallo)) {
    cat("\nValores que no se pudieron convertir en", col, ":\n")
    print(head(unique(crudos[[col]][fallo]), 10))
  }
}
rm(crudos)

# ---------------------------------------------------------------------
# 4. CÓDIGOS MUNICIPALES
#    - 4 o 5 dígitos: municipio (se rellenan ceros a la izquierda)
#    - 7 u 8 dígitos: municipio + centro poblado (se rellenan a 8
#      y se toman los primeros 5)
#    - cualquier otro largo: inválido (NA)
# ---------------------------------------------------------------------
cat("\n== 4. CÓDIGOS MUNICIPALES ==\n")

cat("Largo de los códigos de ORIGEN:\n")
print(count(rndc, largo = nchar(str_trim(CODMUNICIPIOORIGEN))))
cat("Largo de los códigos de DESTINO:\n")
print(count(rndc, largo = nchar(str_trim(CODMUNICIPIODESTINO))))

normalizar_mpio <- function(x) {
  x <- str_trim(x)
  n <- nchar(x)
  solo_digitos <- str_detect(x, "^[0-9]+$")
  case_when(
    solo_digitos & n %in% 4:5 ~ str_pad(x, 5, pad = "0"),
    solo_digitos & n %in% 7:8 ~ str_sub(str_pad(x, 8, pad = "0"), 1, 5),
    TRUE ~ NA_character_
  )
}

rndc <- rndc %>%
  mutate(
    ORIGEN  = normalizar_mpio(CODMUNICIPIOORIGEN),
    DESTINO = normalizar_mpio(CODMUNICIPIODESTINO)
  )

cat("Orígenes inválidos: ", fmt(sum(is.na(rndc$ORIGEN))), "\n")
cat("Destinos inválidos: ", fmt(sum(is.na(rndc$DESTINO))), "\n")

# ---------------------------------------------------------------------
# 5. VARIABLES DERIVADAS
# ---------------------------------------------------------------------
cat("\n== 5. TONELADAS, AUTOLAZOS Y KM POR VIAJE ==\n")

ambos <- sum(rndc$KILOGRAMOS > 0 & rndc$GALONES > 0, na.rm = TRUE)
cat("Filas con kilos Y galones > 0 (se usan los kilos):", fmt(ambos), "\n")

rndc <- rndc %>%
  mutate(
    # Si hay kilos se usan; si no, se convierten los galones
    KG_EQUIV = case_when(
      KILOGRAMOS > 0 ~ KILOGRAMOS,
      GALONES    > 0 ~ GALONES * FACTOR_KG_POR_GALON,
      TRUE           ~ 0
    ),
    TONELADAS = KG_EQUIV / 1000,
    AUTOLAZO  = !is.na(ORIGEN) & !is.na(DESTINO) & ORIGEN == DESTINO,
    # Los km del RNDC son la suma sobre los viajes; 0 = no reportado
    KM_POR_VIAJE = if_else(KILOMETROS > 0 & VIAJESTOTALES > 0,
                           KILOMETROS / VIAJESTOTALES, NA_real_)
  )

sin_carga <- sum(rndc$TONELADAS == 0)
cat("Filas sin carga reportada (ni kilos ni galones):", fmt(sin_carga), "\n")

# ---------------------------------------------------------------------
# 6. REPRODUCIR LAS CIFRAS DEL PAPER
# ---------------------------------------------------------------------
cat("\n== 6. TOTALES (comparar con la Sección II del paper) ==\n")

tot_viajes  <- sum(rndc$VIAJESTOTALES, na.rm = TRUE)
tot_ton     <- sum(rndc$TONELADAS)
tot_ton_kg  <- sum(rndc$KILOGRAMOS, na.rm = TRUE) / 1000

cat("Viajes totales:             ", fmt(tot_viajes), "(paper: ~6 millones)\n")
cat("Toneladas (kilos+galones):  ", fmt(tot_ton), "(paper: 85,7 millones)\n")
cat("Toneladas (solo kilos):     ", fmt(tot_ton_kg), "\n")
cat("Toneladas que aportan los líquidos:", fmt(tot_ton - tot_ton_kg), "\n")

# ---------------------------------------------------------------------
# 7. AUTOLAZOS (carga dentro del mismo municipio)
# ---------------------------------------------------------------------
cat("\n== 7. AUTOLAZOS ==\n")

ton_auto <- sum(rndc$TONELADAS[rndc$AUTOLAZO])
cat("Filas autolazo:", fmt(sum(rndc$AUTOLAZO)), "\n")
cat("Toneladas en autolazos:", fmt(ton_auto),
    sprintf("(%s %% del total)\n", fmt(100 * ton_auto / tot_ton, 1)))

# ---------------------------------------------------------------------
# 8. CRUCE CON DIVIPOLA
# ---------------------------------------------------------------------
cat("\n== 8. CRUCE CON DIVIPOLA ==\n")

if (!COL_COD_DIVIPOLA %in% names(divipola)) {
  cat("No encontré la columna '", COL_COD_DIVIPOLA, "' en divipola.csv.\n",
      "Columnas disponibles: ", paste(names(divipola), collapse = ", "), "\n",
      "Ajusta COL_COD_DIVIPOLA en la sección 0 y vuelve a correr.\n", sep = "")
} else {
  cod_divipola <- unique(normalizar_mpio(divipola[[COL_COD_DIVIPOLA]]))
  
  mpios_rndc <- bind_rows(
    rndc %>% select(COD = ORIGEN,  TONELADAS),
    rndc %>% select(COD = DESTINO, TONELADAS)
  ) %>%
    filter(!is.na(COD)) %>%
    group_by(COD) %>%
    summarise(TONELADAS = sum(TONELADAS), .groups = "drop")
  
  no_cruzan <- mpios_rndc %>%
    filter(!COD %in% cod_divipola) %>%
    arrange(desc(TONELADAS))
  
  cat("Municipios en el RNDC:", fmt(nrow(mpios_rndc)), "\n")
  cat("Municipios que NO cruzan con DIVIPOLA:", fmt(nrow(no_cruzan)), "\n")
  if (nrow(no_cruzan) > 0) {
    cat("Los que más carga tienen:\n")
    print(head(no_cruzan, 15))
  }
}

# ---------------------------------------------------------------------
# 9. COSTO POR TONELADA-KILÓMETRO (base empírica del peso de las aristas)
#    Filas válidas: con flete en todos sus viajes, carga, km y códigos
# ---------------------------------------------------------------------
cat("\n== 9. COSTO POR TONELADA-KM ==\n")

costos <- rndc %>%
  filter(!AUTOLAZO, !is.na(ORIGEN), !is.na(DESTINO),
         VALORESPAGADOS > 0,
         VIAJESVALORCERO == 0,     # si algún viaje no tiene flete, el total está incompleto
         TONELADAS > 0,
         !is.na(KM_POR_VIAJE)) %>%
  mutate(
    TON_POR_VIAJE   = TONELADAS / VIAJESTOTALES,
    FLETE_POR_VIAJE = VALORESPAGADOS / VIAJESTOTALES,
    TON_KM    = TONELADAS * KM_POR_VIAJE,
    COSTO_TKM = VALORESPAGADOS / TON_KM
  )

# Filtros físicos: se reporta cuántas filas marca cada uno
n_inicial <- nrow(costos)
filtros <- list(
  "toneladas por viaje fuera de rango" =
    with(costos, TON_POR_VIAJE < TON_VIAJE_MIN | TON_POR_VIAJE > TON_VIAJE_MAX),
  "km por viaje fuera de rango" =
    with(costos, KM_POR_VIAJE < KM_VIAJE_MIN | KM_POR_VIAJE > KM_VIAJE_MAX),
  "flete por viaje muy bajo" =
    with(costos, FLETE_POR_VIAJE < FLETE_VIAJE_MIN)
)
cat("Filas candidatas:", fmt(n_inicial), "\n")
for (nm in names(filtros)) {
  cat(sprintf("  %-36s %s filas\n", nm, fmt(sum(filtros[[nm]]))))
}
costos <- costos[!Reduce(`|`, filtros), ]
cat("Filas tras filtros físicos:", fmt(nrow(costos)), "\n")

limites <- quantile(costos$COSTO_TKM, c(CUANTIL_INF, CUANTIL_SUP))
costos  <- costos %>%
  mutate(ATIPICO = COSTO_TKM < limites[1] | COSTO_TKM > limites[2])

cat("Filas válidas para costo:", fmt(nrow(costos)),
    sprintf("(%s %% de la base)\n", fmt(100 * nrow(costos) / nrow(rndc), 1)))
cat("Límites de atípicos (COP/ton-km):", fmt(limites[1], 2), "a", fmt(limites[2], 2), "\n")
cat("Distribución del costo por ton-km (sin atípicos):\n")
print(summary(costos$COSTO_TKM[!costos$ATIPICO]))

limpios <- filter(costos, !ATIPICO)
costo_ponderado <- sum(limpios$VALORESPAGADOS) / sum(limpios$TON_KM)
cat("Costo promedio ponderado (COP/ton-km):", fmt(costo_ponderado, 2), "\n")

costo_config <- limpios %>%
  group_by(CONFIG_VEHICULO) %>%
  summarise(
    FILAS            = n(),
    TONELADAS        = sum(TONELADAS),
    COSTO_TKM_MEDIANA   = median(COSTO_TKM),
    COSTO_TKM_PONDERADO = sum(VALORESPAGADOS) / sum(TON_KM),
    .groups = "drop"
  ) %>%
  mutate(CONFIABLE = FILAS >= 500) %>%   # categorías con pocas filas: no interpretar
  arrange(desc(TONELADAS))
cat("Costo por configuración de vehículo:\n")
print(costo_config, n = 30)

# ---------------------------------------------------------------------
# 10. MATRIZ ORIGEN-DESTINO (dirigida: A->B distinto de B->A)
# ---------------------------------------------------------------------
cat("\n== 10. MATRIZ ORIGEN-DESTINO ==\n")

nombres <- bind_rows(
  rndc %>% select(COD = ORIGEN,  NOMBRE = MUNICIPIOORIGEN),
  rndc %>% select(COD = DESTINO, NOMBRE = MUNICIPIODESTINO)
) %>%
  filter(!is.na(COD)) %>%
  count(COD, NOMBRE) %>%
  group_by(COD) %>%
  slice_max(n, n = 1, with_ties = FALSE) %>%   # nombre más frecuente por código
  ungroup() %>%
  select(COD, NOMBRE)

od <- rndc %>%
  filter(!AUTOLAZO, !is.na(ORIGEN), !is.na(DESTINO)) %>%
  group_by(ORIGEN, DESTINO) %>%
  summarise(
    VIAJES        = sum(VIAJESTOTALES, na.rm = TRUE),
    TONELADAS     = sum(TONELADAS),
    VALOR_PAGADO  = sum(VALORESPAGADOS, na.rm = TRUE),
    KM_REPORTADOS = sum(KILOMETROS[KILOMETROS > 0], na.rm = TRUE),
    VIAJES_CON_KM = sum(VIAJESTOTALES[KILOMETROS > 0], na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(KM_POR_VIAJE = if_else(VIAJES_CON_KM > 0,
                                KM_REPORTADOS / VIAJES_CON_KM, NA_real_)) %>%
  left_join(rename(nombres, ORIGEN = COD,  NOMBRE_ORIGEN  = NOMBRE), by = "ORIGEN") %>%
  left_join(rename(nombres, DESTINO = COD, NOMBRE_DESTINO = NOMBRE), by = "DESTINO") %>%
  arrange(desc(TONELADAS)) %>%
  mutate(PART_ACUM = cumsum(TONELADAS) / sum(TONELADAS))

# Quitar pares con municipios que no existen en DIVIPOLA (99999 = sin dato, etc.)
if (exists("cod_divipola")) {
  n_antes <- nrow(od)
  od <- od %>%
    filter(ORIGEN %in% cod_divipola, DESTINO %in% cod_divipola) %>%
    mutate(PART_ACUM = cumsum(TONELADAS) / sum(TONELADAS))
  cat("Pares eliminados por códigos fuera de DIVIPOLA:", fmt(n_antes - nrow(od)), "\n")
}

cat("Pares OD distintos:", fmt(nrow(od)), "\n")
cat("Pares OD sin km reportados:", fmt(sum(is.na(od$KM_POR_VIAJE))), "\n")
ton_con_km <- sum(od$TONELADAS[!is.na(od$KM_POR_VIAJE)])
cat("...pero las toneladas en pares CON km son el",
    fmt(100 * ton_con_km / sum(od$TONELADAS), 1), "% del total\n")
cat("\nTop 15 pares por toneladas:\n")
print(od %>%
        select(NOMBRE_ORIGEN, NOMBRE_DESTINO, VIAJES, TONELADAS, KM_POR_VIAJE) %>%
        head(15))

# ---------------------------------------------------------------------
# 11. CONCENTRACIÓN (PARETO)
# ---------------------------------------------------------------------
cat("\n== 11. PARETO: ¿cuántos pares concentran la carga? ==\n")

pareto <- lapply(c(0.5, 0.8, 0.9, 0.95), function(u) {
  k   <- min(sum(od$PART_ACUM < u) + 1, nrow(od))
  sub <- head(od, k)
  data.frame(
    umbral      = paste0(u * 100, " %"),
    pares_OD    = k,
    pct_pares   = round(100 * k / nrow(od), 2),
    municipios  = n_distinct(c(sub$ORIGEN, sub$DESTINO)),
    pares_con_km = sum(!is.na(sub$KM_POR_VIAJE))
  )
}) %>% bind_rows()
print(pareto)

# ---------------------------------------------------------------------
# 11b. NODOS DE DEMANDA CON COORDENADAS (insumo para Colab)
#      Un punto por municipio: la cabecera municipal si existe
# ---------------------------------------------------------------------
cat("\n== 11b. NODOS DE DEMANDA ==\n")

a_num <- function(x) as.numeric(str_replace(str_trim(x), ",", "."))  # acepta coma o punto decimal

cat("Valores de la columna 'Tipo.' en DIVIPOLA:\n")
print(count(divipola, Tipo.))

coords <- divipola %>%
  mutate(COD = normalizar_mpio(Codigo.Municipio),
         LON = a_num(longitud),
         LAT = a_num(Latitud),
         ES_CABECERA = Tipo. == "CM") %>%      # CM = cabecera municipal
  filter(!is.na(COD), !is.na(LAT), !is.na(LON)) %>%
  arrange(COD, desc(ES_CABECERA)) %>%          # cabecera primero; si no hay, otro centro poblado
  group_by(COD) %>%
  slice(1) %>%
  ungroup() %>%
  select(COD, NOMBRE_MPIO = Nombre.Municipio, DEPARTAMENTO = Nombre_departamento,
         LAT, LON, ES_CABECERA)

fuera_col <- sum(coords$LAT < -5 | coords$LAT > 14 | coords$LON < -82 | coords$LON > -66)
cat("Municipios con coordenadas fuera de Colombia (revisar):", fuera_col, "\n")

k80 <- min(sum(od$PART_ACUM < 0.8) + 1, nrow(od))
nucleo_cod <- unique(c(od$ORIGEN[1:k80], od$DESTINO[1:k80]))

nodos <- bind_rows(
  od %>% group_by(COD = ORIGEN)  %>% summarise(TON_SALE  = sum(TONELADAS)),
  od %>% group_by(COD = DESTINO) %>% summarise(TON_LLEGA = sum(TONELADAS))
) %>%
  group_by(COD) %>%
  summarise(TON_SALE  = sum(TON_SALE,  na.rm = TRUE),
            TON_LLEGA = sum(TON_LLEGA, na.rm = TRUE)) %>%
  mutate(TON_TOTAL = TON_SALE + TON_LLEGA,
         NUCLEO_80 = COD %in% nucleo_cod) %>%
  left_join(coords, by = "COD") %>%
  arrange(desc(TON_TOTAL))

cat("Municipios con demanda:", fmt(nrow(nodos)),
    "| en el núcleo del 80 %:", fmt(sum(nodos$NUCLEO_80)), "\n")
cat("Sin coordenadas:", fmt(sum(is.na(nodos$LAT))), "\n")
cat("Ubicados en cabecera municipal:", fmt(sum(nodos$ES_CABECERA, na.rm = TRUE)), "\n")

# ---------------------------------------------------------------------
# 12. GUARDAR
# ---------------------------------------------------------------------
dir.create(here("data", "final"), showWarnings = FALSE, recursive = TRUE)
write_csv(nodos,        here("data", "final", "nodos_demanda.csv"))
write_csv(od,           here("data", "final", "matriz_od.csv"))
write_csv(costo_config, here("data", "final", "costo_por_config.csv"))
saveRDS(rndc,           here("data", "final", "rndc_limpio.rds"))

cat("\nListo. Archivos guardados en data/final/\n")