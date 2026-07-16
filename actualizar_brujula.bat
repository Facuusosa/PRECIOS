@echo off
REM Actualiza Brujula de Precios: corre los 6 scrapers (3 mayoristas + 3 cadenas),
REM regenera el catalogo y publica. Lo ejecuta el Programador de tareas de Windows
REM cada manana. Tambien sirve para correrlo a mano con doble-click.
cd /d "c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
REM PYTHONUTF8=1 evita el crash de cp1252 con emojis/tildes en los print de los scrapers
set PYTHONUTF8=1
REM Rotacion del log: crece sin limite (~25k lineas en 2 semanas). Si pasa de 2 MB
REM se archiva a .old.log ANTES de abrir el redirect (con el handle abierto Windows
REM no deja mover el archivo).
if exist "data\quality\pipeline_local.log" (
    for %%A in ("data\quality\pipeline_local.log") do (
        if %%~zA gtr 2097152 move /y "data\quality\pipeline_local.log" "data\quality\pipeline_local.old.log" >nul
    )
)
echo ==================================================== >> "data\quality\pipeline_local.log"
echo Corrida: %date% %time% >> "data\quality\pipeline_local.log"
python pipeline_local.py >> "data\quality\pipeline_local.log" 2>&1
