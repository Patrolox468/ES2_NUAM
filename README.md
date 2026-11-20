# Mantenedor de Calificaciones Tributarias de NUAM

Mantenedor de Calificaciones Tributarias para corredores de Nuam. Proyecto Integrado (TIHI43), ES3.

- **Grupo:** Grupo 3
- **Integrantes:** Miguel Cabrera, Pablo Rojas, Natalie Alveal, Patricio Lagos

## Qué hace

Reemplaza el proceso manual de cálculo de calificaciones tributarias a partir de declaraciones juradas (DJ 1948) y certificados en PDF. El flujo ideal permite iniciar sesión por corredora y rol, crear o cargar calificaciones (de forma manual o masiva vía CSV), calcular automáticamente los factores del 8 al 37 con 8 decimales a partir de los montos, validar la regla de suma máxima, guardar los registros de forma aislada por corredora y dejar respaldo en una bitácora inalterable.

## Requisitos

- **Sistema operativo:** Windows 11
- **Lenguaje y versión:** Python 3.12
- **Framework:** Django 5.2.19
- **Base de datos y versión:** SQLite 3.49.1
- **Otras herramientas:** Git y navegador web actualizado.

## Instalación paso a paso

1. **Clonar el repositorio:**
git clone https://github.com/Patrolox468/ES2_NUAM.git
2. Entrar a la carpeta: `cd ES2_NUAM`
3. Crear el entorno e instalar las dependencias: `python -m venv .venv` 
`.\.venv\Scripts\Activate.ps1`
`pip install -r requirements.txt`
4. Crear la base de datos: `python manage.py migrate`
5. Configurar las variables: copiar `.env.example` a `.env` y completar los valores. No subir contraseñas ni llaves reales al repositorio.
DJANGO_SECRET_KEY=una-clave-larga-y-aleatoria
DJANGO_DEBUG=1
FACTORES_MODO_REDONDEO=redondear
6. Cargar los datos de ejemplo (opcional): `python manage.py crear_demo`


## Cómo ejecutar

`python manage.py runserver`

Abrir http://127.0.0.1:8000/ en el navegador. Usuario y clave de demostración: 

| Usuario | Corredora | Perfil |
|---|---|---|
| `admin.andina` | Corredora Andina S.A. | Administrador |
| `analista.andina` | Corredora Andina S.A. | Analista |
| `auditor.andina` | Corredora Andina S.A. | Auditor |
| `analista.boreal` | Corredora Boreal Ltda. | Analista |

Contraseña de todos: `Demo-nuam-2026`

## Cómo ejecutar las pruebas

`python manage.py test`

El informe de pruebas está en https://inacap-ti-262.dreamshaper.com/modules/unidad-3-propuesta-de-asesoria-9jl1/pruebas-uzii

## Estructura del repositorio

- `ES2_NUAM`: 

- bitacora: lógica, modelos y vistas de la bitácora.
- calificaciones: cálculos, carga de calificaciones, vistas y pruebas.
- cuentas: usuarios, permisos y comando para crear datos de demostración.
- config: configuración y rutas principales de Django.
- templates: plantillas HTML de la aplicación.
- static: archivos estáticos, como CSS.
- docs: documentación de reglas del cálculo.
- db.sqlite3: archivo de base de datos SQLite.
- manage.py: comandos de administración de Django.
- README.md: instrucciones y descripción del proyecto.
- requirements.txt: dependencias de Python.
- .env.example: ejemplo de variables de entorno.

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
- **Factores 34 a 37:** Se calculan con la misma fórmula general (monto ÷ suma columnas 8 a 19)

## Problemas frecuentes

- PowerShell bloquea la activación del entorno virtual (Activate.ps1): Ejecutar Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser y volver a intentar.

## Equipo

Contribuciones por integrante: 

Miguel Cabrera: Cálculo, reglas y pruebas matemáticas

Patricio Lagos: Modelo de datos (montos y factores 8–37)

Pablo Rojas: Guía de estilo e interfaces

Natalie Alveal: Instalación, README y plan de pruebas

https://github.com/Patrolox468/ES2_NUAM
