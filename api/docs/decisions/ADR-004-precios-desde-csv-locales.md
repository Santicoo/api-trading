# ADR-004: Calcular las carteras con precios de los CSV locales

## Status
Accepted

## Date
2026-10-16

## Context
Para devolver la ganancia de una cartera (`cantidad × (precio_actual − precio_compra)`) hace falta un precio
actual por activo. El proyecto guarda velas históricas en `data/<ACTIVO>_1h.csv` (formato
`time,open,high,low,close,volume,trades,dt`). La API se demuestra sin conexión a ningún proveedor de precios.

## Decision
Usar el **cierre de la última vela de 1 hora** de `data/<ACTIVO>_1h.csv` como precio actual.
El cliente puede sobrescribirlo enviando `precio_actual` en la posición, lo que además permite activos sin CSV
(por ejemplo acciones). Cada posición devuelve `fuente_precio` indicando de dónde salió el precio y su fecha.

## Alternatives Considered

### Consultar un proveedor de precios en vivo
- Pros: Ganancias al día.
- Cons: Añade dependencia de red, límites de uso y manejo de fallos.
- Rejected: No hace falta para demostrar los cuatro tipos de petición. Es una mejora posible.

### Exigir siempre `precio_actual`
- Pros: Sin datos ocultos.
- Cons: El usuario tendría que buscar el precio en cada petición.
- Rejected: Peor experiencia para el caso común (cripto del proyecto).

## Consequences
- **Los precios son los del último dato guardado, no los del mercado de hoy.** Por eso `fuente_precio` incluye la
  fecha de la vela usada. En este repositorio, `demo-data/data/` trae precios **inventados** de ejemplo.
- Si se reemplazan los CSV por datos propios (por ejemplo apuntando `SIMULADOR_DIR` a otra carpeta), la API usa
  los nuevos precios sin cambios de código.
- Un activo que no está en `data/` y no trae `precio_actual` responde `422` listando los activos disponibles.
- Se usa la vela de 1 h, no las de 15 m o 1 m, solo por simplicidad.
