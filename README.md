

## Installation
download and unzip folder, then commands to prepare 
```
cd funglr-csv-app
source bin/activate
cd webapp
python manage.py migrate
```

## Configuration
In Settings.py file, some configurations:

DOWNLOAD_DIRECTORY
LOG_DIRECTORY
LOG_NAME
TEST_FILES_PATH

The TEST_FILES_PATH, should contain the (three necessary) files for testing. 

The files must be named:
```
eccube.csv
mail_list_allow.csv
mail_list_deny.csv
```
and placed inside the TEST_FILES_PATH directory

## Use

to run tests, just execute
```
python manage.py test
```

start server listening on port (default: 8000):
```
python manage.py runserver [port]
```
