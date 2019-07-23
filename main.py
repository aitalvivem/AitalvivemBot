#-*-coding:utf-8-*
import csv
import pywikibot
import functionsmain.APIfunction

# I set the path of the .csv file with the lexicographical data and get the file
fname = # PATH
file = open(fname, 'rt', encoding='utf-8')


# I take the files datas using csv.reader and store it in 'lecteur'
try:
	lecteur = csv.reader(file, delimiter=";")
	
	for row in lecteur:
		lg = { 'libLg': row[0], 'codeLg': row[1], 'dial': row[7] }
		form = row[2]
		catGram = row[3]
		lemme = row[4]
		catGramL = row[5]
		catLex = row[6]
		
		# I get the id of the lexeme (if the lexeme don't exists, i create it) and then i get the data of the lexeme
		idLex = functionsmain.APIfunction.chercheLex(lemme, lg, catLex, catGram)
		infoLex = functionsmain.APIfunction.getLex(idLex)
		
		# I get the grammaticals category of the form
		catGramW = functionsmain.APIfunction.detailCat(catGram)
		
		formExists = False
		formeMatch = []
		
		# I check if the form already exists
		for formes in infoLex['formes']:
			if form == formes['representation']:
				formExists = True
				formeMatch += [formes]

		if formExists == True:
			memeCat = False
			for forme in formeMatch:
				if catGramW == forme['catGram']:
					memeCat = True
					formeMatch = forme
					break

			# if the form exists with the same grammatical category I check the dialect, if the dialecte don't exists I add it to the form
			if memeCat == True:
				if lg['dial'] != '':
					idDial = lg['dial']
					
					if idDial not in formeMatch['dialectes']:
						functionsmain.APIfunction.setDial(formeMatch['idForm'], lg)
						
			else:
				# else I create a new form
				functionsmain.APIfunction.createForm(idLex, form, catGram, lg)
				
		# else I create a new form		
		else:
			if form != lemme:
				functionsmain.APIfunction.createForm(idLex, form, catGram, lg)

finally:
	# close the file
	file.close()

