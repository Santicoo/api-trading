"""API de ganancias de carteras — FastAPI.

Ejecutar (desde la carpeta que contiene api/):
    python api/main.py
Documentación interactiva: http://127.0.0.1:8000/docs
"""
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import datos

app = FastAPI(
    title="API Ganancias de Carteras",
    description=(
        "Consulta las ganancias de los bots de trading simulado (solo lectura) y gestiona carteras "
        "propias (crear, consultar, reemplazar, eliminar).\n\n"
        "**Tags:** *Bots* y *Simulador* leen los journals de los bots; *Carteras* es el CRUD propio de la API.\n\n"
        "**Importante:** los precios de las carteras salen de `data/<ACTIVO>_1h.csv`, que es una "
        "foto histórica, no un precio en vivo (ver `fuente_precio` en cada respuesta). "
        "Las decisiones de diseño están en `api/docs/decisions/`."
    ),
    version="1.2.0",
)

RESP_404 = {404: {"description": "El bot, grupo o cartera no existe"}}
RESP_422 = {422: {"description": "Cuerpo inválido, o activo sin precio guardado y sin `precio_actual`"}}


# ---------------------------- modelos ----------------------------

class Posicion(BaseModel):
    activo: str = Field(..., examples=["BTC"], description="Símbolo: BTC, ETH, SOL, XRP, HYPE, ZEC")
    cantidad: float = Field(..., gt=0, examples=[0.05])
    precio_compra: float = Field(..., gt=0, examples=[60000])
    precio_actual: float | None = Field(
        None, gt=0, description="Opcional. Si no se envía se usa el último precio guardado en data/")


class CarteraEntrada(BaseModel):
    nombre: str = Field(..., min_length=1, examples=["Mi cartera cripto"])
    posiciones: list[Posicion] = Field(..., min_length=1)


# ---------------------------- utilidades ----------------------------

def _validar_bot(bot: str) -> str:
    bot = bot.lower()
    if bot not in datos.BOTS:
        raise HTTPException(404, f"Bot '{bot}' no existe. Opciones: {list(datos.BOTS)}")
    return bot


def _validar_activos(posiciones: list[Posicion]) -> None:
    for p in posiciones:
        if p.precio_actual is None and datos.ultimo_precio(p.activo) is None:
            raise HTTPException(
                422, f"No hay precio para '{p.activo}'. Envía 'precio_actual' o usa uno de "
                     f"{datos.activos_con_precio()}")


def _calcular_ganancias(cartera: dict) -> dict:
    detalle, invertido, valor = [], 0.0, 0.0
    for p in cartera["posiciones"]:
        if p.get("precio_actual"):
            precio, fuente = p["precio_actual"], "enviado por el usuario"
        else:
            precio, fecha = datos.ultimo_precio(p["activo"])
            fuente = f"data/{p['activo'].upper()}_1h.csv ({fecha})"
        costo = p["cantidad"] * p["precio_compra"]
        actual = p["cantidad"] * precio
        invertido += costo
        valor += actual
        detalle.append({
            "activo": p["activo"].upper(),
            "cantidad": p["cantidad"],
            "precio_compra": p["precio_compra"],
            "precio_actual": precio,
            "fuente_precio": fuente,
            "invertido": round(costo, 2),
            "valor_actual": round(actual, 2),
            "ganancia": round(actual - costo, 2),
            "rentabilidad_pct": round((actual - costo) / costo * 100, 2),
        })
    return {
        "id": cartera["id"],
        "nombre": cartera["nombre"],
        "total_invertido": round(invertido, 2),
        "valor_actual": round(valor, 2),
        "ganancia_total": round(valor - invertido, 2),
        "rentabilidad_pct": round((valor - invertido) / invertido * 100, 2),
        "posiciones": detalle,
    }


def _buscar_cartera(db: dict, cartera_id: int) -> dict:
    cartera = db["carteras"].get(str(cartera_id))
    if cartera is None:
        raise HTTPException(404, f"Cartera {cartera_id} no encontrada")
    return cartera


# ---------------------------- endpoints: bots (GET) ----------------------------

@app.get("/", tags=["General"])
def inicio():
    return {"mensaje": "API de ganancias de carteras", "docs": "/docs", "app": "/app/", "datos": datos.MODO}


@app.get("/bots", tags=["Bots"], summary="Resumen de ganancias de todos los bots")
def listar_bots():
    """Capital inicial, equity, ganancia realizada / no realizada y rentabilidad de `btc`, `multi` y `meme`."""
    return [datos.resumen_bot(b) for b in datos.BOTS]


@app.get("/bots/{bot}/ganancias", tags=["Bots"], summary="Ganancias detalladas de un bot", responses=RESP_404)
def ganancias_bot(bot: str, moneda: str | None = Query(None, description="Filtra por moneda, ej. ETH")):
    """Estadísticas de las operaciones **cerradas** del bot (tasa de acierto, PnL, comisiones, por moneda).

    `resumen` siempre describe el bot completo; con `moneda` solo cambian las estadísticas de operaciones.
    """
    bot = _validar_bot(bot)
    trades = datos.trades_bot(bot)
    if moneda:
        trades = [t for t in trades if t["moneda"].upper() == moneda.upper()]
        if not trades:
            raise HTTPException(404, f"El bot '{bot}' no tiene operaciones en {moneda.upper()}")

    por_moneda: dict[str, dict] = {}
    for t in trades:
        m = por_moneda.setdefault(t["moneda"], {"operaciones": 0, "ganadas": 0, "pnl": 0.0})
        m["operaciones"] += 1
        m["ganadas"] += t["pnl"] > 0
        m["pnl"] = round(m["pnl"] + t["pnl"], 2)

    ganadas = [t for t in trades if t["pnl"] > 0]
    return {
        "resumen": datos.resumen_bot(bot),
        "filtro_moneda": moneda.upper() if moneda else None,
        "operaciones_cerradas": len(trades),
        "ganadas": len(ganadas),
        "perdidas": len(trades) - len(ganadas),
        "tasa_acierto_pct": round(len(ganadas) / len(trades) * 100, 2) if trades else 0,
        "pnl_operaciones": round(sum(t["pnl"] for t in trades), 2),
        "comisiones_pagadas": round(sum(t["comisiones"] for t in trades), 2),
        "mejor_operacion": max(trades, key=lambda t: t["pnl"], default=None),
        "peor_operacion": min(trades, key=lambda t: t["pnl"], default=None),
        "por_moneda": por_moneda,
    }


