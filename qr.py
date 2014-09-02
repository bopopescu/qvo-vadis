import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging
import datetime
import fusion_tables
from lib import get_localization, BaseHandler


DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class LocationHandler(BaseHandler):
    def get(self, now=datetime.datetime.strftime(datetime.datetime.now(), DATE_TIME_FORMAT), location_slug=None):
        configuration = customer_configuration.get_configuration(self.request)
        localization = get_localization()

        condition = "start > '%s'" % now

        # apply commercial limit
        limit = customer_configuration.get_limit(self.request)
        if limit:
            condition += " AND 'start' < '%s'" % limit

        # query on location
        condition += " AND 'location slug' = '%s'" % location_slug

        # sort by datetime slug
        condition += " ORDER BY 'datetime slug'"

        no_results_message = ''
        data = fusion_tables.select(configuration['slave table'], condition=condition)
        if not data:
            no_results_message = 'Geen activiteiten voldoen aan de zoekopdracht.'
            condition = "'location slug' = '%s'" % location_slug  # search without time filter
            data = fusion_tables.select_first(configuration['slave table'], condition)
            if not data:
                # TODO what if the location's events have been deleted?
                logging.error("No events found for location (%s)" % condition)
                raise webapp2.abort(404)

        qr_url = self.request.url
        url = qr_url.replace('/qr/location/','#/location/')

        template = jinja_environment.get_template('qr.html')
        content = template.render(
            configuration=configuration,
            data=data,
            date_time_reformat=date_time_reformat,
            no_results_message=no_results_message,
            url=url,
            localization=localization[configuration['language']]
        )

        # return the web-page content
        self.response.out.write(content)
        return


def date_time_reformat(date, format='full', lang='en'):
    from babel.dates import format_date, format_datetime, format_time
    date_p = datetime.datetime.strptime(date, DATE_TIME_FORMAT)
    return format_datetime(date_p, format=format, locale=lang)


