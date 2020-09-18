# -*- coding: utf-8 -*-

import base64
import json
import logging
import os
import re
import requests
import sys
import urllib
import jinja2

VARIABLES = {
  "CONCOURSE_URL": "The URL through which we'll force resource checks",
  "SLACK_WEBHOOK_URL": "The URL of the Slack webhook we will use to publish messages"
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
        sendSlackErrorMessage(event, None)
        sys.exit(1);

    if event_type in ["pull_request","push"]:
        path = event['path']
        webhook_token = event['multiValueQueryStringParameters']['webhook_token'][0]
        trigger_resource_check(path, webhook_token, event)
    else:
        logging.info(f"Ignoring [{event_type}] event")

    return {
        "statusCode": 200,
        "statusDescription": "200 OK",
        "isBase64Encoded": False
    }

def trigger_resource_check(path, webhook_token, event):
    concourse_url = os.getenv("CONCOURSE_URL")
    url_args = {"webhook_token": webhook_token}
    check_url = f"{concourse_url}{path}?{urllib.parse.urlencode(url_args)}"

    logging.info(f"Triggering resource check - [{check_url}]")
    trigger_response = requests.post(check_url)
    if trigger_response.status_code != 201:
        logging.error(f"Error: {trigger_response.content}")
        sendSlackErrorMessage(event, trigger_response.status_code)
        raise Exception(f"{trigger_response.content}")

def verify_environment(variables):
    for variable in variables:
        value = os.getenv(variable)
        if (value is None):
            logging.error(f"Missing variable [{variable}] - {variables[variable]}")
            sys.exit(1);

def sendSlackErrorMessage(event, status_code):
    payload = extract_payload(event)
    if status_code != None:
        # Append status_code to payload for added context
        # in the output Slack message
        payload['status_code'] = status_code

    slackWebhookUrl = os.getenv("SLACK_WEBHOOK_URL")

    loader = jinja2.FileSystemLoader("templates")
    env = jinja2.Environment(loader=loader)
    env.filters['jsonify'] = json.dumps

    template = env.get_template('failure-message.json.j2')
    message = template.render(payload)

    requests.post(slackWebhookUrl, headers = {'content-type': 'application/json'}, json = json.loads(message))
