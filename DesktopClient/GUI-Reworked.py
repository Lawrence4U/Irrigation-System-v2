import tkinter as tk
import matplotlib
import re
import paho.mqtt.client as mqtt
import json
import threading
import codecs
import pytz

from tkinter.ttk import *
from xmlrpc.client import Boolean
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.pyplot import text
from matplotlib.sankey import RIGHT
from base64 import b64encode, b64decode
from threading import Timer
from dateutil import parser
from config import *


# Variables para identificar los canales de comunicación MQTT
# Cuenta de Lorenzo
application_id = 'tfg-icai'
tenant_id = 'tfg-icai'
device_id = 'arduino-tfg'

### GUI Functions
def saveValveConf():
    return

def toggle():
    print(btnActivo['text'])
    if btnActivo['text'] == "Inactivo":
        btnActivo.state(["pressed"])
        btnActivo.configure(text='Activo')
        print(btnActivo.state())
    else:
        btnActivo.state(["!pressed"])
        btnActivo.configure(text='Inactivo')
        print(btnActivo.state())


def intVartoInt(lista):
    lista = [i.get() for i in lista]
    return lista
    
def cButtonSemanal():
    print(chLunes.state())
    global opcion
    valores = intVartoInt(opcion)
    print(valores)
    print(root.winfo_height())
    
def comboSeleccionado(*args):
    print(selPrograma.get())
    
def commandFreq():
    if varFrecuencia.get():
        print("Personalizado")
    else:
        print("Unico")
        
    return

### MQTT
#-----------------------------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")

def find2nd(string, char):
    start = string.find(char)
    index = string[start + 1:].find(char)
    return index + start + 1

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # print(msg.topic)
    print(msg.payload.decode('utf-8'))
    recibido = json.loads(msg.payload.decode('utf-8'))
    # mensajes desde la placa
    # Cuenta Lorenzo
#    if msg.topic == 'v3/tfg-icai@tfg-icai/devices/arduino-tfg/up':
    # Cuenta INEA-ICAI
    if msg.topic == 'v3/' + application_id + '@' + tenant_id + '/devices/' + device_id + '/up': #TODO cambiar a topic
        print(codecs.decode(str(b64decode(recibido['uplink_message']['frm_payload']).hex()), 'hex').decode(
            'utf-8'))
        if codecs.decode(str(b64decode(recibido['uplink_message']['frm_payload']).hex()), 'hex').decode(
                'utf-8') == 'ERROR':
            # window['warning'].update(visible=True, value='Error en el envío, pruebe a enviarlo de nuevo')
            return

        if codecs.decode(str(b64decode(recibido['uplink_message']['frm_payload']).hex()), 'hex').decode(
                'utf-8') == 'Init':
            return

        try:
            humedad = int(
                codecs.decode(str(b64decode(recibido['uplink_message']['frm_payload']).hex()), 'hex').decode(
                    'utf-8'))
            str_humedad = codecs.decode(str(b64decode(recibido['uplink_message']['frm_payload']).hex()), 'hex').decode(
                    'utf-8')
            humedad_sensor = [int(str_humedad[0:3]), int(str_humedad[3:6]),
                              int(str_humedad[6:9]), int(str_humedad[9:12])]
            print('Humedad sensor 1 = ', humedad_sensor[0])
            print('Humedad sensor 2 = ', humedad_sensor[1])
            print('Humedad sensor 1 = ', humedad_sensor[2])
            print('Humedad sensor 2 = ', humedad_sensor[3])
            t = Timer(390, timerEnd, args=[client])
            t.start()
            
            print('% de humedad:', humedad)
            madridtz = pytz.timezone("Europe/Madrid")
            try:
                tiempo = parser.isoparse(recibido['uplink_message']['received_at']).astimezone(madridtz)
            except:
                tiempo = parser.isoparse(recibido['received_at']).astimezone(madridtz)#al hacer pruebas cuando el paqeute viene de la plataforma es distinto
            print(tiempo)
            fecha = str(tiempo.date())
            hora = str(tiempo.time())
            key = str(fecha + " " + hora[:find2nd(hora, ':')])
            datos_prev = getDatos()

            #print(datos_prev)
            if key not in datos_prev.keys():
                datos_prev[key] = humedad_sensor
            json_completo = json.dumps(datos_prev)

            with open("datos.json", "w") as outfile:
                outfile.write(json_completo)
        except:
            print("valor del arduino no correcto")
        # los datos se guardaran en un dict de manera {(Fecha, Hora) : Valor}



    # mensajes hacia la placa
    # Cuenta Lorenzo
