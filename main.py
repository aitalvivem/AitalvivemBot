#-*-coding:utf-8-*
import csv
import pywikibot
import functionsmain.APIfunction

# I set the path of the .csv file with the lexicographical data and get the file
fname = #PATH
file = open(fname, 'rt', encoding='utf-8')

# I take the files datas using csv.reader and store it in 'lecteur'
try:
	lecteur = csv.reader(file, delimiter="§")
	
	for row in lecteur:
		# I get the id of the lexeme (if the lexeme don't exists, i create it)
		idLex = functionmain.APIfunction.chercheLex(row[1], row[4], row[3], row[2])
                
		# if the form is different from the lemma
		if row[0] != row[1]
			# add the form
			functionmain.APIfunction.createForm(idLex, row[1], rox[3], row[5])

finally:
	# close the .csv file
	file.close()
