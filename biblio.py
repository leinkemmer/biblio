#!/usr/bin/python

# standard library imports
from os import system
from os.path import join,expanduser,basename,splitext,dirname
from argparse import ArgumentParser
import sys
import traceback
import json
# external modules
sys.path.append(join(dirname(__file__),'external'))
# local modules
from misc import *
import urllib2

#
# functions for file handling
#
def load_config(filename):
	"""Loads config file given by filename and returns a dictionary.
	"""
	with open(filename) as f:
		filename = expanduser(f.read().rstrip('\n'))
	ending = splitext(filename)[1]
	return {'directory':dirname(filename), 'file':filename, 'ending':ending}

def load(filename):
	'''Load bibliography database from a file.
	'''
	with open(filename) as f:
		text = f.read()
	return json.loads(unicode2bibtex(text))

def save(filename,db):
	'''Save database to a file
	'''
	text = json.dumps(db,indent=4)
	with open(filename,'w') as f:
		f.write(text)

def load_bibnote(filename):
	'''Load the bibnote format
	'''
	with open(filename) as f:
		text = f.read()
	orig = json.loads(unicode2bibtex(text))
	entries = orig['bibliography']
	values = entries.values()
	swap_key(values, 'key', 'id')
	for it in values:
		it['author'] = authors_to_list(it['author'])
	return [values, entries.keys(), orig]

def save_bibnote(filename, db, orig, keys):
	'''Save in bibnote format
	'''
	# prepare
	swap_key(db, 'id', 'key')
	for it in db:
		it['author'] = list_to_authors(it['author'])
	entries = dict(zip(keys, db))
	orig['bibliography'] = entries
	# save
	text = json.dumps(orig,indent=4)
	with open(filename,'w') as f:
		f.write(text)


def ls(db):
	''' Outputs a colorized list of the biblography entries
	'''
	for it in db:
		n = safedict(names, it, 'Author information unavailable')
		t = safedict(lambda x: x['title'], it, 'Title unavailable')
		y = safedict(year, it, 'Year unavailable')
		j = safedict(journal, it, 'Journal/Publisher information unavailable')
		print "%s|%s|%s|%s"%(n,t,y,j)

def tobib(it, key):
	'''Returns a string in the bibtex format given an item in the bibliography
	database. Note that the key used has to be supplied to this function
	'''
	ty = it['type']
	if ty == 'article':
		return bibstr(it,ty,key,['author','title','year','journal'],['volume','number','pages'])
	elif ty == 'book':
		return bibstr(it,ty,key,['author','title','year','publisher'],['volume','edition'])
	elif ty == 'book':
		return bibstr(it,ty,key,['author','title','year','school'],[])
	else: # this is a default template
		return bibstr(it,ty,key,['author','title','year'],[])

def ls_bib(db):
	''' Outputs a colorized list of the biblography entries
	'''
	for it in db:
		try:
			key = unique_key(db,it)
			print tobib(it,key)
		except KeyError:
			stderr('ERROR: could not construct bibtex entry for item \n%s\n'%s)

def format_bibitem(it):	
	it['id'] = generate_key(it)
	format_authors(it)
	matched = format_journalsabbr(it)
	return matched


def upd(db, db_dir):
	'''Updates the keys from whatever is in the database and renames the files
	if necessary
	'''
	# update key and apply formatting rule
	unmatched_journals = []
	for it in db:
		try:
			if 'update' in it.keys() and it['update'] == 'false':
				print 'key %s ignored'%it['key']
			else:
				matched = format_bibitem(it)
				if matched == False and 'journal' in it.keys():
					unmatched_journals.append(it['journal'])
		except KeyError:
			print 'ERROR: could not compute key of item \n%s\n'%json.dumps(it,indent=4)

	# move files
	for it in db:
		key = unique_key(db,it)
		try:
			file = basename(it['file'])
			new_file = key+'.pdf'
			if new_file != file:
				verbose('%s -> %s'%(file,new_file))
				#system(u'mv -n "%s" "%s"'%(db_dir+file,db_dir+new_file))
		except KeyError:
			print 'no file given for entry with id %s'%key
		it['file'] = new_file
	# output
	if len(unmatched_journals) > 0:
		print '\nThe following journals are unmatched in the database: %s'%'\n\t'.join(set(unmatched_journals))


