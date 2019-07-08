#-*-coding:utf-8-*
import requests
import json

def coApi(URL, S):
	# this function connect the bot to a Wikidata acount and ask for CSRF token
	
	USER_NAME = 'AitalvivemBot'
	USER_PASS = ''
	
	PARAMS_1 = {
		'action': 'query',
		'meta': 'tokens',
		'type': 'login',
		'format': 'json'
	}

	R = S.get(url=URL, params=PARAMS_1)
	DATA = R.json()

	LOGIN_TOKEN = DATA['query']['tokens']['logintoken']

	PARAMS_2 = {
		'action': 'login',
		'lgname': USER_NAME,
		'lgpassword': USER_PASS,
		'format': 'json',
		'lgtoken': LOGIN_TOKEN
	}

	R = S.post(URL, data=PARAMS_2)

	PARAMS_3 = {
		'action': 'query',
		'meta': 'tokens',
		'format': 'json'
	}
	
	R = S.get(url=URL, params=PARAMS_3)
	DATA = R.json()
	CSRF_TOKEN = DATA['query']['tokens']['csrftoken']
	
	return CSRF_TOKEN

def chercheLex(lexeme, lg):
	'''
	this function takes a lexeme and a language
	return the corresponding id
	if the lexeme does not exists, it calls the createLex function
	'''
	S = requests.Session()
	
	URL = "https://test.wikidata.org/w/api.php"
	
	# create the request
	PARAMS = {
		'action':'wbsearchentities',
		'language' : 'oc',
		'type' : 'lexeme',
		'search': lexeme,
		'format':'json'
	}

	R = S.get(url=URL, params=PARAMS)
	DATA = R.json()
	
	lexExists = 0

	for item in DATA['search']:
		# if th lexeme exists
		if item['match']['text'] == lexeme and item['match']['language'] in lg:
			return item['id']
			lexExists = 1
	# else i create it		
	if lexExists == 0:
		id = createLex(lexeme, lg)
		return id

def createLex(lexeme, lg):
	# this function create a lexeme and return the id
	S = requests.Session()
	
	URL = "https://test.wikidata.org/w/api.php"
	
	CSRF_TOKEN = coApi(URL, S)
	
	# i create the json with the datas to import
	data_lex = json.dumps({'labels':{lexeme:{'type':'lexeme', 'language':lg}}})

	# i sent a post to edit a lexeme
	PARAMS_4 = {
		'action': 'wbeditentity',
		'format': 'json',
		'id': id,
		'token': CSRF_TOKEN,
		'data': data_lex 
		# how do i set a reference to a 'Q###' code ?
	}
	
	R = S.post(URL, data=PARAMS_4)
	DATA = R.json()
	
	print('data = ', DATA)
	
	return id

# def createForm(idLex, form, catForm):
	# not created yet

# def getCat(cat):
	'''
	this function takes the Congrès code for a grammatical category
	and return the corresponding code in wikidata
	'''
	
