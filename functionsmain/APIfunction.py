#-*-coding:utf-8-*
import requests
import json
import csv

def coApi(URL, S):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# This function connect the Bot to a wikidata acount and ask for a CSRF token
	
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# the connexion informations
	USER_NAME = # USER_NAME
	USER_PASS = # USER_PASS
	
	# ask for a token
	PARAMS_1 = {
		'action': 'query',
		'meta': 'tokens',
		'type': 'login',
		'format': 'json'
	}

	R = S.get(url=URL, params=PARAMS_1)
	DATA = R.json()

	LOGIN_TOKEN = DATA['query']['tokens']['logintoken']

	# connexion request
	PARAMS_2 = {
		'action': 'login',
		'lgname': USER_NAME,
		'lgpassword': USER_PASS,
		'format': 'json',
		'lgtoken': LOGIN_TOKEN
	}

	R = S.post(URL, data=PARAMS_2)

	# ask for a CSRF token
	PARAMS_3 = {
		'action': 'query',
		'meta': 'tokens',
		'format': 'json'
	}
	
	R = S.get(url=URL, params=PARAMS_3)
	DATA = R.json()
	CSRF_TOKEN = DATA['query']['tokens']['csrftoken']
	
	return CSRF_TOKEN

def chercheLex(info, lg, catLex, catGram): 
	
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# This function search for a lexeme in the wikidata database
		# If the function find the lexeme it return the id
		# else the function call the createLex function
		
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	# the request
	PARAMS = {
		'action':'wbsearchentities',
		'language' : 'oc',
		'type' : 'lexeme',
		'bot':'1',
		'search': info,
		'format':'json'
	}

	R = S.get(url=URL, params=PARAMS)
	DATA = R.json()
	
	lexExists = False
	catLexW = getCat(catLex)

	for item in DATA['search']:
		# If thelexeme exists I return the id
		if item['match']['text'] == info and item['match']['language'] in lg:
			lexQid = getQidCat(item['id'])
			if catLexW == lexQid:
				lexExists = True
				idLex = item['id']
				break
	
	# else I create the lexeme and return the id
	if lexExists == False:
		return createLex(info, lg, catLex, catGram)
	else:
		return idLex

def createLex(lexeme, lg, catLex, catGram): 

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# this function create a lexeme and return the id :
		# 1)	translate the lexical category, the grammatical category and the language to the relevant Wikidata's item id.
		# 2)	create and send the request
		# 3)	call setDial() to create a claim for the dialect
		# 4)	return the id

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	# connect and ask for a CSRF token
	CSRF_TOKEN = coApi(URL, S)
	
	# get the item's id for the lexical category, the grammatical category and the language
	catLexW = getCat(catLex)
	catGramW = detailCat(catGram)
	
	if lg != 'fr':
		dial = lg
		lg = 'oc'
		codeLg ='Q14185'
	else:
		codeLg = 'Q150'
		
	# I create the json with the lexeme's data
	data_lex = json.dumps({'type':'lexeme',
					'lemmas':{
						lg:{
							'value':lexeme, 
							'language':lg
						}
					},
					'language': codeLg,
					'lexicalCategory':catLexW,
					'forms':[
						{
							'add':'',
							'representations':{
								lg:{
									'language': lg,
									'value':lexeme
								}
							},
							'grammaticalFeatures':catGramW,
							'claims':[]
						}
					]
				})

	# send a post to edit a lexeme
	PARAMS = {
		'action': 'wbeditentity',
		'format': 'json',
		'new': 'lexeme',
		'bot':'1',
		'token': CSRF_TOKEN,
		'data': data_lex 
	}
	
	R = S.post(URL, data=PARAMS)
	DATA = R.json()
	
	# I get the id of the lexeme
	idLex = DATA['entity']['id']
	
	# I add a claim for the dialectif it is needed
	if lg == 'oc':
		infoLex = getLex(idLex)
		for form in infoLex['formes']:
			setDial(form['idForm'], dial)
	
	return idLex

def createForm(idLex, form, catForm, lg):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# this function create a form for a lexeme :
		# 1)	translate the the grammatical category to the relevant Wikidata's item id.
		# 2)	create and send the request

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	# connect and ask for a CSRF token
	CSRF_TOKEN = coApi(URL, S)
	
	if lg != 'fr':
		dial = lg
		lg = 'oc'
	
	# get the item's id for the grammatical category 
	catGramW = detailCat(catForm)

	# I create the json with the lexeme's data
	data_form = json.dumps({'representations':{lg:{'value':form, 'language': lg}}, 'grammaticalFeatures':catGramW}) 
	
	# send a post to edit a form
	PARAMS= {
		'action': 'wbladdform',
		'format': 'json',
		'lexemeId' : idLex,
		'token': CSRF_TOKEN,
		'bot':'1',
		'data': data_form
	}
	
	R = S.post(URL, data=PARAMS)
	DATA = R.json()
	
	idForm = DATA['form']['id']
	
	# I add a claim for the dialectif it is needed
	if lg == 'oc':
		setDial(idForm, dial)
	
