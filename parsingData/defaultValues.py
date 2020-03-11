#Valores por defecto para variables.
#Anyadid una linea por variable siguiendo el sigiuiente ejemplo defaultValues['VAR_XXX'] = 'VALORPORDEFECTO' (Con las comillas)
defaultValues = {}
defaultValues['VAR_0650'] = 'A'


def addDefaultValues(res):
    for k, v in defaultValues.items():
        if k not in res:
            res[k] = v
    return res
            