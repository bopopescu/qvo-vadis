import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging
from lib import slugify, get_localization
import fusion_tables
import json

logging.basicConfig(level=logging.INFO)


class EditHandler(webapp2.RequestHandler):
    def get(self, edit_mode='new', event_slug=None, location_slug=None):
        configuration = customer_configuration.get_configuration(self.request)
        event = None
        location_only = 'false'
        if event_slug:
            event = fusion_tables.select_first(configuration['master table'], condition="'event slug' = '%s'" % event_slug)
        elif location_slug:
            event = fusion_tables.select_first(configuration['master table'], condition="'location slug' = '%s'" % location_slug)
            location_only = 'true'
        if edit_mode == 'new':
            if event_slug:
                title = "edit-new-event-based-on-original"
            else:
                title = "edit-new-event-from-scratch"
        else:
            title = "update-event"
        localization = get_localization()
        template = jinja_environment.get_template('editor.html')
        content = template.render(
            configuration=configuration,
            event_json=json.dumps(event),
            location_only=location_only,
            title=title,
            edit_mode=edit_mode,
            slugify=slugify,
            localization=localization[configuration['language']]
        )
        # return the web-page content
        self.response.out.write(content)
        return
