# -*- encoding: utf-8 -*-

class HTMLFormParser(object):
    """
    this class deals with transforming flat html forms 
    into hierarchical structure and vice versa
    """
    def __init__(self):
        self.wildcard = '?*'
        self.regexp = '[](){}^.$:-+\\|?*'

    def isint(self,value):
      """
      check whether the given value is an integer
      """
      try:
        int(value)
        return True
      except:
        return False

    def check_regexp(self,value):
        """
        check whether the field value is a wildcard or a regular expression
        """
        w_r = lambda x: sum((x in self.wildcard, x in self.regexp)) #check for each symbol if it belongs to a wildcard or a regexp syntax
        if all([1 if w_r(x) == 0 else 0 for x in value]): # no symbols of wildcard or regexps
            return 'text'
        if all([1 if w_r(x) != 1 else 0 for x in value]): # no symbols belonging only to regexps (only * or ? (w_r(x) == 2) or other symbols)
            return 'wildcard'
        if any([w_r(x) for x in value]): # at least one symbol belongs to a regexp syntax
            return 'regexp'
    
    
    def parse_form(self,new_entry):
        """
        transform flat html form into the structure that can be processed by the database
        iterative
        """
        for_db = {}
        for key,value in new_entry.items():
            if any(value): # if not empty field
                if self.isint(value): # if it's a foreign key
                    value = int(value)
                if type(value) == list:
                    value = [x for x in value if x] # leave out empty values
                    value = value[-1] # we need only the last filled value ('other' field) if there are many
                if '.' not in key: # not a nested object and no arrays
                    for_db[key] = value
                else: # if field id was a path
                    sep_key = key.split('.')
                    main_key = sep_key[0]
                    sub_db = for_db
                    for i,subkey in enumerate(sep_key[1:]): # go through path
                        if self.isint(main_key): # if it's an index in array go deeper in path
                            main_key = subkey
                            if main_key == sep_key[-1]: # but if you reached the end write the value
                                sub_db[main_key] = value
                        else:
                            if self.isint(subkey): # if the array stuff begins
                                if subkey == sep_key[-1]: # if it's just an array of values
                                    if main_key not in sub_db or not sub_db[main_key]: # if we've created {} a step higher or if it doesn't exist yet
                                        sub_db[main_key] = [value]
                                    else:
                                        sub_db[main_key].append(value)
                                else:
                                    if main_key not in sub_db or not sub_db[main_key]: # if we've created {} a step higher or if it doesn't exist yet
                                        sub_db[main_key] = [dict() for x in range(int(subkey))] # create as many necessary dicts as we can know from the given index
                                    if len(sub_db[main_key]) < int(subkey): # if we've created not enough dicts in the array
                                        sub_db[main_key] += [dict() for x in range((int(subkey)-len(sub_db[main_key])))] # add dicts to the necessary number according to the given index
                                    sub_db = sub_db[main_key][int(subkey)-1] # go to the necessary dict in the array
                                    main_key = subkey # go deeper
                            else:
                                if main_key not in sub_db: 
                                    sub_db[main_key] = {}
                                if subkey == sep_key[-1]: #if we've reached the end
                                    sub_db[main_key][subkey] = value
                                else:
                                    if subkey not in sub_db[main_key]:
                                        sub_db[main_key][subkey] = {} #create new dict and go deeper
                                    sub_db = sub_db[main_key]
                                    main_key = subkey
        return for_db


    def create_query(self,query,path=None):
        """
        transform query from html form (not flat already) into the Elasticsearch query
        path - for nested queries
        recursive
        """
        negation = False # whether the tilde was used
        conditions = []
        for key,value in query.items():
            if path is None: #if it's the first level
                new_path = key
            else:
                new_path = path+'.'+key
            if type(value) != dict: # not a dict - it can be the value of the field (value to search for) or a list of nested dicts
                if type(value) == list and type(value[0]) == dict: # a list of nested dicts
                    for i in value:
                        conditions.append({'nested':{'path':new_path,'query':self.create_query(i,new_path)['query']}})
                else:
                    if type(value) == list: # sometimes values are passed as arrays of one element
                        value = value[-1]
                    w_r = self.check_regexp(value)
                    if w_r == 'wildcard':
                        conditions.append({'wildcard':{new_path:value}})
                    elif w_r == 'regexp':
                        conditions.append({'regexp':{new_path:value}})
                    elif key == 'example':
                        conditions.append({'match':{new_path:value}})
                    else:
                        conditions.append({'term':{new_path:value}})
            else: # if value is a dict
                conditions.append({'nested':{'path':new_path,'query':self.create_query(query[key],new_path)['query']}})
        
        # we get a list of conditions which we pass to the overall query
        return {'query':{'bool':{'filter':conditions}}}



    def mapping_paths(self,d,paths,path='',mode='empty_form',mapping=None): #mode - form, empty_form, search, mapping
        """
        create a structure for html divs and flat html form from complex structure according to the needs of different modes
        """
        if mapping is not None: # if we have a mapping from which we get missing values (empty fields - for 'form' mode)
            for key,value in mapping.items(): # add missing values to the resulting dict
                if key not in d:
                    d[key] = value
        for key,value in d.items():
            paths[key] = dict()
            if key == 'baseverb': # we need only values, not fields in the form
                if mapping is None:
                   paths[key][key] = ''
                else:
                    paths[key][key] = value
                continue
            if not path:
                new_path = key 
            else:
                new_path = path+'.'+key
            if mode != 'form': # no values in initial data
                if value['type'] == 'nested': # if we have a mapping as initial data
                    new_path = new_path+'.1' # nested type implies possible lists
                    self.mapping_paths(d[key]['properties'],paths[key],new_path,mode) # recursive call for a nested object
                else:
                    if mode == 'mapping': # no field name is required, only doc structure
                        paths[key] = ''
                    else: # wrapping div is needed further (new_path - future field name)
                        paths[key][new_path] = ''
            else: # non-empty values in data
                if type(value) == dict: 
                    self.mapping_paths(d[key],paths[key],new_path+'.1',mode,mapping[key]) # recursive call for a nested object
                elif type(value) == list: # list of nested objects
                    paths[key] = [dict() for _ in range(len(value))]
                    for i in range(len(value)):
                        self.mapping_paths(d[key][i],paths[key][i],new_path+'.'+str(i+1),mode,mapping[key]) # recursive call for each object in the list
                else:
                    paths[key][new_path] = value # add value to the structure + wrapping div (new_path - future field name)
        return paths
    
