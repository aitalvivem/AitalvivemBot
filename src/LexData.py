# -*-coding:utf-8-*
import json

import requests

USER_NAME = None
USER_PASS = None


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
                lexQid = Lexeme(item["id"]).getQidCat()
                if lexQid == 1:
                    return 0, 3

                if catLex == lexQid:
                    idLex = item["id"]

                    # Check the claims
                    infoLex = Lexeme(idLex).getQidCat()
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
                            print("--lexème retourné, id =", idLex)
                            break

        # else Create the lexeme
        if lexExists == False:
            return createLex(info, lg, catLex, declaLex)
        else:
            return idLex, 0
    except:
        return 0, 1


def createLex(lexeme, lg, catLex, declaLex):
    """
    Creates a lexeme

    @param lexeme: value of the lexeme
    @param lg: language
    @param catLex: lexicographical category
    @param declaLex: claims to add to the lexeme
    @returns: Object of type Lexeme or None if creation failed
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
    # Get the id of the new lexeme
    idLex = DATA["entity"]["id"]

    print("--Created lexeme : idLex = ", idLex)
    lexeme = Lexeme(idLex)

    if declaLex:
        try:
            for cle, values in declaLex.items():
                for value in values:
                    res = lexeme.__setClaim__(idLex, cle, value)
                    if res == 1:
                        # TODO: raise error?
                        return lexeme
        except:
            return None
    return lexeme


class Claim(dict):
    def __init__(self, claim):
        super().__init__()
        self.update(claim)


class Form(dict):
    def __init__(self, form):
        super().__init__()
        self.update(form)

    def form(self):
        return list(self["representations"].values())[0]["value"]

    def claims(self):
        return {k: [Claim(c) for c in v] for k, v in self["claims"].items()}

    def __repr__(self):
        return "<Form '{}'>".format(self.form())

    def __str__(self):
        return super().__repr__()


class Sense(dict):
    def __init__(self, form):
        super().__init__()
        self.update(form)

    def glosse(self, lang="en"):
        # TODO: Fallback
        return self["glosses"][lang]["value"]

    def claims(self):
        return [Claim(c) for c in self["claims"]]

    def __repr__(self):
        return "<Sense '{}'>".format(self.glosse())

    def __str__(self):
        return super().__repr__()


class Lexeme:
    def __init__(self, idLex):
        self.getLex(idLex)

    def getLex(self, idLex):
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

        self.DATA = DATA["entities"][idLex]

    @property
    def id(self):
        return self.DATA["id"]

    @property
    def lemma(self):
        return list(self.DATA["lemmas"].values())[0]["value"]

    @property
    def language(self):
        return list(self.DATA["lemmas"].values())[0]["language"]

    @property
    def catLex(self):
        return self.DATA["lexicalCategory"]

    @property
    def rawclaims(self):
        return self.DATA["claims"]

    def claims(self):
        claims = {}
        for prop, value in self.rawclaims.items():
            if prop not in claims:
                claims[prop] = []
            for concept in value:
                try:
                    claims[prop].append(concept["mainsnak"]["datavalue"]["value"])
                except:
                    pass

    @property
    def rawforms(self):
        return self.DATA["forms"]

    def forms(self):
        tmp = [Form(f) for f in self.rawforms]
        return tmp

    @property
    def rawsenses(self):
        return self.DATA["senses"]

    def senses(self):
        return [Sense(s) for s in self.rawsenses]

    def getQidCat(self):
        """
        This function returns the id of the lexical Category of a lexeme for a given id
        """
        return self.DATA["catLex"]

    def createForm(self, form, infosGram, lg, declaForm=None):
        """
        this function creates a form for a given lexeme (id):
             1) we create and send the request
             2) we call the __setClaim__ function to add claims
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
            "lexemeId": self.id(),
            "token": CSRF_TOKEN,
            "bot": "1",
            "data": data_form,
        }

        R = S.post(URL, data=PARAMS)
        DATA = R.json()
        idForm = DATA["form"]["id"]
        print("---Created form: idForm = ", idForm)

        # Add the claims
        if declaForm:
            try:
                for cle, values in declaForm.items():
                    for value in values:
                        res = self.__setClaim__(idForm, cle, value)
                        if res == 1:
                            return 2
            except:
                return 1

        return 0

    def __setClaim__(self, idForm, idProp, idItem):
        """
        This function adds a claim to an existing form/lexeme
        """

        S = requests.Session()
        URL = "https://www.wikidata.org/w/api.php"

        CSRF_TOKEN = coApi(URL, S)

        claim_value = json.dumps({"entity-type": "item", "numeric-id": idItem[1:]})

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
            assert "claim" in DATA
            print("---claim added")
            return 0
        except:
            return 1
