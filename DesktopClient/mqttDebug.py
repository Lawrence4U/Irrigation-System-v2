import paho.mqtt.client as mqtt
import base64
import codecs
import json

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic, msg.payload)
    try:
        recibido = json.loads(msg.payload.decode('utf-8'))
        print(codecs.decode(str(base64.b64decode(recibido['data']).hex()), 'hex').decode('utf-8'))
    except:
        print("Message error")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
# client.enable_logger(logger=mqtt.MQTT_LOG_DEBUG)

client.connect("10.130.1.10", port=1883, keepalive=60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()