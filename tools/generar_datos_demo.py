"""Genera demo-data/: datos de ejemplo INVENTADOS con el mismo formato que los de los bots reales.

Uso (desde la raíz del repositorio):
    python tools/generar_datos_demo.py

Es determinista (semilla fija): ejecutarlo dos veces produce los mismos archivos.
Ningún número de aquí corresponde a un mercado, bot o estrategia reales.
"""
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "demo-data"
AHORA = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)      # "ahora" fijo de los datos de ejemplo
INICIO = AHORA - timedelta(days=25)

# Precios base inventados (no son cotizaciones reales)
PRECIOS = {"BTC": 64000, "ETH": 3100, "SOL": 145, "XRP": 0.52, "HYPE": 24, "ZEC": 38,
           "DOGE": 0.16, "kPEPE": 0.0012, "TRUMP": 9.5, "PENGU": 0.031, "kSHIB": 0.0185}
CAMPOS_TRADE = ["id", "coin", "side", "opened_at", "closed_at", "entry_px", "exit_px", "stop_px", "target_px", "liq_px",
                "size", "notional", "leverage", "risk_usd", "hours", "fees", "funding", "pnl", "r_multiple", "reason",
                "equity_after"]
CAMPOS_BTC = [c for c in CAMPOS_TRADE if c != "coin"]
CAMPOS_BTC.insert(2, "tag")


def iso(d):
    return d.isoformat()


