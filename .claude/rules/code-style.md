# Rules: Code Style

## TypeScript
- Nunca `any` explícito — usar tipos concretos o `unknown`
- Preferir `satisfies` sobre `as` para type assertions
- Imports de JSON: única excepción para `any` implícito
- Nombrar: `camelCase` variables/funciones, `PascalCase` componentes/tipos, `UPPER_SNAKE` constantes
- Siempre `const` salvo que haya razón para `let`

## Python
- `snake_case` para todo (variables, funciones, archivos)
- f-strings para interpolación — no `%` ni `.format()`
- Type hints en funciones públicas: `def scrape(session: requests.Session) -> list[dict]`
- Nunca `print()` mezclado con lógica — output al final o logging
- Un solo `return` al final de funciones largas — evitar returns intermedios

## Comentarios
- Agregar cuando el código te va a confundir a vos mismo en 2 semanas: restricción oculta, workaround de bug específico, invariante no obvio
- Nunca comentar WHAT hace el código — los nombres ya lo dicen
- En scrapers: siempre comentar por qué está el delay, por qué el impersonate, por qué ese threshold de fuzzy

## General
- No backwards-compatibility hacks (no `_unused`, no re-exports, no `// removed`)
- No feature flags ni shims cuando se puede cambiar directo el código
- No manejo de errores para escenarios que no pueden pasar
- Funcional > perfecto. Si corre, es suficiente hasta que no lo sea.

## Windows / Python
- Nunca usar caracteres Unicode no-ASCII (`→`, `✓`, `←`) en `print()` — Windows cp1252 no los soporta.
- Usar equivalentes ASCII: `->`, `OK`, `<-`. Aplica a todos los scripts Python del proyecto.
- `subprocess.run()` con `text=True` usa cp1252 por defecto en Windows — SIEMPRE agregar `encoding='utf-8', errors='replace'` para evitar crash con archivos que contengan caracteres no-ASCII.
