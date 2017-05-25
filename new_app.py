# -*- encoding: utf-8 -*-

from html_form_parser import HTMLFormParser
from html_builder import HTMLBuilder
from db_client import DBClient
from flask import Flask, request, render_template, redirect, url_for
import json


app = Flask(__name__)
d = DBClient()
hfp = HTMLFormParser()
hb = HTMLBuilder()


@app.route('/',methods=['GET','POST'])
def list_of_verbs():
    if request.method == 'POST':
        v_id = request.form["delete"]
        d.delete(v_id)
        return '{"result":"success"}'
    words = d.all_words()
    return render_template('index.html',words=words,results=False)

    
@app.route('/add',methods=['GET','POST'])
def add():
    if request.method == 'POST':
        for_db = hfp.parse_form(dict(request.form))
        return '{"result":"success"}'
    page = hb.create_html(d.empty_form_fields(), mode='add')
    return page


@app.route('/<int:verb_id>/edit',methods=['GET','POST'])
def update(verb_id):
    if request.method == 'POST':
        for_db = hfp.parse_form(dict(request.form))
        d.update(verb_id,for_db)
        return '{"result":"success"}'
    f = d.fields_for_edit(verb_id)
    if f:    
        page = hb.create_html(d.fields_for_edit(verb_id),mode='update')
        return page
    else:
        return ''

        
@app.route('/<int:verb_id>')
def view(verb_id):
    f = d.fields_for_edit(verb_id)
    if f:
        page = hb.create_html(f,mode='view',verb_id=str(verb_id))
        return page
    else:
        return ''
 
 
@app.route('/search',methods=['GET'])
def search():
    page = hb.create_html(d.search_form_fields(),mode='search')
    return page  


    
@app.route('/results',methods=['GET'])
def results():
    if request.args:
        for_db = hfp.parse_form(request.args)
        query = json.dumps({"_source":["_id","word"],"query":hfp.create_query(for_db)['query']})
        res = d.search(query)
        ready_words = sorted([(x['_source']['word'],x['_id']) for x in res],key=lambda x: x[0])
        return render_template('index.html',words=ready_words,results=True)
    return ''
    
        
if __name__ == '__main__':
    app.run(debug=True)
