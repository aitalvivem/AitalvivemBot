# -*-coding:utf-8-*
import json

import requests


def setCo(user_name, user_pass):
    global USER_NAME, USER_PASS
    USER_NAME = user_name
    USER_PASS = user_pass


def coApi(URL, S):
    """
    This function connect the Bot to a wikidata account and ask for a CSRF token
    """

    global USER_NAME, USER_PASS

    # Ask for a token
    PARAMS_1 = {"action": "query", "meta": "tokens", "type": "login", "format": "json"}

    R = S.get(url=URL, params=PARAMS_1)
    DATA = R.json()

    LOGIN_TOKEN = DATA["query"]["tokens"]["logintoken"]

    # connexion request
    PARAMS_2 = {
        "action": "login",
        "lgname": USER_NAME,
        "lgpassword": USER_PASS,
        "format": "json",
        "lgtoken": LOGIN_TOKEN,
    }

    R = S.post(URL, data=PARAMS_2)

    # ask for a CSRF token
    PARAMS_3 = {"action": "query", "meta": "tokens", "format": "json"}

    R = S.get(url=URL, params=PARAMS_3)
    DATA = R.json()
    CSRF_TOKEN = DATA["query"]["tokens"]["csrftoken"]

    return CSRF_TOKEN


def chercheLex(info, lg, catLex, declaLex):
    """
    This function search for a lexeme in the wikidata database
        If the function find the lexeme it return the id
        else the function call the createLex function
    """

    S = requests.Session()
    URL = "https://www.wikidata.org/w/api.php"

    PARAMS = {
        "action": "wbsearchentities",
        "language": lg["libLg"],
        "type": "lexeme",
        "search": info,
        "format": "json",
    }

    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()

    lexExists = False

    try:
        for item in DATA["search"]:
            # if the lexeme exists
            if (
                item["match"]["text"] == info
                and item["match"]["language"] == lg["libLg"]
            ):  # TEST
                # Check the grammaticals features
                lexQid = getQidCat(item["id"])
                if lexQid == 1:
                    return 0, 3

                if catLex == lexQid:
                    idLex = item["id"]

                    # Check the claims
                    infoLex = getLex(idLex)
                    if infoLex != 1:
                        compt = 0
                        for cle, values in declaLex.items():
                            for value in values:
                                if (
                                    cle not in infoLex["claim"].keys()
                                    or value not in infoLex["claim"][cle]
                                ):
                                    compt += 1
                                    break

                        if compt == 0:
                            lexExists = True
                            print("--lexème retourné, id =", idLex)  # trace
                            break

        # else Create the lexeme
        if lexExists == False:
            # print('chercheLex : le lexeme n\'existe pas, je le crée') #trace
            return createLex(info, lg, catLex, declaLex)
        else:
            return idLex, 0
    except:
        return 0, 1


def createLex(lexeme, lg, catLex, declaLex):
    """
    this function create a lexeme and return the id :
        1)    create and send the request
        2)    call setClaim() to create a claim
        3)    return the id
    """

    S = requests.Session()
    URL = "https://www.wikidata.org/w/api.php"

    CSRF_TOKEN = coApi(URL, S)

    langue = lg["libLg"]
    codeLangue = lg["codeLg"]

    # Create the json with the lexeme's data
    data_lex = json.dumps(
        {
            "type": "lexeme",
            "lemmas": {langue: {"value": lexeme, "language": langue}},
            "language": codeLangue,
            "lexicalCategory": catLex,
            "forms": [],
        }
    )

    # Send a post to edit a lexeme
    PARAMS = {
        "action": "wbeditentity",
        "format": "json",
        "bot": "1",
        "new": "lexeme",
        "token": CSRF_TOKEN,
        "data": data_lex,
    }

    R = S.post(URL, data=PARAMS)
    DATA = R.json()

    try:
        # Get the id of the lexeme
        idLex = DATA["entity"]["id"]

        print("--lexeme créé : idLex = ", idLex)  # trace

        for cle, values in declaLex.items():
            for value in values:
                res = setClaim(idLex, cle, value)
                if res == 1:
                    return idLex, 4

        return idLex, 0
    except:
        return 0, 2


