library(here)

here()

library(dplyr)
library(ggplot2)
library(readr)
library(readxl)
library(stringr)

rndc <- read.csv(here("data","raw","rndc.csv"))

divipola <- read.csv(here("data","raw","divipola.csv"))

mitad <- nrow(rndc) / 2

base1 <- rndc[1:mitad, ]
base2 <- rndc[(mitad):nrow(rndc), ]

write.csv(base1, "data/raw/base1.csv", row.names = FALSE)
write.csv(base2, "data/raw/base2.csv", row.names = FALSE)

#unir bases

base1 <- read.csv(here("data", "raw", "base1.csv"))
base2 <- read.csv(here("data", "raw", "base2.csv"))

rndc1 <- bind_rows(base1, base2)


rndc <- rndc %>%
  mutate(
    CODMUNICIPIOORIGEN = as.character(CODMUNICIPIOORIGEN),
    CODMUNICIPIOORIGEN = gsub(",", "", CODMUNICIPIOORIGEN),
    CODMUNICIPIOORIGEN = sub("000$", "", CODMUNICIPIOORIGEN),
    
    CODMUNICIPIODESTINO = as.character(CODMUNICIPIODESTINO),
    CODMUNICIPIODESTINO = gsub(",", "", CODMUNICIPIODESTINO),
    CODMUNICIPIODESTINO = sub("000$", "", CODMUNICIPIODESTINO)
  )
verificacion <- 

origen <- rndc%>%
  count(CODMUNICIPIOORIGEN)
destino <- rndc%>%
  count(CODMUNICIPIODESTINO)
#write.csv(df_gr, here("data","final","df_grafo.csv"), row.names = FALSE)
