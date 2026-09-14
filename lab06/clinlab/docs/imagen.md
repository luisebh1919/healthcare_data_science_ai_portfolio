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


## Actividad 3 — Orden correcto de capas

Se reorganizó el Dockerfile para copiar primero los archivos que definen las dependencias:

```dockerfile
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --extra dev --no-install-project
```

Después se copia el código fuente:

```dockerfile
COPY src ./src
COPY tests ./tests
```

De esta forma, cambiar una línea de código no invalida la capa donde se instalan las dependencias.

### Resultados

| Escenario | Orden malo | Orden bueno |
|---|---:|---:|
| Build limpio | 12.262 s | 6.800 s |
| Rebuild tras cambiar código | 7.052 s | 1.034 s |

En el rebuild con orden correcto, Docker reutilizó la caché de:

```text
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --extra dev --no-install-project
```

Por tanto, `uv sync` no volvió a ejecutarse.

El rebuild pasó de 7.052 s a 1.034 s, una reducción aproximada del 85.3%.

Esto demuestra que colocar las dependencias antes del código fuente permite aprovechar correctamente la caché de capas de Docker.


## Actividad 4 — Multi-stage build

La imagen de una sola etapa `clinlab:good-order` tenía un tamaño de:

```text
395 MB
```

Se creó un Dockerfile multi-stage con una etapa `builder` y una etapa final `runtime`.

La etapa final copia únicamente el entorno virtual y los archivos necesarios para ejecutar las pruebas.

### Resultado

| Imagen | Tamaño |
|---|---:|
| Single-stage | 395 MB |
| Multi-stage | 330 MB |

La reducción fue aproximadamente del 16.5%.

La imagen final queda por debajo del objetivo de 500 MB.

### Hallazgo durante la construcción

Inicialmente el paquete se instaló en modo editable:

```dockerfile
RUN uv pip install --python .venv/bin/python --no-deps -e .
```

La imagen se construyó correctamente, pero al ejecutar pytest apareció:

```text
ModuleNotFoundError: No module named 'clinlab'
```

El entorno virtual contenía una referencia al código fuente del builder, pero ese árbol no existía en la etapa runtime.

Se cambió a una instalación normal:

```dockerfile
RUN uv pip install --python .venv/bin/python --no-deps .
```

Después del cambio:

```text
32 passed in 0.68 s
```

Esto demuestra que una imagen que construye correctamente no necesariamente contiene todo lo necesario para ejecutar la aplicación en runtime.


## Actividad 5 — `.dockerignore` y contexto de build

Para medir el efecto de `.dockerignore` se realizó un experimento controlado con un Dockerfile temporal que utilizaba:

```dockerfile
COPY . .
```

### Resultado

| Escenario | Contexto enviado |
|---|---:|
| Sin `.dockerignore` | 15.60 MB |
| Con `.dockerignore` | 986 B |

La reducción del contexto fue superior al 99.99%.

El archivo `.dockerignore` excluye cachés, entornos virtuales, archivos de cobertura, notebooks, documentación, secretos `.env` y otros archivos que no deben formar parte de la imagen.

El Dockerfile final además usa instrucciones `COPY` específicas, por lo que su contexto efectivo fue solamente:

```text
612 B
```

Después de agregar `.dockerignore`, la imagen siguió construyéndose correctamente y la suite dentro del contenedor produjo:

```text
32 passed in 0.69 s
```



## Experimento Alpine

Se creó temporalmente una variante multi-stage basada en `python:3.11-alpine` y se construyó desde cero con:

```bash
docker build --pull --no-cache --progress=plain \
  -f Dockerfile.alpine-experiment \
  -t clinlab:alpine-experiment .
```

En esta máquina el build **sí terminó correctamente**. La imagen ejecutó Python 3.11.16 sobre musl libc 1.2.6, importó NumPy 2.4.6 y pandas 3.0.5, y no contenía GCC (`gcc-not-installed`). El lockfile incluía wheels `cp311-cp311-musllinux_1_2_x86_64` para ambas dependencias, por lo que no fue necesario compilarlas desde código fuente. La construcción local de `clinlab` sí generó su wheel, pero es un paquete Python puro.

Resultados medidos:

