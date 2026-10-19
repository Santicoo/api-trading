# ADR-005: Servir la interfaz web desde la misma API

## Status
Accepted

## Date
2026-10-16

## Context
Para simular una app de consulta de billeteras se necesita una interfaz que use la API. Debe funcionar
sin instalar nada adicional (sin Node, sin proceso de compilación) y sin problemas de CORS.

## Decision
Una página estática única, `api/static/index.html` (HTML, CSS y JavaScript sin librerías), servida por
FastAPI en `/app/` con `StaticFiles`. Llama a la API con rutas relativas (mismo origen).
Tiene dos pestañas: **Simulador** (`GET /simulador`, `GET /bots`) y **Mis carteras** (CRUD de `/carteras`).
La barra inferior muestra el método y estado de la última petición para poder explicar cada pantalla.

## Alternatives Considered

### React/Vue con herramienta de compilación
- Pros: Estructura para interfaces grandes.
- Cons: Requiere Node, dependencias y un paso de build para una sola pantalla.
- Rejected: Desproporcionado; complica ejecutar el proyecto.

### Servir la página desde otro servidor
- Pros: Separa front y back.
- Cons: Exige configurar CORS y arrancar dos procesos.
- Rejected: Mismo origen es más simple y suficiente.

## Consequences
- Un solo comando (`python api/main.py`) levanta API e interfaz.
- Todo el código de la interfaz está en un archivo; si crece mucho, conviene separarlo en módulos.
- La página carga la fuente *Manrope* de Google Fonts; sin internet usa la tipografía del sistema.
- Los textos que vienen de la API se escapan antes de insertarse en el HTML (función `esc`).
