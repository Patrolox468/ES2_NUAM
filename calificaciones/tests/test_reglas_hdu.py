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


class CasosDeBordeTests(TestCase):
    """Casos de borde del cálculo (presentación ES3, «Casos de borde»)."""

    def test_monto_en_cero_es_valido(self):
        factores, _ = services.calcular({8: D(100), 9: D(0)})
        self.assertEqual(factores[9], D("0.00000000"))

    def test_total_en_cero_no_se_puede_calcular(self):
        """Si los montos 8 a 19 suman 0 no hay división (el HDU muestra #DIV/0!)."""
        with self.assertRaises(services.ErrorValidacion) as error:
            services.calcular({8: D(0), 9: D(0), 25: D(500)})
        self.assertIn("es 0", error.exception.mensajes[0])

    def test_seis_montos_iguales_suman_mas_de_1_por_el_redondeo(self):
        """Seis montos iguales dan 0,16666667 cada uno y suman 1,00000002: no cumple."""
        _, resultado = services.calcular({c: D(500000) for c in range(8, 14)})
        self.assertEqual(resultado.suma, D("1.00000002"))
        self.assertFalse(resultado.cumple)

    def test_un_factor_mayor_que_1_se_rechaza(self):
        """El factor 25 sería 5 (500 / 100): ningún factor puede pasar de 1."""
        with self.assertRaises(services.ErrorValidacion) as error:
            services.calcular({8: D(100), 25: D(500)})
        self.assertIn("mayor que 1", error.exception.mensajes[0])

    def test_factores_34_a_37_usan_la_misma_formula(self):
        """Decisión del grupo: los factores 34 a 37 se calculan igual (monto / suma 8 a 19)."""
        factores, _ = services.calcular({8: D(100), 34: D(50), 37: D(25)})
        self.assertEqual(factores[34], D("0.50000000"))
        self.assertEqual(factores[37], D("0.25000000"))
