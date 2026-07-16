@echo off
rem Tarea programada Windows (20hs): RESCATE de MaxiCarrefour.
rem Si la corrida de la manana ya trajo output MCF sano, no hace nada.
rem Si fallo (patron cronico desde el rediseno MAXI PEDIDO), renueva cookies y
rem scrapea ahora — a esta hora Facu suele estar en casa, asi que el beep del
rem click manual de respaldo (90s) tiene sentido, a diferencia de las 10am.
rem El chequeo viejo por edad de cookies (>25 dias) era teatro: la sesion PHP
rem muere en HORAS (regla 02-scrapers), nunca iba a disparar.
cd /d "c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
set PYTHONUTF8=1
python scrape_maxicarrefour.py --solo-si-falta-hoy >> data\quality\renovacion_cookies.log 2>&1
