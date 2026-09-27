# Bitácora — Laboratorio 07

## Actividad 1 — Stack mínimo

Se creó un stack inicial con PostgreSQL y Adminer usando Docker Compose.

Servicios:

- PostgreSQL: `postgres:17-alpine`
- Adminer: `adminer:4.8.1`

Puertos publicados:

- `5433:5432` para acceder a PostgreSQL desde la máquina host.
- `8080:8080` para acceder a Adminer desde el navegador.

Se utilizó el puerto 5433 en el host para evitar posibles conflictos con una instalación local de PostgreSQL que use 5432.

Dentro de la red de Docker Compose, Adminer se conecta a PostgreSQL mediante el nombre del servicio:

`postgres:5432`

Verificación:

```text
stack-adminer-1   Up   0.0.0.0:8080->8080/tcp
stack-postgres-1  Up   0.0.0.0:5433->5432/tcp

```

Adminer pudo conectarse correctamente a la base `clinical` usando `postgres` como nombre del servidor dentro de la red de Docker Compose.

## Actividad 2 — Comunicación entre servicios

Se añadió un servicio Jupyter al stack y se comprobó la conexión a PostgreSQL desde dos ubicaciones distintas.

### Desde Jupyter dentro de Docker

Cadena de conexión:

`postgresql+psycopg2://clinlab:<password>@postgres:5432/clinical`

Resultado:

`('clinical', 'clinlab')`

Dentro de la red privada de Docker Compose se usa `postgres` porque es el nombre DNS del servicio, y `5432` porque es el puerto interno de PostgreSQL.

### Desde la máquina host

Cadena de conexión:

`postgresql://clinlab:<password>@localhost:5433/clinical`

La consulta:

`SELECT current_database(), current_user;`

devolvió:

`clinical | clinlab`

Desde el host se usa `localhost:5433` porque el puerto 5433 de la computadora está publicado hacia el puerto 5432 del contenedor.

Ambas conexiones llegan a la misma base de datos; cambia únicamente la ruta utilizada para alcanzarla.

## Actividad 3 — Persistencia e inicialización de esquemas

Se configuró el volumen nombrado `pgdata` en `/var/lib/postgresql/data` para conservar los datos de PostgreSQL al recrear el contenedor. También se montó `./initdb` como solo lectura en `/docker-entrypoint-initdb.d/`.

El archivo `initdb/01-create-schemas.sql` crea los esquemas `cdm` y `results` mediante `CREATE SCHEMA IF NOT EXISTS`.

Comandos utilizados:

```bash
docker compose down -v
docker compose up -d
docker compose exec postgres psql -U clinlab -d clinical -c "\dn"

```

Verificación exitosa: `\dn` mostró los esquemas `cdm`, `public` y `results`.

También se añadió el segundo script numerado, `initdb/02-create-test-table.sql`, que crea la tabla de prueba `cdm.test_table` con `test_id INTEGER PRIMARY KEY` y `description TEXT NOT NULL` en su versión inicial.

### Experimento de `initdb`

Con el volumen `pgdata` ya existente, ejecutar `docker compose up -d` no creó `cdm.test_table`: el segundo script no se ejecutó. Después de ejecutar `docker compose down -v` y `docker compose up -d`, PostgreSQL inicializó un directorio de datos nuevo y la tabla fue creada.

Luego se modificó el script para cambiar `description` de `TEXT` a `VARCHAR(80)`. Al ejecutar únicamente `docker compose up -d`, la columna existente siguió siendo `description | text`; el cambio del script no alteró la tabla.

Los scripts de `/docker-entrypoint-initdb.d/` se ejecutan sólo cuando PostgreSQL inicializa un directorio de datos nuevo y vacío. Para que un script de `initdb` modificado vuelva a ejecutarse hay que recrear el volumen con `docker compose down -v` antes de `docker compose up -d`; en una base ya inicializada, el cambio debe aplicarse mediante una migración SQL explícita.

## Actividad 5 — Inicio ordenado con healthcheck

PostgreSQL se configuró con un `healthcheck` real basado en `pg_isready -U clinlab -d clinical`. El servicio `notebook` declara `depends_on` sobre `postgres` con `condition: service_healthy`, por lo que Compose espera a que la base de datos esté lista antes de iniciar el notebook.

