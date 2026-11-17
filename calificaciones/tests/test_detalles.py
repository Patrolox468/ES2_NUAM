"""Modelo de datos: una fila de DetalleFactor por cada columna informada (8 a 37)."""
import importlib
from decimal import Decimal as D

from django.conf import settings
from django.db import IntegrityError, transaction
from django.test import TestCase

from calificaciones import services
from calificaciones.models import Calificacion, DetalleFactor, Mercado, Origen
from cuentas.testing import crear_corredora, crear_usuario


class DetalleFactorTests(TestCase):
    def setUp(self):
        self.corredora = crear_corredora()
        self.usuario = crear_usuario("ana", self.corredora)

    def guardar(self, montos, usuario=None, **cambios):
        datos = dict(
            ejercicio=2025,
            mercado=Mercado.ACCIONES,
            instrumento="ACCION-ALFA",
            secuencia=1,
            origen=Origen.CORREDOR,
            montos=montos,
        )
        datos.update(cambios)
        return services.guardar_calificacion(usuario or self.usuario, **datos).calificacion

    def test_grabar_deja_una_fila_por_columna_con_su_factor(self):
        montos = {8: D(1500000), 9: D(900000), 10: D(600000), 11: D(1000000), 12: D(2000000), 19: D(500000)}
        calificacion = self.guardar(montos)
        # Los factores esperados son los que entrega el cálculo vigente (así la prueba
        # sigue valiendo si cambia la fórmula o el redondeo).
        esperados, _ = services.calcular(montos)

        detalles = list(calificacion.detalles.all())
        self.assertEqual([d.columna for d in detalles], sorted(montos))
        for detalle in detalles:
            self.assertEqual(detalle.monto, montos[detalle.columna])
            self.assertEqual(detalle.factor, esperados[detalle.columna])
        desde, hasta = settings.COLUMNAS_SUMA_REGLA
        suma_regla = sum(d.factor for d in detalles if desde <= d.columna <= hasta)
        self.assertEqual(suma_regla, calificacion.suma_factores)

    def test_los_factores_se_guardan_con_ocho_decimales(self):
        calificacion = self.guardar({8: D(1), 9: D(2)})
        factores = {d.columna: format(d.factor, "f") for d in calificacion.detalles.all()}
        self.assertTrue(all(len(f.split(".")[1]) == 8 for f in factores.values()))

    def test_acepta_hasta_la_columna_37(self):
        calificacion = self.guardar({8: D(1), 37: D(1)})
        self.assertEqual([d.columna for d in calificacion.detalles.all()], [8, 37])

    def test_modificar_reemplaza_los_detalles_sin_duplicar(self):
        self.guardar({8: D(100), 9: D(100), 10: D(100)})
        calificacion = self.guardar({8: D(300), 9: D(100)})  # sale la columna 10
        self.assertEqual(DetalleFactor.objects.count(), 2)
        self.assertEqual(calificacion.montos_decimal, {8: D(300), 9: D(100)})

    def test_repetir_el_mismo_guardado_no_duplica_filas(self):
        for _ in range(3):
            self.guardar({8: D(100), 9: D(100)})
        self.assertEqual(DetalleFactor.objects.count(), 2)

    def test_las_propiedades_montos_y_factores_se_leen_desde_la_tabla(self):
        calificacion = self.guardar({8: D(1000000), 9: D(1000000), 10: D(1000000)})
        self.assertEqual(calificacion.montos, {"8": "1000000", "9": "1000000", "10": "1000000"})
        self.assertEqual(set(calificacion.factores), {"8", "9", "10"})

    def test_la_base_no_acepta_columna_repetida(self):
        calificacion = self.guardar({8: D(1)})
        with self.assertRaises(IntegrityError), transaction.atomic():
            DetalleFactor.objects.create(calificacion=calificacion, columna=8, monto=D(1), factor=D(1))

    def test_la_base_no_acepta_columnas_fuera_de_8_a_37(self):
        calificacion = self.guardar({8: D(1)})
        for columna in (7, 38):
            with self.subTest(columna=columna):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    DetalleFactor.objects.create(
                        calificacion=calificacion, columna=columna, monto=D(1), factor=D(1)
                    )

    def test_eliminar_en_forma_logica_conserva_los_detalles(self):
        calificacion = self.guardar({8: D(1), 9: D(1)})
        services.eliminar_logico(self.usuario, calificacion)
        self.assertEqual(DetalleFactor.objects.filter(calificacion=calificacion).count(), 2)

    def test_los_detalles_de_cada_corredora_quedan_separados(self):
        otra = crear_corredora("Corredora Boreal Ltda.")
        otro = crear_usuario("luis", otra)
        self.guardar({8: D(1), 9: D(1)})
        self.guardar({8: D(5)}, usuario=otro)  # misma llave, otra corredora
        propios = DetalleFactor.objects.filter(calificacion__corredora=self.corredora)
        ajenos = DetalleFactor.objects.filter(calificacion__corredora=otra)
        self.assertEqual(propios.count(), 2)
        self.assertEqual(ajenos.count(), 1)
        self.assertEqual(Calificacion.objects.count(), 2)


class CopiaDesdeJsonTests(TestCase):
    """La migración 0003 convierte el JSON antiguo en filas de detalle y viceversa."""

    def setUp(self):
        self.migracion = importlib.import_module("calificaciones.migrations.0003_copiar_json_a_detalles")

    def test_del_json_a_filas(self):
        filas = self.migracion.filas_desde_json(
            {"9": "250000", "8": "750000"}, {"8": "0.75000000", "9": "0.25000000"}
        )
        self.assertEqual(filas, [(8, D("750000"), D("0.75000000")), (9, D("250000"), D("0.25000000"))])

    def test_de_filas_al_json_sin_perder_decimales(self):
        montos, factores = self.migracion.json_desde_filas(
            [(8, D("750000.000000"), D("0.75000000")), (9, D("250000.500000"), D("0.25000000"))]
        )
        self.assertEqual(montos, {"8": "750000", "9": "250000.5"})
        self.assertEqual(factores, {"8": "0.75000000", "9": "0.25000000"})

    def test_json_vacio(self):
        self.assertEqual(self.migracion.filas_desde_json({}, {}), [])
        self.assertEqual(self.migracion.filas_desde_json(None, None), [])
