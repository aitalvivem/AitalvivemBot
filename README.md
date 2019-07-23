# AitalvivemBot
Here is few things you need to setup/install before your start the bot.

First you need ton install the pywikibot framework (https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation/fr).

After dowloading the pywikibot framework, copy and paste main.py and the folder functionsmain inside the core_stable folder of the framework. Then you will need the setup those informations :

In main.py : 
  - set the path to the file « maindata.csv » line 7 and the delimiter line 12

In functionsmain/APIfunction.py :
  - set USER_NAME and USER_PASS line 15 and 16 (corresponding to the username and de password of your bot's acount in Wikidata)
  - set the path to the file « catGenToWikidataCode.csv » line 219 and the delimiter line 225
  - set the path to the file « detailCat.csv » line 249 and the delimiter line 253

For more information please read the documentation (french or english version). You can find a description of the file in the « Files description » section.
To avoid errors please check the Known issues section of the documentation.
