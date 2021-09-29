import argparse
import time
import requests
import logging
import random
import json
from paho.mqtt import client as mqtt_client


logging.basicConfig(level=logging.DEBUG, format="[%(module)s] %(message)s")
log = logging.getLogger(__name__)


def get_response(url):
    headers = {'Content-Type': 'application/json'}
    session = requests.Session()

    response = session.request(
        method='GET',
        url=url,
        headers=headers,
        timeout=8
    )

    log.debug(f'Response status: {response}')

    return response.json()  # dict()


def fresh_list_full():
    # подробный список актуальных датчиков
    url = f'http://{_url}/json.htm?type=devices'
    fresh_info = get_response(url)

    list_accs = []
    try:
        for acc in fresh_info['result']:
            list_accs.append(acc)
    except Exception:
        pass

    return list_accs


def _value(_data, _type):
    if _type == 'Temp':
        value = float(_data.split(' ')[0])
    elif _type == 'Humidity':
        value = float(_data.split(' ')[1])
    elif _type == 'Light/Switch':
        if _data == 'Off':
            value = 'false'
        else:
            value = 'true'
    else:
        value = None

    return value


def form_dom_humidity(acc_info, idx, get_topic):
    return {
        "topic": f"humidity/idx{idx}",
        "name": acc_info["Name"],
        "manufacturer": "DIY",
        "model": "humiditysensor",
        "serialNumber": f'{acc_info["ID"]}_{idx}',
        "type": "humiditysensor",
        "feature": {
            "currentrelativehumidity": {
                "getTopic": get_topic,
                "setTopic": f"humidity/idx{idx}/currentrelativehumidity/set"
            }
        }
    }


def form_dom_temperature(acc_info, idx, get_topic):
    return {
        "topic": f"temperature/idx{idx}",
        "name": acc_info["Name"],
        "manufacturer": "DIY",
        "model": "temperaturesensor",
        "serialNumber": f'{acc_info["ID"]}_{idx}',
        "type": "temperaturesensor",
        "feature": {
            "currenttemperature": {
                "getTopic": get_topic,
                "setTopic": f"temperature/idx{idx}/currenttemperature/set"
            }
        }
    }


def form_dom_motion(acc_info, idx, get_topic):
    return {
        "topic": f"motion/idx{idx}",
        "name": acc_info["Name"],
        "manufacturer": "DIY",
        "model": "motionsensor",
        "serialNumber": f'{acc_info["ID"]}_{idx}',
        "type": "motionsensor",
        "feature": {
            "motiondetected": {
                "getTopic": get_topic,
                "setTopic": f"motion/idx{idx}/motiondetected/set"
            }
        }
    }


def convert_dom(dev_data):
    _type = dev_data['Type']
    idx = dev_data['idx']

    if _type == 'Humidity':
        get_topic = f'humidity/idx{idx}/currentrelativehumidity/get'
        _form = form_dom_humidity(dev_data, idx, get_topic)
    elif _type == 'Temp':
        get_topic = f'temperature/idx{idx}/currenttemperature/get'
        _form = form_dom_temperature(dev_data, idx, get_topic)
    elif _type == 'Light/Switch':
        get_topic = f'motion/idx{idx}/motiondetected/get'
        _form = form_dom_motion(dev_data, idx, get_topic)
    else:
        return None, None, None, None

    return _form, _type, get_topic, idx


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):

    while True:
        time.sleep(3)

        # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

        list_accs = fresh_list_full()
        if list_accs:

            for acc in list_accs:
                msg, _type, get_topic, idx = convert_dom(acc)
                announce_topic = f'announce/idx{idx}/'

                if _type:
                    # отправка анонса
                    result = client.publish(announce_topic, str(msg).replace("'", '"'), retain=True)
                    status = result[0]

                    if status == 0:
                        log.info(f"Send `{msg}` to topic `{announce_topic}`")

                        # отправка значения
                        msg = _value(acc['Data'], _type)
                        result = client.publish(
                            get_topic, str(msg).replace("'", '"'), retain=True)
                        status = result[0]

                        if status == 0:
                            log.info(f"Send `{msg}` to topic `{get_topic}`")
                        else:
                            log.info(
                                f"Failed to send message to topic {get_topic}")

                    else:
                        log.info(f"Failed to send message to topic {announce_topic}")

        else:
            log.info(f"No active devices")

        # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        str_msg = msg.payload.decode()
        dict_msg = json.loads(str_msg)

        try:
            type_access = dict_msg['dtype']
            _idx = dict_msg['idx']

            try:
                value = float(dict_msg['nvalue'])
            except Exception:
                value = dict_msg['nvalue']

        except Exception as exp:
            log.error(exp)
            type_access = None

        if type_access:
            if type_access == 'Temp':
                get_topic = f'temperature/idx{_idx}/currenttemperature/get'
            elif type_access == 'Humidity':
                get_topic = f'humidity/idx{_idx}/currentrelativehumidity/get'
            elif type_access == 'Light/Switch':
                get_topic = f'motion/idx{_idx}/motiondetected/get'
            else:
                get_topic = None

            if get_topic:
                result = client.publish(get_topic, str(value).replace("'", '"'), retain=True)
                status = result[0]

                if status == 0:
                    log.info(f"Send `{value}` to topic `{get_topic}`")
                else:
                    log.info(f"Failed to send message to topic {get_topic}")

        else:
            pass

    client.subscribe(topic)
    client.on_message = on_message


def pub():
    client = connect_mqtt()
    client.loop_start()
    subscribe(client)
    publish(client)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", type=str, help="mqtt username")
    parser.add_argument("-p", "--password", type=str, help="mqtt password")
    parser.add_argument("-b", "--broker", type=str, help="ip mqtt broker")  # "192.168.0.74"
    parser.add_argument("-s", "--port", type=str, help="port mqtt broker")  # "1883"
    parser.add_argument("-t", "--topic", type=str, help="mqtt topic domoticz")  # "domoticz/#"
    parser.add_argument("-h", "--host", type=str, help="host domoticz [host:port]")  # "Host:Port"
    args = parser.parse_args()

    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    username = args.username
    password = args.password
    broker = args.broker
    port = int(args.port)
    topic = args.topic
    _url = args.host

    pub()
