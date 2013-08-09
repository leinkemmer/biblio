#!/usr/bin/python
output_dictionary = []

import csv
with open("mathematical-journals-ams.csv", "rb") as csvfile:
	csvreader = csv.reader(csvfile,delimiter=',',quotechar='"')
	for row in csvreader:
		try:
			if row[0].strip()[-1] == '.':
				output_dictionary.append(row[1].strip() + ',' + row[0].strip())
		except:
			pass

with open("journal_abbreviations_jabref.txt", "r") as f:
	for line in f:
		try:
			[a,b] = line.split('=')
			output_dictionary.append(a.strip() + ',' + b.strip())
		except:
			pass


with open('journal-list.dict','w') as f:
	for entry in output_dictionary:
		f.write(entry + '\n')
