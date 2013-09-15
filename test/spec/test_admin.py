
import test.api as api
import requests
import requests.auth as auth

def xtest_initdb():
    admin_url = api.api_root + "/admin"

    print('about to request')
    response = requests.post(admin_url + "/initdb",
                            auth=auth.HTTPBasicAuth(api.user, api.password))
    print('response: ', response)
    response.raise_for_status()
    #raise Exception("crap")
