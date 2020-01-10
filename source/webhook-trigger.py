# -*- coding: utf-8 -*-

import base64
import json
import logging
import os
import re
import requests
import sys
import urllib

VARIABLES = {
  "CONCOURSE_URL": "The URL through which we'll force resource checks"
}

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

def handler(event, context):
    verify_environment(VARIABLES)

    try:
        event_type = event['multiValueHeaders']['x-github-event'][0]
        github_delivery = event['multiValueHeaders']['x-github-delivery'][0]
        logging.info(f"Webhook received - id:[{github_delivery}]")
    except Exception:
        logging.error('Request parsing failed')
        sys.exit(1);

    if (event_type == 'push'):
        handle_push(event)
    else:
        logging.info(f"Ignoring event: [{event_type}]")

    return {
        "statusCode": 200,
        "statusDescription": "200 OK",
        "isBase64Encoded": False
    }

def handle_push(event):
    try:
        path = event['path']
        webhook_token = event['multiValueQueryStringParameters']['webhook_token'][0]
        base64_decoded = base64.b64decode(event['body'])
        form_data = urllib.parse.parse_qs(base64_decoded)
        payload_json = form_data.get(bytes('payload', 'utf-8'))
        payload = json.loads(payload_json[0])
        sender = payload['pusher']['name']
        repository = payload['repository']['name']
    except Exception:
        logging.error('Request parsing failed')
        sys.exit(1);

    logging.info(f"Processing push event - sender:[{sender}], repository:[{repository}]")
    CONCOURSE_URL = os.getenv("CONCOURSE_URL")

    url_args = {"webhook_token": webhook_token}
    check_url = f"{CONCOURSE_URL}{path}?{urllib.parse.urlencode(url_args)}"

    logging.info(f"Triggering resource check - [{check_url}]")

    trigger_response = requests.post(check_url)
    if trigger_response.status_code != 201:
        logging.error(f"Error: {trigger_response.content}")
        raise Exception(f"{trigger_response.content}")

def verify_environment(variables):
    for variable in variables:
        value = os.getenv(variable)
        if (value is None):
            logging.error(f"Missing variable [{variable}] - {variables[variable]}")
            sys.exit(1);
        else:
            logging.info(f"{variable}: [{value}]")
