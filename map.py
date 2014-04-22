import webapp2
from jinja_templates import jinja_environment
import logging

logging.basicConfig(level=logging.INFO)


class MapHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('map.html')
        content = template.render()
        # return the web-page content
        self.response.out.write(content)
        return
