from parsingDatabaseUtils import cleanString, floatParse, fullCleanTxt, findInXML, removeWords, parseDate
import pandas, numpy as np,re
import collections, datetime, parsingDatabaseUtils
import xml, itertools, xml.etree.ElementTree as ET


class MeasurementsByDay():
    def __init__(self, name = 'pressure'):
        self.maxVals = collections.defaultdict(lambda: 0) 
        self.minVals = collections.defaultdict(lambda: 1000) 
        self.name = name
    def addMeasurement(self, date, p):
        date =  datetime.datetime.strptime(date.split()[0], '%Y-%m-%d')
        if  not isinstance(p, str) or '/' not in p:
            p = '%s/%s' % (p, p)
        maxVal, minVal = p.split('/')
        maxVal, minVal = float(maxVal.replace(',','')), float(minVal.replace(',',''))
        if maxVal and minVal:
            self.maxVals[date] = max(self.maxVals[date], maxVal)
            self.minVals[date] = min(self.minVals[date], minVal)
    def toDict(self):
        res = {}
        for i, d in enumerate(sorted(self.maxVals.keys())):
            res['day_%03d_%s' % (i, self.name)] = str(self.maxVals[d]) + '/' +  str(self.minVals[d])
            res['day_%03d' % i] = d

            
def identifyPressureInText(text):
    text = text.upper()
    return re.findall('(?:TA|PA|TENSION|PRESION)\s*([0-9]+)[-/]([0-9]+)\s*MMHG', text )
    
def identifyHRInText(text):
    text = text.upper()
    return re.findall('(?:FC)\s*([0-9]+)', text )

def identifyRRInText(text):
    text = text.upper()
    return re.findall('(?:FR)\s*([0-9]+)', text )

def identifyTInText(text):
    text = text.upper()
    return re.findall('(?:T)\s*(%s)' % floatParse, text )


def parseVitalSignsFromRegister(r):
    """
    Tries to find the vital signs in both the xml fields and the free text.
    """
    res = []
    et = ET.fromstring(r.RegistroXML)
    fecha = r.FechaAsignacionRegistro.split()[0]
    txt = fullCleanTxt(findInXML('DescripcionNota', et))

    # Pressure
    pressure = findInXML('Presion', et)
    if not pressure or pressure == '/':
        pressure = None
        if txt:
            pressure = identifyPressureInText(txt)
            if pressure:
                pressure = '/'.join(pressure[0])
    if pressure:
        res += [('Pas', fecha, pressure.split('/')[0], r.FechaAsignacionRegistro)]
        res += [('Pad', fecha, pressure.split('/')[1], r.FechaAsignacionRegistro)]

    # FC
    fc = findInXML('FrecuenciaCardiaca', et)
    if not fc:
        if txt:
            fc = identifyHRInText(txt)
            if fc:
                fc = fc[0]
    if fc:
        res += [('hr', fecha, fc, r.FechaAsignacionRegistro)]

    # RR
    rr = findInXML('FrecuenciaRespiratoria', et)
    if not rr:
        if txt:
            rr = identifyRRInText(txt)
            if rr:
                rr = rr[0]
    if rr:
        res += [('rr', fecha, rr, r.FechaAsignacionRegistro)]

    # T    
    temperature = findInXML('Temperatura', et)
    if not temperature or temperature == '/':
        if txt:
            temperature = identifyTInText(txt)
            if temperature:
                temperature = temperature[0]
    if temperature:
        res += [('T', fecha, temperature, r.FechaAsignacionRegistro)]
    return res

