from flask import current_app, json, request, url_for
import config.constants as CONSTANTS
import traceback
import requests

class AddressValidator():
    def validate_street_details(street_json):
        try:
            is_street_valid = True
            if not current_app.config['IS_DEVELOPMENT_MODE'] == 1:
                ss_url = CONSTANTS.SS_SCHEME + CONSTANTS.SS_STREET_HOST_NAME + CONSTANTS.SS_CONTEXT
                ss_request = {}
                ss_json = {}
                ss_request['auth-id'] = current_app.config['SS_API_KEY']
                ss_request['auth-token'] = current_app.config['SS_AUTH_TOKEN']
                ss_json['address1'] = street_json['street_name_1']
                ss_json['address2'] = street_json['street_name_2']
                ss_json['locality'] = street_json['city']
                ss_json['administrative_area'] = street_json['region']
                ss_json['postal_code'] = street_json['postal_code']
                ss_json['country'] = street_json['country_code']
                ss_request = {**ss_request, **ss_json}
                query_string = '&'.join(f'{k}={v}' for k, v in ss_request.items())
                query_string = query_string.replace(" ", "+")
                ss_url += query_string
                print(ss_url)
                #ss_response = None
                ss_response = requests.get(ss_url)
                print(ss_response)
                http_status_code = ss_response.status_code
                if str(http_status_code) == CONSTANTS.HTTP_CODE_200:
                    return ss_response.content
                else:
                    current_app.logger.error("Status code received is " + str(http_status_code) )
                    return None
            else:
                return None
        except Exception:
            print(traceback.format_exc())
            current_app.logger.error("Exception occurred while processing function validate_street_details")
            return None