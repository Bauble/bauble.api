
import test.api as test    
import requests
import requests.auth as auth

def test_initdb():
    admin_url = test.api_root + "/admin"
    
    print('about to request')
    response = requests.post(admin_url + "/initdb", 
                            auth=auth.HTTPBasicAuth(test.user, test.password))
    print('response: ', response)
    response.raise_for_status()
    #raise Exception("crap")
