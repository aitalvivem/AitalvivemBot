#-*-coding:utf-8-*
import pywikibot
import functionsmain.APIfunction
import collections
from lxml import etree
import re
import sys


# I get the name of the xml file
try:
	fname = sys.argv[1]
except:
	print('Erreur : il vous faut renseigner le chemin d\'acces à de votre fichier xml en paramètre')
	sys.exit()

# I set the user name and the password of the bots account
try:
	functionsmain.APIfunction.setCo(sys.argv[2], sys.argv[3])
except:
	print('Erreur : il vous faut renseigner le nom et le mot de passe du compte utilisateur du bot en paramètre')
	sys.exit()

# I look if the mode 'lexeme_only' is on
try:
	if sys.argv[4] == 'lexeme_only':
		lexeme_only = True
	else:
		lexeme_only = False
except:
	lexeme_only = False


try:
	parser = etree.XMLParser(remove_blank_text=True)
	tree = etree.parse(fname, parser)
except:
	print('Erreur : fichier "'+fname+'" introuvable, vérifiez le chemin d\'acces renseigné')
	sys.exit()


# I create the log.txt file which will contains the errors messages
fLog = open('log.txt','w')
err = 0

# I get to the root of the xml file
tei = tree.getroot()


# for each lexeme
for lexeme in tei.xpath('.//form[@type="lemma"]'):

	# I get the id of the lexeme for the errors
	if lexeme.get("{http://www.w3.org/XML/1998/namespace}id"):
		idlexxml=lexeme.get("{http://www.w3.org/XML/1998/namespace}id")
	else:
		idlexxml=""
	
	# I get the infos of the language
	langs=lexeme.xpath('lang')
	
	# if there is no language tag, I send an error and jump to the next lexeme
	if len(langs)==0:
		fLog.write('erreur lexème "'+idlexxml+'" : il doit y avoir une balise <lang> sous les <form type="lemma">\n')
		err += 1
		continue
	else:
		lang=langs[0]
		libLg=lang.get('norm')
		codeLg=lang.text
		
		# if the language tag has no code or Q-id, I send an error and jump to the next lexeme
		if libLg==None or codeLg==None or codeLg=="":
			fLog.write('erreur lexème "'+idlexxml+'" : la balise <lang> ne peut être vide et elle doit avoir un attribut "norm"\n')
			err += 1
			continue
		
		# if the Q-id is not valid, I send an error and jump to the next lexeme
		if not re.search(r'^Q([0-9]+)$', codeLg):
			fLog.write('erreur lexème "'+idlexxml+'" : Qid de langue "'+codeLg+'" invalide\n')
			err += 1
			continue
		
		lg={ 'libLg':libLg , 'codeLg':codeLg }
	
	# i get the spelling
	orths=lexeme.xpath('orth')
	
	# if there is no spelling tag, I send an error and jump to the next lexeme
	if len(orths)==0:
		fLog.write('erreur lexème "'+idlexxml+'" : il doit y avoir une balise <orth> sous les <form type="lemma">\n')
		err += 1
		continue
	else:
		orth=orths[0]
		lemme=orth.text
		
		# if the spelling tag is empty, I send an error and jump to the next lexeme
		if lemme==None or lemme=="":
			fLog.write('erreur lexème "'+idlexxml+'" : la balise <orth> ne peut être vide\n')
			err += 1
			continue
	
	# I get the nature (cats)
	cats=lexeme.xpath('pos')
	
	# if there is no nature tag, I send an error and jump to the next lexeme
	if len(cats)==0:
		fLog.write('erreur lexème "'+idlexxml+'" : il doit y avoir une balise <pos> sous les <form type="lemma">\n')
		err += 1
		continue
	else:
		cat=cats[0]
		catLex=cat.text
		
		# if the pos tag is empty, I send an error and jump to the next lexeme
		if catLex==None or catLex=="":
			fLog.write('erreur lexème "'+idlexxml+'" : la balise <pos> ne peut être vide\n')
			err += 1
			continue
		
		# if the Q-id is not valid, I send an error and jump to the next lexeme
		if not re.search(r'^Q([0-9]+)$', catLex):
			fLog.write('erreur lexème "'+idlexxml+'" : Qid de nature "'+catLex+'" invalide\n')
			err += 1
			continue
	
	# I get the claims if its needed
	declaLex = {}
	for relation in lexeme.xpath('listRelation/relation'):
		prop=relation.get('name')
		concept=relation.get('passive')
		
		if prop==None or concept==None:
			fLog.write('erreur lexème "'+idlexxml+'" : la balise <relation> doit avoir un attribut "name" et un attribut "passive"\n')
			err += 1
			continue
		
		# if the Q-id is not valid, I send an error and jump to the next lexeme
		if concept!=None and not re.search(r'^Q([0-9]+)$', concept):
			fLog.write('erreur lexème "'+idlexxml+'" : Qid "'+concept+'" invalide\n')
			err += 1
			continue
		
		# if the P-id is not valid, I send an error and jump to the next lexeme
		if prop!=None and not re.search(r'^P([0-9]+)$', prop):
			fLog.write('erreur lexème "'+idlexxml+'" : Pid "'+prop+'" invalide\n')
			err += 1
			continue
		
		declaLex[prop]=concept
	
	
	# I get the L-id of the lexeme (if the lexeme don't exists, i create it) and then i get the data of the lexeme
	idLex = functionsmain.APIfunction.chercheLex(lemme, lg, catLex, declaLex)
	infoLex = functionsmain.APIfunction.getLex(idLex)
	
	
	if not lexeme_only:
		for flexion in lexeme.xpath('form[@type="inflected"]'):

			# I get the id of the form for the errors
			if flexion.get("{http://www.w3.org/XML/1998/namespace}id"):
				idformxml=flexion.get("{http://www.w3.org/XML/1998/namespace}id")
			else:
				idformxml=""
			
		
			# I get the spelling
			orthfs=flexion.xpath('orth')
			
			# if there is no spelling tag (orth), I send an error and jump to the next form
			if len(orthfs)==0:
				fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : il doit y avoir une balise <orth> sous les <form type="inflected">\n')
				err += 1
				continue
			else:
				orthf=orthfs[0]
				form=orthf.text
				
				# if the orth tag is empty, I send an error and jump to the next form
				if form==None or form=="":
					fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : la balise <orth> ne peut être vide\n')
					err += 1
					continue
			
			# I get the grammaticals features
			infosGram = []
			for gram in flexion.xpath('gramGrp/gram'):
				infoGram=gram.text
				
				# if the gram tag id empty, I send an error and jump to the next form
				if infoGram==None or infoGram=="":
					fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : la balise <gram> ne peut être vide\n')
					err += 1
					continue
			
				# if the Q-id is not valid, I send an error and jump to the next form
				if infoGram!=None and not re.search(r'^Q([0-9]+)$', infoGram):
					fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : Qid d\'information grammaticale "'+infoGram+'" invalide\n')
					err += 1
					continue
				
				infosGram.append(infoGram)
		
			# if get the claims if its needed
			declaForm = {}
			for relation in flexion.xpath('listRelation/relation'):
				prop=relation.get('name')
				concept=relation.get('passive')
				
				if prop==None or concept==None:
					fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : la balise <relation> doit avoir un attribut "name" et un attribut "passive"\n')
					err += 1
					continue
				
				# if the Q-id is not valid, I send an error and jump to the next form
				if concept!=None and not re.search(r'^Q([0-9]+)$', concept):
					fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : Qid "'+concept+'" invalide\n')
					err += 1
					continue
				
				# if the P-id is not valid, I send an error and jump to the next form
				if prop!=None and not re.search(r'^P([0-9]+)$', prop):
					fLog.write('erreur lexème "'+idlexxml+'" forme "'+idformxml+'" : Pid "'+prop+'" invalide\n')
					err += 1
					continue
			
				declaForm[prop]=concept
			
		
			# I check if the form exists
			formExists = False
			formeMatch = []
			for formes in infoLex['formes']:
				if form == formes['representation']:
					formExists = True
					formeMatch += [formes]

					
			# if the form exists I check the grammaticals features
			if formExists == True:
				memeCat = False
				for forme in formeMatch:
					if collections.Counter(infosGram) == collections.Counter(forme['catGram']):
						memeCat = True
						formeMatch = forme
						break

				# if the grammaticals features are the same
				if memeCat == True:
					lsDial = []
					for cle, valeur in declaForm.items():
						if cle == 'P276':
							lsDial += [valeur]
					
					# I check the existing dialects and add a claim if it is needed
					if lsDial != []:
						for dial in lsDial:
							if dial not in formeMatch['dialectes']:
								functionsmain.APIfunction.setDial(formeMatch['idForm'], 'P276' ,dial)
					
				else:
					# I create the form
					functionsmain.APIfunction.createForm(idLex, form, infosGram, lg, declaForm) 
					
			# I create the form
			else:
				functionsmain.APIfunction.createForm(idLex, form, infosGram, lg, declaForm)


fLog.close()

msg = 'Programme terminé'
if err>0:
	err = str(err)
	msg += '\nIl y a eu '+err+' erreurs, consultez le fichier log.txt pour plus de détails'

print(msg)
