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
    def get(self, now=datetime.datetime.strftime(datetime.datetime.now(), DATE_TIME_FORMAT), location_slug=None):
        configuration = customer_configuration.get_configuration(self)

        query = "start > '" + now + "'"

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
            query = "'location slug' = '" + location_slug + "'"  # search without time filter
            c = service.query().sqlGet(sql="SELECT * FROM " + configuration['slave table'] + " WHERE " + query).execute()
            if 'rows' in c:
                data.append(dict(zip(c['columns'],c['rows'][0])))  # take first row to get location info
                no_results_message = 'Geen activiteiten voldoen aan de zoekopdracht.'
            else:
                # TODO what if the location's events have been deleted?
                raise webapp2.abort(404)

        qr_url = self.request.url
        url = qr_url.replace('/qr/location/','#/location/')

        template = jinja_environment.get_template('qr.html')
        content = template.render(
            configuration=configuration,
            data=data,
            date_time_reformat=date_time_reformat,
            no_results_message=no_results_message,
            url=url
        )

        # return the web-page content
        self.response.out.write(content)
        return


def date_time_reformat(date, format='full', lang='en'):
    from babel.dates import format_date, format_datetime, format_time
    date_p = datetime.datetime.strptime(date, DATE_TIME_FORMAT)
    return format_datetime(date_p, format=format, locale=lang)


