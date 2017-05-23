# chukchi_verb_database

This is a web-application for a Chukchi verb database.
## Requirements
- Python 3.x (also runs on Python 2.x but static files are not loaded (???) )
- Flask
- elasticsearch (running Java app and Python module)
- lxml

## How to run
1) run an Elasticsearch system
2) run `indexator.py` in the `data` folder. This will load an index with the defined mapping and three example documents.
2) in the command line, type `python new_app.py runserver` and the application will be launched.

## TO DO
- Create more example docs for a database (in the `data` folder). Those existing now are just for test and do not reflect characteristics of real Chukchi verbs.
- include real options for select fields
- Think about backups
