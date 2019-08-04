import webapp2
from jinja_templates import jinja_environment
import customer_map
import logging
import datetime
from lib import get_localization, get_language, BaseHandler
import json
import model
import pytz
from babel.dates import format_date, format_datetime, format_time

DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class LocationHandler(BaseHandler):
    def get(self, location_slug=None, timeframe=None, tags=None, hashtags=None):
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
            ed['tags'] = e.tags
            ed['hashtags'] = e.hashtags
            if first:
                # fetch location name, coordinates and address
                location_name = e.location_name
                coordinates = e.coordinates
                address = e.address
                # setup local timespots
                naive_utc_now = datetime.datetime.today()
                utc_now = pytz.utc.localize(naive_utc_now)
                local_now = utc_now.astimezone(pytz.timezone(e.timezone))
                now = local_now.replace(tzinfo=None)
                midnight = now.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
                midnight1 = midnight + datetime.timedelta(days=1)
                midnight7 = midnight + datetime.timedelta(days=7)
                first = False
        # fetch all Instances
        instances = model.Instance.query(model.Instance.location_slug == location_slug, model.Instance.map == map.key).order(model.Instance.start_local)
        if timeframe == 'now':
            instances = instances.filter(model.Instance.start_local < now)
        elif timeframe == 'today':
            instances = instances.filter(model.Instance.start_local < midnight)
        elif timeframe == 'tomorrow':
            instances = instances.filter(model.Instance.start_local < midnight1)
        elif timeframe == 'week':
            instances = instances.filter(model.Instance.start_local < midnight7)
        if timeframe == 'all' and not tags and not hashtags:
            instances = instances.fetch(20)
        # iterate the Instances to finish the filtration and to setup a list with all data required for the HTML
        data = []
        for i in instances:
            visible = True
            ed = events_dict[i.event_slug.id()]
            # remove Instances with end_local < now
            if i.end_local < now:
                continue
            # if timeperiod is "tomorrow", remove Instances with end_local < midnight
            if timeframe == 'tomorrow' and i.end_local < midnight:
                continue
            # if tags are specified, remove Instances that don't match all of the tags
            if tags:
                tags_p = tags.split(',')
                for tag in tags_p:
                    if tag not in ed['tags']:
                        visible = False
                        break
                if not visible:
                    continue
            if hashtags:
                hashtags_p = hashtags.split(',')
                for hashtag in hashtags_p:
                    if hashtag not in ed['hashtags']:
                        visible = False
                        break
                if not visible:
                    continue
            # this instances is OK for output!
            data.append(i)
            i.event_name = ed['event_name']
        no_results_message = ''
        if not data:
            no_results_message = localization[map.language]['no-results']
            logging.error("No events found for location (%s)" % location_slug)
        template = jinja_environment.get_template('location.html')
        content = template.render(
            map=map,
            data=data,
            location_name=location_name,
            address=address,
            latitude=coordinates.lat,
            longitude=coordinates.lon,
            format_datetime=format_datetime,
            no_results_message=no_results_message,
            localization=localization[language]
        )
        # return the web-page content
        self.response.out.write(content)
        return


class EventHandler(BaseHandler):
    def get(self, event_slug=None, date_time_slug=None):
        map = customer_map.get_map(self.request)
        # detect language and use configuration as default
        language = get_language(self.request, map)
        localization = get_localization()
        # query for Event
        event = model.Event.get_by_id(event_slug)
        # query for Instance
        if date_time_slug:
            instance = model.Instance.get_by_id(event_slug + '-' + date_time_slug)
        else:
            instance = model.Instance.query(model.Instance.event_slug == ndb.Key(model.Event, event_slug)).order(model.Instance.start_local).get()
        no_results_message = ''
        if not event or not instance:
            no_results_message = localization[map['language']]['no-results']
        # if data has no address, fetch it
        if not event.address:
            event.address = address(event.latitude, event.longitude, language)
        template = jinja_environment.get_template('event.html')
        content = template.render(
            map=map,
            event=event,
            instance=instance,
            latitude=event.coordinates.lat,
            longitude=event.coordinates.lon,
            format_datetime=format_datetime,
            no_results_message=no_results_message,
            localization=localization[language]
        )
        # return the web-page content
        self.response.out.write(content)
        return


class SitemapByLocationHandler(BaseHandler):
    def get(self):
        map = customer_map.get_map(self.request)
        location_slug = self.request.get("location")
        instances = ndb.gql("SELECT event_slug, date_time_slug FROM Instance WHERE location_slug = :1 AND map = :2", location_slug, map.key)
        no_results_message = ''
        if not instances:
            no_results_message = '# No results'
        template = jinja_environment.get_template('sitemap.txt')
        content = template.render(
            map=map,
            instances=instances,
            no_results_message=no_results_message
        )
        # return the web-page content
        self.response.headers['Content-Type'] = "text/plain"
        self.response.out.write(content)
        return


class IndexByLocationHandler(BaseHandler):
    def get(self):
        map = customer_map.get_map(self.request)
        # get all locations on the active map
        events = ndb.gql("SELECT DISTINCT location_slug FROM Event WHERE map = :1", map.key)
        if not events:
            no_results_message = '# No results'
        template = jinja_environment.get_template('sitemapindexbylocation.xml')
        content = template.render(
            map=map,
            events=events
        )
        # return the web-page content
        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(content)
        return


from google.appengine.ext import ndb
from google.appengine.api import urlfetch


class Address_cache(ndb.Model):
    location = ndb.DateProperty()  # key is string composed of latitude + longitude + language
    content = ndb.TextProperty()


def address(latitude, longitude, language):
    key = "%.6f,%.6f" % (latitude, longitude)
    address_cache = Address_cache.get_or_insert(key)
    if not address_cache.content:
        api_key = "AIzaSyAObYcVpywvDwFBZqDxU6PIRvVji9vM9TQ"
        url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%f,%f&result_type=street_address&language=%s&key=%s" % (latitude, longitude, language, api_key)
        try:
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                address_json = result.content
            else:
                logging.exception("HTTP error fetching url %s" % url)
                address_json = ''
        except urlfetch.Error:
            logging.exception("Caught exception fetching url %s" % url)
        address_cache.content = address_json
        address_cache.put()
    addresses = json.loads(address_cache.content)
    address = addresses['results'][0]['formatted_address']
    return address