def getCat(cat):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# This function translate the the lexical category to the relevant Wikidata's item id using a .csv file which matches the item's code with its lexical category.

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# open the .csv file
	fname = # PATH
	file = open(fname, 'rt', encoding='utf-8')
	
	findcat = False 
	
	try:
		lecteur = csv.reader(file, delimiter=";") 
		for row in lecteur:
			if row[0] == cat:
				catW = row[2]
				findcat = True
				break
		
	finally:
		file.close()

	if findcat:
		return catW

def detailCat(catDet):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------
	
	# This function takes all the grammatical categories from a form and return a list made of the relevant item's code, using a .csv file which matches the item's 
	# code with its grammatical category.
	
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	list = []
	
	fname = # PATH
	file = open(fname, 'rt', encoding='utf-8')
	
	try:
		lecteur = csv.reader(file, delimiter=";") 
		for row in lecteur:
			if row[0] == catDet:
				if row[2] != '':
					list += [row[2]]
				if row[3] != '':
					list += [row[3]]
				if row[4] != '':
					list += [row[4]]
				if row[5] != '':
					list += [row[5]]

	finally:
		file.close()

	return list
	
def setDial(idForm, dial):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# This function add a claim to a form to specifie the dialect

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------
	
	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	# connect and ask for a CSRF token
	CSRF_TOKEN = coApi(URL, S)

	# I get the numeric id of the item representing the dialect
	if dial == 'lang':
		idDial = '65529243'
	elif dial == 'gasc':
		idDial = '191085'
	elif dial == 'prov':
		idDial = '101081'
	elif dial == 'auv':
		idDial = '1152'
	elif dial == 'lim':
		idDial = '65530372'
	elif dial == 'viva':
		idDial = '65530697'

	claim_value = json.dumps({"entity-type":"item", "numeric-id":idDial})
	
	# the request
	PARAMS = {
		"action": "wbcreateclaim",
		"format": "json",
		"entity": idForm,
		"snaktype": "value",
		'bot':'1',
		"property": "P276",
		"value": claim_value,
		'token': CSRF_TOKEN
	}
	
	R = S.post(URL, data=PARAMS)
	DATA = R.json()

def getLex(idLex):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# this function gets and returns the data of a lexeme for a given id

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	# connect and ask for a CSRF token
	CSRF_TOKEN = coApi(URL, S)
	
	PARAMS = {
		"action": "wbgetentities",
		"format": "json",
		"ids": idLex
	}
	
	R = S.post(URL, data=PARAMS)
	DATA = R.json()
	
	dico = DATA['entities'][idLex]['lemmas']
	for cle, valeur in dico.items():
		lg = valeur['language']
		lemme = valeur['value']
	
	result = { 'idLex': DATA['entities'][idLex]['id'], 'lemme': lemme, 'lg': lg, 'formes': [] }

	for form in DATA['entities'][idLex]['forms']:
		forme = {
					'idForm':form['id'], 
					'representation':form['representations'][lg]['value'],
					'catGram':form['grammaticalFeatures'],
					'dialectes':[]
				}
		result['formes'] += [forme]
		
	# get the claims for each form of the lexeme
	for form in result['formes']:
		PARAMS_1 = {
			"action": "wbgetclaims",
			"format": "json",
			"entity": form['idForm'],
			"property": "P276"
		}
		
		R = S.get(url=URL, params=PARAMS_1)
		DATA = R.json()
		
		dico = DATA['claims']
		for key, value in dico.items():
			if key == 'P276':
				claims = value
				for cle in claims:
					form['dialectes'] += [cle['mainsnak']['datavalue']['value']['id']]
	
	return result

def getQidCat(idLex):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# This function returns the id of the lexical Category of a lexeme for a given id

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	PARAMS = {
		"action": "wbgetentities",
		"format": "json",
		"ids": idLex
	}

	R = S.get(url=URL, params=PARAMS)
	DATA = R.json()
	
	catLex = DATA['entities'][idLex]['lexicalCategory']
	
	return catLex
