import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging

logging.basicConfig(level=logging.INFO)


class MapHandler(webapp2.RequestHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self)
        template = jinja_environment.get_template('map.html')
        content = template.render(
            configuration=configuration
        )
        # return the web-page content
        self.response.out.write(content)
        return