| Imagen experimental | Tamaño | Pruebas |
|---|---:|---:|
| `clinlab:alpine-experiment` | 269 MB (269,254,226 bytes) | 32 passed in 0.26 s |

Alpine usa musl libc, mientras que muchas distribuciones binarias del ecosistema científico se publican principalmente como wheels manylinux para glibc. En proyectos o versiones sin wheels musllinux compatibles, NumPy o pandas pueden requerir compiladores, cabeceras y bibliotecas del sistema, haciendo el build más lento y complejo. En las versiones bloqueadas actuales sí hubo wheels compatibles. Aunque la imagen experimental fue 61 MB menor que la imagen Debian slim, se mantiene `python:3.11-slim` como base final por su compatibilidad más amplia y por ser la variante ya validada durante el laboratorio. El Dockerfile temporal fue retirado después de medirlo.


## Actividad 6 — Usuario no-root

La etapa runtime crea el usuario y grupo dedicados `clinlab` con UID/GID 10001 y termina con `USER clinlab`.

Verificación real:

```bash
docker run --rm clinlab:0.1.0 id
```

```text
uid=10001(clinlab) gid=10001(clinlab) groups=10001(clinlab)
```

El entorno virtual, las pruebas y `/app` pertenecen a `clinlab`. Dar propiedad sobre `/app` fue necesario para que pytest pudiera crear `.pytest_cache` sin advertencias de permisos. El usuario no tiene directorio home ni shell de login.

Ejecutar como usuario no-root reduce el impacto de una vulnerabilidad: un proceso comprometido no obtiene automáticamente privilegios administrativos dentro del contenedor. Esto no elimina otros controles necesarios, pero aplica el principio de mínimo privilegio.


## Actividad 8 — Escaneo de vulnerabilidades

Docker Scout no estaba disponible (`docker: unknown command: docker scout`). Se utilizó la imagen oficial `aquasec/trivy:latest`, sin instalar software globalmente, contra la imagen final `clinlab:0.1.0`.

El escaneo del 13 de septiembre de 2026 (14 de septiembre en el registro UTC de Trivy) detectó Debian 13.6 y produjo:

| Severidad | Cantidad |
|---|---:|
| CRITICAL | 3 |
| HIGH | 55 |

Trivy reportó 56 hallazgos del sistema operativo y 2 de paquetes Python; en conjunto son 58 hallazgos HIGH/CRITICAL. Los paquetes Python instalados por el entorno virtual de `clinlab`, incluidos NumPy y pandas, no tuvieron hallazgos; los dos hallazgos Python procedieron de metadatos vendorizados en las herramientas de empaquetado de la imagen base.

### Hallazgos y decisiones

| Paquete | CVE | Severidad | Instalada | Corregida | Decisión |
|---|---|---|---|---|---|
| `perl-base` | CVE-2026-13221 | CRITICAL | 5.40.1-6 | 5.40.1-6+deb13u1 | Reconstruir cuando la imagen oficial `python:3.11-slim` incorpore la actualización Debian; para una publicación inmediata, evaluar actualizar paquetes del runtime y volver a escanear. |
| `gzip` | CVE-2026-41992 | HIGH | 1.13-1 | 1.13-1+deb13u1 | Aplicar la actualización Debian mediante una nueva imagen base/rebuild; no se atribuye explotabilidad a `clinlab` sin análisis adicional. |
| `jaraco.context` (metadatos vendorizados) | CVE-2026-23949 | HIGH | 5.3.0 | 6.1.0 | Actualizar las herramientas de empaquetado de la base o eliminarlas del runtime si dejan de ser necesarias; volver a escanear después. |
| `bsdutils` | CVE-2026-78408 | HIGH | 1:2.41.5-0+deb13u1 | Sin fix reportado | Aceptar temporalmente y vigilar Debian; el runtime no concede privilegios root a la aplicación, pero eso no demuestra que el hallazgo sea inexplotable. |

Los otros dos hallazgos CRITICAL fueron CVE-2026-42496 y CVE-2026-8376 en `perl-base`, ambos con la misma versión corregida `5.40.1-6+deb13u1`. Los conteos representan el estado de la base y de la base de datos de Trivy en el momento del escaneo; pueden cambiar al reconstruir o actualizar el scanner.


