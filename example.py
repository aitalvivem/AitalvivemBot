#!/usr/bin/python3
import LexData
from LexData.languages import en

repo = LexData.WikidataSession("MichaelSchoenitzer", "foobar")

# Open a Lexeme
L2 = LexData.Lexeme(repo, "L2")

# Access the claims
print(L2.claims.keys())
# and Forms
print(len(L2.forms))
F1 = L2.forms[0]
print(F1.claims.keys())
# and senses
print(len(L2.senses))
S1 = L2.senses[0]
print(S1.claims.keys())

# Find or create a Lexeme by lemma, language and grammatical form
L2 = LexData.get_or_create_lexeme(repo, "first", en, "Q1084")
