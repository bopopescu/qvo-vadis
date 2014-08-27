import webapp2
from jinja_templates import jinja_environment
import customer_configuration
from lib import get_localization, slugify
import json
from datetime import date, timedelta
import logging

logging.basicConfig(level=logging.INFO)


class MapHandler(webapp2.RequestHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        localization = get_localization()
        if configuration['id'] == 'www':
            # this is a request for the landing page!
            template = jinja_environment.get_template('www.html')
            content = template.render(
                localization=localization['en']  # TODO add localization to template and get user's langauage
            )
            # return the web-page content
            self.response.out.write(content)
            return
        # apply commercial limit
        limit = customer_configuration.get_limit(self.request)
        template = jinja_environment.get_template('map.html')
        # map colors to tags
        colors = ['purple', 'blue', 'teal', 'lightgreen', 'amber', 'red']
        tags = configuration['tags'].split(',')
        tag_colors = {}
        for i, tag in enumerate(tags):
            tag_colors[slugify(tag)] = colors[i % 6]
        tag_colors['all-tags'] = 'white'
        content = template.render(
            configuration=configuration,
            limit=limit if limit else 0,  # e.g. "2014-07-19 09:00:00"
            tag_colors=tag_colors,
            tag_colors_json=json.dumps(tag_colors),
            day_of_today=date.today().day,
            day_of_tomorrow=(date.today() + timedelta(days=1)).day,
            slugify=slugify,
            localization=localization[configuration['language']]
        )
        # return the web-page content
        self.response.out.write(content)
        return
