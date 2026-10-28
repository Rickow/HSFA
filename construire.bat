@echo off
rem HSFA : construit SFA3, Upper et Hyper pour le coeur FinalBurn Neo HSFA, depuis VOTRE ISO de
rem Street Fighter Alpha Anthology (PS2, USA, SLUS-21317). Windows.
rem Builds SFA3, Upper and Hyper for the FinalBurn Neo HSFA core from YOUR Anthology ISO.
rem   construire.bat              demande le chemin de l'ISO / asks for the ISO path
rem   construire.bat ISO [SORTIE] (glisser l'ISO sur ce fichier marche aussi / drag the ISO onto this file)
rem Il faut Python 3.8+ (python.org, case "Add python.exe to PATH"). Musique en ADX sous Windows, sauf si ffmpeg
rem (libvorbis), gcc et g++ sont dans le PATH (alors Ogg Vorbis, archives plus petites).
setlocal enableextensions
set "ICI=%~dp0"
set "ISO=%~1"
if "%ISO%"=="" set /p "ISO=Chemin de l'ISO de l'Anthology / ISO path: "
set "ISO=%ISO:"=%"
if not exist "%ISO%" (echo ISO introuvable / ISO not found: %ISO% & goto :fin)
set "SORTIE=%~2"
if "%SORTIE%"=="" set "SORTIE=%ICI%sortie"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (echo Python 3.8+ est requis / is required: https://www.python.org/downloads/ & goto :fin)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || (echo Python 3.8+ requis / required & goto :fin)

if not exist "%ICI%.venv\Scripts\python.exe" (
  echo Preparation de Python, une seule fois / Setting up Python, once...
  %PY% -m venv "%ICI%.venv" || goto :fin
)
"%ICI%.venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r "%ICI%requirements.txt" || goto :fin

set "FORMAT=ogg"
for %%o in (ffmpeg gcc g++) do (where %%o >nul 2>nul || set "FORMAT=adx")
if "%FORMAT%"=="ogg" (ffmpeg -hide_banner -encoders 2>nul | findstr /c:"libvorbis" >nul || set "FORMAT=adx")
if "%FORMAT%"=="adx" echo Musique en ADX (archives d'Upper et d'Hyper plus grosses) / Music kept as ADX.

echo Construction, quelques minutes / Building, a few minutes...
"%ICI%.venv\Scripts\python.exe" "%ICI%scripts\construction\hsfa_build.py" --anthology "%ISO%" --sortie "%SORTIE%" --jeux sfa3,upper,hyper --flux-format %FORMAT% || goto :fin

echo.
echo Termine / Done. Archives pour le coeur / core archives:
dir /b "%SORTIE%\archives\*.zip"
echo Copiez-les dans le dossier des ROM de FinalBurn Neo (voir README) / copy them to your FBNeo ROM folder.
:fin
echo.
pause
