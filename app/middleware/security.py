import json


secure_paths = [ 
    {
        "endpoint": "/reg-service/v1/addresses",
        "allowed": "all",
        "method": ["GET", "POST"]
    },
    {
        "endpoint": "/reg-service/v1/users",
        "allowed": "all",
        "method": ["GET"]
    },
    {
        "endpoint": "/reg-service/v1/addresses/<id>/users",
        "allowed": "all",
        "method": ["GET"]
    },
    {
        "endpoint": "/reg-service/v1/users/<id>/address",
        "allowed": "all",
        "method": ["GET"]
    },
    {
        "endpoint": "/reg-service/v1/addresses/<id>",
        "allowed": "all",
        "method": ["GET"]
    },
    {
        "endpoint": "/reg-service/v1/addresses/<id>",
        "allowed": "admin",
        "method": ["DELETE"]
    },
    {
        "endpoint": "/reg-service/v1/users/<id>",
        "allowed": "all",
        "method": ["GET"]
    },
    {
        "endpoint": "/reg-service/v1/users/<id>",
        "allowed": "all",
        "method": ["DELETE"]
    }
]

def check_security(request, blueprint, google):
    path = request.path
    result_ok = False

    if check_path_validity(path):
        user_info_endpoint = '/outh2/v2/userinfo'
        if google.authorized:
            result_ok = True
            '''
            print("Inside if")
            resp = blueprint.session.get(user_info_endpoint)
            user_info = resp.json()
            user_id = str(user_info['id'])
            print("User id:" + str(user_id))
            result_ok = True
            '''
        else:
            print("Inside false")
            result_ok = False
    else:
        result_ok = True

    return result_ok

def check_path_validity(path, method_type=''):
    print(secure_paths)
    if secure_paths is not None:
        for elements in secure_paths:
            if elements['endpoint'] == path:
                return True

    return False