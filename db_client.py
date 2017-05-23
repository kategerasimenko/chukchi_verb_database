# -*- encoding: utf-8 -*-

from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
from html_form_parser import HTMLFormParser
from copy import deepcopy
import json

hfp = HTMLFormParser()

class DBClient(object):
    """
    this class is an interface for interaction of html builder class and the app
    with the database through Python module 'elasticsearch'
    """
    
    def __init__(self,name,doctype):
        self.es = Elasticsearch()
        self.ic_es = IndicesClient(self.es)
        self.name = name
        self.doctype = doctype


    def search(self,query):
        hits = self.es.search(index=self.name,doc_type=self.doctype,body=query)
        return hits['hits']['hits']


    def add(self,query):
        id_needed = max([int(x["_id"]) for x in self.search('{"_source":"_id","query":{"match_all":{}}}')]) + 1 #find id
        self.es.index(index=self.name,doc_type=self.doctype,id=id_needed,body=query)

    def delete(self,verb_id):
        if self.es.exists(index=self.name,doc_type=self.doctype,id=verb_id):
            self.es.delete(index=self.name,doc_type=self.doctype,id=verb_id)

    def update(self,verb_id,query):
        script = json.dumps({'doc':query})
        self.es.update(index=self.name,doc_type=self.doctype,id=verb_id,body=script)

    def all_words(self):
        """
        get list of words with their ids from the database
        """
        words = self.search('{"_source":["_id","word"],"query":{"match_all":{}}}')
        words = sorted([(x['_source']['word'],x['_id']) for x in words],key=lambda x: x[0])
        return words


    def all_derivs(self,to_search):
        """
        get list of all derivation markers/glosses encountered in the database
        """
        words = self.search('{"_source":["'+to_search+'"],"query":{"match_all":{}}}')
        words = sorted(list({x['_source'][to_search] for x in words if x['_source']}))
        return words

    def all_roles_or_cases(self,paths,field):
        """
        get list of all semantic roles/cases encountered in the database
        """
        res = []
        for path in paths:
            words = self.search('{"_source":["'+path+'"],"query":{"match_all":{}}}')
            for word in words:
                res += self.get_leaves(word,field,[])
        return set(res)

    def get_leaves(self,d,field,r):
        """
        get all fields from the document (including fields from nested objects)
        """
        for key,value in d.items():
            if type(value) != list and type(value) != dict and key == field:
                r.append(value)
            if type(value) == dict:
                self.get_leaves(d[key], field, r)
            if type(value) == list:
                for i in range(len(value)):
                    self.get_leaves(d[key][i], field, r)
        return r


    def get_info(self,verb_id):
        """
        get full info about word including a link to a baseverb if it is relevant
        """
        if self.es.exists(index=self.name,doc_type=self.doctype,id=verb_id):
            word = self.es.get(index=self.name,doc_type=self.doctype,id=verb_id,_source=True)['_source']
            if 'baseverb' in word:
                word['baseverb'] = self.get_links_by_id(word['baseverb'])
            return word
        else:
            return {}


    def get_derivatives(self,verb_id):
        """
        get derivatives of the verb (collect all verbs which have a given verb as a baseverb)
        """
        query = '{"_source":["_id","word"],"query":{"bool":{"filter":{"term":{"baseverb":'+str(verb_id)+'}}}}}'
        words = self.search(query)
        words = sorted([(x['_source']['word'],x['_id']) for x in words if x['_source']],key=lambda x: x[0])
        return words if words else ''
    
                        
    def get_links_by_id(self,verb_ids):
        if self.es.exists(index=self.name,doc_type=self.doctype,id=verb_ids):
            full_d = self.es.get(index=self.name,doc_type=self.doctype,id=verb_ids,_source=["word"])['_source']["word"]
            return (full_d,verb_ids)
        return ()

    
    def empty_form_fields(self):
        """
        create fields for html form (flat structure) for adding (empty)
        """
        mapping = self.ic_es.get_mapping(index=self.name,doc_type=self.doctype)['verbs']['mappings']['verb']['properties']
        mapping = hfp.mapping_paths(mapping,paths=dict(),mode='empty_form')
        return mapping


    def fields_for_edit(self,verb_id):
        """
        create fields for html form (flat structure) for updating (values from verb + missing values from mapping)
        """
        mapping = self.ic_es.get_mapping(index=self.name,doc_type=self.doctype)['verbs']['mappings']['verb']['properties']
        m = hfp.mapping_paths(mapping,paths=dict(),mode='mapping') # get doc structure without types
        verb_info = self.get_info(verb_id) # get verb from the database
        if verb_info:
            verb = hfp.mapping_paths(verb_info,paths=dict(),mapping=m,mode='form') # actual verb doc
            verb['derivatives'] = {'derivatives':self.get_derivatives(verb_id)} # add derivatives (not in the mapping)
            return verb
        else:
            return {}
        

    def search_form_fields(self):
        """
        create fields for html form (flat structure) for search (empty, without particular fields (example, derivatives))
        """
        mapping = self.ic_es.get_mapping(index=self.name,doc_type=self.doctype)['verbs']['mappings']['verb']['properties']
        return hfp.mapping_paths(mapping,paths=dict(),mode='search')    

