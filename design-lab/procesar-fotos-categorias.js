// Procesa las fotos que Facu deja en public/ALMACEN, public/BEBIDAS, etc.:
// las copia a public/categories/productos/ con nombres prolijos (almacen-1.webp...),
// mide el bbox del producto (w/h que usa lib/categoria-fotos.ts para escalar)
// y chequea que el fondo sea blanco (el multiply sobre placa lo exige).
//
// Uso:  npm i sharp --no-save && node design-lab/procesar-fotos-categorias.js
// Para las categorías que faltan (BAZAR, CONGELADOS, KIOSCO, MASCOTAS, DESAYUNO):
// sumarlas al mapa CARPETAS y pasar los w/h medidos a lib/categoria-fotos.ts.
const sharp = require('sharp')
const fs = require('fs')
const path = require('path')

const PUB = 'c:/Users/Facun/OneDrive/Escritorio/PROYECTOS PERSONALES/PRECIOS/BRUJULA-DE-PRECIOS/public'
const DESTINO = path.join(PUB, 'categories', 'productos')
const CARPETAS = { ALMACEN: 'almacen', BEBIDAS: 'bebidas', FRESCOS: 'frescos', LIMPIEZA: 'limpieza', PERFUMERIA: 'perfumeria' }
const UMBRAL_BLANCO = 244

async function analizar(buf) {
  const { data, info } = await sharp(buf).resize(150, 150, { fit: 'inside' }).removeAlpha().raw().toBuffer({ resolveWithObject: true })
  let minX = info.width, maxX = -1, minY = info.height, maxY = -1
  for (let y = 0; y < info.height; y++) {
    for (let x = 0; x < info.width; x++) {
      const i = (y * info.width + x) * 3
      if (data[i] < UMBRAL_BLANCO || data[i + 1] < UMBRAL_BLANCO || data[i + 2] < UMBRAL_BLANCO) {
        if (x < minX) minX = x
        if (x > maxX) maxX = x
        if (y < minY) minY = y
        if (y > maxY) maxY = y
      }
    }
  }
  // fondo: promedio de las 4 esquinas (parche 6x6)
  const esquina = (x0, y0) => {
    let s = 0, n = 0
    for (let y = y0; y < y0 + 6; y++) for (let x = x0; x < x0 + 6; x++) {
      const i = (y * info.width + x) * 3
      s += (data[i] + data[i + 1] + data[i + 2]) / 3; n++
    }
    return s / n
  }
  const fondo = Math.min(
    esquina(0, 0), esquina(info.width - 6, 0),
    esquina(0, info.height - 6), esquina(info.width - 6, info.height - 6)
  )
  const wFill = maxX < 0 ? 0 : (maxX - minX + 1) / info.width
  const hFill = maxY < 0 ? 0 : (maxY - minY + 1) / info.height
  return { w: +wFill.toFixed(2), h: +hFill.toFixed(2), fondo: Math.round(fondo) }
}

async function main() {
  const out = {}
  for (const [carpeta, cat] of Object.entries(CARPETAS)) {
    const dir = path.join(PUB, carpeta)
    if (!fs.existsSync(dir)) { console.log(`${carpeta}: no existe, salteada`); continue }
    const archivos = fs.readdirSync(dir).filter(f => /\.(webp|png|jpe?g)$/i.test(f))
    out[cat] = []
    let n = 0
    for (const f of archivos) {
      n++
      const ext = path.extname(f).toLowerCase()
      const nuevo = `${cat}-${n}${ext}`
      const buf = fs.readFileSync(path.join(dir, f))
      const m = await analizar(buf)
      fs.copyFileSync(path.join(dir, f), path.join(DESTINO, nuevo))
      out[cat].push({ file: `categories/productos/${nuevo}`, ...m })
      const alerta = m.fondo < 240 ? '  <-- FONDO NO BLANCO' : ''
      console.log(`${nuevo}  producto ${Math.round(m.w * 100)}% ancho x ${Math.round(m.h * 100)}% alto, fondo ${m.fondo}${alerta}`)
    }
  }
  fs.writeFileSync(path.join(__dirname, 'fotos_facu.json'), JSON.stringify(out, null, 1))
  console.log('---\nJSON: fotos_facu.json')
}

main()
