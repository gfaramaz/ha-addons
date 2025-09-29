#!/usr/bin/python3
# coding: utf-8

import json
import logging
import time
from logging.handlers import TimedRotatingFileHandler
import paho.mqtt.client as mqtt
import socketio

from _config_ import _MCZ_App_URL
from _config_ import _MCZ_device_MAC
from _config_ import _MCZ_device_serial
from _config_ import _MQTT_TOPIC_PUB
from _config_ import _MQTT_TOPIC_SUB
from _config_ import _MQTT_authentication
# MQTT
from _config_ import _MQTT_ip
from _config_ import _MQTT_pass
from _config_ import _MQTT_port
from _config_ import _MQTT_user

try:
    import thread
except ImportError:
    import _thread as thread

# Initialize logger first
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s :%(name)s :: %(levelname)s :: %(message)s')
file_handler = TimedRotatingFileHandler('maestro.log', when='D', interval=1, backupCount=5)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Discovery imports after logger is set up
try:
    from _config_ import _MQTT_DISCOVERY_ENABLED, _MQTT_DISCOVERY_PREFIX, _DEVICE_NAME, _DEVICE_ID
    discovery_available = True
except ImportError:
    # Backward compatibility - discovery config not available
    _MQTT_DISCOVERY_ENABLED = False
    _MQTT_DISCOVERY_PREFIX = 'homeassistant'
    _DEVICE_NAME = 'MCZ Maestro Stove'
    _DEVICE_ID = 'mcz_maestro_stove'
    discovery_available = True

if discovery_available:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
        from discovery import DiscoveryManager
    except ImportError:
        logger.warning("Discovery module not available")
        discovery_available = False

sio = socketio.Client(logger=True, engineio_logger=True)


class PileFifo(object):
    def __init__(self, maxpile=None):
        self.pile = []
        self.maxpile = maxpile

    def empile(self, element, idx=0):
        if (self.maxpile != None) and (len(self.pile) == self.maxpile):
            raise ValueError("erreur: tentative d'empiler dans une pile pleine")
        self.pile.insert(idx, element)

    def depile(self, idx=-1):
        if len(self.pile) == 0:
            raise ValueError("erreur: tentative de depiler une pile vide")
        if idx < -len(self.pile) or idx >= len(self.pile):
            raise ValueError("erreur: element de pile à depiler n'existe pas")
        return self.pile.pop(idx)

    def element(self, idx=-1):
        if idx < -len(self.pile) or idx >= len(self.pile):
            raise ValueError("erreur: element de pile à lire n'existe pas")
        return self.pile[idx]

    def copiepile(self, imin=0, imax=None):
        if imax == None:
            imax = len(self.pile)
        if imin < 0 or imax > len(self.pile) or imin >= imax:
            raise ValueError("erreur: mauvais indice(s) pour l'extraction par copiepile")
        return list(self.pile[imin:imax])

    def pilevide(self):
        return len(self.pile) == 0

    def pilepleine(self):
        return self.maxpile != None and len(self.pile) == self.maxpile

    def taille(self):
        return len(self.pile)


def on_connect_mqtt(client, userdata, flags, rc):
    logger.info("Connected to MQTT broker with code: " + str(rc))
    if rc != 0:
        logger.error(f"MQTT connection failed with code {rc}. Discovery will not work.")
        return
    
    # Resubscribe to the MQTT topic on reconnection
    client.subscribe(_MQTT_TOPIC_SUB, qos=1)
    
    # Initialize and publish discovery configs only if connection successful
    global discovery_manager
    if discovery_available and discovery_manager:
        discovery_manager.publish_discovery_configs()

def on_disconnect_mqtt(client, userdata, rc):
    if rc != 0:
        logger.warning("Unexpected MQTT disconnection. Will auto-reconnect")

def on_message_mqtt(client, userdata, message):
    logger.info('Message MQTT reçu : ' + str(message.payload.decode()))
    cmd = message.payload.decode().split(",")
    if cmd[0] == "42":
        cmd[1] = int(float(cmd[1]) * 2)
    Message_MQTT.empile("C|WriteParametri|" + cmd[0] + "|" + str(cmd[1]))
    logger.info('Contenu Pile Message_MQTT : ' + str(Message_MQTT.copiepile()))
    send()


def secTOdhms(nb_sec):
    qm, s = divmod(nb_sec, 60)
    qh, m = divmod(qm, 60)
    d, h = divmod(qh, 24)
    return "%d:%d:%d:%d" % (d, h, m, s)


