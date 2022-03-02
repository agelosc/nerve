@echo off
R:
CD %NERVE_LOCAL_PATH%\test
python -m unittest discover
