import webapp2
from jinja_templates import jinja_environment
import customer_map
import logging
import datetime
import pytz
import model
from lib import get_localization, get_language, BaseHandler


DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class LocationHandler(BaseHandler):
    def get(self, location_slug=None):
        map = customer_map.get_map(self.request)
        localization = get_localization()
        # detect language and use configuration as default
        language = get_language(self.request, map)
        # fetch all events
        events = model.Event.query(model.Event.location_slug == location_slug, model.Event.map == map.key)
        # setup a dict (by event slug) containing the event name, the timezone, tags and hashtags
        logging.info("Setup events dict")
        events_dict = {}
        first = True
        for e in events:
            events_dict[e.key.id()] = {}
            ed = events_dict[e.key.id()]
            ed['event_name'] = e.event_name
            if first:
                # fetch location name, coordinates and address
                location_name = e.location_name
                address = e.address
                # setup local timespots
                naive_utc_now = datetime.datetime.today()
                utc_now = pytz.utc.localize(naive_utc_now)
                local_now = utc_now.astimezone(pytz.timezone(e.timezone))
                now = local_now.replace(tzinfo=None)
                first = False
        # fetch all Instances
        instances = model.Instance.query(model.Instance.location_slug == location_slug, model.Instance.map == map.key).order(model.Instance.start_local)
        instances = instances.fetch(20)
        # iterate the Instances to finish the filtration and to setup a list with all data required for the HTML
        data = []
        for i in instances:
            ed = events_dict[i.event_slug.id()]
            # remove instances with end_local < now
            if i.end_local < now:
                continue
            # this instances is OK for output!
            data.append(i)
            i.event_name = ed['event_name']
        no_results_message = ''
        if not data:
            no_results_message = localization[map.language]['no-results']
            logging.error("No events found for location (%s)" % location_slug)
            raise webapp2.abort(404)
        qr_url = self.request.url
        url = qr_url.replace('/qr/location/','/all/location/')
        template = jinja_environment.get_template('qr.html')
        content = template.render(
            map=map,
            data=data,
            location_name=location_name,
            address=address,
            date_time_reformat=date_time_reformat,
            no_results_message=no_results_message,
            url=url,
            localization=localization[language]
        )
        # return the web-page content
        self.response.out.write(content)
        return


def date_time_reformat(date, format='full', lang='en'):
    from babel.dates import format_date, format_datetime, format_time
    return format_datetime(date, format=format, locale=lang)


