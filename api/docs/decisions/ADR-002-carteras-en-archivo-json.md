# ADR-002: Guardar las carteras en un archivo JSON

## Status
Accepted

## Date
2026-10-16

## Context
Las carteras que crea el usuario (`POST /carteras`) necesitan persistir entre reinicios del servidor, para que
el `PUT`, el `DELETE` y la app web puedan actuar sobre ellas después. El volumen esperado es de unas pocas
carteras creadas por una sola persona durante una demostración.

## Decision
Guardar todas las carteras en `api/carteras.json` con esta forma:

```json
{ "siguiente_id": 2, "carteras": { "1": { "id": 1, "nombre": "...", "posiciones": [ ... ] } } }
```

El `id` sale de `siguiente_id`, que solo crece: **un id borrado no se reutiliza**. El archivo se crea
con el primer `POST`; si no existe, la API se comporta como si no hubiera carteras.

## Alternatives Considered

### SQLite
- Pros: Escrituras atómicas, consultas, sin servidor aparte.
- Cons: Añade esquema, conexión y manejo de sesiones para guardar un puñado de objetos.
- Rejected: Más código del que justifica el volumen. Es el siguiente paso natural si crece el uso.

### En memoria (un diccionario en el proceso)
- Pros: Lo más simple.
- Cons: Se pierde todo al reiniciar el servidor (y el servidor se reinicia al editar código con `reload`).
- Rejected: Las carteras desaparecerían en mitad de una demostración.

## Consequences
- El archivo se puede leer y editar a mano, y se borra para empezar de cero.
- **No hay bloqueo de archivo**: si dos peticiones escriben a la vez, una puede pisar a la otra. Es aceptable
  para un solo usuario; con varios clientes concurrentes habría que pasar a SQLite.
- Cada petición lee y reescribe el archivo completo, lo cual es lento solo con miles de carteras.
- Si se abren dos servidores a la vez (por ejemplo en puertos distintos), comparten este mismo archivo.
