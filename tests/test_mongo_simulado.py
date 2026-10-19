"""Capa documental sin servidor: la carga con la API de pymongo (contra mongomock), los índices, el BSON y el pipeline de agregación.

Se omiten si faltan pymongo/mongomock (pip install pymongo mongomock) o la base SQLite (corra scripts/run_etl.py).
mongomock es un simulador en memoria: estas pruebas verifican el código del proyecto, no el comportamiento de un servidor MongoDB real.
"""
import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from enoe import config as C, load_mongo as L  # noqa: E402

try:
    import bson  # noqa: F401  (viene con pymongo)
    import mongomock
except ImportError:  # pragma: no cover
    mongomock = None

N = 3000          # personas que se cargan en las pruebas (la carga completa tiene 190,187)


@unittest.skipUnless(mongomock is not None, "Falta pymongo/mongomock (pip install pymongo mongomock)")
@unittest.skipUnless(C.DB_PATH.exists(), "Falta data/processed/enoe_2025t4.sqlite (corra scripts/run_etl.py)")
class TestCargaMongoSimulada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli = mongomock.MongoClient()
        cls.cuentas = L.cargar_mongo(cliente=cls.cli, base="prueba", lote=1000, limite_personas=N, validar=True)
        cls.db = cls.cli["prueba"]

    def test_conteos(self):
        self.assertEqual(self.cuentas, {"entidades": 32, "metadatos": 1, "personas": N})
        for nombre, n in self.cuentas.items():
            self.assertEqual(self.db[nombre].count_documents({}), n)

    def test_la_carga_es_idempotente(self):
        L.cargar_mongo(cliente=self.cli, base="prueba", lote=1000, limite_personas=N)
        self.assertEqual(self.db.personas.count_documents({}), N)       # reemplaza, no duplica

    def test_indices(self):
        info = self.db.personas.index_information()
        self.assertTrue({"cve_ent_1", "cve_ent_1_ingreso.grupo_1", "cve_ent_1_persona.sexo_1", "ix_salarial_por_entidad"} <= set(info))
        self.assertEqual(info["ix_salarial_por_entidad"]["partialFilterExpression"], {"muestras.salarial": True})
        # MongoDB anterior a 7.3 rechaza dos índices con la misma clave que solo difieren en sus opciones (IndexOptionsConflict)
        claves = [tuple(campo for campo, _ in v["key"]) for v in info.values()]
        self.assertEqual(len(claves), len(set(claves)))

    def test_indice_unico_de_entidades(self):
        with self.assertRaises(mongomock.DuplicateKeyError):
            self.db.entidades.insert_one({"_id": 999, "cve_ent": 20})    # la clave 20 ya existe

    def test_ficha_de_entidad(self):
        ficha = self.db.entidades.find_one({"cve_ent": 20})
        self.assertEqual(ficha["entidad"], "Oaxaca")
        self.assertEqual(ficha["informalidad"]["til1_pct"], L.ficha_entidad(20)["informalidad"]["til1_pct"])   # la misma que sirve el tablero
        mas_informales = [d["entidad"] for d in self.db.entidades.find({}, {"entidad": 1}).sort("informalidad.til1_pct", -1).limit(3)]
        self.assertEqual(mas_informales, ["Oaxaca", "Guerrero", "Chiapas"])

    def test_los_documentos_son_bson_validos(self):
        gen = L.documentos_personas()
        try:
            self.assertEqual(L.validar_bson(gen, maximo=5000), 5000)
        finally:
            gen.close()
        self.assertEqual(L.validar_bson(L.documentos_entidades()), 32)
        self.assertEqual(L.validar_bson(L.documento_metadatos()), 1)
        with self.assertRaises(ValueError):
            L.validar_bson([{"_id": 1, "x": object()}])

    def test_pipeline_de_agregacion_con_las_32_entidades(self):
        gen = L.documentos_personas()
        try:
            docs = list(itertools.islice(gen, 0, None, 60))              # muestreo sistemático: salen todas las entidades
        finally:
            gen.close()
        col = mongomock.MongoClient()["prueba"]["personas"]
        col.insert_many(docs)
        motor = L.til1_por_entidad_en_motor(col)
        self.assertEqual(len(motor), 32)
        self.assertLess(L.diferencia_maxima(motor, L.til1_por_entidad_desde_documentos(docs)), 1e-9)


if __name__ == "__main__":
    unittest.main()
