from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calificaciones', '0003_copiar_json_a_detalles'),
    ]

    operations = [
        migrations.RemoveField(model_name='calificacion', name='factores'),
        migrations.RemoveField(model_name='calificacion', name='montos'),
    ]
