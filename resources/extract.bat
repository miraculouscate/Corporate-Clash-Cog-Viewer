@echo off
echo Extracting all .mf files...

for %%G in (*.mf) do (
    echo Extracting %%G...
    multify -x -f "%%G"
)

echo.
echo All .mf files have been extracted.
pause
