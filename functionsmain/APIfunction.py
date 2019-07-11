#-*-coding:utf-8-*
import requests
import json
import csv

def coApi(URL, S):
# ----------------------------------------------------------------------------

	# This function connect the Bot to a wikidata acount and ask for a CSRF token
	
# ----------------------------------------------------------------------------

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
	
# ----------------------------------------------------------------------------

	# This function search for a lexeme in the wikidata database
		# If the function find the lexeme it return the id
		# else the function call the createLex function
		
# ----------------------------------------------------------------------------

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
	
	lexExists = 0

	for item in DATA['search']:
		# If thelexeme exists I return its id
		if item['match']['text'] == info and item['match']['language'] in lg:
			lexExists = 1
			return item['id']
	
	# else I create the lexeme and return the id
	if lexExists == 0:
		return createLex(info, lg, catLex, catGram)

def createLex(lexeme, lg, catLex, catGram): 

# ----------------------------------------------------------------------------

	# this function create a lexeme and return the id :
		# 1)	translate the lexical category, the grammatical category and the 
		# 		language to the relevant Wikidata's item id.
		# 2)	create and send the request
		# 3)	return the id

# ----------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	# connect and ask for a CSRF token
	CSRF_TOKEN = coApi(URL, S)
	
	# get the item's id for the lexical category, the grammatical category and the language
	catLexW = getCat(catLex)
	catGramW = detailCat(catGram)
	
	if lg == 'fr':
		codeLg = 'Q150'
	elif lg == 'oc':
		codeLg ='Q14185'
		
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
	
	return DATA['entity']['id']

def createForm(idLex, form, catForm, lg):

# ----------------------------------------------------------------------------

	# this function create a form for a lexeme :
		# 1)	translate the the grammatical category to the relevant 
		# 		Wikidata's item id.
		# 2)	create and send the request

# ----------------------------------------------------------------------------

	S = requests.Session()
	URL = "https://www.wikidata.org/w/api.php"
	
	# connect and ask for a CSRF token
	CSRF_TOKEN = coApi(URL, S)
	
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
	
def getCat(cat):

# ----------------------------------------------------------------------------

	# This function translate the the lexical category to the relevant 
	# Wikidata's item id using a .csv file which matches the item's code with
	# its lexical category.

# ----------------------------------------------------------------------------

	# open the .csv file
	fname = # PATH
	file = open(fname, 'rt', encoding='utf-8')
	
	try:
		lecteur = csv.reader(file, delimiter="§") 
		for row in lecteur:
			if row[0] == cat:
				catW = row[2]
		
	finally:
		file.close()

	return catW

def detailCat(catDet):

# ----------------------------------------------------------------------------
	
	# This function takes all the grammatical categories from a form and 
	# return a list made of the relevant item's code, using a .csv file 
	# which matches the item's code with its grammatical category.
	
# ----------------------------------------------------------------------------

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
	
	
