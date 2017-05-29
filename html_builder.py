# -*- encoding: utf-8 -*-

from db_client import DBClient
from lxml import etree
import json 
import codecs

d = DBClient()


class HTMLBuilder(object):
    """
    build htmls which include forms - search, add, edit + view mode
    saves hierarchial structure of data using embedded divs
    """
    def __init__(self):
        info = json.loads(codecs.open("html_info.json",'r',encoding='utf-8').read())
        self.fields = info['field_types']
        self.blocks = info['blocks']
        self.subblocks = info['subblocks']
        self.order = info['order']
        self.labels = info['labels']
        self.choices = info['choices']
        self.from_db = info['choices_from_db']
        self.buttons = info['buttons']
        self.parser = etree.HTMLParser()

        
    def create_html(self,values,mode,verb_id=None): #mode - search, add, update, view
        """
        create hierarchial structure of divs + form fields from dict
        """
        basehtml = codecs.open('base.html','r',encoding='utf-8') # a base file into which built structure will be integrated
        root = etree.parse(basehtml,self.parser).getroot()
        title = etree.Element('title')
        header = etree.Element('h1')
        headers = {"search": u"Поиск", "add": u"Добавить глагол", "update": u"Изменить глагол", "view": u"Посмотреть глагол"}
        header.text = headers[mode]
        title.text = headers[mode]
        root[0].append(title)
        root[1][0].append(header)
        if verb_id is not None: # if we want to edit an existing verb
            edit = etree.Element('a',id='edit',href='/'+verb_id+'/edit')
            edit.text = u'Редактировать'
            root[1][0].append(edit)
        show_all = etree.Element('div', attrib={'onclick':'show_all()','class':'button-divs'})
        show_all.text = u'Раскрыть все разделы'
        root[1][0].append(show_all)
        hide_all = etree.Element('div', attrib={'onclick':'hide_all()','class':'button-divs'})
        hide_all.text = u'Скрыть все разделы'
        root[1][0].append(hide_all)
        if mode == 'search': # if search, redirect to results
            root[1][0].append(etree.Element('form', action='/results'))
        else: # if not search, use POST
            root[1][0].append(etree.Element('form', method='POST'))
        root = root[1][0][-1] # get into the form
        for block,label in self.blocks: # upper-level blocks are defined in the html_info.json
            if mode not in ('update','view') and 'derivatives' in block: # include derivatives only in view and update modes
                continue
            header = etree.Element('h2', onclick='show_block(this)')
            header.text = label
            root.append(header) # add block name
            root.append(etree.Element('img', attrib={'src':'/static/arrow_up.png','class':'arrow','onclick':'show_block(this)'}))
            root.append(etree.Element('div',attrib={'class':'block'})) # create a block div
            for i in block:
                if mode == 'search' and i == 'baseverb': # not searching by baseverb (no sense)
                    continue
                root[-1].append(etree.Element('div',id=i))
                self.traverse(root[-1][-1],values[i],parent=i,mode=mode) # go deeper into contents of block element
                
                #in 'add' and 'update' - add more subblocks and create lists of nested objects in the database
                if i in self.buttons and i not in self.subblocks and mode not in ('search', 'view'):
                    button = etree.Element('button',attrib={'class':'button add','type':'button','onclick':"add(this)"})
                    button.text = u'Добавить поле в раздел "' + label + '"'
                    root[-1].append(button)
        
        # submit and reset buttons
        if mode == 'search':
            root.append(etree.Element('input', attrib={'type':'submit', 'value':u'Искать','class':'button submit'}))
            b = etree.Element('input', attrib={'type':'reset','class':'clear'})
            root.append(b) 
            root = root.getparent()
            root = self.append_select_divs(root)
        elif mode != 'view':
            root.append(etree.Element('div',id='message'))
            b = etree.Element('button', attrib={'type':'button', 'onclick':'change_verb()','class':'button submit'})
            b.text = u'Сохранить'
            root.append(b)
            c = etree.Element('input', attrib={'type':'reset','class':'clear'})
            root.append(c)
        root = list(root.iterancestors())[-1]
        ready_html = etree.tostring(root, pretty_print=True, encoding='unicode', method='html') # return tree as a string
        return ready_html


    def traverse(self,root,values,parent,mode):
        """
        depth-first traversal of complex structure necessary to display
        parent - id of parent node and a database field name
        """
        delayed = [] # nested objects and lists of nested objects
        if type(values) == list and type(values[0]) == dict:
            delayed = [(parent,values)] # we'll consider nested objects later
        else:
            if parent in self.order: # we have the order of fields and subblocks in a parent block
                keys = [x for x in self.order[parent] if x in values.keys()]
            else: # if the order is not defined in the file
                keys = values.keys()
            for key in keys:
                value = values[key]
                if type(value) == dict or (type(value) == list and type(value[0]) == dict):
                    delayed.append((key,value)) # we'll consider nested objects later
                else:
                    root.attrib['class'] = 'terminal' # parent node is the div wrapping the field (thus no padding in css etc)
                    if parent in self.fields:
                        field_type = self.fields[parent]
                    else:
                        field_type = 'text'
                    if field_type == 'a': # only for derivatives
                        if value:
                            for deriv in value:
                                one_d = etree.Element('a',href='/'+str(deriv[0])) # create links
                                one_d.text = deriv[0]
                                root.append(one_d)
                        continue
                    if field_type == 'textarea' and mode == 'search':
                        continue # skip examples in search mode
                    label = etree.Element('label') # add labels to fields
                    label.text = self.labels[parent]
                    root.append(label)
                    if mode == 'view': # for view - only text information, no forms
                        if type(value) == tuple: # if a baseverb - value in format (verb,id)
                            if value:
                                info_span = etree.Element('a',href='/'+str(value[0]))
                                info_span.text = value[0]
                            else: # can be empty - the baseverb has been deleted
                                info_span = etree.Element('span')
                                info_span.text = '--'
                        else:
                            info_span = etree.Element('span')
                            if not value: # empty field
                                info_span.text = '--'
                            else:
                                info_span.text = value
                        root.append(info_span)
                        continue
                    select_button = None
                    if 'select' in field_type:
                        if mode == 'search':
                            field_type = 'text' # all fields of text type (for using regexps) + choose from existing values - checkboxes + JS
                            select_button = etree.Element('button',attrib={'class':'button choose_button ','type':'button','onclick':"show_choices(this)"})
                            select_button.text = u'Выбрать'
                        else:
                            root = self.append_select(root,values,field_type,parent,key,value) # there are some special issues concerning select field types
                    if field_type == 'textarea': # examples
                        t = etree.Element('textarea',attrib={'name':key})
                        t.text = value
                        root.append(t)
                    if field_type == 'text':
                        root.append(etree.Element('input',attrib={'name':key,'value':value,'type':'text'}))
                        if select_button is not None: # for search mode
                            root.append(select_button)
        
        # dealing with nested objects
        for item in delayed:
            if item[0] == parent: # we added a redundant div at the previous level - delete it
                p = root.getparent()
                p.remove(root)
                root = p
            # if we have some subblocks defined in html_info.json (transitivity stuff)
            if item[0] in self.subblocks and item[0] != parent:
                subheader = etree.Element('h3', onclick='show_block(this)')
                subheader.text = self.subblocks[item[0]]
                root.append(subheader)
                root.append(etree.Element('img', attrib={'src':'/static/arrow_down.png','class':'arrow','id':'sub_arrow','onclick':'show_block(this)'}))
                root.append(etree.Element('div',attrib={'class':'subblock', 'style':'display:none'})) # add one more div to handle a whole subblock
                root = root[-1]
            if type(item[1]) == dict: # one nested object
                root.append(etree.Element('div',id=item[0]))
                self.traverse(root[-1],values[item[0]],parent=item[0],mode=mode) # recursive call for a nested object
            if type(item[1]) == list: # several nested objects
                for j in item[1]:
                    root.append(etree.Element('div',id=item[0])) 
                    self.traverse(root[-1],j,parent=item[0],mode=mode) # recursive call for each nested object
            
            if item[0] in self.buttons and item[0] in self.subblocks: # if we want to add a subblock and create a list of nested objects in the database
                if (mode == 'search' and item[0] != 'actors'):
                    continue # no arrays in search except for adding actors (other arrays are not needed)
                if mode != 'view':
                    button = etree.Element('button',attrib={'class':'button add','type':'button','onclick':"add(this)"})
                    button.text = u'Добавить поле в раздел "' + self.subblocks[item[0]] + '"'
                    root.append(button)
                root = root.getparent()
            
        return root


    def append_select(self,root,values,field_type,parent,key,value):
        """
        handling select fields
        """
        choices = self.make_choices(parent) # form necessary choices
        if 'select' in field_type:
            sel = False # whether the option is selected
            root.append(etree.Element('select',attrib={'name':key}))
            if type(value) == tuple: # baseverb
                if value:
                    value = (value[0],str(value[1]))
            for i in choices:
                if i == value:
                    option = etree.Element('option',attrib={'selected':'True'})
                    sel = True
                else:
                    option = etree.Element('option')
                if type(i) == tuple:
                    if i:
                        option.text = i[0]
                        option.attrib['value'] = i[1]
                else:
                    option.text = i
                root[-1].append(option)
            if not sel:
                root[-1].insert(0,etree.Element('option',attrib={'value':'','selected':'True'})) # mark empty choice as selected
            else:
                 root[-1].insert(0,etree.Element('option',attrib={'value':''})) # just insert an empty option
        if field_type == 'select-text': # if we want to add other options manually
            if value in choices:
                value = ''
            label = etree.Element('label',attrib={'class':'other'})
            label.text = u'Другое'
            root.append(label)
            root.append(etree.Element('input',attrib={'name':key,'value':value,'type':'text'}))
        return root
                            
    def append_select_divs(self,root):
        """
        make a div with checkboxes form to choose options for search mode
        """
        for item in self.choices.keys():
            if item == 'baseverb': # not include baseverb
                continue
            root.append(etree.Element('div',attrib={'id':item+'_choose','style':"display:none",'class':'choose'}))
            root[-1].append(etree.Element('form'))
            ch = self.make_choices(item)
            for c in ch:
                c_html = etree.Element('input',type='checkbox',name=item+'_choice',value=c)
                c_html.tail = c
                root[-1][-1].append(c_html) # add into form
                root[-1][-1].append(etree.Element('br'))
            root[-1][-1].append(etree.Element('input',attrib={'type':"button",'value':u"Сохранить",'onclick':"handle_choices(this)",'class':'button save'}))
            close_button = etree.Element("button",attrib={'onclick':"close_choices(this)",'class':'button close'})
            close_button.text = u'Закрыть'
            root[-1].append(close_button)
        return root # return div with form
    
    def make_choices(self,parent):
        """
        database-specific function
        get all choices from file and from the database
        """
        if parent == "baseverb":
            choices = d.all_words()
        elif parent in ["derivation_affix","derivation_gloss"]:
            choices = d.all_derivs(parent)
        elif parent in ["case","role"]:
            paths = ['transitivity.models.actors.'+parent,
                     'antipassive.transitivity.models.actors.'+parent,
                     'incorporation.transitivity.models.actors.'+parent]
            choices = sorted(list(d.all_roles_or_cases(paths,parent) | set(self.choices[parent])))
        else:
            choices = self.choices[parent]
        return choices
