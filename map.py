from jinja_templates import jinja_environment
import customer_map
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
        map = customer_map.get_map(self.request)
        # detect language and use configuration as default
        language = get_language(self.request, map)
        # map colors to tags
        colors = ['purple', 'blue', 'teal', 'lightgreen', 'amber', 'red']
        tags = map.tags.split(',')
        tag_colors = {}
        for i, tag in enumerate(tags):
            tag_colors[slugify(tag)] = colors[i % 6]
        tag_colors['all-tags'] = 'white'
        template = jinja_environment.get_template('map.html')
        content = template.render(
            map=map,
            tag_colors=tag_colors,
            tag_colors_json=json.dumps(tag_colors),  # TODO this is UCT, you know?
            day_of_today=date.today().day,  # TODO this is UCT, you know?
            day_of_tomorrow=(date.today() + timedelta(days=1)).day,  # TODO this is UCT, you know?
            slugify=slugify,
            localization=localization[language],
            now=now,
            style=style
        )
        # return the web-page content
        self.response.out.write(content)
        return
