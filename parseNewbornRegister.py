"""
Parse mother and newborn information

TODO: the newborn register also has information on the mother background and previous illnesses, as well as the tests done.
"""
import re
from parsingDatabaseUtils import findInXML, cleanString, removeWords, remove_diacritics, searchFUM, parseDate
import xml.etree.ElementTree as ET


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
    res['VAR_0284']  = parseDate(findInXML('InputText_FechaHoraNacimiento', etRegistro), output = 'string')
    res['VAR_0283'] = findInXML('ASPxTimeEdit_HoraNacimiento', etRegistro).replace(':', '').split()[0]
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
    
    #Antrhopometrics
    res['VAR_0311'] = findInXML('InputText_Peso', etRegistro).replace('.', '').replace(',', '')
    res['VAR_0314'] = findInXML('InputText_Talla', etRegistro).replace(',', '.')
    res['VAR_0313'] = findInXML('InputText_CC', etRegistro).replace(',', '.')
    
    #As a double check of GAPC
    res['VAR_0040'] = findInXML('InputText_ObstetricosGestaciones', etRegistro)
    res['VAR_0041'] = findInXML('InputText_ObstetricosAbortos', etRegistro)
    res['VAR_0046'] = findInXML('InputText_ObstetricosPartos', etRegistro)
    res['VAR_0047'] = findInXML('InputText_ObstetricosCesareas', etRegistro)
    
    #FUM
    fum = findInXML('InputText_FUM', etRegistro)
    if fum:
        res['VAR_0057'] = fum
    else:
        #Parse from "TexTarea_AntecedentesMaternosPrenatales"
        antececedentesText = findInXML('TexTarea_AntecedentesMaternosPrenatales', etRegistro)
        antececedentesText = cleanString(antececedentesText).lower()
        antececedentesText = removeWords(antececedentesText, ['a', 'de', 'el', 'que', 'para', 'y'])
        allFUM = searchFUM.findall(antececedentesText)

        if allFUM:
            
            fum = allFUM[0]
            if  fum in ['?', 'no']:
                res['VAR_0059'] =  'A'
                res['VAR_0057'] = '07/06/1954'
            else:
                res['VAR_0059'] = 'B'
                res['VAR_0057'] = fum

    #Get echos and paraclinics
    #TODO <- important for the registers that did not enter through the emergency room

    res['sufrimientoFetal'] = findInXML('TexTarea_SufrimientoFetal', etRegistro)

    #Paraclinic check on the notes
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
            dischargeDate = dischargeRegister.FechaAsignacionRegistro.split()[0]
            if alta == 'altaMedica':
                res['VAR_0425'] = dischargeDate
                res['VAR_0372'] = 'alta'
            elif alta == 'altaVoluntaria':
                res['VAR_0425'] = dischargeDate
                res['VAR_0372'] = 'altaVol'

            elif alta == 'cuidadosBasicos':
                res['VAR_0425'] = dischargeDate
                res['VAR_0372'] = 'cuidadosBasicos'

            elif alta == 'cuidadosIntermedios':
                res['VAR_0425'] = dischargeDate
                res['VAR_0372'] = 'cuidadosIntermedios'

            elif alta == 'uci':
                res['VAR_0425'] = dischargeDate
                res['VAR_0372'] = 'UCI'

            elif alta == 'alojamientoConjunto':
                res['VAR_0425'] = dischargeDate
                res['VAR_0381'] = 'Cuidados intermedios'
                res['VAR_0330'] = 'A'
    return res