La configuración se validó con `docker compose config`. Tras un inicio limpio mediante `docker compose down -v` y `docker compose up -d`, Docker reportó `postgres` como `Healthy` aproximadamente a los 5.6 s y arrancó `notebook` aproximadamente a los 5.7 s; `docker compose ps` también mostró PostgreSQL en estado `healthy`.

Desde el contenedor `notebook`, una prueba directa de socket alcanzó correctamente `postgres:5432`. La prueba con `psycopg2` falló únicamente porque ese paquete no está instalado en la imagen del notebook, no por falta de conectividad ni por un error de conexión rechazada.

Al depender del estado saludable y no sólo del inicio del proceso, el notebook no intenta conectarse mientras PostgreSQL aún se está inicializando. Esto evita fallos de arranque dependientes del tiempo, como `connection refused`.

## Actividad 6 — Configuración mediante `.env`

La configuración del stack se movió a `.env`: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, los puertos publicados de PostgreSQL, Adminer y Jupyter, y `JUPYTER_TOKEN`. El servicio `notebook` recibe `JUPYTER_TOKEN` desde el entorno para usar ese token de acceso.

El archivo `.env` está ignorado por Git y `.env.example` documenta las mismas variables con valores seguros de ejemplo para poder versionarse. En `compose.yml`, la contraseña se referencia con la sintaxis fail-fast `${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}`; el resto de la configuración también se resuelve desde variables de entorno.

Verificación: `docker compose config` se ejecutó correctamente. `grep -ri "password" compose.yml` sólo mostró la referencia fail-fast de `POSTGRES_PASSWORD`, sin revelar ningún valor secreto.

## Actividad 7 — Perfil de desarrollo para Adminer

Adminer se colocó en el perfil `dev` mediante `profiles: [dev]`, sin modificar la configuración de PostgreSQL ni la dependencia saludable del notebook.

Verificación: `docker compose config` se validó correctamente y, después de `docker compose down` seguido de `docker compose up -d`, `docker compose ps` mostró únicamente `postgres` (healthy) y `notebook`; Adminer no se inició. Tras `docker compose down` y `docker compose --profile dev up -d`, `docker compose ps` mostró `postgres`, `notebook` y `adminer`, con Adminer publicado en el puerto `8080`.

## Actividad 8 — Diagnóstico de una contraseña inconsistente

Se creó un fallo controlado cambiando temporalmente sólo `POSTGRES_PASSWORD` en `.env`, sin borrar el volumen `pgdata`. Como la imagen del notebook no incluye un controlador de PostgreSQL, se instaló `psycopg2-binary` únicamente dentro del contenedor desechable para ejecutar la prueba. Al iniciar el stack, la conexión desde `notebook` hacia `postgres:5432` falló con `FATAL: password authentication failed for user "clinlab"`.

La depuración se realizó en el orden solicitado:

1. `docker compose ps`: mostró `postgres` y `notebook` en ejecución y saludables. Esto descartó contenedores detenidos y un fallo general de arranque, pero no garantizaba que las credenciales fueran correctas.
2. `docker compose logs postgres`: indicó que PostgreSQL estaba listo para aceptar conexiones, que el directorio ya contenía una base y se omitió la inicialización, y registró `password authentication failed` mediante `scram-sha-256`. Esto ubicó el problema en la autenticación y no en la disponibilidad del servidor.
3. `docker compose exec notebook ...`: resolvió `postgres` a `172.19.0.2` y abrió correctamente una conexión TCP a `postgres:5432`, pero `psycopg2` volvió a recibir el error de contraseña. Esto descartó DNS, red y puerto como causas.

Diagnóstico final: `POSTGRES_PASSWORD` sólo se aplica al crear inicialmente la base de datos. Como `pgdata` ya existía, cambiar la variable del contenedor no actualizó la contraseña almacenada para el rol `clinlab`; el cliente usó el valor nuevo mientras PostgreSQL conservó el anterior.

