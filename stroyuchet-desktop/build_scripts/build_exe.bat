@echo off
echo === Сборка СтройУчёт v1.0.0 ===

:: Очистка
rmdir /s /q build dist 2>nul

:: Активация venv
call venv\Scripts\activate

:: Установка зависимостей
pip install -r requirements.txt

:: Сборка через PyInstaller
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "StroyUchet" ^
    --icon "assets\icon.ico" ^
    --add-data "src\resources;resources" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL" ^
    --hidden-import "openpyxl" ^
    --hidden-import "reportlab" ^
    --hidden-import "matplotlib" ^
    --hidden-import "bcrypt" ^
    --collect-all "customtkinter" ^
    src\main.py

:: Сжатие UPX (опционально)
:: upx --best dist\StroyUchet.exe

echo === Готово: dist\StroyUchet.exe ===
pause
