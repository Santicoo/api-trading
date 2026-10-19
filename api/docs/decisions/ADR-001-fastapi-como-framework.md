# ADR-001: Usar FastAPI como framework de la API

## Status
Accepted

## Date
2026-10-16

## Context
La API es una tarea que debe demostrarse en Postman con cuatro tipos de petición (GET, POST, PUT, DELETE).
El proyecto ya está en Python, así que la API debe poder importar y leer los datos del simulador sin
cambiar de lenguaje. El requisito de usar FastAPI venía dado desde el inicio del trabajo.

Necesidades que influyen en el diseño:
- Validar cuerpos JSON (cantidad > 0, al menos una posición, etc.) con errores `422` claros.
- Tener documentación interactiva para la demostración sin escribirla a mano.

## Decision
Usar **FastAPI** con modelos **Pydantic** para validar la entrada, y **uvicorn** como servidor.

## Alternatives Considered

### Flask
- Pros: Muy conocido y mínimo.
- Cons: La validación de cuerpos y la documentación OpenAPI requieren librerías adicionales.
- Rejected: FastAPI trae ambas cosas incluidas.

### Django REST Framework
- Pros: Completo (ORM, autenticación, administración).
- Cons: Mucho andamiaje para 11 endpoints sin base de datos relacional.
- Rejected: Desproporcionado para el tamaño del proyecto.

## Consequences
- `/docs` (Swagger) y `/openapi.json` se generan solos a partir del código; las descripciones de cada
  endpoint viven en los docstrings de `api/main.py`.
- Los errores de validación devuelven `422` con el detalle de qué campo falló.
- La API depende de `fastapi[standard]` (incluye uvicorn). Está en `api/requirements.txt`.
