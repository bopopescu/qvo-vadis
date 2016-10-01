from oauth2client.client import OAuth2WebServerFlow
from oauth2client.appengine import CredentialsProperty
from oauth2client.appengine import StorageByKeyName
import google_credentials
from google.appengine.api import users
from googleapiclient.discovery import build
from google.appengine.ext import db
import webapp2
import httplib2
import urllib
import pickle
import logging

logging.basicConfig(level=logging.INFO)


CALLBACK_DOMAIN = "qvo-vadis.appspot.com"

# global variable to store the services, should not be accessed from outside
_services = {}


def get_callback_domain():
    request = webapp2.get_request()
    host = request.host
    if 'localhost' in host:
        callback_domain = host
    else:
        callback_domain = CALLBACK_DOMAIN
    return callback_domain


def get_service(api_client, version, scope):
    global _services
    key = api_client + version + scope
    # check by id if the service is available in this session, if not
    # start an authentication flow to create it
    if key in _services:
        return _services[key]
    else:
        request = webapp2.get_request()
        # check if credentials are available in the datastore
        cred = CredentialsModel.get_by_key_name(key)
        if not cred:
            user = users.get_current_user()
            if not user:
                login_url = users.create_login_url(request.url)
                webapp2.redirect(login_url, abort=True)
            else:
                # redirect for authentication flow
                callback_domain = get_callback_domain()
                flow = OAuth2WebServerFlow(client_id=google_credentials.CLIENT_ID,
                                           client_secret=google_credentials.CLIENT_SECRET,
                                           scope=scope,
                                           redirect_uri=request.scheme + '://' + callback_domain + '/oauth2callback',
                                           access_type='offline')
                state = {
                    'original_url': request.url,
                    'api_client': api_client,
                    'version': version,
                    'scope': scope
                }
                state_string = pickle.dumps(state)
                auth_uri = flow.step1_get_authorize_url() + '&' + urllib.urlencode({'state': state_string})
                webapp2.redirect(auth_uri, abort=True)
        else:
            credentials = cred.credentials
            http = httplib2.Http()
            http = credentials.authorize(http)
            # store the service in the global variable
            _services[key] = build(api_client, version, http=http)
            return _services[key]


class CredentialsModel(db.Model):
    # storing credentials object in datastore
    credentials = CredentialsProperty()


class OauthHandler(webapp2.RequestHandler):

    def get(self):
        request = webapp2.get_request()
        code = request.get('code')
        state_string = request.get('state')
        state = pickle.loads(state_string)
        api_client = state['api_client']
        version = state['version']
        scope = state['scope']
        key = api_client + version + scope
        original_url = state['original_url']  # url of the original call
        flow = OAuth2WebServerFlow(client_id=google_credentials.CLIENT_ID,
                                   client_secret=google_credentials.CLIENT_SECRET,
                                   scope=scope,
                                   redirect_uri=request.path_url,
                                   access_type='offline')
        credentials = flow.step2_exchange(code)
        # store the credentials in the datastore
        storage = StorageByKeyName(CredentialsModel, key, 'credentials')
        storage.put(credentials)
        return webapp2.redirect(original_url)
