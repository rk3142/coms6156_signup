import requests
import json
import boto3
import os
import re
from utils.rest_utils import RESTContext

notification_path = []
#{
#    "endpoint": "/reg-service/v1/addresses",
#    "method": ["POST", "GET"],
#    "notification": "message here"
#}

class NotificationMiddlewareHandler:
    sns_client = None

    def __init__(self):
        pass

    @classmethod
    def get_notification_request(cls, request):
        rest_request = RESTContext(request_context=request)
        if notification_path is not None or len(notification_path) != 0:
            for paths in notification_path:
                if re.search(paths.get('endpoint'), rest_request.path) and \
                        rest_request.method in paths.get('method'):
                    return paths.get('notification')

        return False

    @classmethod
    def get_sns_client(cls):

        if NotificationMiddlewareHandler.sns_client is None:
            NotificationMiddlewareHandler.sns_client = boto3.client("sns",
                                                                          region_name="us-east-2",
                                                                          aws_access_key_id=os.environ.get(
                                                                              'SNS_AWS_ACCESS_KEY_ID', None),
                                                                          aws_secret_access_key=os.environ.get(
                                                                              'SNS_AWS_SECRET_ACCESS_KEY', None))
        return NotificationMiddlewareHandler.sns_client

    @classmethod
    def get_sns_topics(cls):
        s_client = NotificationMiddlewareHandler.get_sns_client()
        result = s_client.list_topics()
        topics = result["Topics"]
        return topics

    @classmethod
    def send_sns_message(cls, sns_topic, notification):
        s_client = NotificationMiddlewareHandler.get_sns_client()
        response = s_client.publish(
            TargetArn=sns_topic,
            Message=json.dumps({'default': notification}),
            MessageStructure='json'
        )
        print("Publish response = ", json.dumps(response, indent=2))
        return
