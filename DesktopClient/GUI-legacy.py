import PySimpleGUI as sg
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import re
import paho.mqtt.client as mqtt
import json as json
from base64 import b64encode, b64decode
import threading
from threading import Timer
import codecs
from dateutil import parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import pytz

# Variables para identificar los canales de comunicación MQTT
# Cuenta de Lorenzo
application_id = 'tfg-icai'
tenant_id = 'tfg-icai'
device_id = 'arduino-tfg'
# cuenta de INEA
#application_id = 'riego-inea'
#tenant_id = 'inea-icai'
#device_id = 'eui-a8610a32371f8b01'


matplotlib.use('TkAgg')
sg.theme('LightBlue3')

opciones = ['Dias', 'Semanas', 'Meses']
lay1 = [
    [sg.T('Elija desde cuándo quiere representar los datos')],
    [sg.Slider((1, 10), orientation='h', key='slider'),
     sg.Combo(values=opciones, default_value=opciones[0], enable_events=True, readonly=True, k='-COMBO-'),
     sg.B('Mostrar', key='graph')],
    [sg.Canvas(key='Canvas')]
]

lay3 = [
    [sg.T('Valvula 0:')],
    [sg.T('Cada: '), sg.Input(expand_x=True, size=(2, 1), key='gap0'), sg.T('Horas, regar: '),
     sg.Input(expand_x=True, size=(2, 1), key='duracion0'), sg.T('minutos')],
    [sg.T('Valvula 1:')],
    [sg.T('Cada: '), sg.Input(expand_x=True, size=(2, 1), key='gap1'), sg.T('Horas, regar: '),
     sg.Input(expand_x=True, size=(2, 1), key='duracion1'), sg.T('minutos')],
    [sg.T('Valvula 2:')],
    [sg.T('Cada: '), sg.Input(expand_x=True, size=(2, 1), key='gap2'), sg.T('Horas, regar: '),
     sg.Input(expand_x=True, size=(2, 1), key='duracion2'), sg.T('minutos')],
    [sg.T('Valvula 3:')],
    [sg.T('Cada: '), sg.Input(expand_x=True, size=(2, 1), key='gap3'), sg.T('Horas, regar: '),
     sg.Input(expand_x=True, size=(2, 1), key='duracion3'), sg.T('minutos')],
    [sg.T('Todas las valvulas:')],
    [sg.B('Subir', key='SubirA')],
    [sg.T('Acciones inmediatas:', expand_x=True)],
    [sg.B('Abrir valvula 0', key='A0'), sg.B('Cerrar valvula 0', key='C0')],
    [sg.B('Abrir valvula 1', key='A1'), sg.B('Cerrar valvula 0', key='C1')],
    [sg.B('Abrir valvula 2', key='A2'), sg.B('Cerrar valvula 0', key='C2')],
    [sg.B('Abrir valvula 3', key='A3'), sg.B('Cerrar valvula 0', key='C3')],
    [sg.T(visible=False, key='warning')]
]
lay_grp = [[sg.Tab('Lectura de humedad', layout=lay1), sg.Tab('Subir esquema de riego', layout=lay3)]]
layout = [
    [sg.TabGroup(layout=lay_grp,
                 tab_location='topleft',
                 key='tabGroup',
                 expand_x=True,
                 expand_y=True,
                 visible=True)],
]


def find2nd(string, char):
    """Funcion que obtiene la posicion del segundo caracter en un string

    Args:
        string (string): cadena
        char (char): caracter a buscar

    Returns:
        int: posicion
    """
    start = string.find(char)
    index = string[start + 1:].find(char)
    return index + start + 1

def getDatos():
    f = open("datos.json")
    return json.load(f)

def getConfig():
    f = open("config.json")
    return json.load(f)

def guardarConfig(values):
    
    f = open("config.json", "r")
    conf = json.load(f)

    for num in ('0', '1', '2', '3'):
        for i,tipo in enumerate(('gap', 'duracion')):
            if values[tipo + num]=="":
                conf["".join(['V',num])][i] = '0'
            elif values[tipo + num]!="":
                conf["".join(['V',num])][i] = values[tipo + num]
                
    print(conf)                	 
    json_completo = json.dumps(conf)

    with open("config.json", "w") as outfile:
        outfile.write(json_completo)

    return

def cargarConfig(window):
    f = open("config.json", "r")
    conf = json.load(f)
    for num in ('0', '1', '2', '3'):
        for i,tipo in enumerate(('gap', 'duracion')):
            print(window[tipo + num])
            window[tipo + num].update(conf["V"+num][i])
    
    
    return

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # print(msg.topic)
    print(msg.payload.decode('utf-8'))
    recibido = json.loads(msg.payload.decode('utf-8'))
    # mensajes desde la placa
    # Cuenta Lorenzo
