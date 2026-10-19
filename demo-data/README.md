# demo-data

Datos de ejemplo **inventados** para poder ejecutar la API sin tener ningún bot.
Ningún número, fecha, operación o estrategia de esta carpeta corresponde a un mercado, bot o cuenta reales.

La API usa esta carpeta automáticamente cuando no encuentra otros datos (ver
[ADR-003](../api/docs/decisions/ADR-003-journals-de-bots-solo-lectura.md)). Su estructura es la que espera la API:

| Ruta | Contenido |
|---|---|
| `journal/state.json`, `journal/trades.csv` | Bot `btc`: una sola billetera (estado plano) |
| `multi_journal/state.json`, `multi_journal/trades.csv` | Bot `multi`: 5 billeteras |
| `meme_journal/state.json`, `meme_journal/trades.csv` | Bot `meme`: 5 billeteras |
| `matriz/<estrategia>/state.json` | Cuatro estrategias de ejemplo, con 8 billeteras cada una |
| `data/<ACTIVO>_1h.csv` | Velas de 1 hora inventadas de BTC, ETH, SOL, XRP, HYPE y ZEC |

## Regenerarlos

```bash
python tools/generar_datos_demo.py
```

El generador usa una semilla fija: siempre produce los mismos archivos.

## Usar tus propios datos

Apunta la API a una carpeta con esa misma estructura:

```bash
# Linux / macOS
SIMULADOR_DIR=/ruta/a/tus/datos python api/main.py
```

```powershell
# Windows (PowerShell)
$env:SIMULADOR_DIR = "C:\ruta\a\tus\datos"; python api/main.py
```
