from parsingDatabaseUtils import cleanString, removeWords, floatParse, date, sep,findInXML, remove_diacritics, parseDate
import re, datetime, xml, itertools, xml.etree.ElementTree as ET
from parsingData.procedures import classificationProcedures


#Quickfix because I can't reload a function imported, remove after testing
def parseDate(s, output = 'list'):
    """
    Parse dates, in their multiple possibilities to sting ortuples
    """
    if not isinstance(s, str):
        return s
    meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    meses = list(map(lambda s: s[:3].lower(), meses))
    for i, m in enumerate(meses):
        s = s.replace(m, '%d' % (i + 1))    
    p = re.findall('([0-9]+)[^0-9]+([0-9]+)[^0-9]+([0-9]+)', s)
    p = p[0]

    # If they are  in format year - month - day
    if len(p[0]) == 4:
        p = (p[2], p[1], p[0])

    if output == 'timedate':
        return datetime.datetime(day = int(p[0]), month = int(p[1]), year = int(p[2] if len(p[2]) == 4 else '20' + p[2]))
    elif output == 'string':
        if len(p[2]) == 2:
            year = '20' + p[2]
        else:
            year = p[2]
        return '%s-%s-%s' % (year, p[1], p[0])
    elif output == 'list':
        return p
    else:
        raise ValueError('Output format not recognised')


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

    echoLine = '(?:\(|)' + date + '(?:\)|)' + '[^\n]*' + '(?:%s)' % '|'.join(embarazo) + ' ' + '(?P<weeksEG>%s)' % floatParse  + ' ' + semanas
    m = re.findall(echoLine, t, re.MULTILINE)
    return m

def processAllEchos(allTexts):
    allEchos = {}
    res = {}
    res['no_echos_confirmed'] = False
    #parse
    for t in allTexts:
        echos = parseEchographies(t, cleanText = True)
        if echos is False:
            res['no_echos_confirmed'] = True
            break
        for e in echos:
            allEchos[parseDate(e[0], output = 'string')] = e[1].replace(',', '.')

    #Process
    res['VAR_0060'] = 'A'
    for i, (d, e) in enumerate(allEchos.items()):
        res['echo_%d_date' % i] = d
        res['echo_%d_eg' % i] = e
        if float(e) < 20:
            res['VAR_0060'] = 'B'
    return res