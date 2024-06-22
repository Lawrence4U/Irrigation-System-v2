import json

def getDatos():
    f = open("datos.json")
    return json.load(f)

def loadConfig():
    f = open("config.json")
    return json.load(f)

def guardarConfig(values): # TODO
    
    with open("config.json", "w") as outfile:
        outfile.write(json.dumps(values))
    return

def cargarConfig(window):
    f = open("config.json", "r")
    conf = json.load(f)
    for num in ('0', '1', '2', '3'):
        for i,tipo in enumerate(('gap', 'duracion')):
            print(window[tipo + num])
            window[tipo + num].update(conf["V"+num][i])
    
    
    return