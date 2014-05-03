import webapp2
import oauth2_three_legged


OAUTH_SCOPE = 'https://www.googleapis.com/auth/fusiontables.readonly'
API_CLIENT = 'fusiontables'
VERSION = 'v1'
CONFIGURATION_TABLE_ID = '16REZHVjob5ah9sdBwuioQl6z8pqi5NXxMx7RzsDG'


# global variable
_configuration = {}


def get_configuration(handler):
    global _configuration
    if _configuration:
        return _configuration
    else:
        data = {}
        # check if the customer id is provided as URL parameter
        # this overrules the subdomain
        id = handler.request.get('id')
        if not id:
            # otherwise, if the domain is appspot.com, get the subdomain
            domain = handler.request.host
            if '.qvo-vadis.appspot.com' in domain:
                # try fetching this id from the configuration table
                id = domain[:domain.index('.qvo-vadis.appspot.com')]
        if id:
            service = oauth2_three_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
            c = service.query().sqlGet(sql="SELECT * FROM " + CONFIGURATION_TABLE_ID + " WHERE id = '" + id + "'").execute()
            if 'rows' in c:
                _configuration = dict(zip(c['columns'],c['rows'][0]))
                return _configuration
            else:
                raise webapp2.abort(404)
        else:
            raise webapp2.abort(404)

