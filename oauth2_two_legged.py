import logging
from oauth2client.contrib.appengine import AppAssertionCredentials
from httplib2 import Http
from googleapiclient.discovery import build
from lib import DEV
from oauth2client.service_account import ServiceAccountCredentials


logging.basicConfig(level=logging.INFO)


def get_service(api_client, version, scope):
    if DEV:
        scopes = [scope]
        credentials = ServiceAccountCredentials.from_json_keyfile_name('qvo-vadis-0c249553334b.json', scopes)
    else:
        credentials = AppAssertionCredentials(scope)
    http_auth = credentials.authorize(Http())
    service = build(api_client, version, http=http_auth)
    return service

