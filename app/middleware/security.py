import json, re

from flask.globals import request
from utils.rest_utils import RESTContext

secure_paths = [ 
    {
        "endpoint": "/reg-service/v1/addresses",
        "method": ["GET", "POST"]
    },
    {
        "endpoint": "/reg-service/v1/users",
        "method": ["PUT"]
    },
    {
        "endpoint": "/reg-service/v1/addresses/*/users",
        "method": ["GET"]    
    },
    {
        "endpoint": "/reg-service/v1/users/*/address",
        "method": ["GET"]
    },
    {
        "endpoint": "/reg-service/v1/addresses/*",
        "method": ["GET", "DELETE"]
    },
    {
        "endpoint": "/reg-service/v1/users/*",
        "method": ["GET", "DELETE"]
    }
]

def check_security(request, google):
    rest_request = RESTContext(request_context=request)    
    result_ok = False
    if secure_paths is not None:
        if check_path_validity(rest_request):
            if google.authorized:
                result_ok = True
            else:
                result_ok = False
        else:
            result_ok = True
    else:
        result_ok = True

    return result_ok

def check_path_validity(rest_request):
    for access_path in secure_paths:
        if re.search(access_path.get('endpoint'), rest_request.path) and \
            rest_request.method in access_path.get('method'):
            return True
        
    return False