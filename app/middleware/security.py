import json

secure_paths = [
]


def check_security(request, blueprint, google):
    path = request.path
    print(path)
    result_ok = False

    if path not in secure_paths:
        user_info_endpoint = '/outh2/v2/userinfo'
        if google.authorized:
            print("Inside if")
            result_ok = True
            '''
            resp = blueprint.session.get(user_info_endpoint)
            user_info = resp.json()
            user_id = str(user_info['id'])
            '''
        else:
            print("Inside false")
            result_ok = False
    else:
        result_ok = True

    return result_ok