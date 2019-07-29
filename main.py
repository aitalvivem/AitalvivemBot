#-*-coding:utf-8-*
import pywikibot
import functionsmain.APIfunction
import collections
from lxml import etree
import re
import sys


"""
This Bot was made to automaticaly import lexicograficals data to the wikidata database.
This Bot takes the datas from a xml file and uses the wikidata's framework pywikibot.
To identifie itself to the wikidata API, the Bot needs a valid wikidata account.

To run the bot use this command :
	cat <file.xml> | python3 <user_name> <password> (<lexeme_only>)

The lexeme_only parameter is facultative.

To find more informations please read the documentation.
You will find in the doc file the details of the functions used by the bot, an example of xml file, the detail of the utility of the lexeme_only parameter and a "known issues" section.
"""


# I set the user name and the password of the bots account
try:
	functionsmain.APIfunction.setCo(sys.argv[1], sys.argv[2])
except:
	print('Erreur : il vous faut renseigner le nom et le mot de passe du compte utilisateur du bot en paramètre')
	sys.exit()

# I look if the mode 'lexeme_only' is on
try:
	if sys.argv[3] == 'lexeme_only':
		lexeme_only = True
		# print('lexeme_only = True')# trace
	else:
		lexeme_only = False
		# print('lexeme_only = False')# trace
except:
	lexeme_only = False
	# print('lexeme_only = False') # trace


try:
	parser = etree.XMLParser(remove_blank_text=True, encoding="utf-8")
	tree = etree.parse(sys.stdin, parser)
except:
	print('Erreur : fichier XML vide ou illisible')
	sys.exit()


# I create the log.txt file which will contains the errors messages
fLog = open('log.txt','w')
err = 0
compteur = 0
comptForm = 0

# I get to the root of the xml file
tei = tree.getroot()


