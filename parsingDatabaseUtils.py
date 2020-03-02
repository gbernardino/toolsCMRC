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
    text = pars.unescape(str(text))
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

def cleanString(text, removeChars = '-:,;', removeWords = []):
    text = pars.unescape(str(text))
    text = cleanWhites.sub(' ', text)

    #clean html tags, when they are with with &lt; &gt;
    text = re.sub('\&lt\;.*?\&gt\;', ' ',  text)
    text = re.sub('\<.*?\>', ' ',  text)

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
classificationProcedures = {'H0165': 'o', 'H0193': 'o', 'H2120': 'o', 'H2379': 'o', 'H2383': 'o', 'H2386': 'o', 'H2407': 'o', 'H2415': 'o', 'H2595': 'o', 'H2684': 'o', 'H2849': 'o', 'H2852': 'o', 'H2880': 'o', 'H2882': 'o', 'H2884': 'o', 'H2892': 'o', 'H2901': 'o', 'H2904': 'o', 'H2910': 'o', 'H2916': 'o', 'H2959': 'o', 'H2963': 'o', 'H2974': 'a', 'H2975': 'a', 'H3038': 'o', 'H3065': 'o', 'H3066': 'o', 'H3078': 'o', 'H3089': 'p', 'H3092': 'p', 'H3094': 'p', 'H3099': 'a', 'H3100': 'a', 'H3108': 'o', 'H3109': 'o', 'H3111': 'o', 'H3114': 'o', 'H3118': 'o', 'H4421': 'o', 'H4494': 'o', 'H4496': 'o', 'HE020': 'o'}

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
def getAlta(r):
    et = ET.fromstring(r.RegistroXML)
    t = findInXML('DescripcionNota', et)
    txt = cleanString(t).lower()

    if 'alta voluntaria' in txt:
        return 'altaVoluntaria'
    elif 'cuidados intermedios' in txt:
        return 'cuidadosIntermedios'
    elif 'cuidados basicos' in txt:
        return 'cuidadosBasicos'
    elif 'alojamiento conjunto'in txt:
        return 'alojamientoConjunto'
    elif 'alta medica'  in txt or 'alta hospitalaria' in txt:
        return 'altaMedica'
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
        res['VAR_0015'] = 'D'

    res['VAR_0018'] = 'CMRC'
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
        findInXML('aFarmacologicos', etIngreso) == "true"
        findInXML('aGinecoObstetrico', etIngreso)  == "true"
        findInXML('aHospitalarios', etIngreso)  == "true"
        findInXML('aTraumaticos', etIngreso)  == "true"
        findInXML('aPatologicos', etIngreso)  == "true"
        if findInXML('aQuirurgicos', etIngreso)  == "false":
            res['VAR_0032'] = 'A'
        findInXML('aToxico', etIngreso)  == "true"
        findInXML('aTranfusionales', etIngreso)  == "true"
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
            #TODO: parse date
        else:
            res['no_echo'] =  'no_information'

        #PARACLINICS
        #TODO



        # MORBILIDAD:

        #Ingreso
        res['VAR_0183'] =data.casoDesc.FechaHora

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



