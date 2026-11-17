"""Pruebas del plan: aislamiento entre corredoras, bitácora de crear/modificar/eliminar y carga CSV mixta."""
from django.test import TestCase
from django.urls import reverse

from bitacora.models import Registro
from calificaciones import carga
from calificaciones.models import Calificacion
from calificaciones.tests.test_carga import ENCABEZADO
from calificaciones.tests.test_vistas import VistasBase
from cuentas.models import Perfil
from cuentas.testing import crear_corredora, crear_usuario


class DosCorredorasNoVenLoDelOtroTests(VistasBase):
    """Cada corredora ve y toca solo lo suyo (RN6)."""

    def test_cada_corredora_ve_solo_sus_calificaciones(self):
        self.crear(self.analista, "SOLO-ANDINA")
        self.crear(self.ajeno, "SOLO-BOREAL")

        self.entrar(self.analista)
        lista = self.client.get(reverse("calificaciones:lista"))
        self.assertContains(lista, "SOLO-ANDINA")
        self.assertNotContains(lista, "SOLO-BOREAL")
        self.client.logout()

        self.entrar(self.ajeno)
        lista = self.client.get(reverse("calificaciones:lista"))
        self.assertContains(lista, "SOLO-BOREAL")
        self.assertNotContains(lista, "SOLO-ANDINA")

    def test_no_puede_eliminar_la_de_otra_corredora_y_queda_el_intento(self):
        ajena = self.crear(self.ajeno, "SOLO-BOREAL")
        self.entrar(self.analista)
        url = reverse("calificaciones:eliminar", args=[ajena.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url).status_code, 403)
        ajena.refresh_from_db()
        self.assertFalse(ajena.eliminada)
        intentos = Registro.objects.filter(
            operacion=Registro.Operacion.INTENTO_RECHAZADO, usuario=self.analista
        )
        self.assertEqual(intentos.count(), 2)

    def test_la_bitacora_de_una_corredora_no_muestra_a_la_otra(self):
        self.crear(self.ajeno, "SOLO-BOREAL")
        self.entrar(self.auditor)
        self.assertNotContains(self.client.get(reverse("bitacora:lista")), "SOLO-BOREAL")


class BitacoraDeCrearModificarYEliminarTests(VistasBase):
    """Cada operación del mantenedor deja su fila en la bitácora, con usuario y corredora."""

    def registros(self, operacion):
        return Registro.objects.filter(operacion=operacion)

    def test_crear_modificar_y_eliminar_dejan_su_fila(self):
        self.entrar(self.analista)

        # Crear
        self.post_formulario(instrumento="ACCION-BITACORA")
        calificacion = Calificacion.objects.get(instrumento="ACCION-BITACORA")
        ingreso = self.registros(Registro.Operacion.INGRESO).get()
        self.assertEqual(ingreso.usuario, self.analista)
        self.assertEqual(ingreso.corredora, self.andina)
        self.assertIn("ACCION-BITACORA", ingreso.registro)

        # Modificar
        self.client.post(
            reverse("calificaciones:editar", args=[calificacion.pk]),
            {"monto_8": "2000000", "monto_9": "1000000", "monto_10": "1000000", "accion": "guardar"},
        )
        modificacion = self.registros(Registro.Operacion.MODIFICACION).get()
        self.assertEqual(modificacion.usuario, self.analista)
        self.assertEqual(modificacion.corredora, self.andina)
        self.assertIn("Columna 8", modificacion.detalle)

        # Eliminar
        self.client.post(reverse("calificaciones:eliminar", args=[calificacion.pk]))
        eliminacion = self.registros(Registro.Operacion.ELIMINACION).get()
        self.assertEqual(eliminacion.usuario, self.analista)
        self.assertEqual(eliminacion.corredora, self.andina)
        calificacion.refresh_from_db()
        self.assertTrue(calificacion.eliminada)  # eliminación lógica: la fila sigue en la base

        # Las tres operaciones quedaron en la bitácora (sin contar los inicios de sesión)
        self.assertEqual(Registro.objects.exclude(operacion=Registro.Operacion.ACCESO).count(), 3)

        # Y el auditor las ve en la pantalla de bitácora
        self.client.logout()
        self.entrar(self.auditor)
        for operacion in ("INGRESO", "MODIFICACION", "ELIMINACION"):
            pantalla = self.client.get(reverse("bitacora:lista"), {"operacion": operacion})
            self.assertEqual(pantalla.context["pagina"].paginator.count, 1)

    def test_calcular_no_deja_nada_en_la_bitacora(self):
        self.entrar(self.analista)
        self.post_formulario(accion="calcular")
        self.assertEqual(Registro.objects.exclude(operacion=Registro.Operacion.ACCESO).count(), 0)


