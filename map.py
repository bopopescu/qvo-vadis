import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging

logging.basicConfig(level=logging.INFO)


class MapHandler(webapp2.RequestHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        # apply commercial limit
        limit = customer_configuration.get_limit(self.request)
        template = jinja_environment.get_template('map.html')
        content = template.render(
            configuration=configuration,
            limit=limit if limit else 0
        )
        # return the web-page content
        self.response.out.write(content)
        return