def createForm(idLex, form, infosGram, lg, declaForm):
    """
    this function creates a form for a given lexeme (id):
         1) we create and send the request
         2) we call the setClaim function to add claims
    """

    S = requests.Session()
    URL = "https://www.wikidata.org/w/api.php"

    CSRF_TOKEN = coApi(URL, S)

    langue = lg["libLg"]

    # Create the json with the lexeme's data
    data_form = json.dumps(
        {
            "representations": {langue: {"value": form, "language": langue}},
            "grammaticalFeatures": infosGram,
        }
    )

    # send a post to edit a form
    PARAMS = {
        "action": "wbladdform",
        "format": "json",
        "lexemeId": idLex,
        "token": CSRF_TOKEN,
        "bot": "1",
        "data": data_form,
    }

    R = S.post(URL, data=PARAMS)
    DATA = R.json()

    try:
        idForm = DATA["form"]["id"]

        print("---forme crée : idForm = ", idForm)  # trace

        # Add the claims
        for cle, values in declaForm.items():
            for value in values:
                res = setClaim(idForm, cle, value)
                if res == 1:
                    return 2

        return 0
    except:
        return 1


def setClaim(idForm, idProp, idItem):
    """
    This function add a claim to a form
    """

    S = requests.Session()
    URL = "https://www.wikidata.org/w/api.php"

    CSRF_TOKEN = coApi(URL, S)

    idItem = idItem.replace("Q", "")

    claim_value = json.dumps({"entity-type": "item", "numeric-id": idItem})

    PARAMS = {
        "action": "wbcreateclaim",
        "format": "json",
        "entity": idForm,
        "snaktype": "value",
        "bot": "1",
        "property": idProp,
        "value": claim_value,
        "token": CSRF_TOKEN,
    }

    R = S.post(URL, data=PARAMS)
    DATA = R.json()

    try:
        verif = DATA["claim"]
        print("---claim added")  # trace
        return 0
    except:
        return 1


def getLex(idLex):
    """
    this function gets and returns the data of a lexeme for a given id

    @type idLex: string
    @params idLex: Lexeme identifier (example: "L2")
    @returns: Simplified object representation of Lexeme
    """

    S = requests.Session()
    URL = "https://www.wikidata.org/w/api.php"

    PARAMS = {"action": "wbgetentities", "format": "json", "ids": idLex}

    R = S.post(URL, data=PARAMS)
    DATA = R.json()

    dico = DATA["entities"][idLex]["lemmas"]

    for _, value in dico.items():
        lg = value["language"]
        lemme = value["value"]

    result = {
        "idLex": DATA["entities"][idLex]["id"],
        "lemme": lemme,
        "lg": lg,
        "formes": [],
        "claim": {},
        "senses": [],
    }

    for prop, value in DATA["entities"][idLex]["claims"].items():
        if prop not in result["claim"]:
            result["claim"][prop] = []
        for concept in value:
            try:
                result["claim"][prop].append(concept["mainsnak"]["datavalue"]["value"])
            except:
                pass

    # Get the forms
    for form in DATA["entities"][idLex]["forms"]:
        forme = {
            "idForm": form["id"],
            "representation": form["representations"][lg]["value"],
            "catGram": form["grammaticalFeatures"],
            "claim": {},
        }
        for prop, value in form["claims"].items():
            if prop not in forme["claim"]:
                forme["claim"][prop] = []
            for concept in value:
                forme["claim"][prop].append(concept["mainsnak"]["datavalue"]["value"])
        result["formes"] += [forme]

    # Get the senses
    for sense in DATA["entities"][idLex]["senses"]:
        sensee = {
            "idForm": sense["id"],
            "representation": sense["glosses"][lg]["value"],
            "claim": DATA["entities"]["L2"]["forms"][0]["claims"],
        }
        result["senses"] += [sensee]

    return result


def getQidCat(idLex):
    """
    This function returns the id of the lexical Category of a lexeme for a given id
    """

    S = requests.Session()
    URL = "https://www.wikidata.org/w/api.php"

    PARAMS = {"action": "wbgetentities", "format": "json", "ids": idLex}

    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()

    catLex = DATA["entities"][idLex]["lexicalCategory"]

    return catLex
