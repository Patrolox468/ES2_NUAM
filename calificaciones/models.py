from django.conf import settings
from django.db import models


class Mercado(models.TextChoices):
    ACCIONES = "ACCIONES", "Acciones"
    CFI = "CFI", "Cuotas de fondos de inversión"
    FONDOS_MUTUOS = "FONDOS_MUTUOS", "Fondos mutuos"


class Origen(models.TextChoices):
    CORREDOR = "CORREDOR", "Dato del corredor"
    BOLSA = "BOLSA", "Dato base de Bolsa"


class Calificacion(models.Model):
    """Calificación tributaria de un instrumento, de una corredora, en un ejercicio.

    La llave única (RN4, supuesto por confirmar) es: corredora + ejercicio +
    mercado + instrumento + secuencia de evento. Cada monto y cada factor (columnas
    8 a 37) se guarda como una fila de ``DetalleFactor``, con ocho decimales exactos.
    """

    corredora = models.ForeignKey(
        "cuentas.Corredora", on_delete=models.PROTECT, related_name="calificaciones"
    )
    ejercicio = models.PositiveSmallIntegerField()
    mercado = models.CharField(max_length=20, choices=Mercado.choices)
    instrumento = models.CharField(max_length=60)
    secuencia = models.PositiveIntegerField()
    origen = models.CharField(max_length=10, choices=Origen.choices, default=Origen.CORREDOR)

    monto_base = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    suma_factores = models.DecimalField(max_digits=12, decimal_places=8)

    # Eliminación lógica (RN3): el registro se conserva pero deja de mostrarse.
    eliminada = models.BooleanField(default=False, db_index=True)

    creada = models.DateTimeField(auto_now_add=True)
    modificada = models.DateTimeField(auto_now=True)
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    modificada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-ejercicio", "mercado", "instrumento", "secuencia"]
        constraints = [
            models.UniqueConstraint(
                fields=["corredora", "ejercicio", "mercado", "instrumento", "secuencia"],
                name="llave_unica_calificacion",
            )
        ]

    def __str__(self):
        return f"{self.ejercicio} · {self.get_mercado_display()} · {self.instrumento} · sec. {self.secuencia}"

    @property
    def montos_decimal(self):
        """{columna: Decimal} sin ceros sobrantes (500000.000000 se lee como 500000)."""
        return {d.columna: d.monto.normalize() for d in self.detalles.all()}

    @property
    def montos(self):
        """{"8": "500000", ...} como texto, para mostrar el formulario y la bitácora."""
        return {str(d.columna): format(d.monto.normalize(), "f") for d in self.detalles.all()}

    @property
    def factores(self):
        """{"8": "0.50000000", ...} como texto, con los ocho decimales."""
        return {str(d.columna): format(d.factor, "f") for d in self.detalles.all()}

    @property
    def etiqueta(self):
        """Cómo se nombra el registro en la bitácora y los mensajes."""
        return f"{self.instrumento} · sec. {self.secuencia}"


class DetalleFactor(models.Model):
    """Monto y factor de una columna (8 a 37) de una calificación.

    Una fila por columna informada. La llave única (calificación, columna) evita
    duplicados y su índice acelera la lectura de los detalles de una calificación.
    La corredora no se repite aquí: se obtiene siempre desde la calificación
    (``calificacion__corredora``), así los datos de cada corredora quedan separados.
    """

    calificacion = models.ForeignKey(Calificacion, on_delete=models.CASCADE, related_name="detalles")
    columna = models.PositiveSmallIntegerField()
    monto = models.DecimalField(max_digits=24, decimal_places=6)
    factor = models.DecimalField(max_digits=12, decimal_places=8)

    class Meta:
        ordering = ["columna"]
        constraints = [
            models.UniqueConstraint(fields=["calificacion", "columna"], name="detalle_unico_por_columna"),
            models.CheckConstraint(
                condition=models.Q(columna__gte=8, columna__lte=37), name="detalle_columna_8_a_37"
            ),
        ]

    def __str__(self):
        return f"{self.calificacion} · col. {self.columna}"
