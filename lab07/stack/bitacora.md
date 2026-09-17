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
