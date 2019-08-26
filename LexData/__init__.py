# -*-coding:utf-8-*
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

import requests

name = "LexData"
version = "0.1.1"


class WikidataSession:
    """
    Wikidata network and authentication session. Needed for everything this
    framework does.
    """

    URL = "https://www.wikidata.org/w/api.php"

    def __init__(self, username: str, password: str, user_agent=f"{name} {version}"):
        """
        Create a wikidata session by logging in and getting the token
        """
        self.username = username
        self.password = password
        self.headers = {"User-Agent": user_agent}
        self.S = requests.Session()
        self.login()

    def login(self):
        # Ask for a token
        PARAMS_1 = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json",
        }
        DATA = self.get(PARAMS_1)
        LOGIN_TOKEN = DATA["query"]["tokens"]["logintoken"]

        # connexion request
        PARAMS_2 = {
            "action": "login",
            "langname": self.username,
            "langpassword": self.password,
            "format": "json",
            "langtoken": LOGIN_TOKEN,
        }
        self.post(PARAMS_2)

        PARAMS_3 = {"action": "query", "meta": "tokens", "format": "json"}
        DATA = self.get(PARAMS_3)
        self.CSRF_TOKEN = DATA["query"]["tokens"]["csrftoken"]

    def post(self, data: Dict[str, str]) -> Any:
        """
        Send data to wikidata by POST request. The CSRF token is automatically
        filled in if __AUTO__ is given instead.

        @type data: Object
        @param data: Parameters to send via POST
        @return: Answer form the server as Objekt
        """
        if data.get("token") == "__AUTO__":
            data["token"] = self.CSRF_TOKEN
        R = self.S.post(self.URL, data=data, headers=self.headers)
        if R.status_code != 200:
            raise Exception(
                "POST was unsuccessfull ({}): {}".format(R.status_code, R.text)
            )
        return R.json()

    def get(self, data: Dict[str, str]) -> Any:
        """
        Send a GET request to wikidata

        @type data: Object
        @param data: Parameters to send via GET
        @return: Answer form the server as Objekt
        """
        R = self.S.get(self.URL, params=data, headers=self.headers)
        if R.status_code != 200:
            raise Exception(
                "GET was unsuccessfull ({}): {}".format(R.status_code, R.text)
            )
        return R.json()


@dataclass
class Language:
    """
    Dataclass representing a language
    """

    short: str
    qid: str


class Claim(dict):
    """
    Wrapper around a dict to represent a Claim
    """

    def __init__(self, claim: Dict):
        super().__init__()
        self.update(claim)


class Form(dict):
    """
    Wrapper around a dict to represent a From
    """

    def __init__(self, form: Dict):
        super().__init__()
        self.update(form)

    def form(self) -> str:
        return list(self["representations"].values())[0]["value"]

    def claims(self) -> Dict[str, List[Claim]]:
        return {k: [Claim(c) for c in v] for k, v in self["claims"].items()}

    def __repr__(self) -> str:
        return "<Form '{}'>".format(self.form())

    def __str__(self) -> str:
        return super().__repr__()


class Sense(dict):
    """
    Wrapper around a dict to represent a Sense
    """

    def __init__(self, form: Dict):
        super().__init__()
        self.update(form)

    def glosse(self, lang="en") -> str:
        if lang not in self["glosses"]:
            if "en" in self["glosses"]:
                lang = "en"
            else:
                lang = list(self["glosses"].keys())[0]
        return self["glosses"][lang]["value"]

    def claims(self) -> Dict[str, List[Claim]]:
        return {k: [Claim(c) for c in v] for k, v in self["claims"].items()}

    def __repr__(self) -> str:
        return "<Sense '{}'>".format(self.glosse())

    def __str__(self) -> str:
        return super().__repr__()


