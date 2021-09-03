#!/usr/bin/env python3

import logging
import os
import sys

from time import sleep

import boto3
import botocore

from ibmfl.aggregator.aggregator import Aggregator
from ibmfl.aggregator.states import States
from ibmfl.util.config import get_config_from_file

fl_path = os.path.abspath('.')
if fl_path not in sys.path:
    sys.path.append(fl_path)

logger = logging.getLogger(__name__)

s3 = boto3.client("s3")
bucket =  os.environ['BUCKET']
config_file = os.environ['AGG_CONFIG_FILE_KEY']
working_dir = "./workdir"
local_config_file = os.path.join(working_dir, config_file)

if __name__ == '__main__':
    """
    Main function can be used to create an application out \
    of our Aggregator class which could be interactive
    """
    s3.download_file(bucket, config_file, local_config_file)
    if not os.path.isfile(config_file):
        logger.debug("config file '{}' does not exist".format(local_config_file))

   
    commands = ['START', 'TRAIN', 'SYNC', 'SAVE', 'EVAL', 'STOP']

    config_dict = get_config_from_file(local_config_file)
    n_parties = config_dict['hyperparams']['global']['num_parties']
    logger.info("Going to wait for {} parties to register.".format(n_parties))
    agg = Aggregator(config_file=local_config_file)
    for command in commands:
        if command.strip().lower() == ('START').lower():
            agg.proto_handler.state = States.CLI_WAIT
            logger.info("State: " + str(agg.proto_handler.state))
            # Start server
            agg.start()
            while agg.proto_handler.get_n_parties() < n_parties:
                sleep(1)
            logger.info("All parties registered!")
            sleep(10)
        elif command.strip().lower() == ('STOP').lower():
            logger.info("State: " + str(agg.proto_handler.state))
            agg.stop()
            break
        elif command.strip().lower() == ('TRAIN').lower():
            logger.info("State: " + str(agg.proto_handler.state))
            agg.start_training()
        elif command.strip().lower() == ('SAVE').lower():
            logger.info("State: " + str(agg.proto_handler.state))
            agg.save_model()
        elif command.strip().lower() == ('EVAL').lower():
            logger.info("State: " + str(agg.proto_handler.state))
            agg.eval_model()
        elif command.strip().lower() == ('SYNC').lower():
            logger.info("State: " + str(agg.proto_handler.state))
            agg.model_synch()