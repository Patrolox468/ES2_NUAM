import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calificaciones', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetalleFactor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('columna', models.PositiveSmallIntegerField()),
                ('monto', models.DecimalField(decimal_places=6, max_digits=24)),
                ('factor', models.DecimalField(decimal_places=8, max_digits=12)),
                ('calificacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='calificaciones.calificacion')),
            ],
            options={
                'ordering': ['columna'],
                'constraints': [
                    models.UniqueConstraint(fields=('calificacion', 'columna'), name='detalle_unico_por_columna'),
                    models.CheckConstraint(condition=models.Q(('columna__gte', 8), ('columna__lte', 37)), name='detalle_columna_8_a_37'),
                ],
            },
        ),
    ]
