import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging
import datetime
import fusion_tables
from lib import get_localization, BaseHandler


DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class LocationHandler(BaseHandler):
    def get(self, location_slug=None, timeframe=None, tags=None, hashtags=None):
        now = self.request.get("now")
        if not now:
            now = datetime.datetime.strftime(datetime.datetime.now(), DATE_TIME_FORMAT)  # fallback to server time
        configuration = customer_configuration.get_configuration(self.request)
        localization = get_localization()

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
            condition = "start <= '" + now + "' and end >= '" + now + "'"
        elif timeframe == 'today':
            # end > now and start < midnight
            condition = "end >= '" + now + "' and start <= '" + midnight + "'"
        elif timeframe == 'tomorrow':
            # end > midnight and start < midnight + 1 day
            condition = "end >= '" + midnight + "' and start <= '" + midnight1 + "'"
        elif timeframe == 'week':
            # end > now and start < midnight + 7 days
            condition = "end >= '" + now + "' and start <= '" + midnight7 + "'"
        else:  # 'all' and other timeframes are interpreted as 'all'
            # end > now
            condition = "end >= '" + now + "'"

        # apply commercial limit
        limit = customer_configuration.get_limit(self.request)
        if limit:
            condition += " AND 'start' < '%s'" % limit

        # query on tags
        if tags:
            tags_p = tags.split(',')
            for tag in tags_p:
                condition += " AND tags CONTAINS '#" + tag + "#'"
                # tags in the fusion table are surrounded by hash characters to avoid
                # confusion if one tag would be a substring of another tag

        # query on hashtags
        if hashtags:
            hashtags_p = hashtags.split(',')
            for hashtag in hashtags_p:
                condition += " AND hashtags CONTAINS '#" + hashtag + "#'"

        # query on location
        condition += " AND 'location slug' = '" + location_slug + "'"

        # sort by datetime slug
        condition += " ORDER BY 'datetime slug'"

        no_results_message = ''
        data = fusion_tables.select(configuration['slave table'], condition=condition)
        if not data:
            no_results_message = localization[configuration['language']]['no-results']
            condition = "'location slug' = '" + location_slug + "'"  # search without timeframe or tags filter
            data = fusion_tables.select_first(configuration['slave table'], condition=condition)
            if not data:
                # TODO what if the location's events have been deleted?
                # is foreseen: fallback to query on event_slug only
                logging.error("No events found for location (%s)" % condition)
                raise webapp2.abort(404)

        template = jinja_environment.get_template('location.html')
        content = template.render(
            configuration=configuration,
            data=data,
            date_time_reformat=date_time_reformat,
            no_results_message=no_results_message,
            localization=localization[configuration['language']]
        )

        # return the web-page content
        self.response.out.write(content)
        return


class EventHandler(BaseHandler):
    def get(self, event_slug=None, datetime_slug=None):
        configuration = customer_configuration.get_configuration(self.request)
        localization = get_localization()

        # query on event
        condition = "'event slug' = '%s'" % event_slug
        if datetime_slug:
            condition += " AND "
            condition += "'datetime slug' = '%s'" % datetime_slug
        data = fusion_tables.select(configuration['slave table'], condition=condition)
        no_results_message = ''
        if not data:
            no_results_message = localization[configuration['language']]['no-results']

        template = jinja_environment.get_template('event.html')
        content = template.render(
            configuration=configuration,
            data=data[0] if data else {},
            date_time_reformat=date_time_reformat,
            no_results_message=no_results_message,
            localization=localization[configuration['language']]
        )

        # return the web-page content
        self.response.out.write(content)
        return


def date_time_reformat(date, format='full', lang='en'):
    from babel.dates import format_date, format_datetime, format_time
    date_p = datetime.datetime.strptime(date, DATE_TIME_FORMAT)
    return format_datetime(date_p, format=format, locale=lang)
