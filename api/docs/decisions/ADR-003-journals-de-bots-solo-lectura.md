# ADR-003: Leer los journals de los bots en solo lectura

## Status
Accepted

## Date
2026-10-16

## Context
La API nació para mostrar las ganancias de unos bots de trading simulado (paper trading) que corren por separado
y escriben sus datos continuamente en carpetas propias: un `state.json` con el estado y un `trades.csv` con las
operaciones cerradas. Esos bots son un experimento en curso que no debe alterarse, y su código cambia con frecuencia.

La API necesita mostrar las ganancias de esos bots sin interferir con ellos.

## Decision
La API **solo lee** los archivos `state.json` y `trades.csv`, desde `api/datos.py`. No importa el código de los
bots, no los arranca y no escribe en sus carpetas. Lo único que escribe es `api/carteras.json` (ver ADR-002).

Las carpetas se buscan en este orden (`_resolver_raiz()` en `datos.py`):

1. La variable de entorno `SIMULADOR_DIR`, si está definida.
2. La carpeta padre de `api/`, si contiene los journals (el proyecto original donde viven los bots).
3. `demo-data/` en la raíz del repositorio: datos de ejemplo inventados, con el mismo formato.

## Alternatives Considered

### Importar el código de los bots
- Pros: Acceso directo a sus estructuras y funciones.
- Cons: Acopla la API a las partes internas de un código que cambia, y arrastra sus dependencias.
- Rejected: Los archivos `state.json` y `trades.csv` ya contienen todo lo que la API necesita mostrar.

### Copiar los datos a una base propia
- Pros: Aísla por completo a la API.
- Cons: Los datos quedarían desactualizados y habría que sincronizarlos.
- Rejected: Leer el archivo vivo da siempre el dato actual con menos piezas.

## Consequences
- La API refleja el estado real del bot en cada petición, sin caché.
- Depende del formato de esos archivos. Hay dos formas de `state.json`:
  el bot `btc` guarda un estado plano (`equity`, `realized`) **sin capital inicial**, que se deduce como
  `equity - realized`; `multi`, `meme` y la matriz guardan `global` y `books` con una billetera por moneda.
  Si un bot cambia su formato, `api/datos.py` es el único archivo que hay que ajustar.
- `equity` de cada billetera incluye solo operaciones cerradas. La ganancia no realizada de posiciones
  abiertas solo existe agregada por grupo, por eso `/simulador/{grupo}` la da únicamente a nivel de grupo.
- Cualquiera puede ejecutar el repositorio sin tener los bots: arranca con `demo-data/`.
- Una lectura puede coincidir con una escritura del bot; si el archivo se lee a medias, esa petición
  puede fallar con `500` y bastará con repetirla.