def publish_individual_discovery_topics(mqtt_data):
    """Map French cloud data to English discovery topic names and publish individually"""
    if not discovery_available or not discovery_manager or not discovery_manager.discovery_enabled:
        return
    
    # Mapping from French cloud names to English discovery entity keys
    french_to_english_mapping = {
        "Temperature ambiante": "Ambient_Temperature",
        "Temperature des fumees": "Fume_Temperature", 
        "Puffer Temperature": "Puffer_Temperature",
        "Temperature chaudiere": "Boiler_Temperature",
        "Temperature NTC3": "NTC3_Temperature",
        "TEMP - Carte mere": "Temperature_Motherboard",
        "Temperature retour": "Return_Temperature",
        "Etat du poele": "Stove_State", 
        "Etat du ventilateur ambiance": "Fan_State",
        "Etat du ventilateur canalise 1": "DuctedFan1",
        "Etat du ventilateur canalise 2": "DuctedFan2",
        "RPM - Ventilateur fummees": "RPM_Fam_Fume",
        "RPM - Vis sans fin - SET": "RPM_WormWheel_Set",
        "RPM - Vis sans fin - LIVE": "RPM_WormWheel_Live",
        "Etat de la bougie": "Candle_Condition",
        "Brazero": "Brazier",
        "3WayValve": "3WayValve",  # This might not exist in cloud data
        "Pump_PWM": "Pump_PWM",    # This might not exist in cloud data
        "Heures de fonctionnement total (s)": "Total_Operating_Hours",
        "Heures avant entretien": "Hours_To_Service",
        "Nombre d'allumages": "Number_Of_Ignitions",
        "Sonde Pellets": "Pellet_Sensor",
        # Power/mode states - need to convert to 1/0
        "Etat du mode Active": "Power",  # On/Off -> 1/0
        "Mode ECO": "Eco_Mode",          # On/Off -> 1/0 
        "Silence": "Silent_Mode",        # On/Off -> 1/0
        "Mode Chronotermostato": "Chronostat", # On/Off -> 1/0
        "Etat effets sonores": "Sound_Effects", # On/Off -> 1/0
        "Antigel": "AntiFreeze",         # On/Off -> 1/0
        "TEMP - Consigne": "Temperature_Setpoint",
        "TEMP - Boiler": "Boiler_Setpoint",
    }
    
    base_topic = _MQTT_TOPIC_PUB.rstrip('/')
    
    for french_name, english_key in french_to_english_mapping.items():
        if french_name in mqtt_data:
            value = mqtt_data[french_name]
            
            # Convert boolean-like values to 1/0
            if english_key in ["Power", "Eco_Mode", "Silent_Mode", "Chronostat", "Sound_Effects", "AntiFreeze"]:
                if isinstance(value, str):
                    value = 1 if value.lower() in ['on', 'oui', 'yes', 'true'] else 0
            
            # Handle special formatting
            elif english_key == "Stove_State" and isinstance(value, str):
                # Keep as string but could map to numbers later
                pass
            
            # Publish to individual topic
            topic = f"{base_topic}/{english_key}"
            try:
                client.publish(topic, str(value), 1)
                logger.debug(f"Published {english_key}: {value} to {topic}")
            except Exception as e:
                logger.error(f"Failed to publish {english_key}: {e}")
    
    # Handle special case for Power_Level from "Puissance Active"
    if "Puissance Active" in mqtt_data:
        value = mqtt_data["Puissance Active"]
        if isinstance(value, str) and "Puissance" in value:
            import re
            match = re.search(r'Puissance (\d+)', value)
            if match:
                power_level = int(match.group(1))
                # Publish to both sensor and control topics
                try:
                    client.publish(f"{base_topic}/Power_Level", str(power_level), 1)
                    client.publish(f"{base_topic}/Power_Level_Control", str(power_level), 1)
                    logger.debug(f"Published Power_Level: {power_level}")
                except Exception as e:
                    logger.error(f"Failed to publish Power_Level: {e}")


@sio.event
def connect():
    logger.info("Connected")
    logger.info("SID is : {}".format(sio.sid))
    
    # Publish availability online for discovery
    global discovery_manager
    if discovery_available and discovery_manager:
        discovery_manager.publish_availability_online()
    
    sio.emit(
        "join",
        {
            "serialNumber": _MCZ_device_serial,
            "macAddress": _MCZ_device_MAC,
            "type": "Android-App",
        },
    )
    sio.emit(
        "chiedo",
        {
            "serialNumber": _MCZ_device_serial,
            "macAddress": _MCZ_device_MAC,
            "tipoChiamata": 0,
            "richiesta": "RecuperoParametri",
        },
    )
    sio.emit(
        "chiedo",
        {
            "serialNumber": _MCZ_device_serial,
            "macAddress": _MCZ_device_MAC,
            "tipoChiamata": 1,
            "richiesta": "C|RecuperoInfo",
        },
    )


@sio.event
def disconnect():
    logger.error("Disconnected")
    
    # Publish availability offline for discovery
    global discovery_manager
    if discovery_available and discovery_manager:
        discovery_manager.publish_availability_offline()



