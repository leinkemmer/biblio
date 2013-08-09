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
	def extract_bibtex(self,file):
		with open(file) as fh:
			text = fh.read()
		print text
		# process keys one by one
		biblist = []
		for m in re.finditer(r"\\cite\{(.+?)\}",text):
			key = m.group(1)
			# naive matching algo
			match = ''
			try:
				for bibitem in self.db:
					if bibitem['author'][0]['family'].lower() + bibitem['issued']['literal'] == key.lower():
						match = bibitem
						break
			except Exception:
				pass
			if match == '':
				print 'no match found for %s'%key
			else:
				print '%s (%s)'%(match['title'],key)
				biblist.append(match)

		print '%d matches were found.'%len(biblist)
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
		compute_key(bibitem[0])
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
			print self.db
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


# main function
if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('-l', '--list', \
			help='list all references in the bibliography', \
			action='store_true', default=False)
	parser.add_argument('-c', '--cleanup', \
			help='cleanup database (suggests the removal of duplicates)', \
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
	elif args.bibtex:
		db.extract_bibtex(args.bibtex[0])
	elif args.file != None:
		db.add_entry_from_file(args.file)
	else:
		print ""

