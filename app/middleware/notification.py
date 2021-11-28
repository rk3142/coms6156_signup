import requests
import json
import boto3
import os
import re
from utils.rest_utils import RESTContext

notification_path = [{
        "endpoint": "/reg-service/v1/addresses",
        "method": ["POST", "GET"]
    }]

def format_message(text_message, event_type, resource_info):


    a_message = {
        "text": "*" + text_message + "*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*State Change Event:*"
                }
            }
        ]
    }

    for k,v in resource_info.items():
        a_message["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": k + ":\t\t" + str(v)
                }
            }
        )

    return a_message


class NotificationMiddlewareHandler:

    sns_client = None

    def __init__(self):
        pass

    
    def validate_notification_request(request):
        rest_request = RESTContext(request_context=request)
        if notification_path is not None or len(notification_path) != 0:
            for paths in notification_path:
                if re.search(paths.get('endpoint'), rest_request.path) and \
                    rest_request.method in paths.get('method'):
                    return True

        return False
    
    @classmethod
    def get_sns_client(cls):

        if NotificationMiddlewareHandler.sns_client is None:
            NotificationMiddlewareHandler.sns_client = sns = boto3.client("sns",
                   region_name="us-east-2",
           aws_access_key_id=os.environ.get('SNS_AWS_ACCESS_KEY_ID', None),
           aws_secret_access_key=os.environ.get('SNS_AWS_SECRET_ACCESS_KEY', None))
        return NotificationMiddlewareHandler.sns_client

    @classmethod
    def get_sns_topics(cls):
        s_client = NotificationMiddlewareHandler.get_sns_client()
        result = response = s_client.list_topics()
        topics = result["Topics"]
        return topics

    @classmethod
    def send_sns_message(cls, sns_topic, message, request):
        import json

        s_client = NotificationMiddlewareHandler.get_sns_client()
        response = s_client.publish(
            TargetArn=sns_topic,
            Message=json.dumps({'default': json.dumps(message)}),
            MessageStructure='json'
        )
        print("Publish response = ", json.dumps(response, indent=2))
        return
        

    '''
    @staticmethod
    def notify(request, response):

        subscriptions = context.get_context("SUBSCRIPTIONS")

        if request.path in subscriptions:

            notification = {}

            try:
                request_data = request.get_json()
            except Exception as e:
                request_data = None

            path = request.path

            if request.method == 'POST':
                notification["change"] = "CREATED"
                notification['new_state'] = request_data
                notification['params'] = path
            elif request.method == 'PUT':
                notification["change"] = "UPDATE"
                notification['new_state'] = request_data
                notification["params"] = path
            elif request.method == "DELETE":
                notification["change"] = "DELETED"
                notification["params"] = path
            else:
                notification = None

            s_url = context.get_context("SLACK_URL")

            if notification.get("change", None):
                request_data = json.dumps(notification)
                request_data = json.dumps(
                    {'text': request_data }).encode('utf-8')
                response = requests.post(
                    s_url, data=request_data,
                    headers={'Content-Type': 'application/json'}
                )
                print("Respose = ", response.status_code)


    @staticmethod
    def send_slack_message(message, event_type, resource_info):

        s_url = context.get_context("SLACK_URL")

        msg = format_message(message, event_type, resource_info)
        msg = json.dumps(msg).encode('utf-8')


        response = requests.post(
            s_url, data=msg,
            headers={'Content-Type': 'application/json'}
        )
        print("Respose = ", response.status_code)
    '''