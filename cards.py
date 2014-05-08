import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging
import datetime
import oauth2_three_legged

logging.basicConfig(level=logging.INFO)

DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

OAUTH_SCOPE = 'https://www.googleapis.com/auth/fusiontables.readonly'
API_CLIENT = 'fusiontables'
VERSION = 'v1'


class LocationHandler(webapp2.RequestHandler):
    def get(self, now=datetime.datetime.strftime(datetime.datetime.now(), DATE_TIME_FORMAT), location_slug=None, timeframe=None, tags=None):
        configuration = customer_configuration.get_configuration(self)

        ## going to make this a module later on
        # query fusion table on location, timeframe and tags

        # calculate midnight, midnight1 and midnight 7 based on now
        now_p = datetime.datetime.strptime(now, DATE_TIME_FORMAT)
        midnight_p = datetime.datetime.combine(now_p + datetime.timedelta(days=1), datetime.time.min)
        midnight1_p = datetime.datetime.combine(now_p + datetime.timedelta(days=2), datetime.time.min)
        midnight7_p = datetime.datetime.combine(now_p + datetime.timedelta(days=8), datetime.time.min)
        midnight = datetime.datetime.strftime(midnight_p, DATE_TIME_FORMAT)
        midnight1 = datetime.datetime.strftime(midnight1_p, DATE_TIME_FORMAT)
        midnight7 = datetime.datetime.strftime(midnight7_p, DATE_TIME_FORMAT)

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
        else:  # 'all' and other timeframes are interpreted as 'all'
            # start > now
            query = "start > '" + now + "'"

        # query on tags
        if tags:
            tags_p = tags.split(',')
            for tag in tags_p:
                query += " AND tags CONTAINS '#" + tag + "#'"
                # tags in the fusion table are surrounded by hash characters to avoid
                # confusion if one tag would be a substring of another tag

        # query on location
        query += " AND 'location slug' = '" + location_slug + "'"

        service = oauth2_three_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
        c = service.query().sqlGet(sql="SELECT * FROM " + configuration['slave table'] + " WHERE " + query).execute()
        data = []
        no_results_message = ''
        if 'rows' in c:
            for row in c['rows']:
                data.append(dict(zip(c['columns'],row)))
        else:
            query = "'location slug' = '" + location_slug + "'"  # search without timeframe or tags filter
            c = service.query().sqlGet(sql="SELECT * FROM " + configuration['slave table'] + " WHERE " + query).execute()
            if 'rows' in c:
                data.append(dict(zip(c['columns'],c['rows'][0])))  # take first row to get location info
                no_results_message = 'Geen activiteiten voldoen aan de zoekopdracht.'
            else:
                # TODO what if the location's events have been deleted?
                raise webapp2.abort(404)

        template = jinja_environment.get_template('location.html')
        content = template.render(
            data=data,
            date_time_reformat=date_time_reformat,
            no_results_message=no_results_message
        )

        # return the web-page content
        self.response.out.write(content)
        return


class EventHandler(webapp2.RequestHandler):
    def get(self, event_slug=None):
        configuration = customer_configuration.get_configuration(self)

        ## going to make this a module later on
        # query fusion table on location, timeframe and tags

        # query on event
        query = "'event slug' = '" + event_slug + "'"

        service = oauth2_three_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
        c = service.query().sqlGet(sql="SELECT * FROM " + configuration['slave table'] + " WHERE " + query).execute()
        data = []
        no_results_message = ''
        if 'rows' in c:
            data = dict(zip(c['columns'],c['rows'][0]))
            # there should be only one row !!
        else:
            no_results_message = 'Geen activiteiten voldoen aan de zoekopdracht.'

        template = jinja_environment.get_template('event.html')
        content = template.render(
            data=data,
            date_time_reformat=date_time_reformat,
            no_results_message=no_results_message
        )

        # return the web-page content
        self.response.out.write(content)
        return


def date_time_reformat(date, format='full', lang='en'):
    from babel.dates import format_date, format_datetime, format_time
    date_p = datetime.datetime.strptime(date, DATE_TIME_FORMAT)
    return format_datetime(date_p, format=format, locale=lang)


