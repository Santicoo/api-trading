# Changelog

## [1.2.0] - 2026-10-19
### Added
- Variable de entorno `SIMULADOR_DIR` para elegir la carpeta con los datos del simulador. Sin ella, la API usa la
  carpeta padre de `api/` si trae los journals y, si no, `demo-data/` (datos de ejemplo inventados).
- `GET /` devuelve `datos` (`demo`, `proyecto` o `personalizado`) y la app web muestra una etiqueta fija cuando
  trabaja con datos de ejemplo.
- Repositorio público independiente con `demo-data/`, generador de datos de ejemplo, pruebas con `pytest` y
  `docs/API.md`.

### Changed
- Las descripciones de los bots en `/bots` y `/simulador` son genéricas (no describen la estrategia).

## [1.1.1] - 2026-10-16
### Fixed
- App: el botón volver no hacía nada al entrar directo a una pantalla (enlace o recarga), porque dependía del
  historial del navegador. Ahora va siempre a la pantalla anterior lógica.
- App: «Volver al inicio» en la pantalla de error no hacía nada si el error ocurría en el propio inicio.
- App: en el celular, los nombres largos de la matriz ensanchaban la tarjeta y sacaban el saldo de la pantalla.

### Changed
- App: bots y estrategias de la matriz se muestran como lista compacta en dos líneas. Las billeteras de un grupo
  tienen filtros (todas, abiertas, ganando, perdiendo) y se despliegan al tocarlas para ver el detalle.

## [1.1.0] - 2026-10-16
### Added
- `GET /simulador` y `GET /simulador/{grupo}`: billeteras por moneda de los bots y de las estrategias
  de la matriz, con posición abierta, tasa de acierto y caída desde el máximo.
- App web en `/app/` con las pestañas *Simulador* y *Mis carteras*.
- Variable de entorno `PORT` para elegir el puerto.
- Documentación: README completo, registros de decisiones (`docs/decisions/ADR-001` a `ADR-005`) y
  descripciones y códigos de error de cada endpoint en `/docs`.

### Changed
- El reinicio automático del servidor (`reload`) vigila solo la carpeta `api/`, para no reiniciarse cuando los
  bots escriben sus journals.

## [1.0.0] - 2026-10-16
### Added
- `GET /bots`, `GET /bots/{bot}/ganancias`, `GET /bots/{bot}/operaciones`.
- CRUD de carteras: `GET /carteras`, `GET /carteras/{id}/ganancias`, `POST`, `PUT` y `DELETE /carteras`.
- Colección de Postman con las cuatro peticiones.
