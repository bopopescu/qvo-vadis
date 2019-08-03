from jinja_templates import jinja_environment
import customer_map
import logging
from lib import slugify, get_localization, get_language, BaseHandler
import fusion_tables
import json
import model
from google.appengine.ext.ndb import GeoPt


class EditHandler(BaseHandler):
    def get(self, edit_mode='new', event_slug=None, location_slug=None,
            latitude=None, longitude=None, zoom=None, tags=None, hashtags=None):
        map = customer_map.get_map(self.request)
        # detect language and use configuration as default
        language = get_language(self.request, map)
        event = [{}]
        event_default = 'false'
        location_default = 'false'
        coordinates_default = 'false'
        tags_default = 'false'
        hashtags_default = 'false'
        if event_slug:
            event_ndb = model.Event.get_by_id(event_slug)
            event = [event_ndb.to_dict()]
            event_default = 'true'
        if location_slug:
            event_ndb = model.Event.query(model.Event.location_slug == location_slug, model.Event.map == map.key).get()
            event = [event_ndb.to_dict()]
            location_default = 'true'
        if latitude and longitude and not event_slug and not location_slug:
            event[0]['coordinates'] = latitude + "," + longitude
            event[0]['zoom'] = zoom  # zoom is not in a normal event object !
            coordinates_default = 'true'
        if tags and not event_slug:
            event[0]['tags'] = tags.split(',')
            tags_default = 'true'
        if hashtags and not event_slug:
            event[0]['hashtags'] = hashtags.split(',')
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
            map=map,
            # note that event is a [{}] !
            event_json=json.dumps(event, default=str) if event else '[0]',  # check map.html and gmaps.js why
            event_slug=event_slug,
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
