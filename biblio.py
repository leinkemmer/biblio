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
sys.path.append(join(dirname(__file__),'settings'))
from settings import *

#
# functions for file handling
#
def load_config(filename):
	"""Loads config file given by filename and returns a dictionary.
	"""
	with open(filename) as f:
		dir = expanduser(f.read().rstrip('\n'))
	return {'directory':dir, 'file':join(dir,'bibliography.json')}

def load(filename):
	'''Load bibliography database from a file.
	'''
	with open(filename) as f:
		text = f.read()
	return json.loads(text)

def save(filename,db):
	'''Save database to a file
	'''
	text = json.dumps(db,indent=4)
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
		print "%s||%s||%s||%s"%(n,t,y,j)

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


def upd(db, db_dir):
	'''Updates the keys from whatever is in the database and renames the files
	if necessary
	'''
	# update key
	for it in db:
		try:
			key = generate_key(it)
			it['id'] = key
		except KeyError:
			print 'ERROR: could not compute key of item \n%s\n'%it

	# move files
	for it in db:
		key = unique_key(db,it)
		try:
			file = basename(it['file'])
			new_file = key+'.pdf'
			if new_file != file:
				verbose('%s -> %s'%(file,new_file))
				system('mv -n "%s" "%s"'%(db_dir+file,db_dir+new_file))
		except KeyError:
			print 'no file given for entry with id %s'%key

		it['file'] = new_file

def add_interactive(db, file, bibstring):
	it = bibtex2dict(bibstring)
	it['id'] = 'XXX'
	it['file'] = file
	format_bibitem(it)
	# ask user
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
	args = parser.parse_args()
	
	try:
		config = load_config(expanduser('~/.bibliorc'))
		verbose('Bibliography file: %s'%config['file'])
		db = load(config['file'])
		verbose('Loaded %d items from file'%len(db))
		
		if args.sub == 'ls':
			ls(db)
		elif args.sub == 'bib':
			ls_bib(db)
		elif args.sub == 'upd':
			upd(db, config['directory'])
			save(config['file'], db)
			# save
		elif args.sub == 'add':
			ending = splitext(args.file)[1]
			file   = basename(args.file)
			if ending == '.pdf':
				system('cp %s %s'%(file,join(config['directory'],file)))
				add_interactive(db, args.file, args.bibstring)
				save(config['file'], db)
			else:
				stderr('ERROR: file extension is not .pdf')

	except IOError as e:
		stderr('ERROR: cannot open', e.filename)
	except:
		stderr('ERROR: unknown, printing traceback')
		stderr(traceback.print_exc())