def user_accept(db, it):
	while True:
		text = external_edit(json.dumps(it, indent=4), '.json')
		try:
			it = json.loads(text)
			key = generate_key(it)
			it['id'] = key
			print json.dumps(it, indent=4)
			input = raw_input("Save this item to the database? [y,n]")
			if input == 'y':
				db += [it]
				print 'Item has been saved in bibliography.'
				break
			elif input == 'n':
				break	
		except Exception as detail:
			print 'ERROR: could not parse modified json data', detail
			input = raw_input('Edit json? [y,n]')
			if input == 'n':
				break


def add_interactive(db, bibstring, file=''):
	it = bibtex2dict(bibstring)
	it['id'] = 'XXX'
	if file != '':
		it['file'] = file
	format_bibitem(it)
	# ask user
	user_accept(db, it)
	
def add_bibtex(db, file):
	bibstring = read_text(file)
	for it in bibtex2dict(bibstring):
		db += [it]

def search_crossref(db):
	res = ''
	while True:
		s = raw_input('enter search term, the number to save, or q to quit: ')
		if s == 'q':
			return ''
		if s.isdigit():
			n = int(s)
			doi = res[n-1]['doi']
			print 'DOI: %s'%doi
			# get bibtex from doi.org
			request = urllib2.Request(doi,headers={'Accept': 'text/bibliography; style=bibtex'})
			bibtex = urllib2.urlopen(request).read()
			print bibtex
			it = bibtex2dict(bibtex)
			print json.dumps(it, indent=4)
			format_bibitem(it)
			# ask user
			user_accept(db, it)
			return
		res = urllib2.urlopen("http://search.crossref.org/dois?q=%s&sort=score"%s).read()
		res = json.loads(res)
		m = 1
		for x in res:
			print '[%d]\t%s'%(m,x['fullCitation'])
			m+=1
	return ''


#
# main program
#
if __name__ == "__main__":
	parser = ArgumentParser()
	subparsers = parser.add_subparsers(dest='sub',title='command',\
			description='''Use add --help to get additional information on
			               a specific command. The available commands are:''')
	p_ls = subparsers.add_parser('ls')
	p_bib = subparsers.add_parser('bib', description='C')
	p_upd = subparsers.add_parser('upd')
	p_add = subparsers.add_parser('add')
	p_add.add_argument('file', help='a pdf file')
	p_add.add_argument('bibstring', help='a bibtex entry (starting with @)')
	p_addbib = subparsers.add_parser('addbib')
	p_addbib.add_argument('bibfile', help='a .bib file')
	p_add = subparsers.add_parser('search')
	args = parser.parse_args()

	try:
		config = load_config(expanduser('~/.bibliorc'))
		verbose('Bibliography file: %s'%config['file'])
		if config['ending'] == '.bibnote':
			[db, keys, orig] = load_bibnote(config['file'])
		else:
			db = load(config['file'])
		verbose('Loaded %d items from file'%len(db))
	
		tobesaved = False
		if args.sub == 'ls':
			ls(db)
		elif args.sub == 'bib':
			ls_bib(db)
		elif args.sub == 'upd':
			upd(db, config['directory'])
			tobesaved = True
		elif args.sub == 'add':
			ending = splitext(args.file)[1]
			file   = basename(args.file)
			if ending == '.pdf':
				system('cp %s %s'%(file,join(config['directory'],file)))
				add_interactive(db, args.file, args.bibstring)
				tobesaved = True
			else:
				stderr('ERROR: file extension is not .pdf')
		elif args.sub == 'addbib':
			file = args.bibfile
			add_bibtex(db, file)
			print json.dumps(db,indent=4)
			tobesaved = True
		elif args.sub == 'search':
			js = search_crossref(db)
			tobesaved = True

		if tobesaved == True:
			if config['ending'] == '.bibnote':
				save_bibnote(config['file'],db,orig,keys)
			else:
				save(config['file'], db)


	except IOError as e:
		stderr('ERROR: cannot open:%s'%e.filename)
	except:
		stderr('ERROR: unknown, printing traceback')
		stderr(traceback.print_exc())