#    elif msg.topic == 'v3/tfg-icai@tfg-icai/devices/arduino-tfg/down/queued':
    elif msg.topic == 'v3/' + application_id + '@' + tenant_id + '/devices/' + device_id + '/down/queued':
        print(b64decode(recibido['downlink_queued']['frm_payload']).hex().upper())


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
#-----------------------------------------------------------------------------------------------

### Plotting
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------

def enviarPaquete(client):
    listaEnvio = []
    inmediatos = 0
    global listaAcciones
    for num in ('0', '1', '2', '3'):
        for letra in ('A', 'C'):
            if "".join([letra, num]) in listaAcciones:
                inmediatos = (inmediatos << 1) + 1
            else:
                inmediatos = inmediatos << 1
    inmediatos = hex(int(inmediatos))
    inmediatos = inmediatos.split('x')[1] if len(inmediatos.split('x')[1]) == 2 else '0' + inmediatos.split('x')[1]
    listaEnvio.append(inmediatos)
    
    if 'horario' in listaAcciones:        
        conf = loadConfig()
        for valor in conf.values():
            for i in valor:
                if i == '0':
                    listaEnvio.append('00')
                else:
                    elem = hex(int(i))
                    elem = '0' + elem[elem.index('x') + 1:] if len(elem[elem.index('x') + 1:]) == 1 else elem[elem.index('x') + 1:]
                    listaEnvio.append(elem)
    else:
        for i in range(8):
            listaEnvio.append('00')
            
            

    payload = ''.join([str(item) for item in listaEnvio])
    print(payload)
    pay_b64 = b64encode(bytes.fromhex(payload)).decode()
    pay = '{"downlinks":[{"f_port": 1,"frm_payload":"' + pay_b64 + '","priority": "NORMAL"}]}'
    #cuenta Lorenzo
#    client.publish(topic='v3/tfg-icai@tfg-icai/devices/arduino-tfg/down/replace', payload=pay, qos=0, retain=False)
    client.publish(topic='v3/' + application_id + '@' + tenant_id + '/devices/' + device_id + '/down/replace', payload=pay, qos=0, retain=False)
    listaAcciones = []
    return


def mqtt_client_listener(client):
    client.loop_forever()

def timerEnd(client):
    global queued
    print('Activated timer')
    if queued:
        #window['warning'].update(visible=True, value='Enviado')
        enviarPaquete(client)
        queued = False

def checkFormat(values):
    tipo = ('gap', 'duracion')
    for num in ('0', '1', '2', '3'):
        primVacio = False
        for tpo in tipo:
            if tpo=='duracion':
                if primVacio and values["".join([tpo,num])]!="":
                    return False
                elif not primVacio and values["".join([tpo,num])]=="":
                    return False
                    
            
            if not values["".join([tpo,num])].isdigit() and values["".join([tpo,num])]!="":
                return False
            elif values["".join([tpo,num])]=="" and tpo=='gap':
                primVacio=True
            
        
    return True

# def main():
#     # setup MQTT
    

#     # setup GUI
#     fig = Figure()
#     fig.autofmt_xdate()
#     ax = fig.add_subplot(111)
#     ax.set_xlabel("Fecha")
#     ax.set_ylabel("% Humedad")
#     ax.grid()
#     # fig_agg = draw_figure(window['Canvas'].TKCanvas, fig)
    
config = loadConfig()    

