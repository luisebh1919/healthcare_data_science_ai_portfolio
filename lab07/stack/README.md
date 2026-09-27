# Lab 07 — Docker Compose stack

## Requisitos

- Docker con el complemento Docker Compose.

## Inicio

Desde este directorio:

```bash
cp .env.example .env
docker compose up -d
```

El inicio normal levanta PostgreSQL y Jupyter. PostgreSQL queda disponible en `localhost:5433` y Jupyter en `http://localhost:8888`; el token de acceso está definido en `.env`.

Para comprobar el estado:

```bash
docker compose ps
```

## Adminer opcional

Adminer no se inicia de forma predeterminada. Para incluirlo, se debe activar explícitamente el perfil `dev`:

```bash
docker compose --profile dev up -d
```

Adminer queda disponible en `http://localhost:8080`.

## Detener el stack

```bash
docker compose down
```

Para eliminar también los datos persistidos de PostgreSQL y repetir la inicialización desde cero:

```bash
docker compose --profile dev down -v
```