#    if msg.topic == 'v3/tfg-icai@tfg-icai/devices/arduino-tfg/up':
    # Cuenta INEA-ICAI
    if msg.topic == 'v3/' + application_id + '@' + tenant_id + '/devices/' + device_id + '/up':
        print(codecs.decode(str(b64decode(recibido['uplink_message']['frm_payload']).hex()), 'hex').decode(
            'utf-8'))
        if codecs.decode(str(b64decode(recibido['uplink_message']['frm_payload']).hex()), 'hex').decode(
                'utf-8') == 'ERROR':
            window['warning'].update(visible=True, value='Error en el envío, pruebe a enviarlo de nuevo')
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


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


# funcion que teniendo los parámetros coje los elementos de una fuente de datos
# el tiempo se puede coger del propio mensaje del ttn
def mostrarGrafico(values, figura, ax):
    """funcion que muestra los datos obtenidos

    Args:
        values (list): lista de valores de los eventos
        figura (figure): figura de matplotlib
        ax (axis): objeto de ejes de matplotlib
    """
    # int(values['slider'])
    data = getDatos()
    datos = {}
    print(data)
    # ordenamos los datos en caso de que no esten ordenados en el archivo
    ordered_data = dict(sorted(data.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M'), reverse=False))

    for i, j in ordered_data.items():
        datos[datetime.strptime(i, '%Y-%m-%d %H:%M')] = j
    del data
    data = {}
    if values['-COMBO-'] == 'Meses':
        for i, j in datos.items():
            if i > (datetime.now() - relativedelta(months=int(values['slider']))):
                data[i] = j
    elif values['-COMBO-'] == 'Semanas':
        for i, j in datos.items():
            if i > (datetime.now() - timedelta(weeks=int(values['slider']))):
                data[i] = j
    else:
        for i, j in datos.items():
            if i > (datetime.now() - timedelta(days=int(values['slider']))):
                data[i] = j
    del datos

    # al creacion del fig debe tener en cuenta los parametros
    ax.cla()
    ax.grid()

    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    ax.plot(list(data.keys()), list(data.values()))
    ax.legend( ['sensor 1', 'sensor 2', 'sensor 3', 'sensor 4'])
    xfmt = matplotlib.dates.DateFormatter('%d-%m-%y %H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    figura.draw()
    return


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
        conf = getConfig()
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


def main():
    # setup MQTT
    # Cuenta Lorenzo
    access = 'NNSXS.VCOASZCJR2TD4MZ4DYCTDDIJHJDI52LQYWNXWHA.76LAW2FWLS56JOYBJIQB6Z7GTDWZ2F4WKDMVESCENZXH6QGYVY3A'
    mqtt_address = 'eu2.cloud.thethings.industries'
    client = mqtt.Client()
    client.username_pw_set('tfg-icai@tfg-icai', password=access)

    # Cuenta INEA-ICAI
#    access = 'NNSXS.ZELTOL4A3L2C3DFWLKKWPU7I6WZJ2J32MLAIKXQ.DCVPWY7TMWDWMSOHFNJMVEJOHCB4JIWVRZU3QXLE4KLWRGN3RPGQ'
#    mqtt_address = 'eu1.cloud.thethings.industries'
#    client = mqtt.Client()
#    client.username_pw_set('riego-inea@inea-icai', password=access)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.connect(host=mqtt_address, port=1883, keepalive=60)
    hilo = threading.Thread(target=mqtt_client_listener, args=(client,))
    hilo.start()

    # setup GUI
    fig = Figure()
    fig.autofmt_xdate()
    ax = fig.add_subplot(111)
    ax.set_xlabel("Fecha")
    ax.set_ylabel("% Humedad")
    ax.grid()
    fig_agg = draw_figure(window['Canvas'].TKCanvas, fig)
    global values
    while True:
        event, values = window.read()
        global listaAcciones, queued, primEnvio
        if event == sg.WIN_CLOSED:
            client.disconnect()
            break
        if event == 'graph':
            mostrarGrafico(values, fig_agg, ax)
        if event in ('A0', 'C0', 'A1', 'C1', 'A2', 'C2', 'A3', 'C3', 'Subir0', 'Subir1', 'Subir2', 'Subir3'):
            listaAcciones.append(event)
            if not primEnvio:
                window['warning'].update(visible=True, value='Enviado')
                enviarPaquete(client)
                primEnvio = True
            else:
                window['warning'].update(visible=True, value='el paquete se enviará en los próximos 7 minutos')
                queued = True
        
        if event in ('SubirA'):
            if checkFormat(values):
                guardarConfig(values)
                listaAcciones.append('horario')
                if not primEnvio:
                    enviarPaquete(client)
                    window['warning'].update(visible=True, value='Enviado')
                    primEnvio = True
                else:
                    window['warning'].update(visible=True, value='el paquete se enviará en los próximos 7 minutos')
                    queued = True
            else:
                window['warning'].update(visible=True, value='Valores incorrectos en los campos(ambos de una misma válvula deben de estar rellenos y sólo de números)')

if __name__ == "__main__":
    window = sg.Window('Control de Riego', layout=layout, resizable=True, finalize=True)
    cargarConfig(window)
    primEnvio = False
    queued = False
    listaAcciones = []
    main()
