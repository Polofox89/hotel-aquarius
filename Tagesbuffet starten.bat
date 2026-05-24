@echo off
REM Startet den Tagesbuffet-Generator und haelt das Fenster im Fehlerfall offen.
cd /d "%~dp0"
echo Starte Tagesbuffet-Generator ...
echo.
python tagesbuffet_gui.py
echo.
echo ----------------------------------------------------------
echo Programm beendet (Exit-Code: %ERRORLEVEL%).
echo Falls ein Crash auftrat, siehe: tagesbuffet_crash.log
echo ----------------------------------------------------------
pause
