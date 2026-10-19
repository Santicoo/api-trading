"""Lectura (solo lectura) de los datos del proyecto de trading simulado.

Este módulo NUNCA escribe en los journals de los bots: solo los lee.
Lo único que la API guarda es su propio archivo `carteras.json`.
"""
import csv
import json
import os
from pathlib import Path

_API = Path(__file__).resolve().parent
_CARPETAS_DATOS = ("journal", "multi_journal", "meme_journal", "matriz")


def _resolver_raiz() -> tuple[Path, str]:
    """Carpeta que contiene journal/, multi_journal/, meme_journal/, matriz/ y data/, y de dónde sale.

    1. Variable de entorno SIMULADOR_DIR (datos propios).
    2. La carpeta padre de api/, si ya trae los journals (el proyecto original).
    3. demo-data/ junto a api/ (repositorio independiente: datos de ejemplo inventados).
    """
    propia = os.environ.get("SIMULADOR_DIR")
    if propia:
        return Path(propia).expanduser().resolve(), "personalizado"
    padre = _API.parent
    if any((padre / c).exists() for c in _CARPETAS_DATOS):
        return padre, "proyecto"
    return padre / "demo-data", "demo"


RAIZ, MODO = _resolver_raiz()                      # MODO: "personalizado" | "proyecto" | "demo"
DATA = RAIZ / "data"
ARCHIVO_CARTERAS = _API / "carteras.json"

# Los 3 bots de paper trading y dónde vive su journal
BOTS = {
    "btc":   {"carpeta": RAIZ / "journal",       "descripcion": "Bot de una sola moneda (BTC)"},
    "multi": {"carpeta": RAIZ / "multi_journal", "descripcion": "Bot multi-moneda (BTC, ETH, SOL, XRP, HYPE)"},
    "meme":  {"carpeta": RAIZ / "meme_journal",  "descripcion": "Bot de memecoins (DOGE, kPEPE, TRUMP...)"},
}


def _leer_json(ruta: Path) -> dict:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def resumen_bot(nombre: str) -> dict:
    """Capital inicial, equity actual y ganancia total de un bot."""
    estado = _leer_json(BOTS[nombre]["carpeta"] / "state.json")
    if "global" in estado:                       # bots multi y meme
        g = estado["global"]
        inicial, equity, realizado = g["inicial"], g["equity"], g["realized"]
        no_realizado = g.get("unrealized", 0.0)
        actualizado = estado.get("updated")
    else:                                        # bot btc (estado plano)
        # El journal del bot BTC no guarda el capital inicial: se deduce (equity = inicial + realizado).
        equity, realizado = estado["equity"], estado["realized"]
        inicial = equity - realizado
        no_realizado = 0.0
        actualizado = estado.get("updated")
    total = equity + no_realizado
    return {
        "bot": nombre,
        "descripcion": BOTS[nombre]["descripcion"],
        "capital_inicial": round(inicial, 2),
        "equity": round(equity, 2),
        "ganancia_realizada": round(realizado, 2),
        "ganancia_no_realizada": round(no_realizado, 2),
        "ganancia_total": round(total - inicial, 2),
        "rentabilidad_pct": round((total - inicial) / inicial * 100, 2),
        "actualizado": actualizado,
    }


def _posicion(pos: dict | None) -> dict | None:
    if not pos:
        return None
    return {
        "lado": "largo" if pos.get("side") == 1 else "corto",
        "precio_entrada": pos.get("entry_px"),
        "stop": pos.get("stop_px"),
        "objetivo": pos.get("target_px"),
        "apalancamiento": round(pos["leverage"], 1) if pos.get("leverage") else None,
        "nocional": round(pos["notional"], 2) if pos.get("notional") else None,
        "abierta_desde": pos.get("opened_at"),
    }


def _libro(moneda: str, b: dict) -> dict:
    # `equity` de los bots solo suma operaciones cerradas; el no realizado únicamente existe
    # agregado por grupo (state["global"]["unrealized"]), por eso aquí no hay ganancia no realizada.
    inicial, equity = b["inicial"], b["equity"]
    n, wins = b.get("n_trades", 0), b.get("wins", 0)
    peak = b.get("peak") or equity
    return {
        "moneda": moneda,
        "capital_inicial": round(inicial, 2),
        "equity": round(equity, 2),
        "ganancia": round(equity - inicial, 2),
        "rentabilidad_pct": round((equity - inicial) / inicial * 100, 2),
        "operaciones": n,
        "ganadas": wins,
        "tasa_acierto_pct": round(wins / n * 100, 1) if n else 0.0,
        "caida_desde_maximo_pct": round((peak - equity) / peak * 100, 1) if peak else 0.0,
        "detenida": bool(b.get("halted")),
        "motivo_detencion": b.get("halt_reason") or None,
        "posicion": _posicion(b.get("pos")),
    }