# for each lexeme
for lexeme in tei.xpath('.//form[@type="lemma"]'):
	compteur += 1
	
	# I get the id of the lexeme for the errors
	if lexeme.get("{http://www.w3.org/XML/1998/namespace}id"):
		idlexxml=lexeme.get("{http://www.w3.org/XML/1998/namespace}id")
	else:
		idlexxml=""
	
	# I get the infos of the language
	langs=lexeme.xpath('lang')
	
	# if there is no language tag, I send an error and jump to the next lexeme
	if len(langs)==0:
		fLog.write('erreur fichier source lexème "'+idlexxml+'" : il doit y avoir une balise <lang> sous les <form type="lemma">\n')
		err += 1
		continue
	else:
		lang=langs[0]
		libLg=lang.get('norm')
		codeLg=lang.text
		
		# if the language tag has no code or Q-id, I send an error and jump to the next lexeme
		if libLg==None or codeLg==None or codeLg=="":
			fLog.write('erreur fichier source lexème "'+idlexxml+'" : la balise <lang> ne peut être vide et elle doit avoir un attribut "norm"\n')
			err += 1
			continue
		
		# if the Q-id is not valid, I send an error and jump to the next lexeme
		if not re.search(r'^Q([0-9]+)$', codeLg):
			fLog.write('erreur fichier source lexème "'+idlexxml+'" : Qid de langue "'+codeLg+'" invalide\n')
			err += 1
			continue
		
		lg={ 'libLg':libLg , 'codeLg':codeLg }
	
	# i get the spelling
	orths=lexeme.xpath('orth')
	
	# if there is no spelling tag, I send an error and jump to the next lexeme
	if len(orths)==0:
		fLog.write('erreur fichier source lexème "'+idlexxml+'" : il doit y avoir une balise <orth> sous les <form type="lemma">\n')
		err += 1
		continue
	else:
		orth=orths[0]
		lemme=orth.text
		
		# if the spelling tag is empty, I send an error and jump to the next lexeme
		if lemme==None or lemme=="":
			fLog.write('erreur fichier source lexème "'+idlexxml+'" : la balise <orth> ne peut être vide\n')
			err += 1
			continue
	
	# I get the nature (cats)
	cats=lexeme.xpath('pos')
	
	# if there is no nature tag, I send an error and jump to the next lexeme
	if len(cats)==0:
		fLog.write('erreur fichier source lexème "'+idlexxml+'" : il doit y avoir une balise <pos> sous les <form type="lemma">\n')
		err += 1
		continue
	else:
		cat=cats[0]
		catLex=cat.text
		
		# if the pos tag is empty, I send an error and jump to the next lexeme
		if catLex==None or catLex=="":
			fLog.write('erreur fichier source lexème "'+idlexxml+'" : la balise <pos> ne peut être vide\n')
			err += 1
			continue
		
		# if the Q-id is not valid, I send an error and jump to the next lexeme
		if not re.search(r'^Q([0-9]+)$', catLex):
			fLog.write('erreur fichier source lexème "'+idlexxml+'" : Qid de nature "'+catLex+'" invalide\n')
			err += 1
			continue
	
	# I get the claims if its needed
	declaLex = {}
	for relation in lexeme.xpath('listRelation/relation'):
		prop=relation.get('name')
		concept=relation.get('passive')
		
		if prop==None or concept==None:
			fLog.write('erreur fichier source lexème "'+idlexxml+'" : la balise <relation> doit avoir un attribut "name" et un attribut "passive"\n')
			err += 1
			continue
		
		# if the Q-id is not valid, I send an error and jump to the next lexeme
		if concept!=None and not re.search(r'^Q([0-9]+)$', concept):
			fLog.write('erreur fichier source lexème "'+idlexxml+'" : Qid "'+concept+'" invalide\n')
			err += 1
			continue
		
		# if the P-id is not valid, I send an error and jump to the next lexeme
		if prop!=None and not re.search(r'^P([0-9]+)$', prop):
			fLog.write('erreur fichier source lexème "'+idlexxml+'" : Pid "'+prop+'" invalide\n')
			err += 1
			continue
		
		if prop not in declaLex:
					declaLex[prop]=set()
				
		declaLex[prop].add(concept)
	
	print('\ntraitement du lexeme numéro', compteur, ':', lemme) # trace
	# I get the L-id of the lexeme (if the lexeme don't exists, i create it) and then i get the data of the lexeme
	idLex, chercheLerr = functionsmain.APIfunction.chercheLex(lemme, lg, catLex, declaLex)
	
	# if there were an error when researching the lexeme, I send an error and jump to the next lexeme
	if chercheLerr==1:
		fLog.write('erreur lexème "'+idlexxml+'" : erreur lors de la recherche du lexeme\n')
		err += 1
		continue
	# if there were an error while creating, I send an error and jump to the next lexeme
	elif chercheLerr==2:
		fLog.write('erreur lexème "'+idlexxml+'" : erreur lors de la creation du lexeme\n')
		err += 1
		continue
	# if there were an error in the function getQidCat, I send an error and jump to the next lexeme
	elif chercheLerr==3:
		fLog.write('erreur lexème "'+idlexxml+'" : erreur dans la fontion getQidCat lors de la creation du lexeme\n')
		err += 1
		continue
	# if there were an error while adding a claim, I send an error and jump to the next lexeme
	elif chercheLerr==4:
		fLog.write('erreur lexème "'+idlexxml+'" : erreur dans la fontion setClaim lors de la creation du lexeme\n')
		err += 1
		continue
	
	infoLex = functionsmain.APIfunction.getLex(idLex)
	
	# si il y a une erreur dans la récupération des infos du lexeme, on envoie une erreur et on passe au lexème suivant
	if infoLex==1:
		fLog.write('erreur lexème "'+idlexxml+'" : erreur lors de la récupération des infos du lexeme\n')
		err += 1
		continue
	
	# if lexeme_only is not on, I add the forms
	if not lexeme_only:
		# print('paramètre lexeme_only renseigné, j\'ajoute les formes') # trace
		for flexion in lexeme.xpath('form[@type="inflected"]'):
			comptForm += 1
			
			# I get the id of the form for the errors
			if flexion.get("{http://www.w3.org/XML/1998/namespace}id"):
				idformxml=flexion.get("{http://www.w3.org/XML/1998/namespace}id")
			else:
				idformxml=""
			
		
			# I get the spelling
			orthfs=flexion.xpath('orth')
			
			# if there is no spelling tag (orth), I send an error and jump to the next form
			if len(orthfs)==0:
				fLog.write('erreur fichier source lexème "'+idlexxml+'" forme "'+idformxml+'" : il doit y avoir une balise <orth> sous les <form type="inflected">\n')
				err += 1
				continue
			else:
				orthf=orthfs[0]
				form=orthf.text
				
				# if the orth tag is empty, I send an error and jump to the next form
				if form==None or form=="":
					fLog.write('erreur fichier source lexème "'+idlexxml+'" forme "'+idformxml+'" : la balise <orth> ne peut être vide\n')
					err += 1
					continue
			
			# I get the grammaticals features
			infosGram = []
			for gram in flexion.xpath('gramGrp/gram'):
				infoGram=gram.text
				
				# if the gram tag id empty, I send an error and jump to the next form
				if infoGram==None or infoGram=="":
					fLog.write('erreur fichier source lexème "'+idlexxml+'" forme "'+idformxml+'" : la balise <gram> ne peut être vide\n')
					err += 1
					continue
			
				# if the Q-id is not valid, I send an error and jump to the next form
				if infoGram!=None and not re.search(r'^Q([0-9]+)$', infoGram):
					fLog.write('erreur fichier source lexème "'+idlexxml+'" forme "'+idformxml+'" : Qid d\'information grammaticale "'+infoGram+'" invalide\n')
					err += 1
					continue
				
				infosGram.append(infoGram)
		
			# if get the claims if its needed
			declaForm = {}
			for relation in flexion.xpath('listRelation/relation'):
				prop=relation.get('name')
				concept=relation.get('passive')
				
				if prop==None or concept==None:
					fLog.write('erreur fichier source lexème "'+idlexxml+'" forme "'+idformxml+'" : la balise <relation> doit avoir un attribut "name" et un attribut "passive"\n')
					err += 1
					continue
				
				# if the Q-id is not valid, I send an error and jump to the next form
				if concept!=None and not re.search(r'^Q([0-9]+)$', concept):
					fLog.write('erreur fichier source lexème "'+idlexxml+'" forme "'+idformxml+'" : Qid "'+concept+'" invalide\n')
					err += 1
					continue
				
				# if the P-id is not valid, I send an error and jump to the next form
				if prop!=None and not re.search(r'^P([0-9]+)$', prop):
					fLog.write('erreur fichier source lexème "'+idlexxml+'" forme "'+idformxml+'" : Pid "'+prop+'" invalide\n')
					err += 1
					continue
				
				if prop not in declaForm:
					declaForm[prop]=set()
				
				declaForm[prop].add(concept)
			
			print('--traitement de la forme numéro', comptForm, ':', form) # trace
		
			# I check if the form exists
			formExists = False
			formeMatch = []

			# if the form exists I check the grammaticals features
			for formes in infoLex['formes']:
				if form == formes['representation']:
					formExists = True
					formeMatch += [formes]

					
			# if the grammaticals features are the same
			if formExists == True:
				
				# print('main : la forme existe') # trace
				
				memeCat = False
				for forme in formeMatch:
					if collections.Counter(infosGram) == collections.Counter(forme['catGram']):
						memeCat = True
						formeMatch = forme
						continue

				# if the grammaticals features are the same (the form may be in an other dialect)
				if memeCat == True:
					
					# print('main : les catégories sont les mêmes') # trace
					
					# I check the claims and add the missing ones if its needed
					for cle, valeurs in declaForm.items(): 
						for valeur in valeurs:
							if cle not in formeMatch['declaration'].keys() or valeur not in formeMatch['declaration'][cle]:
								# print('j\'ajoute une declaration') #   trace
								functionsmain.APIfunction.setClaim(formeMatch['idForm'], cle, valeur)
					
				else:
					# I create the form
					# print('main : les catégories sont différentes, je crée une nouvelle forme') # trace
					res = functionsmain.APIfunction.createForm(idLex, form, infosGram, lg, declaForm) 
					
					# if there is an error while creating the form, I send an error and jump to the next form
					if res==1:
						fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : erreur lors de la création de la forme\n')
						err += 1
						continue
					
					# if there is an error in setClaim creating the form, I send an error and jump to the next form
					if res==2:
						fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : erreur dans la fonction setClaim lors de la création de la forme\n')
						err += 1
						continue
						
					
			# I create the form	
			else:
				# print('main : la forme n\'existe pas je la crée') # trace
				res = functionsmain.APIfunction.createForm(idLex, form, infosGram, lg, declaForm)
				
				# if there is an error while creating the form, I send an error and jump to the next form
				if res==1:
					fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : erreur lors de la création de la forme\n')
					err += 1
					continue
					
				# if there is an error in setClaim creating the form, I send an error and jump to the next form
				if res==2:
					fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : erreur dans la fonction setClaim lors de la création de la forme\n')
					err += 1
					continue
				
			print('--forme ', form, 'traitée\n') # trace

	print('\nlexeme numéro', compteur, ':', lemme, 'traité') # trace

fLog.close()

msg = 'Programme terminé'
if err>0:
	err = str(err)
	msg += '\nIl y a eu '+err+' erreurs, consultez le fichier log.txt pour plus de détails'

print(msg)