def findDesgarros(text):
    text = text.replace(' de ', ' ').replace(' se ', ' ')
    
    removeWords = ['lateral', 'izquierda', 'derecha', 'superior', 'inferior', 'medial']
    for w in removeWords:
        text = text.replace(' %s ' % w, ' ')

    #Perdida de sangre
    bloodLost = re.findall('perdida estimada sangre(?::)? ([0-9]+) (?:cc|ml)', text)
    ver = '(?:eviden[a-z]*|observ[a-z]*|vis[a-z]*|encont[a-z]*|presen[a-z]*)'   #diferentes manaeras de escribir ver
    negative = ['(?:sin|no) (?:%s )?desgar' % ver]
    positive = 'desgar[a-z]* (?:[a-z]* |(:?pared )?vag[a-z]* )?(?:sangr[a-z]* |no sangrant[a-z]* )?grado (i|ii|iii|1|2|3)'
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
        fechaParto = dateparser.parse(parsingDatabaseUtils.findInXML('fechaCirugia', etDescripcion))
        horaFinCirugia  = dateparser.parse(parsingDatabaseUtils.findInXML('horaFin', etDescripcion)) #If nothing else is found, a candidate for birth
        res['VAR_0284'] = str(fechaParto.year) + '/' +  str(fechaParto.month)  + '/' + str(fechaParto.day)
        res['VAR_0285'] = str(horaFinCirugia.hour) + ':' +  str(horaFinCirugia.minute) 
    except TypeError:
        pass
    # Presentacion
    if 'cefalic' in txtDescription:
        res['VAR_202'] = 'A'
    # Posicion parto
    if 'en posicion de litotomia' in txtDescription:
        res['VAR_029'] = 'C'
    elif 'decubito dorsal' in txtDescription:
        res['VAR_029'] = 'C'

    # Desgarros
    gradoDesgarros = findDesgarros(txtDescription)
    if gradoDesgarros == 'no':
        res['VAR_0293'] = 'X'
    elif gradoDesgarros == 'yes-NoGrade':
        res['VAR_0294'] = '0'
    elif gradoDesgarros != 'unknown':
         res['VAR_0294'] = gradoDesgarros
            
    # Nacimiento vivo / muerto
    newbornPattern = '(rec[a-z]+ na[a-z]+|feto|producto)'
    if  re.findall('%s (unico )?vivo' % newbornPattern, txtDescription):
        res['VAR_0282'] = 'A'
    elif re.findall('%s (muerto|obitado|sin signos vitales)' % newbornPattern, txtDescription):
        res['VAR_0282'] = 'D'
    
    # C-section / vaginal
    if data.procTypeId == 'H3089':
        res['VAR_0287'] = 'A'
    elif data.procTypeId == 'H3094':
        res['VAR_0287'] = 'B'

    # Placenta completa/ retenida
    if re.findall('(extrae|obtiene) placenta (tip[a-z]+ [a-z]+ )?completa', txtDescription):
        res['VAR_0297'] = 'B'
        res['VAR_0298'] = 'A'
        
    # Peso / medidas 
    if re.findall('peso (%s)' % floatParse, txtDescription):
        res['VAR_0311'] = re.findall('peso (%s)' % floatParse, txtDescription)[0]
    if re.findall('talla (%s)' % floatParse, txtDescription):
        res['VAR_0314'] = re.findall('talla (%s)' % floatParse, txtDescription)[0]

    #APGAR: TODO, easier to get from newborn registration, otherwise is dead.
    
    # TODO: defectos
    if 'sin malformaciones evidentes' in txtDescription:
        res['VAR_0335'] = 'A'
    return res

def getNewbornData(data, idNewBornRegister, debug = False):
    register = data.registrosRecienNacido[idNewBornRegister][idNewBornRegister]

    etRegistro = ET.fromstring(register.RegistroXML)
    res = {}
    #prettyPrintXML(register.RegistroXML)
    res['VAR_0284']  = findInXML('InputText_FechaHoraNacimiento', etRegistro)
    res['VAR_0283'] = findInXML('ASPxTimeEdit_HoraNacimiento', etRegistro)
    res['VAR_0198'] = findInXML('InputText_EdadGestac', etRegistro)
    EG2 = findInXML('InputText_EdadGestacDubowitzModificado', etRegistro)
    res['partoVag'] = findInXML('TexTarea_PartoVaginal', etRegistro) == 'SI'
    partoC = findInXML('TexTarea_PartoCesaria', etRegistro) == 'SI'
    res['VAR_0321'] = findInXML('InputText_APGAR', etRegistro)
    if findInXML('ASPxComboBox_Sexo', etRegistro) == 'Masculino':
        res['VAR_0310'] = ' B'
    elif findInXML('ASPxComboBox_Sexo', etRegistro) == 'Femenino':
        res['VAR_0310'] = ' A'
    elif findInXML('ASPxComboBox_Sexo', etRegistro):
        res['VAR_0310'] = ' C'
    vivo = findInXML('InputRadio_VM', etRegistro) == 'Vivo'
    
    #Antrhopometrics
    res['VAR_0311'] = findInXML('InputText_Peso', etRegistro)
    res['VAR_0314'] = findInXML('InputText_Talla', etRegistro)
    res['VAR_0313'] = findInXML('InputText_CC', etRegistro)
    
    #As a double check of GAPC
    G = findInXML('InputText_ObstetricosGestaciones', etRegistro)
    A = findInXML('InputText_ObstetricosAbortos', etRegistro)
    P = findInXML('InputText_ObstetricosPartos', etRegistro)
    C = findInXML('InputText_ObstetricosCesareas', etRegistro)
    
    
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
                res['VDRL'] = 'positive' if r[0] in pos else 'negative'
                break
        except Exception as e:
            pass
    #Hospital discharge, and where

    return res