def _grupo(id_: str, titulo: str, descripcion: str, tipo: str, libros: list[dict],
           no_realizado: float, actualizado: str | None) -> dict:
    inicial = sum(l["capital_inicial"] for l in libros)
    equity = sum(l["equity"] for l in libros)
    total = equity + no_realizado
    return {
        "id": id_, "titulo": titulo, "descripcion": descripcion, "tipo": tipo,
        "capital_inicial": round(inicial, 2),
        "equity": round(equity, 2),
        "ganancia_realizada": round(equity - inicial, 2),
        "ganancia_no_realizada": round(no_realizado, 2),
        "ganancia_total": round(total - inicial, 2),
        "rentabilidad_pct": round((total - inicial) / inicial * 100, 2) if inicial else 0.0,
        "num_billeteras": len(libros),
        "posiciones_abiertas": sum(1 for l in libros if l["posicion"]),
        "billeteras": libros,
        "actualizado": actualizado,
    }


def ids_matriz() -> list[str]:
    return sorted(p.parent.name for p in (RAIZ / "matriz").glob("*/state.json")
                  if "books" in _leer_json(p))


def leer_grupo(id_: str) -> dict:
    """Un grupo = un bot (btc/multi/meme) o una estrategia de la matriz (matriz-don15...)."""
    if id_ == "btc":
        estado = _leer_json(BOTS["btc"]["carpeta"] / "state.json")
        trades = trades_bot("btc")
        libro = _libro("BTC", {
            "inicial": estado["equity"] - estado["realized"], "equity": estado["equity"],
            "peak": estado.get("peak"), "halted": estado.get("halted"),
            "halt_reason": estado.get("halt_reason"), "pos": estado.get("pos"),
            "n_trades": len(trades), "wins": sum(t["pnl"] > 0 for t in trades),
        })
        return _grupo("btc", "Bot BTC", BOTS["btc"]["descripcion"], "bot", [libro], 0.0,
                      estado.get("updated"))
    if id_ in ("multi", "meme"):
        estado = _leer_json(BOTS[id_]["carpeta"] / "state.json")
        libros = [_libro(m, b) for m, b in estado["books"].items()]
        return _grupo(id_, f"Bot {id_.upper()}", BOTS[id_]["descripcion"], "bot", libros,
                      estado["global"].get("unrealized", 0.0), estado.get("updated"))
    if id_.startswith("matriz-") and id_[7:] in ids_matriz():
        estado = _leer_json(RAIZ / "matriz" / id_[7:] / "state.json")
        cfg = estado.get("cfg", {})
        libros = [_libro(m, b) for m, b in estado["books"].items()]
        desc = f"{cfg.get('interval', '')} · origen {cfg.get('origen', '')}".strip(" ·")
        return _grupo(id_, cfg.get("titulo", id_[7:]), desc, "matriz", libros,
                      estado["global"].get("unrealized", 0.0), estado.get("updated"))
    raise KeyError(id_)


def todos_los_grupos() -> list[dict]:
    ids = ["btc", "multi", "meme"] + [f"matriz-{m}" for m in ids_matriz()]
    return [leer_grupo(i) for i in ids]


def trades_bot(nombre: str) -> list[dict]:
    """Operaciones cerradas del bot (desde trades.csv)."""
    trades = []
    with open(BOTS[nombre]["carpeta"] / "trades.csv", encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            trades.append({
                "id": int(fila["id"]),
                "moneda": fila.get("coin") or "BTC",
                "lado": "largo" if int(fila["side"]) == 1 else "corto",
                "abierto": fila["opened_at"],
                "cerrado": fila["closed_at"],
                "precio_entrada": float(fila["entry_px"]),
                "precio_salida": float(fila["exit_px"]),
                "comisiones": round(float(fila["fees"]), 4),
                "pnl": round(float(fila["pnl"]), 2),
                "motivo_cierre": fila["reason"],
            })
    return trades


def ultimo_precio(activo: str) -> tuple[float, str] | None:
    """Último cierre de la vela de 1h guardada en data/<ACTIVO>_1h.csv."""
    ruta = DATA / f"{activo.upper()}_1h.csv"
    if not ruta.exists():
        return None
    with open(ruta, encoding="utf-8") as f:
        ultima = f.readlines()[-1].strip().split(",")
    # columnas: time,open,high,low,close,volume,trades,dt
    return float(ultima[4]), ultima[7]


def activos_con_precio() -> list[str]:
    return sorted(p.name.removesuffix("_1h.csv") for p in DATA.glob("*_1h.csv"))


# ---------- almacenamiento propio de la API (carteras) ----------

def cargar_carteras() -> dict:
    # Sin bloqueo de archivo: dos escrituras simultáneas pueden pisarse (ver ADR-002).
    # Es aceptable para un solo usuario; no usar tal cual con varios clientes concurrentes.
    if not ARCHIVO_CARTERAS.exists():
        return {"siguiente_id": 1, "carteras": {}}
    return _leer_json(ARCHIVO_CARTERAS)


def guardar_carteras(db: dict) -> None:
    with open(ARCHIVO_CARTERAS, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