def getVitalSignsFromEntry(entry):
    """
    m dataframe with all entries of a single case at a given date
    """
    res = ()
    dateRegister = entry.FechaRegistro.split()[0]
    if entry.CodSignoVitalTipo == 'PRSI' or entry.CodSignoVitalTipo == 'PAS':
        res= ('Pas', dateRegister, entry.Valor, dateRegister)
    elif entry.CodSignoVitalTipo == 'PRDI' or entry.CodSignoVitalTipo == 'PAD':
        res =('Pad', dateRegister, entry.Valor, dateRegister)
    elif entry.CodSignoVitalTipo in ['FRCA', 'FC']:
        res = ('hr', dateRegister, entry.Valor, dateRegister)
    elif entry.CodSignoVitalTipo in ['FRRE', 'FR']:
        res = ('rr', dateRegister, entry.Valor, dateRegister)
    elif entry.CodSignoVitalTipo == 'T':
        res = ('T', dateRegister, entry.Valor, dateRegister)
    return res

def getAllVitalSigns(data):
    vitalSigns = []
    for r in data.registersMother:
        vitalSigns += parseVitalSignsFromRegister(r)
    
    for e in data.entriesInfirmaryMother:
        entryParsed = getVitalSignsFromEntry(e)
        if entryParsed:
            vitalSigns += [entryParsed]
    return vitalSigns

meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
meses = meses + list(map(lambda s: s[:3], meses))
sep= '\s*[,;:]?\s*'
separadorFecha = '(?:[\.\\/-]|DE|DEL|\s)'
date =  '\(?' +  '((?:[0-9]+)'+ sep + separadorFecha + sep + '(?:[0-9]+|%s)'%  '|'.join(meses) + \
                       sep + separadorFecha + sep + '(?:[0-9]+))' + '\)?' 

# read paraclinics. Assume that the date is just before them, or in the same line
pos = ['pos', '\+', 'reac']
neg = ['neg', '-', 'no']
vih1  = 'vih\s*[1i]'
vih2 = 'vih\s*(:?2|ii)'
vih12 = 'vih\s*[1i]\s*(:?2|ii)'
prt = '(:?PRUEBA RAPIDA TREPONEMICA|PRT)'
vdrl = '(:?VDRL|SIF[A-Z]*|RPR|FTA|FTA ABS)'
floatParse = '[0-9]*[\.,]?[0-9]+'

hematology = {
'HCT' : '(HCT|HTO|HTC|HEMATO[A-Z]*)',
'HB' : '(HB|HEMOGLOB[A-Z]*)',
'LEU' : '(LEU[A-Z]*)',
'NEU' : '(NEU[A-Z]*)',
'LIN' : '(LIN)',
'MONO' : '(MONO[A-Z]*)',
'PLAQ' : '(PL[A-Z]*|PQT)'}

meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
meses = meses + list(map(lambda s: s[:3], meses))
sep= '\s*[,;:]?\s*'
separadorFecha = '(?:[\.\\/-]|DE|DEL|\s)'
date =  ' \(?' +  '((?:[0-9]|[0-3][0-9])'+ sep + separadorFecha + sep + '(?:[0-9]+|%s)'%  '|'.join(meses) + \
                       sep + separadorFecha + sep + '(?:[0-9]+))' + '\)?' 
def parseParaclinicsFromText(txt, date, datehour):
    results = []
    #haematology
    for p, v in hematology.items():
        hematologyRes = re.findall('%s (%s)[^x]' % (v, floatParse), txt, re.IGNORECASE)
        if hematologyRes:
            results += [(p, date, hematologyRes[0][1], datehour)]

    #sifilis
    sif1 = ' ' + vdrl + " (%s)" % '|'.join(pos + neg)
    searchSif1 = re.findall(sif1, txt, re.IGNORECASE)
    sif2 = ' ' + prt + " (%s)" % '|'.join(pos + neg)    
    searchSif2 = re.findall(sif2, txt, re.IGNORECASE)
    if searchSif1:
        results += [('vdrl', date, searchSif1[0][1] in pos, datehour)]
    if searchSif2:
        results += [('prt', date, searchSif2[0][1] in pos, datehour)]
    # TODO: vih
    return results
          
