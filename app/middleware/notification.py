import requests
import json
import boto3
import os


notification_path = [{
        "endpoint": "/reg-service/v1/addresses",
        "allowed": "all",
        "method": ["GET", "POST"]
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

    @classmethod
    def get_sns_client(cls):

        if NotificationMiddlewareHandler.sns_client is None:
            NotificationMiddlewareHandler.sns_client = sns = boto3.client("sns",
                   region_name="us-east-2",
           aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
           aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
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

        if notification_path is not None:
            for elements in notification_path:
                if elements['endpoint'] == request.path:
                    s_client = NotificationMiddlewareHandler.get_sns_client()
                    response = s_client.publish(
                        TargetArn=sns_topic,
                        Message=json.dumps({'default': json.dumps(message)}),
                        MessageStructure='json'
                    )
                    print("Publish response = ", json.dumps(response, indent=2))
                    return
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