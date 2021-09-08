#!/usr/bin/env python3

import logging
import os
import sys
import yaml

import boto3
import botocore

import paho.mqtt.client as mqtt

from time import sleep

from ibmfl.party.party import Party
from ibmfl.party.status_type import StatusType
from ibmfl.util.config import get_config_from_file

fl_path = os.path.abspath('.')
if fl_path not in sys.path:
    sys.path.append(fl_path)

logger = logging.getLogger(__name__)

s3 = boto3.client("s3")
bucket =  os.environ['BUCKET']
config_file = os.environ['PARTY_CONFIG_FILE_KEY']
working_dir = "./workdir"
local_config_file = os.path.join(working_dir, config_file)
model_file = os.environ['MODEL_FILE_KEY']
local_model_file = os.path.join(working_dir, model_file)
mqtt_notification_topic = ""
data_path = ""
data_type = ""

def run_party():
    s3.download_file(bucket, config_file, local_config_file)
    if not os.path.isfile(config_file):
        logger.debug("config file '{}' does not exist".format(local_config_file))
    s3.download_file(bucket, model_file, local_model_file)
    if not os.path.isfile(model_file):
        logger.debug("model file '{}' does not exist".format(local_model_file))

    f = open(local_config_file)
    config_dict = yaml.load(f, Loader=yaml.FullLoader)
    f.close()
    config_dict['model']['spec']['model_definition'] = local_model_file
    # if data_path is set in MQTT, use it here 
    if data_path != "" and data_type != "":
        config_dict["data"]["info"][data_type] = data_path

    f = open(local_config_file, "w")
    yaml.dump(config_dict, f)
    f.close()

    p = Party(config_file=local_config_file)
    commands = ['START', 'REGISTER', 'SAVE', 'EVAL']
    # Loop over commands passed by runner
    for command in commands:
        if command.lower() == ('START').lower():
            # Start server
            p.start()
        if command.lower() == ('STOP').lower():
            p.connection.stop()
            break
        if command.lower() == ('REGISTER').lower():
            p.register_party()
        if command.lower() == ('SAVE').lower():
            p.save_model()
        if command.lower() == ('EVAL').lower():
            p.evaluate_model()

    # Stop only when aggregator tells us;
    # in the future, dynamically deciding commands can be supported.
    while p.proto_handler.status != StatusType.STOPPING:
        sleep(1)

    p.stop()

def on_connect(client, userdata, flags, rc):
    print("Connection code: {0}".format(str(rc)))
    client.subscribe(mqtt_notification_topic)


def on_message(client, userdata, msg):
    print("Message received from: " + msg.topic + " payload:" + str(msg.payload))
    msg_decode =str(msg.payload.decode("utf-8","ignore"))
    msg_json = json.loads(msg_decode)
    data_path = msg_json["path"]
    data_type = msg_json["type"]
    run_party()

if __name__ == '__main__':
    """
    Main function can be used to create an application out \
    of our Aggregator class which could be interactive
    """
    try:
        mqtt_notification_topic = os.environ['MQTT_TOPIC']
        client = mqtt.Client("fl_party_client")  
        client.on_connect = on_connect  
        client.on_message = on_message  
        client.connect('127.0.0.1', 1883)
        client.loop_forever()

    except KeyError: 
        run_party()