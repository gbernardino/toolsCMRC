import pandas, os

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.exceptions import PreventUpdate

class Data:
    def __init__(self, path = '../Casos2019'):
        self.pacientes = pandas.read_csv(os.path.join(path, 'pacientes.csv'), index_col = 0)
        self.pacientes.index = self.pacientes.index.map(str)
        self.registros = pandas.read_csv(os.path.join(path, 'registrosFiltered.csv'), index_col = 0)
        self.registros.index = self.registros.index.map(str)
        self.casos = pandas.read_csv(os.path.join(path, 'casos.csv'), index_col = 0)
        self.casos['Paciente'] = self.casos['Paciente'].map(str)
        self.procedimientos = pandas.read_csv(os.path.join(path, 'procedimientos.csv'), index_col = 0)
        
        #Filter patients and cases
        ids = self.registros.NumeroHistoria.drop_duplicates().map(str)
        idsOK = ids.loc[ids.map(lambda s: s in self.pacientes.index)]
        self.pacientes = self.pacientes.loc[idsOK]

        ids = self.registros.Caso.drop_duplicates().map(str)
        idsOK = ids.loc[ids.map(lambda s: s in self.casos.index)]
        self.casos = self.casos.loc[idsOK]
        
        self.casosByPatient = self.casos.groupby('Paciente')
        self.registrosByCase = self.registros.groupby('Caso')

data = Data()
print('Data read')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([
        html.Div(html.Label(
            [
                "Patient selecter",
                dcc.Dropdown(
                    id='patient-Selecter',
                    options = [ { 'value' : k, 'label': i } for  k, i in data.pacientes['Identificacion'].items()] 

                    )
            ]),  style={'width': '30%', 'display': 'inline-block'}),

        html.Div(html.Label(
            [
                'Case selecter',
                dcc.Dropdown(
                    id = 'case-Selecter'
                )
           ]), style={'width': '30%', 'display': 'inline-block'}),

        html.Div(html.Label(
            [  
                'Register selecter',
                dcc.Dropdown(
                    id = 'register-Selecter')
            
            ]), style = {'width': '30%', 'display': 'inline-block'}),
    
        html.Div(['hi'], id='dd-output-container')
    ]
)

@app.callback(
    dash.dependencies.Output('case-Selecter', 'options'),
    [dash.dependencies.Input('patient-Selecter', 'value')])
def updateOptionsCase(value):
    if value is not None:
        return [ {'value': k, 'label' : k}  for k in data.casosByPatient.get_group(value).index]
    else:
        raise PreventUpdate

@app.callback(
    dash.dependencies.Output('case-Selecter', 'value'),
    [dash.dependencies.Input('case-Selecter', 'options')])
def setCaseValue(options):
    if options:
        return options[0]['value']
    else:
       raise PreventUpdate

@app.callback(
    dash.dependencies.Output('register-Selecter', 'options'),
    [dash.dependencies.Input('case-Selecter', 'value')])
def setRegisterOptions(value):
    if value:
        return [ {'value': str(k), 'label' : str(k) + ' - ' + str(row.Asunto) + ' - '  + row.FechaAsignacionRegistro}  for k, row in data.registrosByCase.get_group(value).iterrows()]
    else:
       raise PreventUpdate


#####
# Write a case
#####
import xml
from html.parser import HTMLParser
pars =HTMLParser()
import html2markdown, re

def convert_html_to_dash(el,style = None):
    if type(el) == bs.element.NavigableString:
        return str(el)
    else:
        name = el.name
        style = extract_style(el) if style is None else style
        contents = [convert_html_to_dash(x) for x in el.contents]
        return getattr(html,name.title())(contents,style = style)
def extract_style(el):
    return {k.strip():v.strip() for k,v in [x.split(": ") for x in el.attrs["style"].split(";")]}

def fieldToHTMLLong(key, value):
    value = html2markdown.convert(value)
    value = re.sub('\<[^<]*?\>', ' ',  value)
    r = html.Div(
            [html.H4(key, style = { 'font-weight': 'bold'}), 
            dcc.Markdown(value, style={'width': '95%'}) ],
            style = {"border":"2px black solid", 'border-radius': '5px', 'background-color': 'azure'}
        )
    return r

def fieldToHTMLShort(key, value):
    value = html2markdown.convert(value)
    value = re.sub('\<[^<]*?\>', ' ',  value)
    r = html.Div(
            [ html.Div(html.H6(key, style = {'font-weight': 'bold'}), style={'width': '30%', 'display': 'inline-block'}), 
              html.Div(html.Label(value), style={'width': '30%', 'display': 'inline-block'}) ]
        )
    return r

def displayRegistroRecienNacido(et):
    pass

def displayProcedimiento(et):
    procId = et.find('row[@NombreCampo="CodigoActo"]').attrib['ValorCampo']
    pr = data.procedimientos.loc[data.procedimientos.ActoQuirurgico == procId].iloc[0]
    e = xml.etree.ElementTree.fromstring(pr.XmlDescripcion)
    allDisplayInfo = []
    for eChild in e.iter():
        if not eChild.text:
            continue
        elif len(eChild.text) > 100:
            r = fieldToHTMLLong(eChild.tag, pars.unescape(eChild.text))
        else:
            r = fieldToHTMLShort(eChild.tag, pars.unescape(eChild.text)) 
        allDisplayInfo.append(r)
    return allDisplayInfo

def displayGeneralRegister(et):
    allDisplayInfo = [] 
    for row in et.findall('.//row'):
        key = row.attrib['NombreCampo']
        value = pars.unescape(row.attrib['ValorCampo'])
        if not value:
            continue
        elif len(value) > 100:
            r = fieldToHTMLLong(key, value)
        else:
            r = fieldToHTMLShort(key, value)
        allDisplayInfo.append(r)
    return allDisplayInfo
@app.callback(
    dash.dependencies.Output('dd-output-container', 'children'),
    [dash.dependencies.Input('register-Selecter', 'value')])
def setInformation(value):
    if value:
        text = data.registros.loc[value].RegistroXML
        et = xml.etree.ElementTree.fromstring(text)
        codigo = data.registros.loc[value].CodigoRegistro
        if codigo ==145:
            return displayProcedimiento(et)
        #elif codigo ==165:
        #    displayRegistroRecienNacido(et)
        else:
            return displayGeneralRegister(et)
    else:
        raise  PreventUpdate()
if __name__ == '__main__':
    app.run_server(debug=True)