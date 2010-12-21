SET APP=%1
IF "%APP%" == "" SET APP=hellocgi
start dev_appserver.py %APP%