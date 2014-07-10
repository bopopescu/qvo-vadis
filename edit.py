import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging
from lib import slugify, get_localization
import csv

logging.basicConfig(level=logging.INFO)


class EditHandler(webapp2.RequestHandler):
    def get(self, edit_mode='new', event_slug=None):
        configuration = customer_configuration.get_configuration(self.request)
        localization = get_localization()
        template = jinja_environment.get_template('editor.html')
        content = template.render(
            configuration=configuration,
            slugify=slugify,
            localization=localization[configuration['language']]
        )
        # return the web-page content
        self.response.out.write(content)
        return
