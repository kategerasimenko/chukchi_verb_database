# -*- encoding: utf-8 -*-

from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
import json
import codecs

class Indexator(object):
    def __init__(self,name,doctype):
        self.es = Elasticsearch()
        self.ic_es = IndicesClient(self.es)
        self.name = name
        self.doctype = doctype
        self.find_mapping()
        if self.ic_es.exists(index=self.name):
            self.delete_index()
        self.create_index()
        self.add_docs()

    def find_mapping(self):
        m = codecs.open('mapping_'+self.name+'.json','r',
                 encoding='utf-8-sig').read()
        self.mapping = json.loads(m)

    def create_index(self):
        self.ic_es.create(index=self.name, body=self.mapping)

    def delete_index(self):
        self.ic_es.delete(index=self.name)

    def get_docs(self):
        m = codecs.open('aggregation_'+self.name+'.json','r',
                 encoding='utf-8-sig').read()
        self.docs = json.loads(m)

    def add_docs(self):
        self.get_docs()
        for i in range(len(self.docs)):
            self.es.index(index=self.name,body=self.docs[i],id=i+1,
                          doc_type=self.doctype)
        

        
if __name__ == '__main__':
    idx = Indexator('verbs','verb')
##    time.sleep(1)
##    se = Search('verbs','verb')
##    res = se.search('{"_source":["_id","word"],"query":{"match_all":{}}}')
##    words = [{x['_source']['word']: '/'+se.name+'/'+se.doctype+'/'+str(x['_id'])} \
##             for x in res]
##    print(words)
