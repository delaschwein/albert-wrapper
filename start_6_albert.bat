@echo off
if "%~1"=="" (
    echo Usage: %~nx0 [number_of_instances]
    exit /b 1
)

for /l %%x in (1, 1, %1) do (
    start "" "C:\Program Files (x86)\daide\albert\Albert.exe"
)
