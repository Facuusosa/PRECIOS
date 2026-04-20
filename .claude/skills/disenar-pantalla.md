# Skill: /disenar-pantalla
## Descripcion
Screenshot loop para mejorar el diseno visual del frontend. Toma screenshot del estado actual, propone mejora con referencia de godly.website o 21st.dev, implementa y itera hasta aprobacion. Siempre respetar el orden: skills.sh -> 21st.dev -> ReactBits -> construir desde cero.

## Uso
`/disenar-pantalla [vista]` — donde vista es: inicio | comparar | lista | cuenta | general

## Pasos

1. **Screenshot del estado actual**
   - Usar Puppeteer MCP para navegar a `http://localhost:3000`
   - Tomar screenshot de la vista especificada
   - Si el servidor no esta corriendo: recordar al usuario que corra `npm run dev` en `BRUJULA-DE-PRECIOS/`

2. **Identificar problema o area de mejora**
   - Analizar el screenshot visualmente
   - Preguntar: que parte se ve menos pulida? que elemento podria tener mayor impacto visual?
   - Especificar el problema concreto antes de buscar solucion

3. **Buscar referencia (orden obligatorio)**
   - Primero: skills.sh — buscar animacion o componente relevante
   - Segundo: 21st.dev/community/components — componente React listo para usar
   - Tercero: ReactBits en `components/reactbits/` — ya integrado en el proyecto
   - Solo si no existe nada: construir desde cero
   - Mostrar la referencia encontrada antes de implementar

4. **Proponer mejora concreta**
   - Describir exactamente que va a cambiar (archivo, lineas, componente)
   - Mostrar preview del resultado esperado
   - Pedir aprobacion de Facu antes de tocar el codigo

5. **Implementar**
   - Hacer el cambio en el archivo correspondiente en `BRUJULA-DE-PRECIOS/components/`
   - Verificar TypeScript: `npx tsc --noEmit`
   - Verificar sin errores de consola

6. **Screenshot de resultado**
   - Tomar nuevo screenshot del mismo elemento
   - Comparar lado a lado con el screenshot inicial
   - Reportar: "Mejoro? o itero?"

7. **Iterar hasta aprobacion**
   - Si Facu aprueba: guardar el cambio, reportar como DONE
   - Si no: identificar que no le gusto y volver al paso 3

## Reglas de diseno obligatorias
- Mobile-first: siempre verificar con viewport movil tambien
- Dark mode por defecto (comerciantes usan en ambientes variados)
- Usar design tokens del proyecto — no hex directos
- Radix UI para componentes interactivos — no reinventar dropdowns, modals
