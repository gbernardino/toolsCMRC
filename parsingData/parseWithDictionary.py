def parseWithDictionary(allCodes, dictionary):
    res = {}
    allInstructions = []
    for c in allCodes:
        allInstructions += dictionary[c].split(';')
    for c in filter(lambda s: s, allInstructions):
        rhs, lhs = c.split('=')
        res[rhs.strip()] = lhs.strip()
    return res