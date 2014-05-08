import webapp2
from jinja_templates import jinja_environment
import logging
import datetime

logging.basicConfig(level=logging.INFO)

DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class AppCacheHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('status.appcache')
        # TODO the 'now' variable is for debugging only
        now = datetime.datetime.strftime(datetime.datetime.now(), DATE_TIME_FORMAT)
        content = template.render(now=now)
        # return the web-page content
        self.response.headers['Content-Type'] = "text/cache-manifest"
        self.response.out.write(content)
        return