def escribir_json(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def escribir_csv(ruta, campos, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


def simular_libro(rng, moneda, n_trades, inicial=1000.0, prob_gana=0.4, id0=1):
    """Operaciones de una billetera: gana 2R o pierde 1R con ruido. Devuelve (trades, equity, pico, ganadas)."""
    base = PRECIOS[moneda]
    equity, pico, ganadas, trades = inicial, inicial, 0, []
    t = INICIO + timedelta(hours=rng.uniform(1, 30))
    for i in range(n_trades):
        lado = rng.choice([1, -1])
        gana = rng.random() < prob_gana
        r = rng.uniform(1.6, 2.6) if gana else -rng.uniform(0.9, 1.15)
        entrada = base * rng.uniform(0.92, 1.08)
        dist = rng.uniform(0.012, 0.03)                          # distancia del stop (fracción del precio)
        riesgo = equity * rng.uniform(0.04, 0.08)
        nocional = riesgo / dist
        tam = nocional / entrada
        horas = rng.uniform(0.5, 40)
        abre = t
        cierra = abre + timedelta(hours=horas)
        if cierra > AHORA - timedelta(hours=3):
            break
        salida = entrada * (1 + lado * dist * r)
        comision = nocional * 0.0006
        pnl = riesgo * r - comision
        equity += pnl
        pico = max(pico, equity)
        ganadas += pnl > 0
        trades.append({
            "id": id0 + i, "coin": moneda, "side": lado, "opened_at": iso(abre), "closed_at": iso(cierra),
            "entry_px": round(entrada, 8), "exit_px": round(salida, 8),
            "stop_px": round(entrada * (1 - lado * dist), 8), "target_px": round(entrada * (1 + lado * dist * 2.2), 8),
            "liq_px": round(entrada * (1 - lado * 0.5), 8), "size": round(tam, 6), "notional": round(nocional, 2),
            "leverage": round(nocional / max(equity - pnl, 1), 3), "risk_usd": round(riesgo, 2), "hours": round(horas, 3),
            "fees": round(comision, 4), "funding": round(rng.uniform(-0.6, 0.6), 4), "pnl": round(pnl, 4),
            "r_multiple": round(r, 4), "reason": "objetivo" if gana else "stop", "equity_after": round(equity, 4),
        })
        t = cierra + timedelta(hours=rng.uniform(1, 40))
    return trades, equity, pico, ganadas


def posicion_abierta(rng, moneda, equity):
    lado = rng.choice([1, -1])
    entrada = PRECIOS[moneda] * rng.uniform(0.95, 1.05)
    dist = rng.uniform(0.012, 0.03)
    riesgo = equity * 0.06
    nocional = riesgo / dist
    return {"coin": moneda, "side": lado, "entry_px": round(entrada, 8),
            "stop_px": round(entrada * (1 - lado * dist), 8), "target_px": round(entrada * (1 + lado * dist * 2.2), 8),
            "size": round(nocional / entrada, 6), "notional": round(nocional, 2),
            "leverage": round(nocional / equity, 3), "risk_usd": round(riesgo, 2),
            "liq_px": round(entrada * (1 - lado * 0.5), 8),
            "opened_at": iso(AHORA - timedelta(hours=rng.uniform(2, 40)))}


def libro_estado(rng, moneda, trades, equity, pico, ganadas, inicial=1000.0, abierta=False):
    return {"coin": moneda, "inicial": inicial, "equity": round(equity, 4), "peak": round(pico, 4),
            "realized": round(equity - inicial, 4), "n_trades": len(trades), "wins": int(ganadas),
            "halted": False, "halt_reason": "", "pos": posicion_abierta(rng, moneda, equity) if abierta else None}


def global_estado(libros, rng):
    inicial = sum(b["inicial"] for b in libros.values())
    equity = sum(b["equity"] for b in libros.values())
    abiertas = [b for b in libros.values() if b["pos"]]
    no_real = round(sum(rng.uniform(-0.03, 0.04) * b["pos"]["risk_usd"] * 6 for b in abiertas), 4)
    return {"inicial": inicial, "equity": round(equity, 4), "realized": round(equity - inicial, 4),
            "unrealized": no_real, "total": round(equity + no_real, 4),
            "pnl_pct": round((equity + no_real - inicial) / inicial * 100, 4),
            "activos": len(abiertas), "halted": sum(b["halted"] for b in libros.values())}


def bot_multimoneda(nombre, carpeta, monedas, semilla, prob_gana, n_rango):
    rng = random.Random(semilla)
    todos, libros, siguiente = [], {}, 1
    abiertas = set(rng.sample(monedas, k=2))
    for m in monedas:
        trades, eq, pico, g = simular_libro(rng, m, rng.randint(*n_rango), prob_gana=prob_gana, id0=siguiente)
        siguiente += len(trades)
        todos += trades
        libros[m] = libro_estado(rng, m, trades, eq, pico, g, abierta=m in abiertas)
    todos.sort(key=lambda t: t["closed_at"])
    escribir_csv(SALIDA / carpeta / "trades.csv", CAMPOS_TRADE, todos)
    escribir_json(SALIDA / carpeta / "state.json", {"global": global_estado(libros, rng), "books": libros, "updated": iso(AHORA)})
    print(f"  {carpeta}: {len(monedas)} billeteras, {len(todos)} operaciones")


def bot_btc():
    rng = random.Random("btc")
    trades, eq, pico, _ = simular_libro(rng, "BTC", 22, prob_gana=0.42)
    filas = [{**t, "tag": "demo"} for t in trades]
    escribir_csv(SALIDA / "journal" / "trades.csv", CAMPOS_BTC, filas)
    escribir_json(SALIDA / "journal" / "state.json", {
        "equity": round(eq, 4), "realized": round(eq - 1000, 4), "peak": round(pico, 4), "trade_id": len(trades) + 1,
        "halted": False, "halt_reason": "", "pos": None, "updated": iso(AHORA)})
    print(f"  journal: 1 billetera, {len(trades)} operaciones")


def estrategia_matriz(carpeta, titulo, intervalo, semilla, sesgo):
    rng = random.Random(semilla)
    monedas = ["BTC", "ETH", "SOL", "XRP", "HYPE", "DOGE", "kPEPE", "TRUMP"]
    libros = {}
    for m in monedas:
        n = rng.randint(3, 22)
        gan = min(n, max(0, round(rng.gauss(n * 0.4, 1.5))))
        equity = max(40.0, 1000 * (1 + rng.gauss(sesgo, 0.28)))
        pico = max(1000.0, equity) * rng.uniform(1.0, 1.25)
        libros[m] = {"coin": m, "inicial": 1000.0, "equity": round(equity, 4), "peak": round(pico, 4),
                     "realized": round(equity - 1000, 4), "n_trades": n, "wins": gan, "halted": False,
                     "halt_reason": "", "pos": posicion_abierta(rng, m, equity) if rng.random() < 0.35 else None}
    detenida = rng.choice(monedas)                                 # una billetera detenida, para mostrar ese estado
    libros[detenida].update({"halted": True, "halt_reason": "límite de pérdida alcanzado (ejemplo)", "pos": None})
    escribir_json(SALIDA / "matriz" / carpeta / "state.json", {
        "estrategia": carpeta, "cfg": {"titulo": titulo, "origen": "8 monedas", "interval": intervalo},
        "global": global_estado(libros, rng), "books": libros, "updated": iso(AHORA)})
    print(f"  matriz/{carpeta}: {len(libros)} billeteras")


def precios_csv():
    for activo in ("BTC", "ETH", "SOL", "XRP", "HYPE", "ZEC"):
        rng = random.Random("px-" + activo)
        px, filas = PRECIOS[activo], []
        for h in range(72, 0, -1):
            t = AHORA - timedelta(hours=h)
            o = px
            c = o * (1 + rng.gauss(0, 0.004))
            hi, lo = max(o, c) * (1 + abs(rng.gauss(0, 0.002))), min(o, c) * (1 - abs(rng.gauss(0, 0.002)))
            filas.append({"time": int(t.timestamp() * 1000), "open": round(o, 6), "high": round(hi, 6), "low": round(lo, 6),
                          "close": round(c, 6), "volume": round(rng.uniform(100, 9000), 4), "trades": rng.randint(300, 6000),
                          "dt": t.strftime("%Y-%m-%d %H:%M:%S+00:00")})
            px = c
        escribir_csv(SALIDA / "data" / f"{activo}_1h.csv", ["time", "open", "high", "low", "close", "volume", "trades", "dt"], filas)
    print("  data: 6 archivos de precios de ejemplo (72 velas de 1 h)")


if __name__ == "__main__":
    print("Generando datos de ejemplo en", SALIDA)
    bot_btc()
    bot_multimoneda("multi", "multi_journal", ["BTC", "ETH", "SOL", "XRP", "HYPE"], "multi", 0.40, (3, 9))
    bot_multimoneda("meme", "meme_journal", ["DOGE", "kPEPE", "TRUMP", "PENGU", "kSHIB"], "meme", 0.46, (6, 18))
    estrategia_matriz("demo-a", "Estrategia A", "15m", "a", 0.10)
    estrategia_matriz("demo-a_azar", "Estrategia A · entrada al azar", "15m", "aa", -0.25)
    estrategia_matriz("demo-b", "Estrategia B", "4h", "b", 0.02)
    estrategia_matriz("demo-b_largo", "Estrategia B · siempre largo", "4h", "bl", -0.12)
    precios_csv()
    print("Listo.")