if __name__ == "__main__":
    #setup MQTT
    access = 'NNSXS.VCOASZCJR2TD4MZ4DYCTDDIJHJDI52LQYWNXWHA.76LAW2FWLS56JOYBJIQB6Z7GTDWZ2F4WKDMVESCENZXH6QGYVY3A'
    mqtt_address = 'eu2.cloud.thethings.industries'
    client = mqtt.Client()
    client.username_pw_set('tfg-icai@tfg-icai', password=access)

    # client.on_connect = on_connect
    # client.on_message = on_message
    # client.on_disconnect = on_disconnect
    # client.connect(host=mqtt_address, port=1883, keepalive=60)
    # hilo = threading.Thread(target=mqtt_client_listener, args=(client,))
    # hilo.start()
    
    ##GUI
    root = tk.Tk()
    root.title("Interfaz")
    root.geometry("550x650+600+300")
    
    #cargando estilos
    style = Style()
    style.theme_use('clam')
    style.configure('A.TButton', width = 10, foreground = 'white', borderwidth=0, focusthickness=0, focuscolor='none', takefocus=False)
    style.map("A.TButton", background=[('pressed', 'green4'), ('!pressed', 'grey27')])
    style.configure('TLabels', width = 10, foreground = 'white2')
    style.configure('TRadiobutton', indicatoron=0)
    style.configure('A.TCheckbutton', foreground = 'white', anchor='center', width=3, indicatorrelief=tk.FLAT, indicatormargin=-10, indicatordiameter=-10, heigth=3)
    style.map('A.TCheckbutton', background=[('!selected', 'grey27'), ('selected', 'green4')])
    style.configure('A.TSpinbox',)
    style.configure('B.TButton', width = 1, height = 1 ,foreground = 'white')
    style.map("B.TButton", background=[('pressed', 'green4'), ('!pressed', 'grey27')])
    
    #Cargando ventana
    top_frame = Frame(root)
    top_frame.pack(side=tk.TOP, padx=10, pady=10, anchor=tk.W)
    ##Selector de programas
    Label(top_frame, text='Programa:').pack(side=tk.TOP, anchor=tk.W)
    selPrograma = Combobox(top_frame, values=[1,2,3,4,5,6], width= 5, justify= 'center', state='readonly')
    selPrograma.current(0)
    selPrograma.bind("<<ComboboxSelected>>", comboSeleccionado)
    selPrograma.pack(side=tk.TOP, anchor=tk.W)
    
    tabGroup = Notebook(top_frame)
    
    tabValves = Frame(tabGroup)
    tabLigths = Frame(tabGroup)
    tabWindows = Frame(tabGroup)
    tabHeating = Frame(tabGroup)
    tabBlinds = Frame(tabGroup)
    
    tabGroup.add(tabValves, text='Válvulas')
    tabGroup.add(tabLigths, text='Luces')
    tabGroup.add(tabWindows, text='Ventanas')
    tabGroup.add(tabHeating, text='Calefacción')
    tabGroup.add(tabBlinds, text='Persianas')
    tabGroup.pack(padx=10, pady=10, fill='both', expand=True)
    
    
    ##Activación/desactivación del programa
    btnActivo = Button(tabValves, command=toggle, text='Inactivo', style='A.TButton')
    btnActivo.grid(column=0, row=tabValves.grid_size()[1], pady=5, padx=10, sticky='w')
    ##Etiqueta
    Label(tabValves, text='Frecuencia del programa').grid(column=0, row=tabValves.grid_size()[1], pady=10, sticky='w', padx=10)
    
    ##Selector de frecuencia
    varFrecuencia = tk.IntVar()
    fr_freq = Frame(tabValves)
    radFreq1 = tk.Radiobutton(fr_freq, text='Único',indicatoron=0, variable=varFrecuencia, value =0, command=commandFreq)
    radFreq2 = tk.Radiobutton(fr_freq, text='Personalizado',indicatoron= 0,variable=varFrecuencia, value =1, command=commandFreq)
    fr_freq.grid(column=0, row=tabValves.grid_size()[1], pady=5, columnspan=3, padx=10, sticky='w')
    radFreq1.pack(side='left')
    radFreq2.pack(side='right')


    ##Programacion semanal
    ###Primero habria que cargar la selección existente para este dia TODO
    fr_sem = Frame(tabValves)
    opcion= [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    chLunes = Checkbutton(fr_sem, text="L", variable=opcion[0], command=cButtonSemanal, style='A.TCheckbutton')
    chMartes = Checkbutton(fr_sem, text="M", variable=opcion[1], command=cButtonSemanal, style='A.TCheckbutton')
    chMiercoles = Checkbutton(fr_sem, text="X", variable=opcion[2], command=cButtonSemanal, style='A.TCheckbutton')
    chJueves = Checkbutton(fr_sem, text="J", variable=opcion[3], command=cButtonSemanal, style='A.TCheckbutton')
    chViernes = Checkbutton(fr_sem, text="V", variable=opcion[4], command=cButtonSemanal, style='A.TCheckbutton')
    chSabado = Checkbutton(fr_sem, text="S", variable=opcion[5], command=cButtonSemanal, style='A.TCheckbutton')
    chDomingo = Checkbutton(fr_sem, text="D", variable=opcion[6], command=cButtonSemanal, style='A.TCheckbutton')
    chLunes.grid(row=0, column=0, padx=5)
    chMartes.grid(row=0, column=1, padx=5)
    chMiercoles.grid(row=0, column=2, padx=5)
    chJueves.grid(row=0, column=3, padx=5)
    chViernes.grid(row=0, column=4, padx=5)
    chSabado.grid(row=0, column=5, padx=5)
    chDomingo.grid(row=0, column=6, padx=5)
    fr_sem.grid(column=0, row=tabValves.grid_size()[1], pady=5, columnspan=3, padx=30, sticky="ew")
    
    ##configuración de los programas
    listaOpciones=[]
    for i in range(144):
        for j in range(6):
            listaOpciones.append(f'{i%24}:{(j*10):02d}')
    
    listaOpciones = tuple(listaOpciones)
    
    ##valvulas
    Label(tabValves, text='Tiempos de arranque:').grid(column=0, row=tabValves.grid_size()[1], pady=5, padx=10, sticky='w')
    
    tiempos = {}
    for i in range(4):
        fr_hora = Frame(tabValves)
        Label(fr_hora, text='Hora: ').grid(column=0, row=0, pady=5, padx=10)
        tiempos[i] = {"start": tk.StringVar(value='0:00'), "duration": tk.StringVar(value='0:00')}
        Spinbox(fr_hora, textvariable=tiempos[i]['start'], wrap=True, values=listaOpciones, style='A.TSpinbox', width=5).grid(column=1, row=0, pady=5, padx=10)

        Label(fr_hora, text='Duracion: ').grid(column=2, row=0, pady=5, padx=10)
        Spinbox(fr_hora, textvariable=tiempos[i]['duration'], wrap=True, values=listaOpciones, style='A.TSpinbox', width=5).grid(column=3, row=0, pady=5, padx=10)
        
        fr_hora.grid(column=0, row=tabValves.grid_size()[1], pady=5, columnspan=3, padx=30, sticky="ew")
    
    ##Valvulas a las que aplicar el programa
    optVal = [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    Label(tabValves, text='Valvulas a operar:').grid(column=0, row=tabValves.grid_size()[1], pady=5, padx=10, sticky="w")
    Checkbutton(tabValves, text="Valvula 1", variable=optVal[0]).grid(column=0, row=tabValves.grid_size()[1],padx=20, sticky="w")
    Checkbutton(tabValves, text="Valvula 2", variable=optVal[1]).grid(column=0, row=tabValves.grid_size()[1],padx=20, sticky="w")
    Checkbutton(tabValves, text="Valvula 3", variable=optVal[2]).grid(column=0, row=tabValves.grid_size()[1],padx=20, sticky="w")
    Checkbutton(tabValves, text="Valvula 4", variable=optVal[3]).grid(column=0, row=tabValves.grid_size()[1],padx=20, sticky="w")
    
    ##Guardado de configuración
    Button(tabValves, text='Guardar Programa', command=saveValveConf).grid(column=0, row=tabValves.grid_size()[1],padx=10, pady=15, sticky="w")
    
    ### Luces ----------------------------------------------------------------------------------------------------
    
    ##Activación/desactivación del programa
    btnActivo_lights = Button(tabLigths, command=toggle, text='Inactivo', style='A.TButton')
    btnActivo_lights.grid(column=0, row=tabLigths.grid_size()[1], pady=5, padx=10, sticky='w')
    ##Etiqueta
    Label(tabLigths, text='Frecuencia del programa').grid(column=0, row=tabLigths.grid_size()[1], pady=10, sticky='w', padx=10)
    
    ##Selector de frecuencia
    varFrecuencia = tk.IntVar()
    fr_freq = Frame(tabLigths)
    radFreq1_lights = tk.Radiobutton(fr_freq, text='Único',indicatoron=0, variable=varFrecuencia, value =0, command=commandFreq)
    radFreq2_lights = tk.Radiobutton(fr_freq, text='Personalizado',indicatoron= 0,variable=varFrecuencia, value =1, command=commandFreq)
    fr_freq.grid(column=0, row=tabLigths.grid_size()[1], pady=5, columnspan=3, padx=10, sticky='w')
    radFreq1_lights.pack(side='left')
    radFreq2_lights.pack(side='right')


    ##Programacion semanal
    ###Primero habria que cargar la selección existente para este dia TODO
    fr_sem = Frame(tabLigths)
    opcion= [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    chLunes = Checkbutton(fr_sem, text="L", variable=opcion[0], command=cButtonSemanal, style='A.TCheckbutton')
    chMartes = Checkbutton(fr_sem, text="M", variable=opcion[1], command=cButtonSemanal, style='A.TCheckbutton')
    chMiercoles = Checkbutton(fr_sem, text="X", variable=opcion[2], command=cButtonSemanal, style='A.TCheckbutton')
    chJueves = Checkbutton(fr_sem, text="J", variable=opcion[3], command=cButtonSemanal, style='A.TCheckbutton')
    chViernes = Checkbutton(fr_sem, text="V", variable=opcion[4], command=cButtonSemanal, style='A.TCheckbutton')
    chSabado = Checkbutton(fr_sem, text="S", variable=opcion[5], command=cButtonSemanal, style='A.TCheckbutton')
    chDomingo = Checkbutton(fr_sem, text="D", variable=opcion[6], command=cButtonSemanal, style='A.TCheckbutton')
    chLunes.grid(row=0, column=0, padx=5)
    chMartes.grid(row=0, column=1, padx=5)
    chMiercoles.grid(row=0, column=2, padx=5)
    chJueves.grid(row=0, column=3, padx=5)
    chViernes.grid(row=0, column=4, padx=5)
    chSabado.grid(row=0, column=5, padx=5)
    chDomingo.grid(row=0, column=6, padx=5)
    fr_sem.grid(column=0, row=tabLigths.grid_size()[1], pady=5, columnspan=3, padx=30, sticky="ew")
    
    ##configuración de los programas
    listaOpciones=[]
    for i in range(144):
        for j in range(6):
            listaOpciones.append(f'{i%24}:{(j*10):02d}')
    
    listaOpciones = tuple(listaOpciones)
    
    Label(tabLigths, text='Tiempos de arranque:').grid(column=0, row=tabLigths.grid_size()[1], pady=5, padx=10, sticky='w')
    
    tiempos = {}
    for i in range(4):
        fr_hora = Frame(tabLigths)
        Label(fr_hora, text='Hora: ').grid(column=0, row=0, pady=5, padx=10)
        tiempos[i] = {"start": tk.StringVar(value='0:00'), "duration": tk.StringVar(value='0:00')}
        Spinbox(fr_hora, textvariable=tiempos[i]['start'], wrap=True, values=listaOpciones, style='A.TSpinbox', width=5).grid(column=1, row=0, pady=5, padx=10)

        Label(fr_hora, text='Duracion: ').grid(column=2, row=0, pady=5, padx=10)
        Spinbox(fr_hora, textvariable=tiempos[i]['duration'], wrap=True, values=listaOpciones, style='A.TSpinbox', width=5).grid(column=3, row=0, pady=5, padx=10)
        
        fr_hora.grid(column=0, row=tabLigths.grid_size()[1], pady=5, columnspan=3, padx=30, sticky="ew")
    
    ##Valvulas a las que aplicar el programa
    optVal = [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    Label(tabLigths, text='Focos a operar:').grid(column=0, row=tabLigths.grid_size()[1], pady=5, padx=10, sticky="w")
    Checkbutton(tabLigths, text="Foco 1", variable=optVal[0]).grid(column=0, row=tabLigths.grid_size()[1],padx=20, sticky="w")
    Checkbutton(tabLigths, text="Foco 2", variable=optVal[1]).grid(column=0, row=tabLigths.grid_size()[1],padx=20, sticky="w")
    Checkbutton(tabLigths, text="Foco 3", variable=optVal[2]).grid(column=0, row=tabLigths.grid_size()[1],padx=20, sticky="w")
    Checkbutton(tabLigths, text="Foco 4", variable=optVal[3]).grid(column=0, row=tabLigths.grid_size()[1],padx=20, sticky="w")
    
    ##Guardado de configuración
    Button(tabLigths, text='Guardar Programa', command=saveValveConf).grid(column=0, row=tabValves.grid_size()[1],padx=10, pady=15, sticky="w")
    
    ##-------------------------------------------------------------------------------------------------------------------------------------
    
    ### Ventanas ----------------------------------------------------------------------------------------------------
    
    ##Activación/desactivación del programa
    btnActivo_wd = Button(tabWindows, command=toggle, text='Inactivo', style='A.TButton')
    btnActivo_wd.grid(column=0, row=tabWindows.grid_size()[1], pady=5, padx=10, sticky='w')
    ##Etiqueta
    Label(tabWindows, text='Frecuencia del programa').grid(column=0, row=tabWindows.grid_size()[1], pady=10, sticky='w', padx=10)
    
    ##Selector de frecuencia
    varFrecuencia = tk.IntVar()
    fr_freq = Frame(tabWindows)
    radFreq1_wd = tk.Radiobutton(fr_freq, text='Único',indicatoron=0, variable=varFrecuencia, value =0, command=commandFreq)
    radFreq2_wd = tk.Radiobutton(fr_freq, text='Personalizado',indicatoron= 0,variable=varFrecuencia, value =1, command=commandFreq)
    fr_freq.grid(column=0, row=tabWindows.grid_size()[1], pady=5, columnspan=3, padx=10, sticky='w')
    radFreq1_wd.pack(side='left')
    radFreq2_wd.pack(side='right')


    ##Programacion semanal
    ###Primero habria que cargar la selección existente para este dia TODO
    fr_sem = Frame(tabWindows)
    opcion= [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    chLunes = Checkbutton(fr_sem, text="L", variable=opcion[0], command=cButtonSemanal, style='A.TCheckbutton')
    chMartes = Checkbutton(fr_sem, text="M", variable=opcion[1], command=cButtonSemanal, style='A.TCheckbutton')
    chMiercoles = Checkbutton(fr_sem, text="X", variable=opcion[2], command=cButtonSemanal, style='A.TCheckbutton')
    chJueves = Checkbutton(fr_sem, text="J", variable=opcion[3], command=cButtonSemanal, style='A.TCheckbutton')
    chViernes = Checkbutton(fr_sem, text="V", variable=opcion[4], command=cButtonSemanal, style='A.TCheckbutton')
    chSabado = Checkbutton(fr_sem, text="S", variable=opcion[5], command=cButtonSemanal, style='A.TCheckbutton')
    chDomingo = Checkbutton(fr_sem, text="D", variable=opcion[6], command=cButtonSemanal, style='A.TCheckbutton')
    chLunes.grid(row=0, column=0, padx=5)
    chMartes.grid(row=0, column=1, padx=5)
    chMiercoles.grid(row=0, column=2, padx=5)
    chJueves.grid(row=0, column=3, padx=5)
    chViernes.grid(row=0, column=4, padx=5)
    chSabado.grid(row=0, column=5, padx=5)
    chDomingo.grid(row=0, column=6, padx=5)
    fr_sem.grid(column=0, row=tabWindows.grid_size()[1], pady=5, columnspan=3, padx=30, sticky="ew")
    
    ##configuración de los programas
    listaOpciones=[]
    for i in range(144):
        for j in range(6):
            listaOpciones.append(f'{i%24}:{(j*10):02d}')
    
    listaOpciones = tuple(listaOpciones)
    
    Label(tabWindows, text='Tiempos de arranque:').grid(column=0, row=tabWindows.grid_size()[1], pady=5, padx=10, sticky='w')
    
    tiempos = {}
    for i in range(4):
        fr_hora = Frame(tabWindows)
        Label(fr_hora, text='Hora: ').grid(column=0, row=0, pady=5, padx=10)
        tiempos[i] = {"start": tk.StringVar(value='0:00'), "duration": tk.StringVar(value='0:00'),  "apertura": tk.StringVar(value='0:00')}
        Spinbox(fr_hora, textvariable=tiempos[i]['start'], wrap=True, values=listaOpciones, style='A.TSpinbox', width=5).grid(column=1, row=0, pady=5, padx=10)

        Label(fr_hora, text='Duracion: ').grid(column=2, row=0, pady=5, padx=10)
        Spinbox(fr_hora, textvariable=tiempos[i]['duration'], wrap=True, values=listaOpciones, style='A.TSpinbox', width=5).grid(column=3, row=0, pady=5, padx=10)
        
        Label(fr_hora, text='Apertura %: ').grid(column=4, row=0, pady=5, padx=10)
        Spinbox(fr_hora,from_=0, to=100, textvariable=tiempos[i]['apertura'], wrap=True, style='A.TSpinbox', width=5).grid(column=5, row=0, pady=5, padx=10)
        
        fr_hora.grid(column=0, row=tabWindows.grid_size()[1], pady=5, columnspan=3, padx=30, sticky="ew")
    
    ##Valvulas a las que aplicar el programa
    optVal = [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    Label(tabWindows, text='Ventanas a operar:').grid(column=0, row=tabWindows.grid_size()[1], pady=5, padx=10, sticky="w")
    Checkbutton(tabWindows, text="Ventana 1", variable=optVal[0]).grid(column=0, row=tabWindows.grid_size()[1],padx=20, sticky="w")
    Checkbutton(tabWindows, text="Ventana 2", variable=optVal[1]).grid(column=0, row=tabWindows.grid_size()[1],padx=20, sticky="w")

    
    ##Guardado de configuración
    Button(tabWindows, text='Guardar Programa', command=saveValveConf).grid(column=0, row=tabValves.grid_size()[1],padx=10, pady=15, sticky="w")
    
    ##-------------------------------------------------------------------------------------------------------------------------------------
    
    ### Persianas ----------------------------------------------------------------------------------------------------
    
    ##Activación/desactivación del programa
    btnActivo_blinds = Button(tabBlinds, command=toggle, text='Inactivo', style='A.TButton')
    btnActivo_blinds.grid(column=0, row=tabBlinds.grid_size()[1], pady=5, padx=10, sticky='w')
    ##Etiqueta
    Label(tabBlinds, text='Frecuencia del programa').grid(column=0, row=tabBlinds.grid_size()[1], pady=10, sticky='w', padx=10)
    
    ##Selector de frecuencia
    varFrecuencia = tk.IntVar()
    fr_freq = Frame(tabBlinds)
    radFreq1_blinds = tk.Radiobutton(fr_freq, text='Único',indicatoron=0, variable=varFrecuencia, value =0, command=commandFreq)
    radFreq2_blinds = tk.Radiobutton(fr_freq, text='Personalizado',indicatoron= 0,variable=varFrecuencia, value =1, command=commandFreq)
    fr_freq.grid(column=0, row=tabBlinds.grid_size()[1], pady=5, columnspan=3, padx=10, sticky='w')
    radFreq1_blinds.pack(side='left')
    radFreq2_blinds.pack(side='right')


    ##Programacion semanal
    ###Primero habria que cargar la selección existente para este dia TODO
    fr_sem = Frame(tabBlinds)
    opcion= [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    chLunes = Checkbutton(fr_sem, text="L", variable=opcion[0], command=cButtonSemanal, style='A.TCheckbutton')
    chMartes = Checkbutton(fr_sem, text="M", variable=opcion[1], command=cButtonSemanal, style='A.TCheckbutton')
    chMiercoles = Checkbutton(fr_sem, text="X", variable=opcion[2], command=cButtonSemanal, style='A.TCheckbutton')
    chJueves = Checkbutton(fr_sem, text="J", variable=opcion[3], command=cButtonSemanal, style='A.TCheckbutton')
    chViernes = Checkbutton(fr_sem, text="V", variable=opcion[4], command=cButtonSemanal, style='A.TCheckbutton')
    chSabado = Checkbutton(fr_sem, text="S", variable=opcion[5], command=cButtonSemanal, style='A.TCheckbutton')
    chDomingo = Checkbutton(fr_sem, text="D", variable=opcion[6], command=cButtonSemanal, style='A.TCheckbutton')
    chLunes.grid(row=0, column=0, padx=5)
    chMartes.grid(row=0, column=1, padx=5)
    chMiercoles.grid(row=0, column=2, padx=5)
    chJueves.grid(row=0, column=3, padx=5)
    chViernes.grid(row=0, column=4, padx=5)
    chSabado.grid(row=0, column=5, padx=5)
    chDomingo.grid(row=0, column=6, padx=5)
    fr_sem.grid(column=0, row=tabBlinds.grid_size()[1], pady=5, columnspan=3, padx=30, sticky="ew")
    
    ##configuración de los programas
    listaOpciones=[]
    for i in range(144):
        for j in range(6):
            listaOpciones.append(f'{i%24}:{(j*10):02d}')
    
    listaOpciones = tuple(listaOpciones)
    
    Label(tabBlinds, text='Tiempos de arranque:').grid(column=0, row=tabBlinds.grid_size()[1], pady=5, padx=10, sticky='w')
    
    tiempos = {}
    for i in range(4):
        fr_hora = Frame(tabBlinds)
        Label(fr_hora, text='Hora: ').grid(column=0, row=0, pady=5, padx=10)
        tiempos[i] = {"start": tk.StringVar(value='0:00'), "duration": tk.StringVar(value='0:00'),  "apertura": tk.IntVar(value=0)}
        Spinbox(fr_hora, textvariable=tiempos[i]['start'], wrap=True, values=listaOpciones, style='A.TSpinbox', width=5).grid(column=1, row=0, pady=5, padx=10)

        Label(fr_hora, text='Duracion: ').grid(column=2, row=0, pady=5, padx=10)
        Spinbox(fr_hora, textvariable=tiempos[i]['duration'], wrap=True, values=listaOpciones, style='A.TSpinbox', width=5).grid(column=3, row=0, pady=5, padx=10)
        
        Label(fr_hora, text='Apertura %: ').grid(column=4, row=0, pady=5, padx=10)
        Spinbox(fr_hora, wrap=True, from_=0, to=100, textvariable=tiempos[i]['apertura'], style='A.TSpinbox', width=5).grid(column=5, row=0, pady=5, padx=10)
        
        fr_hora.grid(column=0, row=tabBlinds.grid_size()[1], pady=5, columnspan=3, padx=30, sticky="ew")
    
    ##Valvulas a las que aplicar el programa
    optVal = [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    Label(tabBlinds, text='Ventanas a operar:').grid(column=0, row=tabBlinds.grid_size()[1], pady=5, padx=10, sticky="w")
    Checkbutton(tabBlinds, text="Ventana 1", variable=optVal[0]).grid(column=0, row=tabBlinds.grid_size()[1],padx=20, sticky="w")
    Checkbutton(tabBlinds, text="Ventana 2", variable=optVal[1]).grid(column=0, row=tabBlinds.grid_size()[1],padx=20, sticky="w")

    
    ##Guardado de configuración
    Button(tabBlinds, text='Guardar Programa', command=saveValveConf).grid(column=0, row=tabValves.grid_size()[1],padx=10, pady=15, sticky="w")
    
    ##-------------------------------------------------------------------------------------------------------------------------------------
    
    ##CALEFACCION -------------------------------------------------------------------------------------------------------------------------
    
    Label(tabHeating, text='Temeperatura objetivo:').grid(column=0, row=tabHeating.grid_size()[1], pady=5, padx=10, sticky="w")
    Entry(tabHeating).grid(column=0, row=tabHeating.grid_size()[1], pady=5, padx=10, sticky="w")
    
    
    ##Guardado de configuración
    Button(tabHeating, text='Guardar Programa', command=saveValveConf).grid(column=0, row=tabHeating.grid_size()[1],padx=10, pady=15, sticky="w")

    
    root.update_idletasks() #hacemos update del root para que este todo listo
    #distribución
    # labPrograma.place(x=20, y=20)
    # selPrograma.place(x=20, y=50)
    # btnActivo.place(x=20, y=80)
    # labFreq.place(x=20, y=110)
    # radFreq1.place(x=30, y=150)
    # radFreq2.place(x=71, y=150)
    # chLunes.place(x= 20, y=190)
    # chMartes.place(x= 50, y=190)
    # chMiercoles.place(x= 80, y=190)
    # chJueves.place(x= 110, y=190)
    # chViernes.place(x= 140, y=190)
    # chSabado.place(x= 170, y=190)
    # chDomingo.place(x= 200, y=190)
    
    # labStart.place(x= 20,y=230)
    # butAddHora.place(x= 150, y=235)
    # labHora.place(x= 20,y=270)
    # spinHora.place(x= 60,y=270)
    # labDura.place(x= 140,y=270)
    # spinDuracion.place(x= 200,y=270)
    
    # labVal.place(x= 20, y= 300)
    # chVal1.place(x= 40, y= 330)
    # chVal2.place(x= 40, y= 350)
    # chVal3.place(x= 40, y= 370)
    # chVal4.place(x= 40, y= 390)
    # butSave.place(x= 20, y= root.winfo_height()-80)
    
    root.mainloop()