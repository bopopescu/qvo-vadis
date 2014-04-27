import webapp2
from jinja_templates import jinja_environment
from oauth2_three_legged import Oauth2_service
import logging

logging.basicConfig(level=logging.INFO)

OAUTH_SCOPE = 'https://www.googleapis.com/auth/fusiontables.readonly'
API_CLIENT = 'fusiontables'
VERSION = 'v1'
CONFIGURATION_TABLE_ID = '16REZHVjob5ah9sdBwuioQl6z8pqi5NXxMx7RzsDG'

class MapHandler(webapp2.RequestHandler):
    def get(self):
        service = Oauth2_service(API_CLIENT, VERSION, OAUTH_SCOPE).service
        # check if the customer id is provided as URL parameter
        # this overrules the subdomain
        id = self.request.get('id')
        # otherwise, if the domain is appspot.com, get the subdomain
        if not id:
            domain = self.request.host
            if '.qvo-vadis.appspot.com' in domain:
                # try fetching this id from the configuration table
                id = domain[:domain.index('.qvo-vadis.appspot.com')]
        if id:
            c = service.query().sqlGet(sql="SELECT * FROM " + CONFIGURATION_TABLE_ID + " WHERE id = '" + id + "'").execute()
            configuration = dict(zip(c['columns'],c['rows'][0]))
            # get the configuration data by id

        # if no valid configuration is found, return an error

        template = jinja_environment.get_template('map.html')
        content = template.render(
            configuration=configuration
        )
        # return the web-page content
        self.response.out.write(content)
        return
