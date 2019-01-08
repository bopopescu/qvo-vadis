from google.appengine.ext import ndb
from lib import slugify
from recurrenceinput import calculate_occurrences
import datetime
import model
from google.appengine.api import urlfetch
import logging
import json
import pytz


DATE_FORMAT = '%Y-%m-%d'
ISO_DATE_TIME_FORMAT = '%Y%m%dT%H%M%S'
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def naive_local_datetime_to_naive_utc_datetime(naive_local_datetime, latitude, longitude, event):
    # the event is there to store the timezone name, so it can be reused
    # for offline processing after one call to the API
    # (it's assumed that the event entity is later on put to the datastore, but not necessary)
    if not event.timezone:
        key = "%.4f,%.4f" % (latitude, longitude)
        api_key = "AIzaSyAObYcVpywvDwFBZqDxU6PIRvVji9vM9TQ"
        timestamp = (naive_local_datetime - datetime.datetime(1970, 1, 1)).total_seconds()  # actually shouldn't do this, because date_p isn't UTC
        url = "https://maps.googleapis.com/maps/api/timezone/json?location=%.6f,%.6f&timestamp=%d&key=%s" % (latitude, longitude, timestamp, api_key)
        try:
            logging.info("Fetching timezone info [%s]" % url)
            result = urlfetch.fetch(url)
            if result.status_code == 200 and 'dstOffset' in result.content:
                timezone_json = result.content
            else:
                logging.exception("HTTP error fetching url %s" % url)
                timezone_json = ''
        except urlfetch.Error:
            logging.exception("Caught exception fetching url %s" % url)
        event.timezone = json.loads(timezone_json)['timeZoneId']
    # process that timezone info using pytz
    tz = pytz.timezone(event.timezone)
    local_datetime = tz.localize(naive_local_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    naive_utc_datetime = utc_datetime.replace(tzinfo=None)
    return naive_utc_datetime


class Map(ndb.Model):
    """ models the configuration data for a map
        The key contains the id of the map configuration """
    title = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    qr_code_string = ndb.TextProperty()
    commercial_limit = ndb.IntegerProperty()
    language = ndb.StringProperty()
    plan = ndb.StringProperty()
    help = ndb.TextProperty()
    latitude = ndb.FloatProperty()
    longitude = ndb.FloatProperty()
    zoom = ndb.IntegerProperty()


class Location(ndb.Model):
    """ models a predefined location """
    name = ndb.TextProperty()
    coordinates = ndb.GeoPtProperty()
    geohash = ndb.StringProperty()
    tile = ndb.StringProperty(repeated=True)
    map = ndb.KeyProperty(repeated=True, kind=Map)


class Instance(ndb.Model):
    date_time_slug = ndb.StringProperty()
    previous_start_utc = ndb.DateTimeProperty()
    start_local = ndb.DateTimeProperty()
    start_utc = ndb.DateTimeProperty()
    end_local = ndb.DateTimeProperty()
    end_utc = ndb.DateTimeProperty()


class Event(ndb.Model):
    """ models an event, including the recurring instances as a structured property
        The key contains the event slug """
    map = ndb.KeyProperty()
    start = ndb.DateTimeProperty()
    end = ndb.DateTimeProperty()
    calendar_rule = ndb.TextProperty()
    event_name = ndb.TextProperty()
    description = ndb.TextProperty()
    contact = ndb.TextProperty()
    website = ndb.TextProperty()
    registration_required = ndb.BooleanProperty()
    owner = ndb.StringProperty()
    moderator = ndb.StringProperty()
#    state = ndb.StringProperty()
#    update_after_sync = ndb.BooleanProperty()
    sync_date = ndb.DateTimeProperty()
    final_date = ndb.DateTimeProperty()
    location_name = ndb.TextProperty()
    address = ndb.TextProperty()
    postal_code = ndb.StringProperty()
    coordinates = ndb.GeoPtProperty()
    geohash = ndb.StringProperty()
    tile = ndb.StringProperty(repeated=True)
    location_slug = ndb.StringProperty()
    location_details = ndb.TextProperty()
    tags = ndb.StringProperty(repeated=True)
    hashtags = ndb.StringProperty(repeated=True)
    timezone = ndb.TextProperty()
    instances = ndb.StructuredProperty(Instance, repeated=True)


def update_instances(event):
    previous_start_utc = datetime.datetime.strptime("1970-01-01 00:00:00", DATE_TIME_FORMAT)
    # calculate the date occurrences
    if event.calendar_rule:
        # start field holds the start date for the recurrence rule
        # the start and end time are in the timezone of the event's location
        start_date = event.start.date()
        end_date = event.end.date()
        days = end_date - start_date
        today_date = datetime.datetime.today().date()
        if start_date <= today_date:
            start_date = today_date
        data = {
            'year': start_date.year,
            'month': start_date.month,
            'day': start_date.day,
            'rrule': event.calendar_rule,
            'format': DATE_FORMAT,
            'batch_size': 10,
            'start': 0
        }
        start = event.start.time()
        end = event.end.time()
        today_plus_13_months_date = today_date + datetime.timedelta(days=13*30)  # naive, don't care
        instances = []
        done = False
        final_date = datetime.datetime.strptime("1970-01-01 00:00:00", DATE_TIME_FORMAT)
        logging.info("Starting loop processing instances of event %s" % event.key.id())
        while True:
            occurrences = [o for o in calculate_occurrences(data)['occurrences'] if o['type'] != 'exdate']
            for occurrence in occurrences:
                start_date = datetime.datetime.strptime(occurrence['date'], ISO_DATE_TIME_FORMAT).date()
                start_local = datetime.datetime.combine(start_date, start)
                logging.info("Instance on %s" % start_local)
                end_local = datetime.datetime.combine(start_date + days, end)
                if today_date <= start_date < today_plus_13_months_date:
                    # only add events within one year timeframe from now
                    new_instance = model.Instance(
                        start_local=start_local,
                        start_utc=naive_local_datetime_to_naive_utc_datetime(
                            start_local,
                            event.coordinates.lat,
                            event.coordinates.lon,
                            event
                        ),
                        end_local=end_local,
                        end_utc=naive_local_datetime_to_naive_utc_datetime(
                            end_local,
                            event.coordinates.lat,
                            event.coordinates.lon,
                            event
                        ),
                        date_time_slug=slugify(start_local.strftime(DATE_TIME_FORMAT)),
                        previous_start_utc=previous_start_utc
                    )
                    previous_start_utc = new_instance.start_utc
                    if final_date < new_instance.end_utc:
                        final_date = new_instance.end_utc
                    instances.append(new_instance)
                else:
                    done = True
                    logging.info("Done processing instances of event %s" % event.key.id())
                    break  # for
            if occurrences and not done:
                data['start'] += data['batch_size']
            else:
                break  # while
        event.instances = instances
        event.final_date = final_date
    else:  # not recurring, can span multiple days
        logging.info("Creating non-recurring instance for event %s" % event.key.id())
        instance = model.Instance(
            start_local=event.start,
            start_utc=naive_local_datetime_to_naive_utc_datetime(
                event.start,
                event.coordinates.lat,
                event.coordinates.lon
            ),
            end_local=event.end,
            end_utc=naive_local_datetime_to_naive_utc_datetime(
                event.end,
                event.coordinates.lat,
                event.coordinates.lon
            ),
            date_time_slug=slugify(event.start.strftime(DATE_TIME_FORMAT)),
            previous_start_utc=previous_start_utc
        )
        event.instances = [instance]
        event.final_date = instance.end_utc
    event.sync_date = datetime.datetime.today()
    event.put()
    return
