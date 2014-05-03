import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging
import time
import datetime
import oauth2_three_legged

logging.basicConfig(level=logging.INFO)

DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

OAUTH_SCOPE = 'https://www.googleapis.com/auth/fusiontables.readonly'
API_CLIENT = 'fusiontables'
VERSION = 'v1'


class LocationHandler(webapp2.RequestHandler):
    def get(self, now=time.strftime(DATE_TIME_FORMAT), location=None, timeframe=None, tags=None):
        configuration = customer_configuration.get_configuration(self)
        template = jinja_environment.get_template('map.html')
        content = template.render(
            configuration=configuration.data
        )

        table_id = configuration.data['slave table']

        ## going to make this a module later on
        # query fusion table on location, timeframe and tags

        # calculate midnight, midnight1 and midnight 7 based on now
        now_p = now.strptime(now, DATE_TIME_FORMAT)
        midnight_p = datetime.combine(now_p + datetime.timedelta(days=1), datetime.time.min)
        midnight1_p = datetime.combine(now_p + datetime.timedelta(days=2), datetime.time.min)
        midnight7_p = datetime.combine(now_p + datetime.timedelta(days=8), datetime.time.min)
        midnight = midnight_p.strftime(DATE_TIME_FORMAT)
        midnight1 = midnight1_p.strftime(DATE_TIME_FORMAT)
        midnight7 = midnight7_p.strftime(DATE_TIME_FORMAT)

        # query on timeframe
        if timeframe == 'now':
            # start < now and end > now
            query = "start < '" + now + "' and end > '" + now + "'"
        elif timeframe == 'today':
            # start > now and start < midnight
            query = "start > '" + now + "' and start < '" + midnight + "'"
        elif timeframe == 'tomorrow':
            # start > midnight and start < midnight + 1 day
            query = "start > '" + midnight + "' and start < '" + midnight1 + "'"
        elif timeframe == 'week':
            # start > now and start < midnight + 7 days
            query = "start > '" + midnight + "' and start < '" + midnight7 + "'"
        elif timeframe == 'all':
            # start > now
            query = "start > '" + now + "'"

        # query on tags
        tags_p = tags.split(',')
        for tag in tags:
            query += " AND tags CONTAINS '#" + tag + "#'"
            # tags in the fusion table are surrounded by hash characters to avoid
            # confusion if one tag would be a substring of another tag

        # query on location
        query += " AND 'location slug' = '" + location + "'"

        service = oauth2_three_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
        c = service.query().sqlGet(sql="SELECT * FROM " + configuration['slave table'] + " WHERE " + query).execute()
        if 'rows' in c:
            data = dict(zip(c['columns'],c['rows'][0]))
        else:
            raise webapp2.abort(404)

        # return the web-page content
        self.response.out.write()
        return
