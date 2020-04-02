"""
Parse epicrisis
 s
- FUM
- ECHOS
- PARACLINICS (TO SOME EXTENT)
"""
from parsingDatabaseUtils import cleanString, removeWords, floatParse, date, sep,findInXML, remove_diacritics, parseDate, searchFUM
import re, dateparser, parsingDatabaseUtils
import xml, itertools, xml.etree.ElementTree as ET
from parsingData.procedures import classificationProcedures

tofloat = lambda s: float(s.replace(',', '.'))

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

noRecuerda = ['no', '\?']
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

def normalizeVenezuelanName(s):
    s = str(s)
    s = s.lower().replace('ven', 'v').replace('v', 'VEN')
    return s

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
    res['VAR_0019'] = normalizeVenezuelanName(data.motherData.Identificacion) 
    
    #Edad maternal
    res['VAR_0009'] = parseDate(data.epicrisis.FechaAsignacionRegistro,'datetime')-  parseDate(res['VAR_0006'],'datetime')
    res['VAR_0009'] = int(res['VAR_0009'].days/365.25)
    res['VAR_0010'] = 'A' if res['VAR_0009'] >= 15 and 35 >= res['VAR_0009'] else 'B' 

    return res

def getDataFromHospitalAdmision(data):
    # Antecedentes
    res = {}
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
        res['aFarm'] = findInXML('aFarmacologicos', etIngreso) == "true"
        findInXML('aGinecoObstetrico', etIngreso)  == "true"
        res['aHosp'] = findInXML('aHospitalarios', etIngreso)  == "true"
        res['aTraum'] = findInXML('aTraumaticos', etIngreso)  == "true"
        res['aPathol'] = findInXML('aPatologicos', etIngreso)  == "true"
        if findInXML('aQuirurgicos', etIngreso)  == "false":
            res['VAR_0032'] = 'A'
        res['aToxic'] = findInXML('aToxico', etIngreso)  == "true"
        res['aTransf'] = findInXML('aTranfusionales', etIngreso)  == "true"

        #If all are false, and 1-> \n in the description, put the 

        #Height and weight
        try:
            res['VAR_0055'] = float(findInXML("Peso", etIngreso))
            res['VAR_0056'] = float(findInXML("Talla", etIngreso)) * 100 - 100
        except:
            pass
        return res

def getDataFromEpicrisis(data):
    res = {}
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
                res['VAR_0057'] = parsingDatabaseUtils.parseDateInRangetRange(gpca_fum['fum'], data.procedure.FechaRegistro)

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
    #Parto aborto
    if classificationProcedures[data.procTypeId] == 'p':
        res['VAR_0182'] = 'A' 
    if classificationProcedures[data.procTypeId] == 'a':
        res['VAR_0182'] = 'B'

    return res
