"""Pruebas de la API con los datos de ejemplo de demo-data/. Ejecutar con:  pytest"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
os.environ["SIMULADOR_DIR"] = str(REPO / "demo-data")     # siempre datos de ejemplo, estén donde estén los bots
sys.path.insert(0, str(REPO / "api"))

import datos  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    """Cliente de pruebas con un archivo de carteras temporal (nunca toca api/carteras.json)."""
    monkeypatch.setattr(datos, "ARCHIVO_CARTERAS", tmp_path / "carteras.json")
    return TestClient(app)


CARTERA = {"nombre": "Prueba", "posiciones": [
    {"activo": "BTC", "cantidad": 0.05, "precio_compra": 60000, "precio_actual": 70000},
    {"activo": "AAPL", "cantidad": 2, "precio_compra": 200, "precio_actual": 230}]}


def test_inicio_indica_de_donde_salen_los_datos(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert r.json()["datos"] == "personalizado"            # SIMULADOR_DIR está definido en este archivo


def test_bots(cliente):
    bots = cliente.get("/bots").json()
    assert [b["bot"] for b in bots] == ["btc", "multi", "meme"]
    assert all(b["capital_inicial"] > 0 for b in bots)


def test_bot_ganancias_con_y_sin_filtro(cliente):
    todo = cliente.get("/bots/multi/ganancias").json()
    eth = cliente.get("/bots/multi/ganancias", params={"moneda": "eth"}).json()
    assert eth["filtro_moneda"] == "ETH"
    assert 0 < eth["operaciones_cerradas"] < todo["operaciones_cerradas"]
    assert cliente.get("/bots/multi/ganancias", params={"moneda": "ZZZ"}).status_code == 404
    assert cliente.get("/bots/inexistente/ganancias").status_code == 404


def test_operaciones_recientes_y_limite(cliente):
    ops = cliente.get("/bots/btc/operaciones", params={"limite": 3}).json()
    assert len(ops) == 3
    assert ops[0]["cerrado"] >= ops[1]["cerrado"]          # de la más nueva a la más antigua
    assert cliente.get("/bots/btc/operaciones", params={"limite": 0}).status_code == 422


def test_simulador_lista_y_detalle(cliente):
    grupos = cliente.get("/simulador").json()
    ids = [g["id"] for g in grupos]
    assert ids[:3] == ["btc", "multi", "meme"] and any(i.startswith("matriz-") for i in ids)
    assert all("billeteras" not in g for g in grupos)      # la lista no trae el detalle por moneda
    multi = cliente.get("/simulador/multi").json()
    assert multi["num_billeteras"] == len(multi["billeteras"]) == 5
    assert cliente.get("/simulador/nada").status_code == 404


def test_crud_de_carteras(cliente):
    creada = cliente.post("/carteras", json=CARTERA)
    assert creada.status_code == 201
    cid = creada.json()["id"]
    assert cliente.get(f"/carteras/{cid}/ganancias").json() == creada.json()

    nueva = {"nombre": "Cambiada", "posiciones": [{"activo": "AAPL", "cantidad": 1, "precio_compra": 100, "precio_actual": 90}]}
    actualizada = cliente.put(f"/carteras/{cid}", json=nueva)
    assert actualizada.status_code == 200
    assert actualizada.json()["nombre"] == "Cambiada" and actualizada.json()["ganancia_total"] == -10

    assert cliente.delete(f"/carteras/{cid}").status_code == 204
    assert cliente.get(f"/carteras/{cid}/ganancias").status_code == 404
    assert cliente.delete(f"/carteras/{cid}").status_code == 404


def test_ganancia_es_cantidad_por_diferencia_de_precio(cliente):
    r = cliente.post("/carteras", json=CARTERA).json()
    btc, aapl = r["posiciones"]
    assert btc["ganancia"] == 500 and aapl["ganancia"] == 60       # 0,05 × 10 000 y 2 × 30
    assert r["total_invertido"] == 3400 and r["ganancia_total"] == 560


def test_ids_de_carteras_no_se_reutilizan(cliente):
    primero = cliente.post("/carteras", json=CARTERA).json()["id"]
    cliente.delete(f"/carteras/{primero}")
    assert cliente.post("/carteras", json=CARTERA).json()["id"] == primero + 1


def test_precio_guardado_si_no_se_envia_precio_actual(cliente):
    r = cliente.post("/carteras", json={"nombre": "x", "posiciones": [{"activo": "btc", "cantidad": 1, "precio_compra": 1}]}).json()
    assert r["posiciones"][0]["fuente_precio"].startswith("data/BTC_1h.csv")


@pytest.mark.parametrize("cuerpo", [
    {"nombre": "x", "posiciones": [{"activo": "BTC", "cantidad": -1, "precio_compra": 1}]},     # cantidad negativa
    {"nombre": "x", "posiciones": []},                                                           # sin posiciones
    {"nombre": "", "posiciones": [{"activo": "BTC", "cantidad": 1, "precio_compra": 1}]},       # nombre vacío
    {"nombre": "x", "posiciones": [{"activo": "FOO", "cantidad": 1, "precio_compra": 1}]},      # activo sin precio
])
def test_datos_invalidos_responden_422(cliente, cuerpo):
    assert cliente.post("/carteras", json=cuerpo).status_code == 422
