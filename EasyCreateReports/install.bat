@echo off
chcp 65001 >nul
echo === Installing EasyCreateReports for Windows ===

:: Define installation directory
set "INSTALL_DIR=%LOCALAPPDATA%\EasyCreateReports"

echo Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy files to installation directory
echo Copying files...
xcopy /s /y *.* "%INSTALL_DIR%\" >nul

:: Install Python packages (PyQt6, PyQt6-WebEngine, PyYAML, xhtml2pdf)
echo Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install pyqt6 pyqt6-webengine pyyaml xhtml2pdf

:: Create executable launcher (run.bat)
echo Creating executable script...
(
@echo off
cd /d "%INSTALL_DIR%"
python app_gui.py
) > "%INSTALL_DIR%\run.bat"

:: Create Desktop shortcut via PowerShell
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\EasyCreateReports.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\run.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo.
echo === Installation completed successfully! ===
echo You can now open the application from the new icon on your Desktop.
pause