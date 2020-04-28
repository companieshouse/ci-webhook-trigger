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

def extract_payload(event):
    try:
        base64_decoded = base64.b64decode(event['body'])
        form_data = urllib.parse.parse_qs(base64_decoded)
        payload_json = form_data.get(bytes('payload', 'utf-8'))
        payload = json.loads(payload_json[0])
        return payload
    except Exception:
        logging.error('Payload parsing failed')
        sys.exit(1);

def handler(event, context):
    verify_environment(VARIABLES)

    try:
        event_type = event['multiValueHeaders']['x-github-event'][0]
        github_delivery = event['multiValueHeaders']['x-github-delivery'][0]
        payload = extract_payload(event)
        sender = payload['sender']['login']
        repository = payload['repository']['name']
        logging.info(f"Webhook received - id:[{github_delivery}], repository:[{repository}], type:[{event_type}], user:[{sender}]")
    except Exception:
        logging.error('Request parsing failed')
        sys.exit(1);

    if event_type in ["pull_request","push"]:
        path = event['path']
        webhook_token = event['multiValueQueryStringParameters']['webhook_token'][0]
        trigger_resource_check(path, webhook_token)
    else:
        logging.info(f"Ignoring [{event_type}] event")

    return {
        "statusCode": 200,
        "statusDescription": "200 OK",
        "isBase64Encoded": False
    }

def trigger_resource_check(path, webhook_token):
    concourse_url = os.getenv("CONCOURSE_URL")
    url_args = {"webhook_token": webhook_token}
    check_url = f"{concourse_url}{path}?{urllib.parse.urlencode(url_args)}"

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