Finalmente se restauró el valor correcto en `.env`, se reaplicó el stack y la consulta desde el notebook devolvió `('clinical', 'clinlab')`. El contenedor del notebook se recreó después para eliminar la instalación temporal del controlador.

## Actividad 9 — Prueba de reproducibilidad limpia

Se eliminó el entorno anterior, incluido el volumen de datos, con `docker compose --profile dev down -v`. Después se copió el contenido versionable del stack a un directorio temporal aislado, sin incluir `.env`, para representar una copia limpia del proyecto aún no confirmada en Git.

Desde esa copia se ejecutaron únicamente los pasos documentados:

```bash
cp .env.example .env
docker compose up -d
```

El arranque limpio pasó en el primer intento: PostgreSQL alcanzó el estado `healthy` y Jupyter inició y quedó `healthy`. `docker compose ps` mostró sólo esos dos servicios, confirmando que Adminer no se inicia de forma predeterminada.

La consulta de verificación sobre la base recién inicializada mostró los esquemas `cdm` y `results`, además de la tabla `cdm.test_table`. Posteriormente, `docker compose --profile dev up -d` inició Adminer y `docker compose ps` lo mostró publicado en el puerto `8080`, tal como indica el README.

No fue necesario ningún paso manual no documentado ni corregir la configuración después de la prueba. Se añadió `README.md` al directorio del stack con los requisitos, los dos pasos de inicio, la comprobación de estado y el uso opcional del perfil `dev`.

La validación en la máquina de un compañero permanece pendiente: esta prueba demuestra reproducibilidad en un directorio aislado local, no en una segunda máquina humana.

## Actividad 10 — Comparación con la solución de referencia

Se comparó nuestra configuración con el [`compose.yml` oficial de referencia](https://github.com/insomnium098/curso-ciencia-datos-2027-1/blob/main/labs/s07-docker-compose/solucion/compose.yml). No se copiaron sus decisiones; se evaluaron las siguientes tres diferencias.

### Diferencia 1 — Construcción de la imagen de Jupyter

Nuestra implementación usa directamente `jupyter/scipy-notebook:latest`, mientras que la referencia construye Jupyter con `build`, usando `./docker` como contexto y un `Dockerfile` propio. Nuestra opción reduce archivos y tiempo de mantenimiento, pero la etiqueta `latest` puede cambiar y la imagen no incorpora dependencias específicas del proyecto; esto quedó visible cuando fue necesario instalar temporalmente un controlador PostgreSQL en la Actividad 8. La referencia requiere mantener y construir una imagen, pero permite fijar dependencias y reproducir un entorno adaptado al curso. Las estrategias no son arquitectónicamente equivalentes: ambas levantan Jupyter, pero sólo la referencia controla explícitamente su construcción.

### Diferencia 2 — Límite de acceso e integración del notebook

Nuestro servicio monta únicamente `./notebooks` en `/home/jovyan/work` y recibe sólo `JUPYTER_TOKEN`; la referencia monta el proyecto completo (`./`) y entrega también al contenedor `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`. Nuestro enfoque expone menos archivos y no entrega la contraseña de la base al proceso de Jupyter, lo que reduce superficie de acceso, pero obliga a proporcionar por otra vía la configuración necesaria para que un notebook se conecte. La referencia facilita conexiones inmediatas y permite trabajar con todos los archivos del proyecto, a costa de mayor exposición del árbol local y de las credenciales. Son materialmente diferentes en aislamiento y experiencia de uso, aunque ambos montajes persisten el trabajo del usuario.

### Diferencia 3 — Ciclo de vida de Adminer

Nuestra implementación coloca Adminer en el perfil `dev`, por lo que el inicio normal ejecuta sólo PostgreSQL y Jupyter y Adminer requiere `docker compose --profile dev up -d`. En la referencia, Adminer no tiene perfil y se inicia siempre con el stack. El perfil reduce servicios y puertos activos cuando la interfaz web no se necesita, pero añade un comando explícito para habilitarla; la referencia ofrece acceso inmediato con una operación más simple, aunque mantiene Adminer activo en todo arranque. Las alternativas son materialmente diferentes en su topología predeterminada, aun cuando ambas proporcionan el mismo servicio al activarlo.
