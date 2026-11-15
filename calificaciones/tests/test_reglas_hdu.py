"""Pruebas del plan de la ES3 sobre el cálculo y las reglas del HDU.

P01: ejemplo resuelto del HDU (hoja 3.2).
P02: suma de factores exactamente 1 -> se acepta.
P03: suma de factores mayor que 1 -> se rechaza con mensaje.
"""
from decimal import Decimal as D

from django.test import TestCase

from calificaciones import services
from calificaciones.models import Calificacion, Mercado, Origen
from cuentas.models import Perfil
from cuentas.testing import crear_corredora, crear_usuario

# Montos del ejemplo del HDU, hoja 3.2 (la suma de las columnas 8 a 19 es 368.745.318)
MONTOS_HDU = {
    8: D(192770580),
    9: D(64161878),
    10: D(0),
    11: D(111812860),
    25: D(71298705),
    30: D(15837333),
}


class ReglasHduTests(TestCase):
    def setUp(self):
        corredora = crear_corredora()
        self.analista = crear_usuario("ana", corredora, Perfil.Rol.ANALISTA)

    def guardar(self, montos, monto_base=None):
        return services.guardar_calificacion(
            self.analista,
            ejercicio=2025,
            mercado=Mercado.ACCIONES,
            instrumento="ACCION-HDU",
            secuencia=1,
            origen=Origen.CORREDOR,
            montos=montos,
            monto_base=monto_base,
        )

    def test_p01_ejemplo_del_hdu(self):
        """P01 (flujo ideal): los montos del HDU dan los factores del HDU."""
        factores, resultado = services.calcular(MONTOS_HDU)

        self.assertEqual(factores[8], D("0.52277431"))
        self.assertEqual(factores[9], D("0.17400052"))
        self.assertEqual(factores[10], D("0.00000000"))
        self.assertEqual(factores[11], D("0.30322517"))
        self.assertEqual(factores[25], D("0.19335488"))
        self.assertEqual(factores[30], D("0.04294924"))

        # La regla solo suma el rango 8 a 16, no todos los factores
        self.assertEqual(resultado.suma, D("1.00000000"))
        self.assertTrue(resultado.cumple)

    def test_p02_suma_exactamente_1_se_acepta(self):
        """P02 (borde): factores 8 y 9 de 0,5 cada uno suman 1,00000000 y se graban."""
        guardado = self.guardar({8: D(500000), 9: D(500000)})

        self.assertEqual(guardado.estado, "creada")
        self.assertEqual(guardado.calificacion.suma_factores, D("1.00000000"))

    def test_p03_suma_mayor_que_1_se_rechaza(self):
        """P03 (error): con un monto base menor, los factores suman 1,2 y no se graba."""
        with self.assertRaises(services.ErrorValidacion) as error:
            self.guardar({8: D(600000), 9: D(600000)}, monto_base=D(1000000))

        self.assertIn("mayor que 1", error.exception.mensajes[0])
        self.assertEqual(Calificacion.objects.count(), 0)
