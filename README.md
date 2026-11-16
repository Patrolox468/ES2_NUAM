# ES2_NUAM – Calificaciones tributarias

Prototipo Django para ingresar, calcular y consultar calificaciones tributarias de
corredoras de bolsa. Cada corredora ve solo lo suyo y toda operación queda en una
bitácora que no se puede modificar ni borrar.

## Requisitos

- Python 3.10 o superior
- pip
- Git

## Instalación

```bash
git clone https://github.com/Patrolox468/ES2_NUAM.git
cd ES2_NUAM

# Entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .venv\Scripts\Activate.ps1

# Dependencias (Django 5.1)
pip install -r requirements.txt

# Base de datos (SQLite, se crea sola como db.sqlite3)
python manage.py migrate
```

## Variables de entorno

Son opcionales: sin ellas el sistema corre en modo desarrollo. El archivo
`.env.example` muestra los nombres y valores posibles. Django no lee `.env`
automáticamente, así que se cargan en la terminal antes de iniciar:

```bash
export DJANGO_SECRET_KEY="una-clave-larga-y-aleatoria"
export DJANGO_DEBUG=1
export FACTORES_MODO_REDONDEO=redondear
# Windows (PowerShell): $env:DJANGO_DEBUG = "1"
```

| Variable | Valores | Para qué sirve |
|---|---|---|
| `DJANGO_SECRET_KEY` | texto largo | Clave secreta de Django. Cambiarla fuera de desarrollo. |
| `DJANGO_DEBUG` | `1` (desarrollo) u otro valor | Con un valor distinto de `1` las cookies pasan a ser solo HTTPS. |
| `FACTORES_MODO_REDONDEO` | `redondear` o `truncar` | `redondear` es medio hacia arriba (lo que pide el HDU). |

## Datos de demostración

```bash
python manage.py crear_demo
```

Crea dos corredoras (Andina y Boreal), usuarios de cada perfil y cuatro
calificaciones de ejemplo. Solo se puede ejecutar una vez. **Solo para desarrollo:
las contraseñas son públicas.**

## Usuarios de prueba

Contraseña de todos: `Demo-nuam-2026`

| Usuario | Corredora | Perfil |
|---|---|---|
| `admin.andina` | Corredora Andina S.A. | Administrador |
| `analista.andina` | Corredora Andina S.A. | Analista |
| `auditor.andina` | Corredora Andina S.A. | Auditor |
| `analista.boreal` | Corredora Boreal Ltda. | Analista |

## Correr el sistema

```bash
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/> e iniciar sesión con alguno de los usuarios de arriba.
La sesión se cierra tras 30 minutos sin uso.

## Correr las pruebas

```bash
python manage.py test
```

Todas deben pasar antes de abrir un pull request.

## Decisiones del caso

- **Llave de la calificación:** corredora + ejercicio + mercado + instrumento + secuencia.
  Guardar de nuevo la misma llave actualiza en vez de duplicar.
- **Regla de la suma:** la suma de los factores de las columnas **8 a 16** no puede
  superar 1. Si la supera, el guardado se bloquea y se explica el motivo.
- **Carga masiva (CSV):** se guardan las filas válidas y se rechazan solo las
  inválidas, indicando fila y motivo. La vista previa no guarda nada.
- **Eliminación:** es lógica; el registro se conserva y queda en la bitácora.
- **Bitácora:** solo se agregan registros; no se pueden modificar ni borrar.
- **Aislamiento:** cada corredora ve solo sus calificaciones; un intento de ver la de
  otra queda en la bitácora.
- **Cálculo:** usa `Decimal` (nunca `float`) con 8 decimales.
- **Factores 34 a 37:** pendiente de confirmar con el cliente (ver
  `docs/reglas_calculo.md` cuando esté listo).
