# Chukchi verb database

This is a web-application for a Chukchi verb database.
## Requirements
- Python 3.x (also runs on Python 2.x but static files are not loaded (???) )
- Flask
- elasticsearch (running Java app and Python module)
- lxml

## How to run
1) run an Elasticsearch system
2) run `indexator.py` in the `data` folder. This will load an index with the defined mapping and four example documents.
3) in the command line, type `python chukchi_verb_database.wsgi` and the application will be launched.
