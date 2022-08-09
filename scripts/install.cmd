@echo off
setx MAYA_PYTHON_VERSION 2
setx NERVE_LOCAL_PATH N:\software\nerve
set NERVE_LOCAL_PATH N:\software\nerve
cd setup
REM Install Python 3.9.9
python-3.9.9-amd64.exe TargetDir=C:\Python\Python39 PrependPath=1 SimpleInstall=1
REM Install Image Magik
ImageMagick-7.1.0-21-Q16-HDRI-x64-dll.exe /VERYSILENT /NORESTART
REM update pip
C:\Python\Python39\python.exe -m pip install --upgrade pip
REM install python requirements
C:\Python\Python39\python.exe -m pip install -r requirements.txt
pause