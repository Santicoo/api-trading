# Referencia de la API

Documentación detallada de cada endpoint. Para instalar y ejecutar, mira el [README](../README.md).
La misma información, siempre al día, está en la documentación interactiva: `http://127.0.0.1:8000/docs`.

**Contenido:** [Endpoints](#endpoints) · [Crear una cartera](#crear-una-cartera-post) ·
[Billeteras del simulador](#billeteras-del-simulador-get) · [Errores](#errores) · [Precios](#precios-de-las-carteras) ·
[Formato de los datos del simulador](#formato-de-los-datos-del-simulador) · [Limitaciones](#limitaciones-conocidas)

## Endpoints

| Método | Ruta | Respuesta | Qué hace |
|---|---|---|---|
| GET | `/` | 200 | Mensaje de bienvenida y origen de los datos (`demo`, `proyecto` o `personalizado`) |
| GET | `/bots` | 200 | Capital inicial, equity y ganancia de los bots `btc`, `multi` y `meme` |
| GET | `/bots/{bot}/ganancias?moneda=ETH` | 200, 404 | Operaciones cerradas del bot: tasa de acierto, PnL, comisiones, por moneda |
| GET | `/bots/{bot}/operaciones?limite=10` | 200, 404, 422 | Últimas operaciones cerradas (`limite` entre 1 y 500) |
| GET | `/simulador` | 200 | Todos los grupos del simulador (bots y estrategias de la matriz), sin detalle por moneda |
| GET | `/simulador/{grupo}` | 200, 404 | Una billetera por moneda de un bot o estrategia (`btc`, `multi`, `meme`, `matriz-<estrategia>`) |
| GET | `/carteras` | 200 | Todas las carteras propias con sus ganancias |
| GET | `/carteras/{id}/ganancias` | 200, 404 | Ganancia de una cartera, por posición |
| **POST** | `/carteras` | **201**, 422 | Crea una cartera |
| **PUT** | `/carteras/{id}` | **200**, 404, 422 | Reemplaza por completo nombre y posiciones |
| **DELETE** | `/carteras/{id}` | **204**, 404 | Elimina la cartera (sin cuerpo en la respuesta) |

Los ids de los grupos de la matriz son `matriz-` más el nombre de su carpeta; `GET /simulador` los lista todos.

## Crear una cartera (POST)

Cuerpo:

```json
{
  "nombre": "Mi cartera",
  "posiciones": [
    { "activo": "BTC",  "cantidad": 0.05, "precio_compra": 60000 },
    { "activo": "AAPL", "cantidad": 2,    "precio_compra": 200, "precio_actual": 230 }
  ]
}
```

| Campo | Regla |
|---|---|
| `nombre` | Texto, no vacío |
| `posiciones` | Lista con al menos una posición |
| `posiciones[].activo` | Símbolo. Sin `precio_actual`, debe tener un archivo `data/<ACTIVO>_1h.csv` (BTC, ETH, SOL, XRP, HYPE, ZEC en los datos de ejemplo) |
| `posiciones[].cantidad` | Número mayor que 0 |
| `posiciones[].precio_compra` | Número mayor que 0 |
| `posiciones[].precio_actual` | Opcional, mayor que 0. Sobrescribe el precio guardado |

La ganancia de cada posición es `cantidad × (precio_actual − precio_compra)`. Respuesta `201 Created`:

```json
{
  "id": 1,
  "nombre": "Mi cartera",
  "total_invertido": 3400.0,
  "valor_actual": 3560.96,
  "ganancia_total": 160.96,
  "rentabilidad_pct": 4.73,
  "posiciones": [
    {
      "activo": "BTC", "cantidad": 0.05, "precio_compra": 60000.0, "precio_actual": 62019.152696,
      "fuente_precio": "data/BTC_1h.csv (2026-10-15 11:00:00+00:00)",
      "invertido": 3000.0, "valor_actual": 3100.96, "ganancia": 100.96, "rentabilidad_pct": 3.37
    },
    {
      "activo": "AAPL", "cantidad": 2.0, "precio_compra": 200.0, "precio_actual": 230.0,
      "fuente_precio": "enviado por el usuario",
      "invertido": 400.0, "valor_actual": 460.0, "ganancia": 60.0, "rentabilidad_pct": 15.0
    }
  ]
}
```

`PUT /carteras/{id}` usa el mismo cuerpo y la misma respuesta, pero con `200 OK`. Reemplaza todo: las posiciones
que no envíes se pierden. El `id` es secuencial y **no se reutiliza** tras un `DELETE`.

## Billeteras del simulador (GET)

`GET /simulador/multi` (recortado a una billetera):

```json
{
  "id": "multi", "titulo": "Bot MULTI", "tipo": "bot",
  "capital_inicial": 5000.0, "equity": 5423.71,
  "ganancia_realizada": 423.71, "ganancia_no_realizada": -9.11,
  "ganancia_total": 414.6, "rentabilidad_pct": 8.29,
  "num_billeteras": 5, "posiciones_abiertas": 2,
  "billeteras": [
    {
      "moneda": "XRP", "capital_inicial": 1000.0, "equity": 1189.88, "ganancia": 189.88,
      "rentabilidad_pct": 18.99, "operaciones": 6, "ganadas": 3, "tasa_acierto_pct": 50.0,
      "caida_desde_maximo_pct": 0.0, "detenida": false, "motivo_detencion": null,
      "posicion": {
        "lado": "largo", "precio_entrada": 0.49625975, "stop": 0.48492294, "objetivo": 0.52120074,
        "apalancamiento": 2.6, "nocional": 3125.16, "abierta_desde": "2026-10-14T19:12:37.128685+00:00"
      }
    }
  ]
}
```

- Cada **billetera** es el libro de una moneda dentro de un bot o estrategia, con su propio capital.
- `equity` de la billetera cuenta solo operaciones cerradas. La `ganancia_no_realizada` (posiciones abiertas)
  solo se conoce para el grupo completo.
- `posicion` es `null` cuando la billetera no tiene una operación abierta.
- `GET /bots` devuelve el resumen de cada bot (`capital_inicial`, `equity`, `ganancia_realizada`,
  `ganancia_no_realizada`, `ganancia_total`, `rentabilidad_pct`, `actualizado`).

## Errores

| Código | Cuándo | Cuerpo |
|---|---|---|
| 404 | El bot, grupo o cartera no existe | `{"detail": "Cartera 99 no encontrada"}` |
| 422 | Un campo no cumple las reglas | `{"detail": [{"loc": ["body","posiciones",0,"cantidad"], "msg": "Input should be greater than 0", ...}]}` |
| 422 | Activo sin precio guardado y sin `precio_actual` | `{"detail": "No hay precio para 'FOO'. Envía 'precio_actual' o usa uno de ['BTC', 'ETH', ...]"}` |

El `detail` de los errores 422 de validación es una lista (formato estándar de FastAPI); el de los demás errores es un texto.

## Precios de las carteras

El precio actual de un activo es el cierre de la última vela de 1 hora de `data/<ACTIVO>_1h.csv`. No es un precio
en vivo: `fuente_precio` indica de dónde salió y la fecha de esa vela. Para activos sin CSV (por ejemplo acciones)
hay que enviar `precio_actual`. En este repositorio, los CSV de `demo-data/data/` traen precios **inventados**.
Más detalle en [ADR-004](../api/docs/decisions/ADR-004-precios-desde-csv-locales.md).

## Formato de los datos del simulador

Para usar tus propios datos, apunta `SIMULADOR_DIR` a una carpeta con esta estructura (puedes copiar la de
[`demo-data/`](../demo-data)). La API **solo lee** estos archivos.

| Ruta | Qué debe contener |
|---|---|
| `journal/state.json` | Bot `btc` (estado plano): `equity`, `realized` y, opcionalmente, `peak`, `halted`, `halt_reason`, `pos`, `updated`. El capital inicial se deduce como `equity − realized` |
| `journal/trades.csv` | Operaciones cerradas del bot `btc` |
| `multi_journal/`, `meme_journal/` | `state.json` con `global` (`inicial`, `equity`, `realized`, `unrealized`), `books` (una billetera por moneda) y `updated`; más `trades.csv` con la columna `coin` |
| `matriz/<estrategia>/state.json` | `cfg` (`titulo`, `interval`, `origen`), `global` y `books` |
| `data/<ACTIVO>_1h.csv` | Velas con las columnas `time,open,high,low,close,volume,trades,dt` (se usa `close` de la última fila y su `dt`) |

Cada billetera de `books` tiene `coin`, `inicial`, `equity`, `peak`, `n_trades`, `wins`, `halted`, `halt_reason` y
`pos`. Una posición abierta (`pos`) trae `side` (1 largo, −1 corto), `entry_px`, `stop_px`, `target_px`, `leverage`,
`notional` y `opened_at`. Las columnas de `trades.csv` son `id`, `coin`, `side`, `opened_at`, `closed_at`,
`entry_px`, `exit_px`, `fees`, `pnl` y `reason` (más otras que la API ignora).

## Limitaciones conocidas

- **Sin bloqueo de archivo** en `carteras.json`: dos escrituras simultáneas pueden pisarse. Pensado para un
  solo usuario ([ADR-002](../api/docs/decisions/ADR-002-carteras-en-archivo-json.md)).
- **Sin autenticación**: escucha solo en `127.0.0.1`, así que solo es accesible desde tu equipo.
- **Las posiciones abiertas no se valoran por moneda**: su ganancia solo aparece sumada por grupo.
- **Los precios de las carteras no son en vivo.**
