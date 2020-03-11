"""
Set of utils for parsing data out of free text.
"""


"""
Cleaning free text
"""

import pandas, numpy as np,re
import collections, unicodedata
import xml, itertools, xml.etree.ElementTree as ET
from html.parser import HTMLParser

floatParse = '[0-9]*[\.,]?[0-9]+'
pars =HTMLParser()
cleanWhites = re.compile("[^\S\n]+")


def findInXML(s, et): 
    if isinstance(et, str):
        raise ValueError('et should be a tree, not a string')
    r =et.find('.//row[@NombreCampo="%s"]' % s)
    if r is not None:
        return r.get('ValorCampo')
    return None
def prettyPrintXML(s):
    r = xml.dom.minidom.parseString(s) #r.RegistroXML)
    print(pars.unescape(r.toprettyxml()))
    
# Maybe I should start tokenizing
def remove_diacritics(text):
    """
    Returns a string with all diacritics (aka non-spacing marks) removed.
    For example "Héllô" will become "Hello".
    Useful for comparing strings in an accent-insensitive fashion.
    """
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

def cleanString(text, removeChars = '-:,;', removeWords = []):
    for c in removeChars:
        text = re.sub('(?<![0-9])\%s' %c, ' ',  text)
        text = re.sub('\%s(?![0-9])' %c, ' ',  text)

    text = cleanWhites.sub(' ', text)
    for w in removeWords:
        text = text.replace(' ' + w + ' ', ' ')
    return text.strip()

def removeWords(text, words = []):
    for w in words:
        text = text.replace(' %s ' % w, ' ')
        
        
def isMaternalRegister(c, registers, raiseError = False):
    """
    Gets whether the record is of the mother or the newborn
    
    TODO: double check that everything is OK
    - Several updates on newborn
    """
    asunto = remove_diacritics(str(c.Asunto)).lower()
    try:
        if 'neonato' in asunto or 'nacido' in asunto: 
            return  False
        elif 'Registro del recién nacido' == registros.loc[int(c.Padre)].Asunto:
            return False
        else:
            return True
    except KeyError as e:
        if raiseError:
            raise(e)
        else:
            return True