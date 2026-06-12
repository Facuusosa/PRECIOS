@echo off
rem Tarea programada Windows: chequea cookies MC a diario, renueva solo si tienen >25 dias.
rem Si el auto-click falla, suena un beep y espera 90s un click manual en Chrome.
cd /d "c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
python scripts\renovar_cookies_carrefour.py >> data\quality\renovacion_cookies.log 2>&1