def parseParaclinicsBeforeHospitalisation(r):
    lastDate = None
    if not isinstance(r, str):
        rET = ET.fromstring(r.RegistroXML)
        rTxt = fullCleanTxt(findInXML('AntecedentesHTML', rET))
        rTxt = removeWords(rTxt, ['de', 'y', 'a', 'el', 'los'])
    else:
        rTxt = r
        
        
    lastDate = None
    results = []
    if re.findall('(no|sin|ni) (prese[a-z]*|tien[a-z]*|tra[a-z]*)(\s)*para', rTxt):
        results  += [('controlesPrenatal', 'sinControles', 0, 'NONE' )]
        return results
    
    for i, l in enumerate(rTxt.splitlines()):
        l = ' ' + l
        # use instead dateparser.search.search_dates  <- it goes too slow
        d = re.findall(date, l, re.IGNORECASE)
        # dFiltered = [dateparser.parse(dd) for dd in d]
        #dFiltered = [dd for dd in dFiltered if dd]

        if len(d) == 1.:
            dateParsed = parseDate(d[0], output = 'string')
        elif len(d):
            lastDate = None
            
        if len(d) <= 1 and lastDate:
            r = parseParaclinicsFromText(l, lastDate, lastDate)
            results += r
    return results
                
def getParaClinicsHospitalisation(data): 
    resultNotes = []
    for r in data.registersMother:
        txt = findInXML('DescripcionNota' , r.RegistroXML)
        if not txt:
          continue
        txt = fullCleanTxt(txt)
        noteResult = parseParaclinicsFromText(txt, r.FechaAsignacionRegistro.split()[0], r.FechaAsignacionRegistro)
        if noteResult:
            resultNotes += noteResult
    return resultNotes


def getParaClinicsNewbornRegistry(r): 
    txt = findInXML('TexTarea_AntecedentesMaternosPrenatales' , r)
    txt = fullCleanTxt(txt)
    result = parseParaclinicsFromText(txt, r.FechaAsignacionRegistro.split()[0], r.FechaAsignacionRegistro)
    return result


def getAllMotherParaclinics(data):
    if data.epicrisis is not None:
        resultsEpi = parseParaclinicsBeforeHospitalisation(data.epicrisis)
    else:
        resultsEpi = []
    resultNotes = getParaClinicsHospitalisation(data)
    return resultsEpi + resultNotes


def measurementsToDict(dfMeasurements, name = 'day'):
    res = {}
    dfMeasurementsByDate = dfMeasurements.groupby('Fecha')
    for i, d in enumerate(dfMeasurementsByDate.groups):
        dfValues =dfMeasurementsByDate.get_group(d).groupby('Campo')['Valor'].agg(['median', 'max', 'min'])
        res['%s_%d' % (name,i)] = d
        for var, row in dfValues.iterrows():
            res[var + '_median_%s_%d' % (name,i)] = row.median()
            res[var + '_max_%s_%d' % (name,i)] = row.max()
            res[var + '_min_%s_%d' % (name,i)] = row.min()
    return res

def processPrenatalMeasurements(measurementsControlsPrenatal, fum):
    res = {}
    for test, date, value, _ in measurementsControlsPrenatal.values:
        if test in ['vdrl', 'HB', 'prt']:
            weeks = parsingDatabaseUtils.dateDifferenceDays(date, fum)//7
            if weeks < 0:
                #print('Error, negative weeks found')
                res['negative_week'] = True
                #raise ValueError('Inconsistent!')

            elif weeks <= 20:
                if test == 'vdrl':
                    #no treponemica
                    res['VAR_0112'] = 'A' if not value else 'B'
                    res['VAR_0412'] = weeks # Weeks

                elif test == 'prt':
                    #treponemica
                    res['VAR_0415'] = 'A' if not value else 'B'
                    res['VAR_0413'] = weeks # Weeks

                elif test == 'HB':
                    res['VAR_0095'] = value

            elif weeks > 20 and weeks < 60:
                if test == 'vdrl':
                    res['VAR_0114'] = 'A' if not value else 'B'
                    res['VAR_0419'] = weeks # Weeks

                elif test == 'prt':
                    res['VAR_0421'] = 'A' if not value else 'B'
                    res['VAR_0420'] = weeks # Weeks

                elif test == 'HB':
                    res['VAR_0099'] = value
    return res