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

`postgresql+psycopg2://clinlab:dev_password@postgres:5432/clinical`

Resultado:

`('clinical', 'clinlab')`

Dentro de la red privada de Docker Compose se usa `postgres` porque es el nombre DNS del servicio, y `5432` porque es el puerto interno de PostgreSQL.

### Desde la máquina host

Cadena de conexión:

`postgresql://clinlab:dev_password@localhost:5433/clinical`

La consulta:

`SELECT current_database(), current_user;`

devolvió:

`clinical | clinlab`

Desde el host se usa `localhost:5433` porque el puerto 5433 de la computadora está publicado hacia el puerto 5432 del contenedor.

Ambas conexiones llegan a la misma base de datos; cambia únicamente la ruta utilizada para alcanzarla.
