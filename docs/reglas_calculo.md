# Reglas del cálculo de factores

Decisiones del Grupo 1 sobre el cálculo y los puntos que el HDU deja abiertos.

## Cálculo

| Regla | Qué hace el sistema | Dónde está |
|---|---|---|
| Fórmula | Factor = monto ÷ suma de los montos de las columnas 8 a 19 (HDU, hoja 3) | `calificaciones/services.py`, función `calcular` |
| Decimales | 8 decimales, redondeando (medio hacia arriba), igual que el ejemplo del HDU (hoja 3.2) | `config/settings.py`, `FACTORES_MODO_REDONDEO` |
| Factor máximo | Ningún factor puede ser mayor que 1; si pasa, se muestra un error y no se graba | `calificaciones/services.py`, función `calcular` |
| Total en cero | Si los montos 8 a 19 suman 0, no se puede calcular y se muestra un error | `calificaciones/services.py`, función `calcular` |

## Decisiones sobre lo que el HDU no define

| Tema | Decisión |
|---|---|
| Rango de la suma de factores | **8 al 16**. La suma de los factores 8 a 16 debe ser menor o igual a 1. Exactamente 1,00000000 se acepta. |
| Factores 34 a 37 | Se calculan con la misma fórmula (monto ÷ suma 8 a 19), a la espera de que el cliente defina otra regla. |
| CSV con filas inválidas | Se guardan las filas válidas y se rechazan solo las inválidas, indicando el número de fila y el motivo. |
| Llave de una calificación | Corredora + ejercicio + mercado + instrumento + secuencia. Si la llave existe se actualiza; si no, se crea. |
| Redondeo y suma | La suma se valida con los factores ya redondeados. Por eso seis montos iguales (0,16666667 × 6 = 1,00000002) no cumplen la regla. |

## Ejemplo del HDU (hoja 3.2)

La suma de los montos de las columnas 8 a 19 es 368.745.318.

| Factor | Monto | Factor esperado | Factor del sistema |
|---|---|---|---|
| 8 | 192.770.580 | 0,52277431 | 0,52277431 |
| 9 | 64.161.878 | 0,17400052 | 0,17400052 |
| 10 | 0 | 0,00000000 | 0,00000000 |
| 11 | 111.812.860 | 0,30322517 | 0,30322517 |
| 25 | 71.298.705 | 0,19335488 | 0,19335488 |
| 30 | 15.837.333 | 0,04294924 | 0,04294924 |

## Pruebas

Las pruebas de estas reglas están en `calificaciones/tests/test_reglas_hdu.py`:

```
python manage.py test calificaciones.tests.test_reglas_hdu
```

| ID | Tipo | Qué se prueba | Resultado esperado |
|---|---|---|---|
| P01 | Flujo ideal | Montos del ejemplo del HDU | Los factores de la tabla anterior; suma 8 a 16 = 1,00000000 |
| P02 | Borde | Suma de factores exactamente 1 | Se acepta y se graba |
| P03 | Error | Suma de factores mayor que 1 | Se rechaza con el mensaje «mayor que 1» y no se graba |
| B01 | Borde | Un monto en cero | Su factor es 0,00000000 |
| B02 | Error | Montos 8 a 19 suman 0 | Se rechaza: no se puede dividir por 0 |
| B03 | Borde | Seis montos iguales | Suma 1,00000002: no cumple la regla |
| B04 | Error | Un factor mayor que 1 | Se rechaza con el mensaje «mayor que 1» |
| B05 | Borde | Montos en las columnas 34 y 37 | Se calculan con la misma fórmula |
