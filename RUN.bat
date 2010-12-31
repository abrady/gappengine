SET APP=%1
IF "%APP%" == "" SET APP=gappengine
python d:\Google\google_appengine\dev_appserver.py --port 8083 .
REM start dev_appserver.py %APP%