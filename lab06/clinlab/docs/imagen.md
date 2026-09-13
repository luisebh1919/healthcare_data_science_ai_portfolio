# Mediciones de la imagen Docker

## Actividad 2 — Dockerfile con orden incorrecto

En esta actividad se construyó primero un Dockerfile con un orden intencionalmente ineficiente: el código del proyecto se copia antes de instalar las dependencias.

Dockerfile utilizado:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY . .

RUN uv sync --frozen --extra dev

CMD ["/app/.venv/bin/pytest"]
```

### Build limpio

Comando utilizado:

```bash
time docker build --no-cache -t clinlab:bad-order .
```

Resultados:

- Tiempo real total: 12.262 s
- Contexto de build enviado: 15.92 MB
- Tiempo de `RUN pip install --no-cache-dir uv`: 1.8 s
- Tiempo de `RUN uv sync --frozen --extra dev`: 5.8 s

### Rebuild después de cambiar una línea de código

Se añadió temporalmente una línea de comentario a:

```text
src/clinlab/data_quality.py
```

Después se reconstruyó la imagen sin utilizar `--no-cache`:

```bash
time docker build -t clinlab:bad-order .
```

Resultados:

- Tiempo real total: 7.052 s
- `WORKDIR /app`: CACHED
- `RUN pip install --no-cache-dir uv`: CACHED
- `COPY . .`: se volvió a ejecutar
- `RUN uv sync --frozen --extra dev`: se volvió a ejecutar y tardó 5.9 s

### Interpretación

El cambio de una sola línea en el código modificó el contenido utilizado por la instrucción:

```dockerfile
COPY . .
```

Docker reutilizó las capas anteriores, pero invalidó esa capa y todas las capas posteriores.

Como la instalación de dependencias mediante:

```dockerfile
RUN uv sync --frozen --extra dev
```

estaba después de `COPY . .`, Docker tuvo que repetirla aunque las dependencias del proyecto no habían cambiado.

Esto demuestra que colocar el código antes de instalar las dependencias genera rebuilds innecesariamente lentos. En la siguiente actividad se cambiará el orden para aprovechar mejor la caché de capas de Docker.