class CargaCsvNuevaExistenteEInvalidaTests(TestCase):
    """Un CSV con una fila nueva, una que ya existe y una inválida: se guardan las válidas y solo se rechaza la inválida."""

    def setUp(self):
        self.corredora = crear_corredora()
        self.analista = crear_usuario("ana", self.corredora, Perfil.Rol.ANALISTA)
        fila_existente = "2025,Acciones,INS-EXISTE,1,corredor,400000,300000,1000000"
        carga.ejecutar_carga(
            self.analista, carga.leer_csv(f"{ENCABEZADO}\n{fila_existente}\n", self.corredora), "previa.csv"
        )

    def test_guarda_la_nueva_reconoce_la_existente_y_rechaza_la_invalida(self):
        texto = "\n".join(
            [
                ENCABEZADO,
                "2025,Acciones,INS-NUEVA,1,corredor,400000,300000,1000000",   # nueva
                "2025,Acciones,INS-EXISTE,1,corredor,400000,300000,1000000",  # ya existe, igual
                "2025,Fondos Mutuos,,1,corredor,400000,300000,1000000",       # inválida: sin instrumento
            ]
        )
        filas = carga.leer_csv(texto, self.corredora)
        resultado = carga.ejecutar_carga(self.analista, filas, "mixto.csv")

        self.assertEqual(resultado.nuevas, 1)
        self.assertEqual(resultado.sin_cambios, 1)
        self.assertEqual(resultado.actualizadas, 0)
        self.assertEqual(len(resultado.rechazadas), 1)
        self.assertEqual(Calificacion.objects.count(), 2)  # la existente + la nueva
        self.assertTrue(Calificacion.objects.filter(instrumento="INS-NUEVA").exists())

    def test_la_fila_invalida_no_impide_guardar_las_validas(self):
        texto = "\n".join(
            [
                ENCABEZADO,
                "2025,Fondos Mutuos,,1,corredor,400000,300000,1000000",       # inválida primero
                "2025,Acciones,INS-NUEVA,1,corredor,400000,300000,1000000",
            ]
        )
        carga.ejecutar_carga(self.analista, carga.leer_csv(texto, self.corredora), "mixto.csv")
        self.assertTrue(Calificacion.objects.filter(instrumento="INS-NUEVA").exists())

    def test_el_resumen_queda_en_la_bitacora(self):
        texto = "\n".join(
            [
                ENCABEZADO,
                "2025,Acciones,INS-NUEVA,1,corredor,400000,300000,1000000",
                "2025,Acciones,INS-EXISTE,1,corredor,400000,300000,1000000",
                "2025,Fondos Mutuos,,1,corredor,400000,300000,1000000",
            ]
        )
        carga.ejecutar_carga(self.analista, carga.leer_csv(texto, self.corredora), "mixto.csv")
        resumen = Registro.objects.get(operacion=Registro.Operacion.CARGA_MASIVA, registro="mixto.csv")
        self.assertIn("1 nuevas", resumen.detalle)
        self.assertIn("1 rechazadas", resumen.detalle)
