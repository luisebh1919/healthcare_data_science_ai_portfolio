# DQD sobre una copia NUEVA de la OMOP nueva; nunca sobre las bases históricas.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Uso: Rscript omop_cdm/src/run_dqd.R nueva_omop.duckdb directorio_nuevo")
needed <- c("DataQualityDashboard", "DatabaseConnector", "SqlRender", "duckdb")
missing <- needed[!vapply(needed, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop(paste("Faltan paquetes; no se instala automáticamente:", paste(missing, collapse = ", ")))
source <- normalizePath(args[1], mustWork = TRUE)
if (basename(source) %in% c("omop_minimal.duckdb", "clinical.duckdb")) stop("Base histórica protegida")
if (file.exists(paste0(source, ".wal"))) stop("La fuente debe estar cerrada y sin WAL")
out <- args[2]
if (file.exists(out)) stop("Elegir un directorio de resultados nuevo")
# df POSIX ofrece KiB disponibles. No copiar si la reserva no puede demostrarse.
parent <- dirname(normalizePath(out, mustWork = FALSE))
free <- system2("df", c("-Pk", shQuote(parent)), stdout = TRUE)
free_kib <- suppressWarnings(as.numeric(strsplit(trimws(tail(free, 1)), "[[:space:]]+")[[1]][4]))
if (is.na(free_kib) || free_kib * 1024 < file.info(source)$size * 3 + 1024^3) stop("Espacio insuficiente para copia y resultados DQD")
dir.create(out, recursive = TRUE)
copy <- file.path(out, "validation_copy.duckdb")
stopifnot(file.copy(source, copy, overwrite = FALSE))
details <- DatabaseConnector::createConnectionDetails(dbms = "duckdb", server = normalizePath(copy))
connection <- DatabaseConnector::connect(details)
tryCatch({
  n <- DatabaseConnector::querySql(connection, "SELECT COUNT(*) AS n FROM omop.cdm_source")
  if (n[[1]][1] != 1) stop("Se requiere CDM_SOURCE poblada: no ejecutar sobre el esquema vacío")
}, finally = DatabaseConnector::disconnect(connection))
DataQualityDashboard::executeDqChecks(
  connectionDetails = details,
  cdmDatabaseSchema = "omop",
  resultsDatabaseSchema = "omop",
  vocabDatabaseSchema = "omop",
  cdmSourceName = "Synthea OMOP 5.4 independiente",
  cdmVersion = "5.4",
  numThreads = 1,
  outputFolder = out,
  outputFile = "dqd.json",
  writeToTable = FALSE
)
writeLines(capture.output(sessionInfo()), file.path(out, "sessionInfo.txt"))
