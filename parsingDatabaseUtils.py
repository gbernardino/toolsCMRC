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
import dateparser, datetime
from parsingData.procedures import classificationProcedures

floatParse = '[0-9]*[\.,]?[0-9]+'
pars =HTMLParser()
cleanWhites = re.compile("[^\S\n]+")
fullCleanTxt  = lambda s: cleanString(remove_diacritics(str(s))).lower() 


def addZeros(s, d):
    s = str(s)
    return '0' * (d - len(str(s))) + s 

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
    text = pars.unescape(str(text))
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

def cleanString(text, removeChars = '-:,;\.', removeWords = []):
    text = pars.unescape(str(text))
    text = cleanWhites.sub(' ', text)

    #clean html tags, when they are with with &lt; &gt;
    #text = re.sub('\&lt\;.*?\&gt\;', ' ',  text)
    text = re.sub('\<[^<]*?\>', ' ',  text)

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

    #Quick fix, of some mistakes
    if p[0] in ['219', '201'] and len(p[2]) == 2:
        p = ('2019', p[1], p[2])
    if p[2] in ['219', '201'] and len(p[0]) == 2:
        p = (p[0], p[1], '2019')

    # If they are  in format year - month - day
    if len(p[0]) == 4:
        p = (p[2], p[1], p[0])
    if int(p[1]) > 12:
        p = (p[1], p[0], p[2])
    if output == 'datetime':
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

meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
meses = meses + list(map(lambda s: s[:3], meses))
sep= '\s*[,;:]?\s*'
separadorFecha = '(?:[\.\\/-]|\s*DE\s*|\s*DEL\s*| )'
date =  '\(?' +  '((?:[0-9]+)'  + separadorFecha  + '(?:[0-9]+|%s)'%  '|'.join(meses) + \
                        separadorFecha  + '(?:[0-9]+))' + '\)?' 
floatParse = '[0-9]*[\.,]?[0-9]+'

