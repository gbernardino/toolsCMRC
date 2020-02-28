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
        et = ET.fromstring(et)
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
    normalized = unicodedata.normalize("NFKD", str(text))
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
    return text
        
def isMaternalRegister(c, registers, idx = None, raiseError = False):
    """
    Gets whether the record is of the mother or the newborn
    
    TODO: double check that everything is OK
    - Several updates on newborn
    """
    unknown = 'NA'
    asunto = remove_diacritics(str(c.Asunto)).lower()
    try:
        if 'registro del recien nacido' == asunto: 
            return  'newborn', idx
        elif 'ingreso de urgencias' in asunto or 'notas de ingreso a piso' in asunto:
            return 'mother', None
        elif c.Padre == c.Padre:
            return isMaternalRegister(registers.loc[c.Padre], registers, c.Padre, raiseError)
        else:
            return unknown, None
    except KeyError as e:
        if raiseError:
            raise(e)
        else:
            return unknown, None


def parseAntecedentes(t):
    t = t.upper().strip()
    antecedentes = []
    negative = ['NO', 'NIEG', 'SIN DATOS', 'NEGATIVO', 'NO REFIERE', 'SIN']
    
    if 'TBC' in t or 'TUBERC' in t:
        antecedentes.append('TBC')
    if 'HIPERTEN' in t or 'HTA' in t:
        antecedentes.append('HTA')
    if any([n in t for n in negative]) or t == '':
        antecedentes.append('None')
    if 'DIAB' in t or 'DM' in t:
        antecedentes.append('Diabetes')
    if 'ASMA' in t:
        antecedentes.append('Asma')
    if 'CARDIO' in t:
        antecedentes.append('Cardo')
    if 'PREECLAMPSIA' in t:
        antecedentes.append('Preclampsia')

    # TODO: check that no other word means anything

    return antecedentes

def parseDate(s):
    """
    Parse dates, in their multiple possibilities
    """
    if not isinstance(s, str):
        return s
    meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    meses = list(map(lambda s: s[:3].lower(), meses))
    for i, m in enumerate(meses):
        s = s.replace(m, '%d' % (i + 1))
        
    p = re.findall('([0-9]+)[^0-9]+([0-9]+)[^0-9]+([0-9]+)', s)
    return p[0]

meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
meses = meses + list(map(lambda s: s[:3], meses))
sep= '\s*[,;:]?\s*'
separadorFecha = '(?:[\.\\/-]|DE|DEL|\s)'
date =  '\(?' +  '((?:[0-9]+)'+ sep + separadorFecha + sep + '(?:[0-9]+|%s)'%  '|'.join(meses) + \
                       sep + separadorFecha + sep + '(?:[0-9]+))' + '\)?' 
floatParse = '[0-9]*[\.,]?[0-9]+'

"""
Parse epicrisis

- FUM
- ECHOS
- PARACLINICS (TO SOME EXTENT)
"""

def parseEchographies(t, cleanText = False):
    """
    Finds the echos. Returns False if it is stated in the report that there were no echos, or a list  if some echos were found. An empty list is non conclusive
    """
    # Cleaning
    if cleanText:
        t = cleanString(t).lower()
        t = removeWords(t, ['a', 'de', 'el', 'que', 'para'])

    if 'no trae eco' in t or 'ni eco' in t:
        return False

    paraHoyPossibilities = ['hoy', 'para dia hoy']
    paraHoy = '(?:%s)' % '|'.join(paraHoyPossibilities)
    semanas = '(?:%s)' % '|'.join(['semanas', 'sem', 'sems'])
    embarazo = ['embarazo', 'emb', 'embarazo', 'emb', 'reporta embarazo']

    echoLine = '(:?eco[a-z]*\%s|)' % sep +  date +  sep + '(?:%s)' % '|'.join(embarazo) + ' ' + '(' + '(?P<weeksEG>%s)' % floatParse  + ' ' + semanas  + '[,]?)'\
    +  '( ' + paraHoy + ' ' + floatParse + ' ' + '(:?%s)?' % semanas +  ')?' + '[^\n]*'

    queryEchos = '(eco[a-z]*' + sep +  '(' + echoLine  + '\s*' ')+)'
    m = re.findall(echoLine, t, re.MULTILINE)
    return m

noRecuerda = ['no', '\?']
searchFUM = re.compile('fum'+ sep + '(?::|.)?'+ sep +'(:?' +  date + '|%s)' % ('|'.join(noRecuerda)), flags = re.IGNORECASE)
def parseGPCA_and_fum(text):
    """
    Gets the GPCA and FUM from the Triage or epicrisis.
    
    NOTE: some of the cases are incorrect, double check
    TODO: actually, registro del recien nacido has it as a field.
    """    
    allowedStarts = ['7-&gt;', '-', '- antecedentes', 'antecedentes']
    line = re.findall('^%s(?:%s)?%s' % (sep, '|'.join(allowedStarts), sep) + 'G' + sep + '[0-9]+.*$', text, re.M)
    if line:
        f = line[0]
        G = f(re.findall('g' + sep + '([0-9]+)', line[0]))
        A = f(re.findall('a' + sep + '([0-9]+)', line[0]))
        C = f(re.findall('c' + sep + '([0-9]+)', line[0]))
        P = f(re.findall('p' + sep + '([0-9]+)', line[0])) 
        parsedGPCA = [G, P, A, C]
        GPCA_OK = True
    else:
        parsedGPCA = []
        GPCA_OK = False
    #Prob athere is a better way...
    parsedFUM = searchFUM.findall(text)
    #print(parsedFUM[0])
    return {'fum' : parsedFUM[0][0] if parsedFUM else '',
            'fum_OK' : len(parsedFUM) > 0 ,
            'GPCA_OK' : GPCA_OK,
            'fum_Data' : parsedFUM,
            'parsedGPCA' : parsedGPCA}