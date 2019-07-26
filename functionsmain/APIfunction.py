#-*-coding:utf-8-*
import requests
import json
import csv

def setCo(user_name, user_pass):
	global USER_NAME, USER_PASS
	USER_NAME = user_name
	USER_PASS = user_pass

def coApi(URL, S):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# This function connect the Bot to a wikidata account and ask for a CSRF token
	
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	global USER_NAME, USER_PASS
	
	# I ask for a token
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

def chercheLex(info, lg, catLex, declaLex): 

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# This function search for a lexeme in the wikidata database
		# If the function find the lexeme it return the id
		# else the function call the createLex function

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	PARAMS = {
		'action':'wbsearchentities',
		'language' : lg['libLg'],
		'type' : 'lexeme',
		'search': info,
		'format':'json'
	}

	R = S.get(url=URL, params=PARAMS)
	DATA = R.json()
	
	lexExists = False

	for item in DATA['search']:
		# If the lexeme exists I return the id
		if item['match']['text'] == info and item['match']['language'] == lg['libLg']: 
			lexQid = getQidCat(item['id'])
			if catLex == lexQid:
				lexExists = True
				idLex = item['id']
				break
				
	# else I create the lexeme and return the id
	if lexExists == False:
		return createLex(info, lg, catLex, declaLex) 
	else:
		return idLex

def createLex(lexeme, lg, catLex, declaLex): 

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# this function create a lexeme and return the id :
		# 1)	create and send the request
		# 2)	call setClaim() to create a claim
		# 3)	return the id

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	CSRF_TOKEN = coApi(URL, S)
	
	langue = lg['libLg']
	codeLangue = lg['codeLg']
		
	# I create the json with the lexeme's data
	data_lex = json.dumps({
							'type':'lexeme',
							'lemmas':{
								langue:{
									'value':lexeme, 
									'language':langue
								}
							},
							'language': codeLangue,
							'lexicalCategory':catLex,
							'forms':[]
						})

	# I send a post to edit a lexeme
	PARAMS = {
		'action': 'wbeditentity',
		'format': 'json',
		'bot':'1',
		'new': 'lexeme',
		'token': CSRF_TOKEN,
		'data': data_lex 
	}
	
	R = S.post(URL, data=PARAMS)
	DATA = R.json()
	
	# I get the id of the lexeme
	idLex = DATA['entity']['id']
	
	# I add a claim for the dialectif it is needed
	for cle, valeur in declaLex.items():
		setClaim(idLex, cle, valeur)
	
	return idLex

def createForm(idLex, form, infosGram, lg, declaForm):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# cette fonction crée une forme pour un lexeme (id) donné :
		# 1)	on crée et on envoie la requete
		# 2)	on appele la fonction setClaim pour ajouter les déclarations

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	CSRF_TOKEN = coApi(URL, S)
	
	langue = lg['libLg']

	# I create the json with the lexeme's data
	data_form = json.dumps({'representations':{langue:{'value':form, 'language': langue}}, 'grammaticalFeatures':infosGram}) 
	
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
	for cle, valeur in declaForm.items():
		setClaim(idForm, cle, valeur)

def setClaim(idForm, idProp, idItem):

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# This function add a claim to a form

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------
	
	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	CSRF_TOKEN = coApi(URL, S)
	
	idItem = idItem.replace("Q", "")

	claim_value = json.dumps({"entity-type":"item", "numeric-id":idItem})
	
	PARAMS = {
		"action": "wbcreateclaim",
		"format": "json",
		"entity": idForm,
		"snaktype": "value",
		'bot':'1',
		"property": idProp,
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
		
	# I get the claims of a dialect for each forms
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
	
	# on crée la requete
	PARAMS = {
		"action": "wbgetentities",
		"format": "json",
		"ids": idLex
	}

	R = S.get(url=URL, params=PARAMS)
	DATA = R.json()
	
	catLex = DATA['entities'][idLex]['lexicalCategory']
	
	return catLex

