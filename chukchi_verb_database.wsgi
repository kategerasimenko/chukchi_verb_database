#coding:utf-8

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from new_app import app as application

if __name__=="__main__":
    application.run(debug=True)
