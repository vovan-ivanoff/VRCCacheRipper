
powershell -Command "Invoke-WebRequest https://github.com/AssetRipper/AssetRipper/releases/download/0.3.0.5/AssetRipper_win_x64.zip -OutFile package.zip"
tar -xvf package.zip
python -m venv vrcrip
call ./vrcrip/Scripts/activate.bat
pip install vrchatapi
call ./vrcrip/Scripts/deactivate.bat
echo.
echo ---------------DONE!-------------
pause