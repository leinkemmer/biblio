import hashlib, base64, traceback, os 

#
# rule 1:use C. Lubich instead of Christian Lubich
#	
def format_firstname(given):
	given_plain = given.replace(" ","").replace("\t","")
	if given.find('.') != -1:
		pass # most likely already ok
	if len(given_plain) == 1: # almost correct add a punctuation
		given = given_plain + "."
	elif given_plain == 2: # add punctuation
		given = given_plain[0] + "." + given_plain[1] + "."
	else:
		l = given.split(' ')
		for i,name in enumerate(l):
			l[i] = name.strip()[0] + "."
		given = ''.join(l)
	return given
def find_abbreviation(full_name):
	abbreviation = ''
	# ams list
	with open("/home/lukas/Dropbox/programming/rommie/journal-list.dict") as fh:
		for line in fh:
			l = line.split(',')
			if len(l) == 2:
				[name, abbr] = line.split(',')
			else:
				pass # we just don't use these for now
			if name == full_name:
				abbreviation = abbr.replace("\n","")
				break
		
	if abbreviation == '':
		print 'no match found'
	return abbreviation
def format_bibitem(item):
	# iterate over all authors and apply the specific rules
	try:
		authorlist = item['author']
		for i,dictentry in enumerate(authorlist):
			try:
				givenname = dictentry['given']
				authorlist[i]['given'] = format_firstname(givenname)
			except:
				print 'could not parse given name number %d properly - retaining original formatting.'%i
	except:
		print 'could not access author information.'

	# determine the journal (if possible) and change it to the abbreviation
	try:
		abbreviation = find_abbreviation(item['journal'])
		if abbreviation != '':
			item['journal'] = abbreviation
	except:
		print 'could not access journal information.', traceback.print_exc()

# rename the file according to the entry
def rename_file(file,item):
	try:
		file_new = ''
		authorlist = item['author']
		for i,dictentry in enumerate(authorlist):
			family_name = dictentry['family'].lower()
			file_new += family_name + ' '

		file_new += item['issued']['literal'] + ' ('
		file_new += item['title'] + ',' + item['journal'] + ').pdf'
		
		if file != file_new:
			os.system('mv -n "%s" "%s"'%(file,file_new))
		return file_new
	except:
		print 'could not parse given name number %d properly - retaining original formatting.'%i,traceback.print_exc()
		return file

# generate a number of keys separated by :, the first key should be unique
def compute_key(item):
	try:
		m = hashlib.md5()

		# we only use the author list, title, and journal information (including publication date)
		s = str(item['author']) + item['title'] + item['issued']['literal']
		# these are optional items
		s += item['journal'] if 'journal' in item else ''
		s += item['volume'] if 'volume' in item else ''
		s += item['page'] if 'page' in item else ''
		# compute md5 hash
		m.update(s)
		hash = base64.b64encode(m.digest()).replace('=','')
		# this should be a unique hash
		item['id'] = item['author'][0]['family'].lower() + item['issued']['literal'] + '-' + hash
		# simple hash
		item['id'] += ':' + item['author'][0]['family'].lower() + item['issued']['literal'] 
		# three digit number as hash (but possibly not unique in some dbs)
		dig = ( ord(m.digest()[0]) + 256*ord(m.digest()[1]) ) % 1000;
		item['id'] += ':' + item['author'][0]['family'].lower() + item['issued']['literal'] + '-' + str(dig)
	except:
		print 'could not parse bibliography entry - not able to generate key',traceback.print_exc()

