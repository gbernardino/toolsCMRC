"""
Structure to hold the information relative to 
"""
import re, xml.etree.ElementTree as ET
import parsingDatabaseUtils, numpy as np, collections, itertools

def similarNewbornRegister(reg1, reg2):
    """
    Check whether two registers are actually the same, check antropometric parameters.
    """
    et1 = ET.fromstring(reg1.RegistroXML)
    et2 = ET.fromstring(reg1.RegistroXML)
    parametersToCheck = ['InputText_Peso', 'InputText_Talla', 'InputText_CC', 'InputText_CT']
    return all([parsingDatabaseUtils.findInXML(p, et1) == parsingDatabaseUtils.findInXML(p, et2) for p in parametersToCheck])

class BirthDataset:
    """
    Data structure with the information regarding a case, including:
    
    - Procedure
    - Epicrisis
    - Registro de urgencias
    - newborn registration / updates
    - newborn discharge
    """
    posibilitiesAlta = ['alta', 'salida', 'egreso', 'remision', 'traslado']
    def __init__(self, caso, casoDesc, procedure, registros, pacientes, ordenNacimiento = 0):
        self.casoID = caso 
        self.casoDesc = casoDesc
        self.procedure = procedure
        self.procTypeId = procedureType = re.findall('<idProcedimiento>([a-zA-Z0-9]*)</idProcedimiento>', procedure.XmlDescripcion)[0]
        #Split between mother and newborn
        self.registersMother = []
        self.registersNewborn = []
        self.registersUnassigned = []
        self.epicrisis = None
        self.ingreso = None
        self.motherData = pacientes.loc[str(registros.iloc[0].NumeroHistoria)]
        self.registrosRecienNacido = collections.defaultdict(dict)
        #Assign each register to mother/newborn or unknown
        for rId, reg in registros.iterrows():
            patient, newbornRegisterRoot = parsingDatabaseUtils.isMaternalRegister(reg, registros, rId)
            if patient == 'mother':
                self.registersMother.append(reg)
            elif patient == 'newborn':
                self.registersNewborn.append(reg)
                self.registrosRecienNacido[newbornRegisterRoot][rId] = reg
            #Ignore the ones that are registro de incapacidad (#46), or a link to the description of a procedure(#145)
            elif reg.CodigoRegistro not in [145, 46]:
                #print(caso, reg.Asunto)
                self.registersUnassigned.append(reg)
            if 'Epicrisis' in str(reg.Asunto):
                self.epicrisis = reg
            if 'Ingreso de Urgencias' == reg.Asunto:
                self.ingreso = reg
                
        self.cleanRegistersNewBorn(registros)
        #Find discharge of baby
        self.newbornDischarge = list(filter(lambda s:
                                       any([p in parsingDatabaseUtils.remove_diacritics(str(s.Asunto)).lower()
                                            for p in BirthDataset.posibilitiesAlta]),
                                       self.registersNewborn
                                      )
                                  )
        if self.newbornDischarge:
            self.newbornDischarge = self.newbornDischarge[0]
            
        elif len(self.newbornDischarge) == 0 and len(self.registersNewborn) > 1: 
            i = np.argmax([p.FechaAsignacionRegistro for p in self.registersNewborn])
            self.newbornDischarge = self.registersNewborn[i]
    def cleanRegistersNewBorn(self, registers):
        """
        Sometimes several registers are added. Clean them.
        """
        toDelete = []
        for i, j in itertools.permutations(self.registrosRecienNacido.keys(), 2):
            if i < j and  similarNewbornRegister(registers.loc[i], registers.loc[j]):
                if len(self.registrosRecienNacido[i]) == 1:
                    toDelete.append(i)
                elif len(self.registrosRecienNacido[j]) == 1:
                    toDelete.append(j)
        for d in set(toDelete):
            del self.registrosRecienNacido[d]
            
    def getMotherLastState(self):
        """
        Get the last state (probably a discharge)
        """
        m = None
        for  r in self.registersMother:
            if 'Epicrisis' not in r.Asunto:
                if  m is None or m.FechaAsignacionRegistro < r.FechaAsignacionRegistro:
                    m = r
        return m

    def getNewbornLastState(self, newbornRegisterId):
        """
        Get the last state (probably a discharge)
        """
        m = None
        for  r in self.registrosRecienNacido[newbornRegisterId].values():
            if all([p not in str(r.Asunto).lower() for p in ['registro', 'correccion', 'nan']]):
                if  m is None or m.FechaAsignacionRegistro < r.FechaAsignacionRegistro:
                    m = r
        return m        
