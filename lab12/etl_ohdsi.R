# Ruta preferida alternativa: requiere paquetes, PostgreSQL, JDBC y ATHENA.
# Configurar variables de entorno; nunca guardar contraseñas en el repositorio.
required <- c('OMOP_SERVER','OMOP_USER','OMOP_PASSWORD','SYNTHEA_CSV','ATHENA_DIR','SYNTHEA_VERSION','JDBC_DIR')
stopifnot(all(nzchar(Sys.getenv(required))))
library(ETLSyntheaBuilder)
cd <- DatabaseConnector::createConnectionDetails(dbms='postgresql',server=Sys.getenv('OMOP_SERVER'),user=Sys.getenv('OMOP_USER'),password=Sys.getenv('OMOP_PASSWORD'),pathToDriver=Sys.getenv('JDBC_DIR'))
# Esquemas nuevos y vacíos creados previamente por el propietario.
cdm <- 'lab12_cdm'
native <- 'lab12_native'
version <- Sys.getenv('SYNTHEA_VERSION')
stopifnot(version %in% c('2.7.0','3.0.0','3.1.0','3.2.0','3.3.0'))
CreateCDMTables(cd,cdm,cdmVersion='5.4')
CreateSyntheaTables(cd,native,syntheaVersion=version)
LoadSyntheaTables(cd,native,Sys.getenv('SYNTHEA_CSV'))
LoadVocabFromCsv(cd,cdm,Sys.getenv('ATHENA_DIR'))
CreateMapAndRollupTables(cd,cdm,native,cdmVersion='5.4',syntheaVersion=version)
LoadEventTables(cd,cdm,native,cdmVersion='5.4',syntheaVersion=version)
print(sessionInfo())
