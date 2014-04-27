import webapp2
from jinja_templates import jinja_environment
from oauth2_three_legged import Oauth2_service
import logging

logging.basicConfig(level=logging.INFO)


class ICalHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('calendar.ics')
        content = template.render( )
        # return the web-page content
        self.response.headers['Content-Type'] = "text/calendar"
        self.response.headers['Content-Disposition'] = 'attachment;filename="calendar.ics"'
        self.response.out.write(content)
        return