class Lexeme(dict):
    """
    Wrapper around a dict to represent a Lexeme
    """

    def __init__(self, repo: WikidataSession, idLex: str):
        super().__init__()
        self.repo = repo
        self.getLex(idLex)

    def getLex(self, idLex: str):
        """
        this function gets and returns the data of a lexeme for a given id

        @type idLex: string
        @param idLex: Lexeme identifier (example: "L2")
        @returns: Simplified object representation of Lexeme
        """

        PARAMS = {"action": "wbgetentities", "format": "json", "ids": idLex}

        DATA = self.repo.post(PARAMS)

        self.update(DATA["entities"][idLex])

    @property
    def lemma(self) -> str:
        return list(self["lemmas"].values())[0]["value"]

    @property
    def language(self) -> str:
        return list(self["lemmas"].values())[0]["language"]

    @property
    def claims(self) -> Dict[str, List[Claim]]:
        return {k: [Claim(c) for c in v] for k, v in super().get("claims", {}).items()}

    @property
    def forms(self) -> List[Form]:
        return [Form(f) for f in super().get("forms", [])]

    @property
    def senses(self) -> List[Sense]:
        return [Sense(s) for s in super().get("senses", [])]

    def createSense(self, glosses: Dict[str, str], claims=None) -> str:
        """
        Create a sense for the lexeme

        @param glosses: glosses for the sense
        @param claims: claims to add to the new form
        """
        # Create the json with the sense's data
        data_sense: Dict[str, Dict[str, Dict[str, str]]] = {"glosses": {}}
        for lang, gloss in glosses.items():
            data_sense["glosses"][lang] = {"value": gloss, "language": lang}

        # send a post to add sense to lexeme
        PARAMS = {
            "action": "wbladdsense",
            "format": "json",
            "lexemeId": self["id"],
            "token": "__AUTO__",
            "bot": "1",
            "data": json.dumps(data_sense),
        }
        DATA = self.repo.post(PARAMS)
        idSense = DATA["sense"]["id"]
        logging.info("---Created sense: idsense = %s", idSense)

        # Add the claims
        self.__setClaims__(idSense, claims)
        self.getLex(self["id"])

        return idSense

    def createForm(
        self, form: str, infosGram: str, language: Language = None, claims=None
    ) -> str:
        """
        Create a form for the lexeme

        @param form: the new form to add
        @param infosGram: grammatical features
        @param language: the language of the form
        @param claims: claims to add to the new form
        """

        if language is None:
            languagename = self.language
        else:
            languagename = language.short

        # Create the json with the forms's data
        data_form = json.dumps(
            {
                "representations": {
                    languagename: {"value": form, "language": languagename}
                },
                "grammaticalFeatures": infosGram,
            }
        )

        # send a post to add form to lexeme
        PARAMS = {
            "action": "wbladdform",
            "format": "json",
            "lexemeId": self["id"],
            "token": "__AUTO__",
            "bot": "1",
            "data": data_form,
        }
        DATA = self.repo.post(PARAMS)
        idForm = DATA["form"]["id"]
        logging.info("---Created form: idForm = %s", idForm)

        # Add the claims
        self.__setClaims__(idForm, claims)

        self.getLex(self["id"])
        return idForm

    def createClaims(self, claims):
        """
        Add claims to the Lexeme

        @type  claims: dict(List[dict()])
        @param claims: The set of claims to be added
        """
        self.__setClaims__(self["id"], claims)

    def __setClaims__(self, parent: str, claims):
        """
        Add claims to a Lexeme, Form or Sense

        @type  parent: string
        @param parent: the id of the Lexeme/Form/Sense
        @type  claims: dict(List[dict()])
        @param claims: The set of claims to be added
        """
        for cle, values in claims.items():
            for value in values:
                self.__setClaim__(parent, cle, value)
        self.getLex(self["id"])

    def __setClaim__(self, parent: str, idProp: str, idItem: str):
        """
        This function adds a claim to an existing lexeme/form/sense

        @type  parent: string
        @param parent: the id of the Lexeme/Form/Sense
        @param idProp: id of the property
        @param idItem: id of the Item
        """

        claim_value = json.dumps({"entity-type": "item", "numeric-id": idItem[1:]})

        PARAMS = {
            "action": "wbcreateclaim",
            "format": "json",
            "entity": parent,
            "snaktype": "value",
            "bot": "1",
            "property": idProp,
            "value": claim_value,
            "token": "__AUTO__",
        }

        try:
            DATA = self.repo.post(PARAMS)
            assert "claim" in DATA
            logging.info("---claim added")
        except Exception as e:
            raise Exception("Unknown error adding claim", e)


def get_or_create_lexeme(repo, lemma: str, lang: Language, catLex: str) -> Lexeme:
    """
    Search for a lexeme in wikidata if not found, create it

    @param repo: WikidataSession
    @param lemma: the lemma of the lexeme
    @param lang: language of the lexeme
    @param catLex: lexical Category of the lexeme
    @rtype: Lexeme
    @returns: Lexeme with the specified properties
    """

    PARAMS = {
        "action": "wbsearchentities",
        "language": lang.short,
        "type": "lexeme",
        "search": lemma,
        "format": "json",
    }

    DATA = repo.get(PARAMS)

    for item in DATA["search"]:
        # if the lexeme exists
        if (
            item["match"]["text"] == lemma
            and item["match"]["language"] == lang.short
            and catLex == Lexeme(repo, item["id"])["lexicalCategory"]
        ):
            idLex = item["id"]

            logging.info("--Found lexeme, id = %s", idLex)
            return Lexeme(repo, idLex)

    # Not found, create the lexeme
    return create_lexeme(repo, lemma, lang, catLex)


def create_lexeme(repo, lemma: str, lang: Language, catLex: str, claims=None) -> Lexeme:
    """
    Creates a lexeme

    @param lemma: value of the lexeme
    @param lang: language
    @param catLex: lexicographical category
    @param claims: claims to add to the lexeme
    @returns: Object of type Lexeme
    """

    # Create the json with the lexeme's data
    data_lex = json.dumps(
        {
            "type": "lexeme",
            "lemmas": {lang.short: {"value": lemma, "language": lang.short}},
            "language": lang.qid,
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
        "token": "__AUTO__",
        "data": data_lex,
    }

    DATA = repo.post(PARAMS)
    # Get the id of the new lexeme
    idLex = DATA["entity"]["id"]

    logging.info("--Created lexeme : idLex = %s", idLex)
    lexeme = Lexeme(repo, idLex)

    lexeme.createClaims(claims)

    return lexeme
