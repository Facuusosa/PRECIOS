# Skill: /auditoria-seguridad
## Descripcion
Auditoria completa de seguridad del proyecto. Detecta credenciales hardcodeadas, configuraciones inseguras y vulnerabilidades antes de cada deploy. Reporta CRITICO / ATENCION / OK por categoria.

## Pasos

### 1. Credenciales hardcodeadas
Buscar en TODO el codigo (Python y TypeScript):
- Patrones: password=, secret=, token=, api_key=, PHPSESSID=, cf_clearance=
- Excluir: `.env`, `*.md`, `node_modules/`, `.claude/`
- Si encuentra algo: CRITICO — mostrar archivo y linea exacta

### 2. Verificar .gitignore
- `.env` esta en .gitignore? -> OK o CRITICO
- Archivos de cookies o tokens estan en .gitignore?
- `settings.local.json` esta en .gitignore? (tiene hooks con comandos locales)
- Buscar en git history si alguna vez se commiteo un .env por error

### 3. Variables de entorno en scripts
- Verificar que TODOS los scripts Python usan `os.getenv()` + `load_dotenv()`
- Verificar que NO hay fallbacks peligrosos (ej: `os.getenv("PASSWORD", "admin")`)
- Verificar que `.env` existe y tiene todas las variables requeridas:
  - YAGUAR_USERNAME, YAGUAR_PASSWORD
  - CARREFOUR_PHPSESSID, CARREFOUR_CF_CLEARANCE
  - (cualquier variable de Maxiconsumo)

### 4. Seguridad del frontend
- Buscar `console.log` con datos sensibles en `BRUJULA-DE-PRECIOS/`
- Verificar que localStorage NO guarda credenciales ni datos de pago
- Verificar que las rutas de API (si las hay) no exponen datos sin autenticacion

### 5. Checklist pre-deploy
```
[ ] .env en .gitignore
[ ] Sin credenciales hardcodeadas en el codigo
[ ] Todos los scripts usan os.getenv()
[ ] Sin console.log con datos sensibles en produccion
[ ] Sin archivos de debug o output temporales commiteados
[ ] URL de deploy no es trivialmente predecible
```

### 6. Reporte final
```
=== AUDITORIA DE SEGURIDAD ===
Credenciales hardcodeadas: [CRITICO/OK]
.gitignore configurado:     [CRITICO/OK]
Variables de entorno:       [CRITICO/ATENCION/OK]
Frontend seguro:            [ATENCION/OK]
Checklist pre-deploy:       [X/5 items OK]

PROXIMOS PASOS:
[lista de acciones criticas si las hay]
```
