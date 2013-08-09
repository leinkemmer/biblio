#!/usr/bin/python

# import external libraries
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__),'external'))
sys.path.append(os.path.join(os.path.dirname(__file__),'settings'))
from  gscholar import pdflookup, FORMAT_BIBTEX
from bib import Bibparser, clear_comments
from settings import *

# something from the stdlib
import json, tempfile, re, traceback
from argparse import ArgumentParser
from os import environ, system

class Bibdb:
	bibliography_file = 'bibliography.json'
	db = []
	def load_db(self):
		try:
			with open(self.bibliography_file) as fh:
				bib = fh.read()
			self.db = json.loads(bib)
			print 'loaded %d items from file'%len(self.db)
		except IOError:
			print 'WARNING: file does not exists. Returning empty list.'
	def save_db(self):
		text = json.dumps(self.db, indent=4)
		with open(self.bibliography_file, 'w') as fh:
			fh.write(text)
	def list_bibliography(self):
		for bibitem in self.db:
			try:
				s = ''
				authorlist = bibitem['author']
				for i,dictentry in enumerate(authorlist):
					s += ', ' if i==0 else ''
					s += dictentry['given'] + ' ' + dictentry['family'];
				s += '. ' + bibitem['title'] + '. ' + bibitem['issued']['literal']
				try: #optional
					s += '. ' + bibitem['journal']
					s += ', ' + bibitem['volume']
					s += ', ' + bibitem['number']
					s += ', ' + bibitem['page']
				except:
					pass
				print s
			except:
				print 'entry is missing information',traceback.print_exc()	
	def bibentry_to_bibtex(self,bibitem):
		bibtex = ''
		# this is redundant as we put the item in the bibtex file for each key saved
		for key in bibitem['id'].split(':'):
			# article type
			bibtex += '@%s{%s,\n'%(bibitem['type'],key)
			# author
			s = ''
			authorlist = bibitem['author']
			for i,dictentry in enumerate(authorlist):
				s += ' and ' if i!=0 else ''
				s += dictentry['given'] + ' ' + dictentry['family'];
			bibtex += 'author = {%s}\n'%s
			# title
			bibtex += 'title = {{%s}}\n'%bibitem['title']
			try: #optional
				bibtex += 'journal = {%s}\n'%bibitem['journal']
				bibtex += 'volume= {%s}\n'%bibitem['volume']
				bibtex += 'number= {%s}\n'%bibitem['number']
				bibtex += 'page= {%s}\n'%bibitem['page']
			except:
				pass
		return bibtex + '}'
	def extract_bibtex(self,file):
		with open(file) as fh:
			text = fh.read()
		# used to build a regex key to modify the .tex file
		regexfinal = []
		# process keys one by one
		biblist = []
		for m in re.finditer(r"\\cite\{(.+?)\}",text):
			key = m.group(1)
			# naive matching algo
			match = []
			try:
				for bibitem in self.db:
					bi_keys = bibitem['id'].split(':')
					if key in bi_keys:
						match.append(bibitem)
						break
			except Exception:
				pass
			if match == []:
				print 'no match found for %s'%key
				continue
			elif len(match)==1:
				print '%s (%s)'%(match[0]['title'],key)
				choice = 0
				biblist.append(match[0])
			else:
				for m in match:
					print m
				choice = int(raw_input('please enter index of desired reference'))
				if choice >= len(match):
					continue
				biblist.append(match[1])
			if key != match[choice]['id'].split(':')[0]:
				regexfinal.append("sed -i s,\\cite\{%s\},\\cite\{%s\},g %s"%(key,match[choice]['id'].split(':')[0],file))
		# change the tex file (if user agrees)
		if len(regexfinal)>0:
			print '\n'.join(regexfinal)
			answer = raw_input("perform replacement? [y,n]")
			if answer == 'y':
				for command in regexfinal:
					os.system(command)
		else:
			print 'all references have a full key'
		# create bibtex file
		with open(file+'.bib','w') as fh:
			for item in biblist:
				fh.write(self.bibentry_to_bibtex(item) + '\n')
		

	def add_entry_from_file(self,file):
		# get bibtex code from pdf and google scholar
		bibitem = pdflookup(file, False, FORMAT_BIBTEX)[0]
		# parse bibtex to dictionary format
		bibitem = clear_comments(bibitem)
		bibparser = Bibparser(bibitem)
		bibparser.parse()
		bibitem = bibparser.records.values()
		# standard formatting rules are applied
		format_bibitem(bibitem[0])
		# a key is computed
		print bibitem[0]
		compute_key(bibitem[0])
		print bibitem[0]
		# allow the user to make modifications
		tmpfile = tempfile.NamedTemporaryFile().name + ".json"
		with open(tmpfile, "w") as fh:
			fh.write(json.dumps(bibitem, indent=4))
		try:
			editor = environ['EDITOR']
		except KeyError:
			editor = 'vim'
		# modify and read back the filea
		loop = True
		while loop:
			system(editor + ' ' + tmpfile)
			with open(tmpfile) as fh:
					bibitem = fh.read()
			try:
				bibitem = json.loads(bibitem)
				print json.dumps(bibitem, indent=4)
				input = raw_input("Save this item to the database? [y,n]")
				if input == 'y':
					self.db += bibitem
					self.save_db()
					loop = False
					print 'saved bibliography entry'
					try:
						rename_file(file, bibitem[0])
					except:
						print 'renaming file failed', traceback.print_exc()
				elif input == 'n':
					loop = False
			except Exception as detail:
				print 'ERROR: could not parse modified json data', detail
				raw_input('press enter to continue')
	def cleanup_bibliography(self):
		print 'not yet implemented'
	def recompute_keys(self):
		print 'not yet implemented'

# main function
if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('-l', '--list', \
			help='list all references in the bibliography', \
			action='store_true', default=False)
	parser.add_argument('-c', '--cleanup', \
			help='cleanup database (suggests the removal of duplicates)', \
			action='store_true', default=False)
	parser.add_argument('-k', '--key', \
			help='recompute keys (useful if entries have been added by hand)', \
			action='store_true', default=False)
	parser.add_argument('-b', '--bibtex', \
			help='generate a bibtex file from the latex references', \
			nargs=1, default=False)
	parser.add_argument('file', \
			help='filename to add to the bibliography', \
			nargs='?') # optional

	args = parser.parse_args()
	db = Bibdb()
	db.load_db()
	
	if args.list:
		db.list_bibliography()
	elif args.cleanup:
		db.cleanup_bibliography()
	elif args.key:
		db.recompute_key()
	elif args.bibtex:
		db.extract_bibtex(args.bibtex[0])
	elif args.file != None:
		db.add_entry_from_file(args.file)
	else:
		print ""