"""
Parse epicrisis
 s
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

    echoLine = date + '[^\n]*' + '(?:%s)' % '|'.join(embarazo) + ' ' + '(?P<weeksEG>%s)' % floatParse  + ' ' + semanas
    #echoLine = '(?:eco[a-z]*\%s|)' % sep +  date  +  sep   + '(?:%s)' % '|'.join(embarazo) #+ ' ' + '(' + '(?P<weeksEG>%s)' % floatParse  + ' ' + semanas  + '[,]?)'\
    #+  '( ' + paraHoy + ' ' + floatParse + ' ' + '(:?%s)?' % semanas +  ')?' + '[^\n]*'
    #queryEchos = '(eco[a-z]*' + sep +  '(' + echoLine  + '\s*' ')+)'
    m = re.findall(echoLine, t, re.MULTILINE)
    return m

noRecuerda = ['no', '\?']
searchFUM = re.compile('(?:fum|ultima menstruacion)'+ sep + '(?::|\.)?'+ sep +'(:?' +  date + '|%s)' % ('|'.join(noRecuerda)), flags = re.IGNORECASE)
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
def getAlta(txt, newborn = False ):
    if txt is None:
        txt = ''
    if 'alta voluntaria' in txt:
        return 'altaVoluntaria'
    elif 'cuidados intermedios' in txt:
        return 'cuidadosIntermedios'
    elif 'cuidados basicos' in txt:
        return 'cuidadosBasicos'
    elif 'alojamiento conjunto'in txt:
        return 'alojamientoConjunto'
    elif 'alta medica'  in txt or 'alta hospitalaria' in txt or ('alta' in txt and newborn):
        return 'altaMedica'
    elif ' uci' in txt or 'cuidados intensivo' in txt:
        return 'uci'
    else:
        return 'unknown'

def getMotherData(data):
    """
    Parse the data relative to the mother and general pregnancy (from patient info, epicrisis and admision to the emergency room)
    """        
    res = {}
    res['VAR_0006'] = data.motherData.FechaNac
    #Etnia
    if data.motherData.Etnia == 1:
        res['VAR_0011'] = 'B'
    #Raizal, palenquero, negros/mulatos
    elif data.motherData.Etnia in [3,4,5]:   
        res['VAR_0011'] = 'D'
    #Otras etnias?
    elif data.motherData.Etnia in [2]:
        res['VAR_0011'] = 'E'

    #Estudios y alfabetiacion
    if data.motherData.Escolaridad in [2, 3, 4,5,6]:
        res['VAR_0012'] = 'B'
    elif data.motherData.Escolaridad in [1, 8]:
        res['VAR_0012'] = 'A'

    #TODO: Que hacer con pre-escolar? 
    if data.motherData.Escolaridad in [8, 1]:
        res['VAR_0013'] = 'A'
    elif data.motherData.Escolaridad in [3]:
        res['VAR_0013'] = 'B'
    elif data.motherData.Escolaridad in [4, 5]:
        res['VAR_0013'] = 'C'
    elif data.motherData.Escolaridad in [6]:
        res['VAR_0013'] = 'D'

    if data.motherData.EstadoCivil in ['Casado']:
        res['VAR_0015'] = 'A'
    elif data.motherData.EstadoCivil in ['Soltero']:
        res['VAR_0015'] = 'C'
    elif remove_diacritics(
        data.motherData.EstadoCivil) in ['Union Libre']:
        res['VAR_0015'] = 'B'

    res['VAR_0018'] = '806001061-8'
    res['VAR_0019'] = data.motherData.Identificacion 

    # Antecedentes
    if data.ingreso is not None:
        etIngreso = ET.fromstring(data.ingreso.RegistroXML)

        #Antecedentes familiares
        aFamiliares = findInXML("AntecedentesFamiliares", etIngreso)
        antecedentes = parseAntecedentes(aFamiliares)
        if ('None' in antecedentes and len(antecedentes) > 1) or len(antecedentes) == 0:
            """
            Something weird happened
            """
            pass
        else:
            res['VAR_0020'] = 'B' if 'TBC' in antecedentes else 'A'
            res['VAR_0022'] = 'B' if 'Diabetes' in antecedentes else 'A'
            res['VAR_0024'] = 'B' if 'HTA' in antecedentes else 'A'
            res['VAR_0026'] = 'B' if 'Preeclampsia' in antecedentes else 'A'
            res['VAR_0028'] = 'B' if 'Eclampsia' in antecedentes else 'A'
            res['VAR_0030'] = 'B' if 'Otros' in antecedentes else 'A'

        #Personales solo si no hay nada
        #TODO: a bit of parsing could be done, but I do not have time
        aFarm = findInXML('aFarmacologicos', etIngreso) == "true"
        findInXML('aGinecoObstetrico', etIngreso)  == "true"
        aHosp = findInXML('aHospitalarios', etIngreso)  == "true"
        aTraum = findInXML('aTraumaticos', etIngreso)  == "true"
        aPathol = findInXML('aPatologicos', etIngreso)  == "true"
        if findInXML('aQuirurgicos', etIngreso)  == "false":
            res['VAR_0032'] = 'A'
        aToxic = findInXML('aToxico', etIngreso)  == "true"
        aTransf = findInXML('aTranfusionales', etIngreso)  == "true"

        #If all are false, and 1-> \n in the description, put the 

        #Height and weight
        try:
            res['VAR_0055'] = float(findInXML("Peso", etIngreso))
            res['VAR_0056'] = float(findInXML("Talla", etIngreso)) * 100 - 100
        except:
            pass
    if data.epicrisis is not None:    
        et = ET.fromstring(data.epicrisis.RegistroXML)
        antececedentesText = findInXML('AntecedentesHTML', et)
        antececedentesText = cleanString(antececedentesText).lower()
        antececedentesText = removeWords(antececedentesText, ['a', 'de', 'el', 'que', 'para', 'y'])

        # G P C A : Double check, sometimes it is wrong and FUM
        gpca_fum = parseGPCA_and_fum(antececedentesText)
        if gpca_fum['GPCA_OK']:
            gpca_fum['VAR_0040'] = int(res['G'])
            gpca_fum['VAR_0042'] = int(res['P'])
            gpca_fum['VAR_0047'] = int(res['C'])
            gpca_fum['VAR_0041'] = int(res['A'])

        if gpca_fum['fum_OK']:
            if  gpca_fum['fum'] in ['?', 'no']:
                res['VAR_0059'] =  'A'
                res['VAR_0057'] = '07/06/1954'
            else:
                res['VAR_0059'] = 'B'
                res['VAR_0057'] = '/'.join(parseDate(gpca_fum['fum']))

        #Echos
        m = parseEchographies(antececedentesText)
        if m is False:
            res['no_echo'] = 'no_echo_confirmed'
            res['VAR_0060'] = 'A'
        elif isinstance(m, list):
            res['no_echo'] =  'echo_confirmed'
            for i, e in enumerate(m):
                res['echo_%d_date' % i] =   str(dateparser.parse(e[0])).split()[0]
                res['echo_%d_eg' % i] = e[1]
                if float(e[1]) < 20:
                    res['VAR_0060'] = 'B'
        else:
            res['no_echo'] =  'no_information'

        # MORBILIDAD: (see analysis of hospital discharge)

        #Used medication
        # MD0430 -> oxitocina para inducir parto / reducir hemorrageas
        medication = findInXML('MedicamentosAdministrado', et)
        #MedicationByDate
        medicationByDate = medication.split('Fecha:')
        medicationByDate = map(lambda s: s.strip(), medicationByDate)
        medicationByDate = {m.split()[0] : m for m in medicationByDate if m}
        
        res['oxitocina'] = 'MD0430' in medication
        res['penilicilinaSifilis'] = 'MD0441' in medication
        res['sulfatoFerroso'] = 'MD0284' in medication
        res['magnesio'] = any( [m in medication for m in ['IM5038', 'IM5392', 'MD0028', 'MD0351', 'MD70149']])
        res['VAR_0443'] = 'B' if res['magnesio'] else 'A'
        res['VAR_0444'] = 'B' if res['magnesio'] else 'A'

        #Antibiotics
        #cefradina
        #cefalozina

        res['cefradina'] = any( [m in medication for m in ['MD0097', 'MD0098', 'MD0879']])
        res['ampicilina'] = any( [m in medication for m in ['IM5018', 'IM5235','MD0046','MD0047',
        'MD0048','MD0049','MD0050','MD0051']])
        res['cefalopina'] = any( [m in medication for m in ['IM5338', 'MD0095']])
        res['cefalozina']= any( [m in medication for m in ['MD0096']])

        if res['cefradina'] or res['ampicilina'] or res['cefalopina'] or res['cefalozina']:
            res['VAR_0301'] = 'B'
        else:
            res['VAR_0301'] = 'B'
        #Transfusion
        res['plasma']  = any( [m in medication for m in ['MD0460']])

        #anestesia local
        res['lidocaina']  = any( [m in medication for m in ['IM5072','IM5109','IM5365','IM5418','MD0332','MD0333','MD0334','MD0335','MD0336','MD0337','MD0338','MD0679']])
        res['roxitaina']  = any( [m in medication for m in ['MD0677', 'MD0678', 'MD0680']])
        if res['lidocaina'] or res['roxitaina']:
            res['VAR_0303'] = 'B'
        else:
            res['VAR_0303'] = 'A'

        #anestesia regional
        res['bupinet']  = any( [m in medication for m in ['139555', '218170-2', 'MD0078']])
        if res['bupinet']:
            res['VAR_0404'] = 'B'
        else:
            res['VAR_0404'] = 'A'
        #Anestesia general
        # sintosinal
        # pitusina
        # misoprostal, prostalglandiac


        #Ingreso
        res['VAR_0183'] = data.casoDesc.FechaHora.split('.')[0]

        #Fecha / motivo egreso
        lastRegister = data.getMotherLastState()
        alta = getAlta(lastRegister)
        if alta != 'unknown':
            if alta == 'altaMedica':
                res['VAR_0379'] =lastRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0382'] = 'A'
            elif alta == 'altaVoluntaria':
                res['VAR_0379'] =lastRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0382'] = 'C'
            elif alta == 'cuidadosBasicos':
                res['VAR_0379'] =lastRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0381'] = 'Cuidados basicos'
                res['VAR_0382'] = 'C'

            elif alta == 'cuidadosIntermedios':
                res['VAR_0379'] =lastRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0381'] = 'Cuidados intermedios'
                res['VAR_0382'] = 'C'
        #Edad maternal
        res['VAR_0009'] = dateDifferenceDays( data.epicrisis.FechaAsignacionRegistro, res['VAR_0006']) / 365.25
        res['VAR_0010'] = 'A' if res['VAR_0009'] >= 15 and 35 >= res['VAR_0009'] else 'B' 
    #Parto aborto
    res['VAR_0182'] = 'A' if classificationProcedures[data.procTypeId] == 'p'  else ''
    res['VAR_0182'] = 'B' if classificationProcedures[data.procTypeId] == 'a'  else ''

   
   
    return res


def getDateFromQuirurgicDescription(txt):
    """

    """

    pattern = 'fecha %s a las ([0-9]+):([0-9]+)'  % date
    res = re.findall(pattern, txt)
    return res

def getBloodLoss(text):
    
    removeWords = ['lateral', 'izquierda', 'derecha', 'superior', 'inferior', 'medial', 'de', 'se', 'estimada']
    for w in removeWords:
        text = text.replace(' %s ' % w, ' ')

    #Perdida de sangre
    bloodLost = re.findall('(?:sangre|hematica)(?::)? ([0-9]+)(?:)?(?:cc|ml)', text)
    try:
        return bloodLost[0]
    except:
        return None

def findDesgarros(text):
    text = text.replace(' de ', ' ').replace(' se ', ' ')
    
    removeWords = ['lateral', 'izquierda', 'derecha', 'superior', 'inferior', 'medial']
    for w in removeWords:
        text = text.replace(' %s ' % w, ' ')

    #Perdida de sangre
    ver = '(?:eviden[a-z]*|observ[a-z]*|vis[a-z]*|encont[a-z]*|presen[a-z]*)'   #diferentes manaeras de escribir ver
    negative = ['(?:sin|no) (?:%s )?desgar' % ver]
    positive = 'desgar[a-z]* (?:[a-z]* |(:?pared )?vag[a-z]* )?(?:sangr[a-z]* |no sangrant[a-z]* )?grado (i|ii|iii|1|2|3)[\. ,]'
    positiveUnidentified = '(?:%s )?desgar' % ver

    if re.findall('(:?%s)' % '|'.join(negative), text) or ('desgarro' not in text): #and 'sin complicaciones' in text):
        desgarro = 'no'
    elif re.findall(positive, text):
        desgarro = re.findall(positive, text)[0][1]
        if desgarro == 'i':
            desgarro = '1'
        elif desgarro == 'ii':
            desgarro = '2'
        elif desgarro == 'iii':
            desgarro = '3'

    elif re.findall(positiveUnidentified, text):
        desgarro = 'yes-NoGrade'
    else:
        desgarro = 'unknown'
    return desgarro


def dateDifferenceDays(d1, d2):
    p1 = parseDate(d1, 'datetime') if isinstance(d1, str) else d1
    p2 = parseDate(d2, 'datetime') if isinstance(d2, str) else d2
    return (p1 - p2).days


#####
# Info from newborn
####

def getInformationFromProcedureDescription(data):
    """
    Get information from the procedure
    """
    etDescripcion = ET.fromstring(data.procedure.XmlDescripcion)
    txtDescription = remove_diacritics(cleanString(
        etDescripcion.find('detalle/procedimientos/procedimiento/descripcion').text.lower()))
    res = {}
    
    #Fecha parto
    # TODO: beware of laboors that are near 12 am
    try:
        fechaParto = dateparser.parse(findInXML('fechaCirugia', etDescripcion))
        horaFinCirugia  = dateparser.parse(findInXML('horaFin', etDescripcion)) #If nothing else is found, a candidate for birth
        res['VAR_0284'] = str(fechaParto.year) + '/' +  str(fechaParto.month)  + '/' + str(fechaParto.day)
        res['VAR_0285'] = str(horaFinCirugia.hour) +  str(horaFinCirugia.minute) 
    except TypeError:
        pass

    # Presentacion
    if 'cefalic' in txtDescription:
        res['VAR_202'] = 'A'
    elif 'decubito dorsal' in txtDescription:
        res['VAR_0202'] = 'C'

    # Posicion parto
    if 'en posicion de litotomia' in txtDescription:
        res['VAR_0291'] = 'C'

    #Cordon umbilical
    if 'se pinza y corta cordon umbilical' in txtDescription:
        res['VAR_0299'] = 'A'
    #Episotomia
    if 'episiotomia' in txtDescription:
        res['VAR_0292'] = 'B'
    else:
        res['VAR_0292'] = 'A'

    #Reanimacion TODO

    #Ocitodicos TODO

    # Desgarros
    gradoDesgarros = findDesgarros(txtDescription)
    if gradoDesgarros == 'no':
        res['VAR_0293'] = 'X'
    elif gradoDesgarros == 'yes-NoGrade':
        res['VAR_0294'] = '0'
    elif gradoDesgarros != 'unknown':
         res['VAR_0294'] = gradoDesgarros
    
    #Sangre
    res['perdidaEstimadaSangre'] = getBloodLoss(txtDescription)
    # Nacimiento vivo / muerto
    newbornPattern = '(rec[a-z]+ na[a-z]+|feto|producto)'
    if  re.findall('%s (unico )?vivo' % newbornPattern, txtDescription):
        res['VAR_0282'] = 'A'
    elif re.findall('%s (muerto|sin signos vitales)' % newbornPattern, txtDescription):
        res['VAR_0282'] = 'D'
    elif re.findall('%s (obitado)' % newbornPattern, txtDescription) or 'obito' in txtDescription:
        res['VAR_0282'] = 'B'
    elif 'mortinato' in  txtDescription:
        res['VAR_0282'] = 'C'

    # OxitocinaTDP
    if 'oxitocina' in txtDescription:
        res['VAR_0300'] = 'B'
    else:
        res['VAR_0300'] = 'A'

    # C-section / vaginal
    if data.procTypeId == 'H3089' or data.procTypeId == 'H3092':
        res['VAR_0287'] = 'A'
    elif data.procTypeId == 'H3094':
        res['VAR_0287'] = 'B'
    elif data.procTypeId == 'H3085':
        res['VAR_0287'] = 'C'

    # Placenta completa/ retenida
    if re.findall('(extrae|obtiene) placenta (tip[a-z]+ [a-z]+ )?completa', txtDescription):
        res['VAR_0297'] = 'B'
        res['VAR_0298'] = 'A'
    elif re.findall('(extrae|obtiene) placenta (tip[a-z]+ [a-z]+ )?incompleta', txtDescription):
        res['VAR_0297'] = 'A'
        res['VAR_0298'] = 'A'

    # Peso / medidas 
    # Remove the points cause they create problems (they use points every 3 digits sometimes)
    if re.findall('peso (%s)' % floatParse, txtDescription):
        res['VAR_0311'] = re.findall('peso (%s)' % floatParse, txtDescription)[0].replace('.', '').replace(',', '')
    if re.findall('talla (%s)' % floatParse, txtDescription):
        res['VAR_0314'] = int(float(re.findall('talla (%s)' % floatParse, txtDescription)[0].replace(',', '.'))*10)

    #APGAR: TODO, easier to get from newborn registration, otherwise is dead.
    
    # TODO: defectos
    if 'sin malformaciones evidentes' in txtDescription:
        res['VAR_0335'] = 'A'
    return res

def parseAPGAR(s):
    if s != s:
        return False
    s = re.sub('(?<=[0-9])/10', '', s)
    s = re.sub('[^0-9]', " ", s)
    r = s.split()
    if len(r) == 1:
        return [r[0]]
    if len(r) == 2:
        return r
    elif len(r) == 3:
        return [r[0], r[1] if r[1] != '5' else r[2]]
    elif len(r) == 4 and r[1] == '1' and r[3] == '5':
        return [r[0], r[2]]
    elif len(r) == 4 and r[0] == '1' and r[2] == '5':
        return [r[1], r[3]]
    else:
        return False

def getNewbornData(data, idNewBornRegister, debug = False):
    """
    Paese information from 
    """
    register = data.registrosRecienNacido[idNewBornRegister][idNewBornRegister]

    etRegistro = ET.fromstring(register.RegistroXML)
    res = {}
    #prettyPrintXML(register.RegistroXML)
    res['VAR_0284']  = findInXML('InputText_FechaHoraNacimiento', etRegistro)
    res['VAR_0283'] = findInXML('ASPxTimeEdit_HoraNacimiento', etRegistro).replace(':', '')
    res['VAR_0198'] = findInXML('InputText_EdadGestac', etRegistro)
    EG2 = findInXML('InputText_EdadGestacDubowitzModificado', etRegistro)
    res['partoVag'] = findInXML('TexTarea_PartoVaginal', etRegistro) == 'SI'
    partoC = findInXML('TexTarea_PartoCesaria', etRegistro) == 'SI'
    res['VAR_0190'] = 'A' if res['partoVag'] else 'B'
    apgar =  parseAPGAR(findInXML('InputText_APGAR', etRegistro))
    try:
        res['VAR_0321'] = apgar[0]
    except:
        pass
    try:
        res['VAR_0322'] = apgar[1]
    except:
        pass

    if findInXML('ASPxComboBox_Sexo', etRegistro) == 'Masculino':
        res['VAR_0310'] = 'B'
    elif findInXML('ASPxComboBox_Sexo', etRegistro) == 'Femenino':
        res['VAR_0310'] = 'A'
    elif findInXML('ASPxComboBox_Sexo', etRegistro):
        res['VAR_0310'] = 'C'
    vivo = findInXML('InputRadio_VM', etRegistro) == 'Vivo'
    
    #FUM
    fum = findInXML('InputText_FUM', etRegistro)
    if fum:
        res['FUM'] = fum

    #Antrhopometrics
    res['VAR_0311'] = findInXML('InputText_Peso', etRegistro).replace('.', '').replace(',', '')
    res['VAR_0314'] = findInXML('InputText_Talla', etRegistro).replace(',', '.')
    res['VAR_0313'] = findInXML('InputText_CC', etRegistro).replace(',', '.')
    
    #As a double check of GAPC
    res['VAR_0040'] = findInXML('InputText_ObstetricosGestaciones', etRegistro)
    res['VAR_0041'] = findInXML('InputText_ObstetricosAbortos', etRegistro)
    res['VAR_0046'] = findInXML('InputText_ObstetricosPartos', etRegistro)
    res['VAR_0047'] = findInXML('InputText_ObstetricosCesareas', etRegistro)
    
    res['sufrimientoFetal'] = findInXML('TexTarea_SufrimientoFetal', etRegistro)

    #Paraclinic check
    for r in data.registrosRecienNacido[idNewBornRegister].values():
        et = ET.fromstring(r.RegistroXML)
        #prettyPrintXML(r.RegistroXML)
        pos = ['react', '\+', 'pos']
        neg = ['no', '-', 'neg']
        try:
            #if debug:
            #    print(findInXML( 'DescripcionNota', et))
            txtNotas = cleanString(remove_diacritics(findInXML( 'DescripcionNota', et))).lower()
            if debug:
                print(txtNotas)
            r = re.findall('vdrl\s+(%s)' % '|'.join(pos + neg), txtNotas) 
            if r:
                res['VAR_0343'] = 'B' if r[0] in pos else 'A'
                break
        except Exception as e:
            pass

        #Hospital of newborn discharge, and reason
        dischargeRegister = data.getNewbornLastState(idNewBornRegister)
        if dischargeRegister is not None:
            et = ET.fromstring(dischargeRegister.RegistroXML)
            txt = cleanString(remove_diacritics(findInXML( 'DescripcionNota', et))).lower()
            txt = removeWords(txt, ['a', 'de', 'el', 'que', 'para'])
        else:
            dischargeRegister = data.registrosRecienNacido[idNewBornRegister][idNewBornRegister]
            et = ET.fromstring(dischargeRegister.RegistroXML)
            txt = cleanString(remove_diacritics(findInXML( 'TexTarea_PlanTratamiento', et))).lower()
            txt = removeWords(txt, ['a', 'de', 'el', 'que', 'para'])

        if txt is None:
            txt = ''
        alta = getAlta(txt, newborn = True)
        if alta != 'unknown':
            if alta == 'altaMedica':
                res['VAR_0425'] =dischargeRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0372'] = 'alta'
            elif alta == 'altaVoluntaria':
                res['VAR_0425'] =dischargeRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0372'] = 'altaVol'

            elif alta == 'cuidadosBasicos':
                res['VAR_0425'] =dischargeRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0372'] = 'cuidadosBasicos'

            elif alta == 'cuidadosIntermedios':
                res['VAR_0425'] =dischargeRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0372'] = 'cuidadosIntermedios'

            elif alta == 'uci':
                res['VAR_0425'] =dischargeRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0372'] = 'UCI'

            elif alta == 'alojamientoConjunto':
                res['VAR_0425'] =dischargeRegister.FechaAsignacionRegistro.split()[0]
                res['VAR_0381'] = 'Cuidados intermedios'
                res['VAR_0330'] = 'A'
    return res