## Actividad 9 — Pruebas dentro del contenedor

La imagen final se verificó formalmente con:

```bash
docker run --rm clinlab:0.1.0 pytest
```

Resultado real:

```text
platform linux -- Python 3.11.16, pytest-9.1.1, pluggy-1.6.0
collected 32 items
tests/test_data_quality.py ................................ [100%]
32 passed in 0.70 s
```

La imagen final mide 330 MB (329,545,088 bytes) y su ID al verificarla fue `sha256:019054a90d9ed4d2a6c027af7d85b010d01d104c01a18e5db448cf4fb24b125b`.


## Actividad 10 — GitHub Actions y GHCR

El remoto del repositorio es `https://github.com/luisebh1919/healthcare_data_science_ai_portfolio.git`, por lo que el nombre previsto para publicación es:

```text
ghcr.io/luisebh1919/clinlab
```

El workflow debe vivir en `.github/workflows/` de la raíz del repositorio y usar `lab06/clinlab` como contexto de Docker. Debe ejecutar las pruebas antes de publicar y producir las etiquetas `0.1.0` y el SHA del commit usando `GITHUB_TOKEN`, con permisos mínimos `contents: read` y `packages: write`.

Se creó `.github/workflows/lab06-ghcr.yml` en la raíz del repositorio. El workflow usa `actions/checkout@v7`, `docker/setup-buildx-action@v4`, `docker/login-action@v4`, `docker/metadata-action@v6` y `docker/build-push-action@v7`. Primero construye `clinlab:ci-test` y ejecuta `docker run --rm clinlab:ci-test pytest`; solamente si esa prueba pasa inicia sesión en GHCR y publica `ghcr.io/luisebh1919/clinlab` con las etiquetas `0.1.0` y el SHA completo del commit.

El YAML se analizó correctamente, `actionlint` terminó sin hallazgos y se validaron mediante aserciones el trigger `push` a `main`, los permisos, las acciones, el contexto, las etiquetas y el orden prueba→publicación. Al momento de documentarlo, el workflow todavía no había corrido y GHCR todavía no se había verificado; por tanto, la publicación permanece **PENDIENTE DE EJECUCIÓN EN GITHUB ACTIONS**.

Puede ser necesario configurar la visibilidad del paquete en GitHub y permitir que el repositorio administre el paquete desde la sección de Packages. El workflow usa `GITHUB_TOKEN`; no deben agregarse tokens personales al YAML.


## Verificación por otra persona

**PENDING MANUAL VERIFICATION**

Después de una publicación exitosa y de configurar la visibilidad apropiada, otra persona debe ejecutar:

```bash
docker run --rm ghcr.io/luisebh1919/clinlab:0.1.0 pytest
```

El resultado de terceros no se considera completado hasta recibir evidencia de esa ejecución.



## Actividad 7 — Secretos en capas de Docker

Se realizó una demostración controlada usando un secreto falso:

```text
FAKE_API_KEY=super-fake-secret-12345
```

El archivo `.env` se copió dentro de una imagen y posteriormente se eliminó en una capa siguiente:

```dockerfile
COPY .env /app/.env
RUN rm /app/.env
```

Al ejecutar el contenedor final, el archivo ya no estaba presente en `/app`.

Sin embargo, `docker history --no-trunc` mostró que una capa anterior había ejecutado:

```text
COPY .env /app/.env
```

La imagen se exportó con `docker save`, se extrajeron sus capas y el secreto pudo recuperarse desde:

```text
extracted/blobs/sha256/b24e41d5a5beda7e8abe6196b3686afeec4d27121bae59865d2580a460a5f32d
```

El contenido recuperado fue:

```text
FAKE_API_KEY=super-fake-secret-12345
```

Esto demuestra que eliminar un secreto en una capa posterior no lo elimina de las capas anteriores de la imagen.

La práctica correcta es no copiar secretos durante el build. Los secretos deben proporcionarse en tiempo de ejecución mediante variables de entorno, mecanismos de secretos del entorno de despliegue o soluciones equivalentes.

El `.dockerignore` final del proyecto excluye `.env`, evitando que este tipo de archivo entre accidentalmente al contexto de construcción.

