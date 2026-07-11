# Regla: Dominios y deploy — bug de Vercel con dominios con tilde (IDN)

## El problema (09-10/07/2026)

Facu registró `brújuladeprecios.com.ar` (con tilde, IDN) en NIC.ar. Delegar el DNS
directo a los nameservers de Vercel (`ns1/ns2.vercel-dns.com`) NUNCA funcionó — SERVFAIL
persistente, incluso consultando directo contra los servidores raíz de `.ar` (`c.dns.ar`)
y contra los propios nameservers de Vercel. Se descartaron uno por uno: DNSSEC (no hay
DS record), guardado sin confirmar en NIC.ar (se verificó "Ejecutar Cambios"), trámite
administrativo incompleto (el expediente GDE estaba finalizado).

**Causa real:** bug conocido y no resuelto de Vercel con dominios internacionalizados
(IDN — con tilde/ñ). Confirmado con casos idénticos de otros usuarios en la comunidad de
Vercel y de Netlify (dominios con tilde/ñ atascados en "Invalid Configuration" /
"Failed to Generate Cert", soporte de Vercel reconoció el problema y lo escaló a
ingeniería sin resolución). Vercel no logra activar una "zona DNS" propia para estos
dominios aunque la delegación esté bien hecha.

## La solución que funcionó: Cloudflare como intermediario

En vez de delegar el DNS directo a Vercel, se delega a **Cloudflare (gratis)**, y dentro
de Cloudflare se cargan registros normales apuntando a Vercel:
- `A @ → 76.76.21.21`
- `CNAME www → cname.vercel-dns.com`
- Proxy status: **DNS only** (nube gris, no naranja) — evita variables extra mientras se
  depura.

Cloudflare sí maneja bien los dominios IDN — el problema es específico de la "zona DNS"
propia de Vercel, no de tener un dominio con tilde en sí.

## Pasos exactos (repetibles para cualquier dominio nuevo con tilde)

1. NIC.ar → Delegaciones → cargar los 2 nameservers de Cloudflare (`sierra.ns.cloudflare.com`
   y `terin.ns.cloudflare.com` en esta cuenta — Cloudflare los reusa por cuenta, no por dominio).
2. **Guardar cada fila con el disquete 💾 Y ADEMÁS clickear "EJECUTAR CAMBIOS"** — guardar
   la fila sola NO alcanza, es un paso de confirmación aparte y es fácil saltearlo.
3. Cloudflare → Add a domain → Connect a domain → cargar los 2 registros (A y CNAME) → Continue
   to activation → "I updated my nameservers" (recién después de haber hecho el paso 2).
4. Vercel → proyecto → Domains → Add Existing → cargar el dominio en su forma **punycode**
   (ej. `xn--brjuladeprecios-3ub.com.ar`) — Vercel no acepta la tilde directo en el campo de
   texto, hay que convertirla a mano. Conversión rápida en PowerShell:
   `(New-Object System.Globalization.IdnMapping).GetAscii("brújuladeprecios.com.ar")`
5. Esperar propagación: NIC.ar dice "hasta 1 hora", Cloudflare dice "1-2 horas, hasta 24".
   En la práctica puede tardar varias horas. Un SERVFAIL que no cambia en minutos NO es
   señal de error — es esperable, solo hay que dejarlo correr.

## Verificación — NUNCA confiar en un solo resolver

- `nslookup`/`Resolve-DnsName` contra Google (8.8.8.8) puede dar una respuesta distinta a
  consultar DIRECTO contra un servidor raíz de `.ar` (ej. `c.dns.ar`, IP `200.108.148.50`)
  — la .ar tiene 5 servidores raíz (`c/d/e/f.dns.ar` + `a.lactld.org`) y no siempre están
  sincronizados; Google puede tener éxito con uno aunque otro falle.
- **who.is (y probablemente otros agregadores de WHOIS) NO distinguen bien entre la
  versión con tilde y sin tilde de un mismo dominio IDN** — devuelven los datos del que
  SÍ existe aunque preguntes por el que no, con la misma fecha de creación. Encontrado dos
  veces en esta sesión. Para confirmar disponibilidad real de un dominio, usar DNS directo
  (NXDOMAIN = libre) o el buscador oficial de NIC.ar a mano — nunca who.is para dominios IDN.
- Prueba final real: `curl -I https://dominio` (sin `-k`, para que valide el certificado
  SSL de verdad) — un HTTP 200 con `ssl_verify_result: 0` confirma que el sitio anda de
  punta a punta, no solo que el DNS resuelve.

## Arquitectura final (decisión de Facu, 10/07/2026)

Facu no quería depender solo del dominio con tilde por dos motivos reales: (1) nadie
escribe la tilde de memoria, (2) algunos navegadores muestran el punycode feo
(`xn--...`) en vez de la tilde por protección anti-phishing de dominios IDN (comportamiento
estándar de navegador, no bug nuestro).

Se registró TAMBIÉN `brujuladeprecios.com.ar` (sin tilde, mismo trámite en NIC.ar) y
quedó como dominio **principal**. El dominio con tilde no se dio de baja (ya pagado, sin
razón para perderlo) — se configuró en Vercel como **"Redirect to Another Domain"** hacia
el sin tilde (apex → apex, www → www). Los dos siguen registrados y funcionando; el que
se comparte siempre es el sin tilde.

## Regla derivada

Ante cualquier dominio `.com.ar` con tilde/ñ que no conecte a Vercel con SERVFAIL
persistente: no seguir insistiendo con delegación directa a Vercel, ir directo a la
solución de Cloudflare como intermediario. Y si el negocio se puede permitir un segundo
dominio sin caracteres especiales, registrarlo de entrada — evita todo este quilombo.
