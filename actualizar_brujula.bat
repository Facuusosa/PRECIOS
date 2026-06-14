@echo off
REM Actualiza Brujula de Precios: corre los 3 scrapers, regenera el catalogo y publica.
REM Lo ejecuta el Programador de tareas de Windows cada manana. Tambien sirve para
REM correrlo a mano con doble-click.
cd /d "c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
REM PYTHONUTF8=1 evita el crash de cp1252 con emojis/tildes en los print de los scrapers
set PYTHONUTF8=1
echo ==================================================== >> "data\quality\pipeline_local.log"
echo Corrida: %date% %time% >> "data\quality\pipeline_local.log"
python pipeline_local.py >> "data\quality\pipeline_local.log" 2>&1
