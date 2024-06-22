import json
import paho.mqtt.client as mqtt
import pytz
import codecs
from base64 import b64encode, b64decode

application_id = 'tfg-icai'
tenant_id = 'tfg-icai'
device_id = 'arduino-tfg'

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