@sio.event
def rispondo(response):
    logger.info("Received 'rispondo' message")
    datas = response["stringaRicevuta"].split("|")
    from _data_ import RecuperoInfo
    for i in range(0, len(datas)):
        for j in range(0, len(RecuperoInfo)):
            if i == RecuperoInfo[j][0]:
                if len(RecuperoInfo[j]) > 2:
                    for k in range(0, len(RecuperoInfo[j][2])):
                        if int(datas[i], 16) == RecuperoInfo[j][2][k][0]:
                            MQTT_MAESTRO[RecuperoInfo[j][1]] = RecuperoInfo[j][2][k][1]
                            break
                        else:
                            MQTT_MAESTRO[RecuperoInfo[j][1]] = ('Code inconnu :', str(int(datas[i], 16)))
                else:
                    if i == 6 or i == 26 or i == 28:
                        MQTT_MAESTRO[RecuperoInfo[j][1]] = float(int(datas[i], 16)) / 2

                    elif i >= 37 and i <= 42:
                        MQTT_MAESTRO[RecuperoInfo[j][1]] = secTOdhms(int(datas[i], 16))
                    else:
                        MQTT_MAESTRO[RecuperoInfo[j][1]] = int(datas[i], 16)
    logger.info('Publication sur le topic MQTT ' + str(_MQTT_TOPIC_PUB) + ' le message suivant : ' + str(
        json.dumps(MQTT_MAESTRO)))
    client.publish(_MQTT_TOPIC_PUB, json.dumps(MQTT_MAESTRO), 1)
    
    # Also publish individual topics for discovery entities  
    publish_individual_discovery_topics(MQTT_MAESTRO)
    
    # Ensure availability is online when publishing data
    if discovery_available and discovery_manager:
        discovery_manager.publish_availability_online()


def receive(*args):
    while True:
        time.sleep(30)
        logger.info("Websocket still connected ? " + str(sio.connected))
        if sio.connected:
            logger.info("Envoi de la commande pour rafraichir les donnees")
            sio.emit(
                "chiedo",
                {
                 "serialNumber": _MCZ_device_serial,
                 "macAddress": _MCZ_device_MAC,
                 "tipoChiamata": 1,
                 "richiesta": "C|RecuperoInfo",
                },
            )
            time.sleep(15)
        else:
            logger.warning("Websocket disconnected ! Waiting 30seconds")
            time.sleep(30)


def send():
    def run(*args):
        time.sleep(_INTERVALLE)
        logger.info("Websocket still connected ? " + str(sio.connected))
        if sio.connected:
            if Message_MQTT.pilevide():
                Message_MQTT.empile("C|RecuperoInfo")
            cmd = Message_MQTT.depile()
            logger.info("Envoi de la commande : " + str(cmd))
            sio.emit(
              "chiedo",
               {
                   "serialNumber": _MCZ_device_serial,
                   "macAddress": _MCZ_device_MAC,
                   "tipoChiamata": 1,
                   "richiesta": cmd,
               },
            )
        else:
            logger.warning("Websocket disconnected ! waiting 30 seconds")
            time.sleep(30)

    thread.start_new_thread(run, ())


Message_MQTT = PileFifo()
Message_WS = PileFifo()

_INTERVALLE = 1
_TEMPS_SESSION = 60

MQTT_MAESTRO = {}
discovery_manager = None

logger.info('Lancement du deamon')
logger.info('Anthony L. 2019')
logger.info("Pipolaq's version")
logger.info('Niveau de LOG : DEBUG')

sio.connect(_MCZ_App_URL)

logger.info('Connection en cours au broker MQTT (IP:' + _MQTT_ip + ' PORT:' + str(_MQTT_port) + ')')
logger.info(f'MQTT Authentication: {_MQTT_authentication}, User: "{_MQTT_user}", Pass: {"[HIDDEN]" if _MQTT_pass else "[EMPTY]"}')
client = mqtt.Client()
if _MQTT_authentication:
    logger.info('Setting MQTT credentials...')
    client.username_pw_set(username=_MQTT_user, password=_MQTT_pass)
else:
    logger.info('MQTT authentication disabled, connecting without credentials')
client.on_connect = on_connect_mqtt
client.on_message = on_message_mqtt
client.on_disconnect = on_disconnect_mqtt
client.connect(_MQTT_ip, _MQTT_port)
client.loop_start()

# Initialize discovery manager
if discovery_available:
    discovery_config = {
        '_MQTT_DISCOVERY_ENABLED': _MQTT_DISCOVERY_ENABLED,
        '_MQTT_DISCOVERY_PREFIX': _MQTT_DISCOVERY_PREFIX,
        '_DEVICE_NAME': _DEVICE_NAME,
        '_DEVICE_ID': _DEVICE_ID,
        '_MQTT_TOPIC_PUB': _MQTT_TOPIC_PUB,
        '_MQTT_TOPIC_SUB': _MQTT_TOPIC_SUB,
        '_VERSION': '1.5'
    }
    discovery_manager = DiscoveryManager(client, discovery_config)

thread.start_new_thread(receive, ())
