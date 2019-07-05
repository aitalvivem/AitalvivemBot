#-*-coding:utf-8-*
import csv
import pywikibot
import functionsmain.APIfunction

# i set the path of the .csv file with the lexicographical datas
fname = #PATH
# i get the file
file = open(fname, 'rt', encoding='utf-8')

# i take the files datas using csv.reader and store it in 'lecteur'
try:
	lecteur = csv.reader(file, delimiter="§") 
	# for row in lecteur:
		# i retrieve the id of the lexeme (if the lexeme don't exists, i create it)
		# idLex = functionmain.APIfunction.chercheLex(row[2], row[5])
                
		# if row[1] != row[2]
			# add the form
			# functionmain.APIfunction.createForm(idLex, row[1], rox[3])

finally:
	# close the .csv file
	file.close()
	

