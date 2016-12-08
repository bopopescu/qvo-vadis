from jinja_templates import jinja_environment
import customer_configuration
from lib import get_localization, get_language, slugify, BaseHandler
import json
from datetime import date, timedelta


localization = get_localization()


class MapHandler(BaseHandler):
    def get(self, *args, **kwargs):
        style = self.request.get("style")  # hidden feature
        now = self.request.get("now")  # hidden feature
        if not now:
            now = ''  # no fallback needed here!
        configuration = customer_configuration.get_configuration(self.request)
        # detect language and use configuration as default
        language = get_language(self.request, configuration)
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
            localization=localization[language],
            now=now,
            style=style
        )
        # return the web-page content
        self.response.out.write(content)
        return
