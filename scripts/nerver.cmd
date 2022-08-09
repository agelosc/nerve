@echo off
N:
CD %NERVE_LOCAL_PATH%
python %NERVE_LOCAL_PATH%/www/nerver/manage.py runserver
