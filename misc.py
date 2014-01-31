import sys
import hashlib
import base64 
import unicodedata
from os import system, environ
import tempfile
from bib import Bibparser, clear_comments

#
# bibliography helper functions
#
def names(item, separator=', '):
	'''Returns a string with the author names separated by "separator"
	'''
	authorlist = item['author']
	return separator.join(
			[a['given']+' '+a['family'] for a in authorlist]
		)

def year(item):
	'''Returns the year of the publication
	'''
	return item['issued']['literal']

def journal(item):
	'''Returns a string specifying the journal information/publisher and the
	type (article, book, ...)
	'''
	if item['type'] == 'article':
		l = [item[x] for x in ['journal','volume','number','page'] if x in item.keys()]
		return ', '.join(l)
	elif item['type'] == 'book':
		return item['publisher']
	elif item['type'] == 'phdthesis':
		return 'PhD thesis'
	else:
		return 'unknown type'

def bibstr(it, typ, key, mandatory, optional):
	'''Constructs a bibtex string from item where the mandatory and optional
	elements are given as input arguments
	'''
	# we have to treat author, title, and year differently from the rest
	# as they require special formatting rules (author, title) or do not
	# share the same key as will be in the bibtex entry (year)
	n = 'author = {%s}'%names(it, separator=' and ')
	t = 'title = {{%s}}'%it['title']
	y = 'year = {%s}'%year(it)
	mandatory = [x for x in mandatory if x not in ['author','title','year']]
	
	l = [n,t,y]+['%s = {%s}'%(x,it[x]) for x in mandatory+optional if x in it.keys()]
	return '@%s{%s,\n'%(typ,key) + ',\n'.join(l) + '\n}\n'

def primary_key(it):
	return it['id'].split(':')[0]

def long_key(it):
	return it['id'].split(':')[1]

def unique_key(db,it):
	'''returns a unique key for the database under consideration
	'''
	key = primary_key(it)
	keys = [x for x in db if primary_key(x)==key]
	if len(keys)>1:
		return long_key(it)
	else:
		return key

def generate_key(it):
	m = hashlib.md5()

	s =  names(it)+it['title']+year(it)+journal(it)
	optional = ['volume','pages','school']
	s +=  str([it[x] for x in optional if x in it.keys()])
	hash32 = base64.b32encode(m.digest()).replace('=','') # also valid as a filename

	key = remove_bibtex(it['author'][0]['family'].lower())+year(it)

	return key+':'+key+'-'+hash32

#
# general utility
#

def stderr(message):
	'''Writes a message to stderr'''
	sys.stderr.write(str(message)+'\n')

def verbose(message):
	'''Program information that can be disabled in non-verbose mode'''
	stderr(message)

def safedict(f,args,message):
	'''Catches an exception of type KeyError and substitutes an appropriate 
	error messages instead
	''' 
	try:
		return f(args)
	except KeyError:
		return message


def remove_bibtex(s):
	'''Removes all {, \\, and whitespaces from string
	'''
	return s.replace('"','').replace('{','').replace('}','').replace('\\','').replace(' ','')

def get_environ(name, default):
	'''Get environment variables where a default is returned for a not-defined or empty
	variable
	'''
	try:
		editor = environ['EDITOR']
	except KeyError:
		return default
	if editor == '':
		return default
	else:
		return editor

def read_text(filename):
	'''Reads an entire text file
	'''
	with open(filename) as fh:
		text = fh.read()
	return text

def write_text(filename, text):
	'''Write a text to a file
	'''
	with open(filename, "w") as fh:
		fh.write(text)


def external_edit(text, ending):
	'''Calls an editor ($EDITOR or vim) in order to edit a piece of text
	'''
	editor = get_environ('EDITOR','vim')
	tmpfile = tempfile.NamedTemporaryFile().name+ending
	write_text(tmpfile, text)
	system(editor + ' ' + tmpfile)
	return read_text(tmpfile)

def bibtex2dict(bibstring):
	'''Converts bibtex to the json dictionary format used internally
	'''
	it = clear_comments(bibstring)
	bibparser = Bibparser(it)
	bibparser.parse()
	return bibparser.records.values()[0]


# not currently used
#def remove_accents(input_str):
#	'''removes accents and umlaute from the string. See
#	http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
#	'''
#    nkfd_form = unicodedata.normalize('NFKD', input_str)
#    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


