"""Copia los montos y factores que estaban en JSON a la tabla DetalleFactor.

Se puede deshacer: la operación inversa reconstruye el JSON desde la tabla.
"""
from decimal import Decimal

from django.db import migrations


def filas_desde_json(montos, factores):
    """[(columna, monto, factor)] a partir de los dos JSON de una calificación."""
    filas = []
    for columna, texto in sorted((montos or {}).items(), key=lambda par: int(par[0])):
        factor = (factores or {}).get(columna, "0")
        filas.append((int(columna), Decimal(texto), Decimal(factor)))
    return filas


def json_desde_filas(filas):
    """({columna: monto}, {columna: factor}) en texto, a partir de [(columna, monto, factor)]."""
    montos = {str(c): format(m.normalize(), "f") for c, m, _ in filas}
    factores = {str(c): format(f, "f") for c, _, f in filas}
    return montos, factores


def copiar_a_detalles(apps, schema_editor):
    Calificacion = apps.get_model("calificaciones", "Calificacion")
    DetalleFactor = apps.get_model("calificaciones", "DetalleFactor")
    for calificacion in Calificacion.objects.all().iterator():
        DetalleFactor.objects.bulk_create(
            DetalleFactor(calificacion_id=calificacion.pk, columna=c, monto=m, factor=f)
            for c, m, f in filas_desde_json(calificacion.montos, calificacion.factores)
        )


def copiar_a_json(apps, schema_editor):
    Calificacion = apps.get_model("calificaciones", "Calificacion")
    DetalleFactor = apps.get_model("calificaciones", "DetalleFactor")
    for calificacion in Calificacion.objects.all().iterator():
        filas = [
            (d.columna, d.monto, d.factor)
            for d in DetalleFactor.objects.filter(calificacion_id=calificacion.pk).order_by("columna")
        ]
        calificacion.montos, calificacion.factores = json_desde_filas(filas)
        calificacion.save(update_fields=["montos", "factores"])


class Migration(migrations.Migration):

    dependencies = [
        ('calificaciones', '0002_detallefactor'),
    ]

    operations = [
        migrations.RunPython(copiar_a_detalles, copiar_a_json),
    ]
