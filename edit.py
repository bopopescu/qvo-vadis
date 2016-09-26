from jinja_templates import jinja_environment
import customer_configuration
import logging
from lib import slugify, get_localization, get_language, BaseHandler
import fusion_tables
import json


class EditHandler(BaseHandler):
    def get(self, edit_mode='new', event_slug=None, location_slug=None,
            latitude=None, longitude=None, zoom=None, tags=None, hashtags=None):
        configuration = customer_configuration.get_configuration(self.request)
        # detect language and use configuration as default
        language = get_language(self.request, configuration)
        event = [{}]
        event_default = 'false'
        location_default = 'false'
        coordinates_default = 'false'
        tags_default = 'false'
        hashtags_default = 'false'
        if event_slug:
            event = fusion_tables.select_first(configuration['master table'], condition="'event slug' = '%s'" % event_slug)
            event_default = 'true'
        if location_slug:
            event = fusion_tables.select_first(configuration['master table'], condition="'location slug' = '%s'" % location_slug)
            location_default = 'true'
        if latitude and longitude and not event_slug and not location_slug:
            event[0]['latitude'] = latitude
            event[0]['longitude'] = longitude
            event[0]['zoom'] = zoom  # zoom is not in a normal event object !
            coordinates_default = 'true'
        if tags and not event_slug:
            event[0]['tags'] = ','.join(["#%s#" % t for t in tags.split(',')])
            tags_default = 'true'
        if hashtags and not event_slug:
            event[0]['hashtags'] = ','.join(["#%s#" % h for h in hashtags.split(',')])
            hashtags_default = 'true'
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
            # note that event is a [{}] !
            event_json=json.dumps(event) if event else '[0]',  # check map.html and gmaps.js why
            event_default=event_default,
            location_default=location_default,
            coordinates_default=coordinates_default,
            tags_default=tags_default,
            hashtags_default=hashtags_default,
            title=title,
            edit_mode=edit_mode,
            slugify=slugify,
            language=language,
            localization=localization[language]
        )
        # return the web-page content
        self.response.out.write(content)
        return
