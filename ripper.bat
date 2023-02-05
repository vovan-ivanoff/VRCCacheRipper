@echo off
call ./vrcrip/Scripts/activate.bat
python script.py %*
call ./vrcrip/Scripts/deactivate.bat
pause