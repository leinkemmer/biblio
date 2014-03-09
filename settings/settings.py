import traceback
import os

def format_firstname(given):
	"""Use C. Lubich instead of Christian Lubich
	"""
	given_plain = given.replace(" ","").replace("\t","")
	if given == '':
		return given
	if given.find('.') != -1:
		return given # most likely already ok
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

def format_journal(full_name):
	"""Tries to find an abbreviation from a list of journal names
	"""
	with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../journal-list.dict")) as fh:
		for line in fh:
			l = line.split(',')
			if len(l) == 2:
				[name, abbr] = line.split(',')
				name = str(name.strip())
				abbr = str(abbr.strip())
			else:
				pass # we don't use these for now
			#print '"%s" "%s" "%s"'%(name, abbr, full_name)
			if name.lower() == str(full_name).lower() or abbr == str(full_name):
				return abbr
	return ''