@app.get("/bots/{bot}/operaciones", tags=["Bots"], summary="Últimas operaciones cerradas de un bot",
         responses=RESP_404)
def operaciones_bot(bot: str, limite: int = Query(10, ge=1, le=500)):
    """Las `limite` operaciones más recientes, de la más nueva a la más antigua."""
    bot = _validar_bot(bot)
    return datos.trades_bot(bot)[-limite:][::-1]


# ---------------------------- endpoints: billeteras del simulador (GET) ----------------------------

@app.get("/simulador", tags=["Simulador"],
         summary="Grupos de billeteras del simulador (bots y matriz), sin el detalle por moneda")
def listar_simulador():
    grupos = datos.todos_los_grupos()
    return [{k: v for k, v in g.items() if k != "billeteras"} for g in grupos]


@app.get("/simulador/{grupo}", tags=["Simulador"], responses=RESP_404,
         summary="Billeteras (una por moneda) de un bot o de una estrategia de la matriz")
def detalle_simulador(grupo: str):
    """`grupo` es `btc`, `multi`, `meme` o `matriz-<estrategia>` (ej. `matriz-don4h`); `/simulador` lista los ids.

    El `equity` de cada billetera incluye solo operaciones cerradas. La ganancia de posiciones abiertas
    (`ganancia_no_realizada`) solo se conoce a nivel de grupo, no por moneda.
    """
    try:
        return datos.leer_grupo(grupo.lower())
    except KeyError:
        raise HTTPException(404, f"Grupo '{grupo}' no existe. Prueba con /simulador para ver los ids")


# ---------------------------- endpoints: carteras (CRUD) ----------------------------

@app.get("/carteras", tags=["Carteras"], summary="Listar carteras con sus ganancias")
def listar_carteras():
    db = datos.cargar_carteras()
    return [_calcular_ganancias(c) for c in db["carteras"].values()]


@app.get("/carteras/{cartera_id}/ganancias", tags=["Carteras"], summary="Ganancias de una cartera",
         responses=RESP_404)
def ganancias_cartera(cartera_id: int):
    return _calcular_ganancias(_buscar_cartera(datos.cargar_carteras(), cartera_id))


@app.post("/carteras", tags=["Carteras"], status_code=status.HTTP_201_CREATED,
          summary="Crear una cartera", responses=RESP_422)
def crear_cartera(entrada: CarteraEntrada):
    """Crea la cartera y devuelve sus ganancias calculadas. Responde `201`; el `id` es secuencial y no se reutiliza."""
    _validar_activos(entrada.posiciones)
    db = datos.cargar_carteras()
    nuevo_id = db["siguiente_id"]
    db["carteras"][str(nuevo_id)] = {
        "id": nuevo_id,
        "nombre": entrada.nombre,
        "posiciones": [p.model_dump() for p in entrada.posiciones],
        "creada": datetime.now(timezone.utc).isoformat(),
    }
    db["siguiente_id"] = nuevo_id + 1
    datos.guardar_carteras(db)
    return _calcular_ganancias(db["carteras"][str(nuevo_id)])


@app.put("/carteras/{cartera_id}", tags=["Carteras"], summary="Reemplazar una cartera",
         responses={**RESP_404, **RESP_422})
def actualizar_cartera(cartera_id: int, entrada: CarteraEntrada):
    """Reemplaza por completo el nombre y las posiciones (no es una actualización parcial)."""
    _validar_activos(entrada.posiciones)
    db = datos.cargar_carteras()
    cartera = _buscar_cartera(db, cartera_id)
    cartera["nombre"] = entrada.nombre
    cartera["posiciones"] = [p.model_dump() for p in entrada.posiciones]
    cartera["actualizada"] = datetime.now(timezone.utc).isoformat()
    datos.guardar_carteras(db)
    return _calcular_ganancias(cartera)


@app.delete("/carteras/{cartera_id}", tags=["Carteras"], status_code=status.HTTP_204_NO_CONTENT,
            summary="Eliminar una cartera", responses=RESP_404)
def eliminar_cartera(cartera_id: int):
    db = datos.cargar_carteras()
    _buscar_cartera(db, cartera_id)
    del db["carteras"][str(cartera_id)]
    datos.guardar_carteras(db)


# Interfaz web (simula una app de billeteras) que consume esta misma API
app.mount("/app", StaticFiles(directory=datos.Path(__file__).parent / "static", html=True), name="app")


if __name__ == "__main__":
    import os
    import uvicorn
    carpeta = str(datos.Path(__file__).parent)
    uvicorn.run("main:app", host="127.0.0.1", port=int(os.environ.get("PORT", 8000)),
                reload=True, reload_dirs=[carpeta], app_dir=carpeta)
