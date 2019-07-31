from google.appengine.ext import ndb
from lib import slugify
from recurrenceinput import calculate_occurrences
import datetime
import model
from google.appengine.api import urlfetch
import logging
import json
import pytz
from google.appengine.api.runtime import runtime
from google.appengine.ext import db
import time
import gc


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
        for attempt in range(10):
            try:
                logging.info("Fetching timezone info [%s]" % url)
                result = urlfetch.fetch(url)
                if result.status_code == 200 and 'dstOffset' in result.content:
                    timezone_json = result.content
                    event.timezone = json.loads(timezone_json)['timeZoneId']
                elif result.status_code == 200:
                    logging.exception("No timezone data returned when fetching url %s, taking Europe/Amsterdam as default" % url)
                    event.timezone = "Europe/Amsterdam"
                else:
                    logging.exception("HTTP error fetching url %s, going to retry" % url)
                    raise urlfetch.Error
            except (urlfetch.Error) as e:
                logging.warning("HttpError trying to query %s (%s)." % (url, e))
            else:
                break  # no error caught
        else:
            logging.critical("Retried 10 times querying %s." % url)
            return ''
            #raise  # attempts exhausted
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
    language = ndb.StringProperty()
    plan = ndb.StringProperty()
    help = ndb.TextProperty()
    latitude = ndb.FloatProperty()
    longitude = ndb.FloatProperty()
    zoom = ndb.IntegerProperty()

    def flush_events_and_instances(self):
        # delete all Event and Instance entities for this map configuration
        logging.info("Deleting all Event and Instance entities for map %s" % self.key.id())
        event_keys = Event.query(Event.map == self.key).fetch(keys_only=True)
        ndb.delete_multi(event_keys)
        instance_keys = Instance.query(Instance.map == self.key).fetch(keys_only=True)
        sleep = 10
        for attempt in range(10):
            try:
                ndb.delete_multi(instance_keys)
            except (db.TransactionFailedError, db.Timeout) as e:
                time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
                logging.warning("Sleeping %d seconds because of error trying to delete all instances in %s (%s)" % (sleep, self.key.id(), e))
                sleep = sleep * 2
            else:
                break  # no error caught
        else:
            logging.critical("Retried 10 times to delete all instances in %s" % self.key.id())
            raise  # attempts exhausted
        logging.info("Deleted all Event and Instance entities for map %s" % self.key.id())

    def flush_locations(self):
        # delete all predefined location for this map configuration
        logging.info("Deleting all predefined locations for map %s" % self.key.id())
        event_keys = Location.query(Location.map == self.key).fetch(keys_only=True)
        ndb.delete_multi(event_keys)
        logging.info("Deleted all predefined locations for map %s" % self.key.id())


class Location(ndb.Model):
    """ models a predefined location """
    name = ndb.TextProperty()
    coordinates = ndb.GeoPtProperty()
    geohash = ndb.StringProperty()
    tile = ndb.StringProperty(repeated=True)
    map = ndb.KeyProperty()


class Instance(ndb.Model):
    # instace slug is the key, composed of event slug + datetime slug
    date_time_slug = ndb.StringProperty()
    event_slug = ndb.KeyProperty()  # key of the Event entity
    location_slug = ndb.StringProperty()
    map = ndb.KeyProperty()
    tile = ndb.StringProperty(repeated=True)  # stores multiple precisions of geohashes, currently 2, 3, 4 and 5
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
    tile = ndb.StringProperty(repeated=True)  # stores multiple precisions of geohashes, currently 2, 3, 4 and 5
    location_slug = ndb.StringProperty()
    location_details = ndb.TextProperty()
    tags = ndb.StringProperty(repeated=True)
    hashtags = ndb.StringProperty(repeated=True)
    timezone = ndb.StringProperty()
#    instances = ndb.StructuredProperty(Instance, repeated=True)

    def generate_and_store_instances(self, start_from_final_date=False):
        previous_start_utc = datetime.datetime.strptime("1970-01-01 00:00:00", DATE_TIME_FORMAT)
        # calculate the date occurrences
        if self.calendar_rule:
            # start field holds the start date for the recurrence rule
            # the start and end time are in the timezone of the event's location
            today_date = datetime.datetime.today().date()
            start_date = self.start.date()
            end_date = self.end.date()
            days = end_date - start_date
            if start_from_final_date:
                final_date = self.final_date
                if start_date <= final_date.date():
                    start_date = final_date.date()
            else:
                final_date = datetime.datetime.strptime("1970-01-01 00:00:00", DATE_TIME_FORMAT)
                if start_date <= today_date:
                    start_date = today_date
            data = {
                'year': start_date.year,
                'month': start_date.month,
                'day': start_date.day,
                'rrule': self.calendar_rule,
                'format': DATE_FORMAT,
                'batch_size': 10,
                'start': 0
            }
            start = self.start.time()
            end = self.end.time()
            today_plus_13_months_date = today_date + datetime.timedelta(days=13*30)  # naive, don't care
            done = False
            logging.info("Starting loop processing instances of event %s" % self.key.id())
            while True:
                occurrences = [o for o in calculate_occurrences(data)['occurrences'] if o['type'] != 'exdate']
                for occurrence in occurrences:
                    start_date = datetime.datetime.strptime(occurrence['date'], ISO_DATE_TIME_FORMAT).date()
                    start_local = datetime.datetime.combine(start_date, start)
                    logging.info("Instance on %s" % start_local)
                    #logging.info(runtime.memory_usage())
                    end_local = datetime.datetime.combine(start_date + days, end)
                    date_time_slug = slugify(start_local.strftime(DATE_TIME_FORMAT))
                    if today_date <= start_date < today_plus_13_months_date:
                        # only add events within one year timeframe from now
                        instance = model.Instance(
                            id=self.key.id() + '-' + date_time_slug,
                            date_time_slug=date_time_slug,
                            event_slug=self.key,
                            location_slug=self.location_slug,
                            map=self.map,
                            tile=self.tile,
                            start_local=start_local,
                            start_utc=naive_local_datetime_to_naive_utc_datetime(
                                start_local,
                                self.coordinates.lat,
                                self.coordinates.lon,
                                self
                            ),
                            end_local=end_local,
                            end_utc=naive_local_datetime_to_naive_utc_datetime(
                                end_local,
                                self.coordinates.lat,
                                self.coordinates.lon,
                                self
                            ),
                            previous_start_utc=previous_start_utc
                        )
                        previous_start_utc = instance.start_utc
                        if final_date < instance.end_utc:
                            final_date = instance.end_utc
                        sleep = 10
                        for attempt in range(10):
                            try:
                                instance.put()
                            except (db.TransactionFailedError, db.Timeout) as e:
                                time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
                                logging.warning("Sleeping %d seconds because of error trying to put instance %s (%s)" % (sleep, instance.key.id(), e))
                                sleep = sleep * 2
                            else:
                                break  # no error caught
                        else:
                            logging.critical("Retried 10 times to put instance %s" % instance.key.id())
                            raise  # attempts exhausted
                    else:
                        done = True
                        logging.info("Done processing instances of event %s" % self.key.id())
                        break  # for
                if occurrences and not done:
                    data['start'] += data['batch_size']
                else:
                    break  # while
            self.final_date = final_date
        elif not start_from_final_date:
            # not recurring, can span multiple days; if start_from_final_date, assume it's already created
            logging.info("Creating non-recurring instance for event %s" % self.key.id())
            date_time_slug = slugify(self.start.strftime(DATE_TIME_FORMAT))
            instance = model.Instance(
                id=self.key.id() + '-' + date_time_slug,
                date_time_slug=date_time_slug,
                event_slug=self.key,
                location_slug=self.location_slug,
                map=self.map,
                tile=self.tile,
                start_local=self.start,
                start_utc=naive_local_datetime_to_naive_utc_datetime(
                    self.start,
                    self.coordinates.lat,
                    self.coordinates.lon
                ),
                end_local=self.end,
                end_utc=naive_local_datetime_to_naive_utc_datetime(
                    self.end,
                    self.coordinates.lat,
                    self.coordinates.lon
                ),
                previous_start_utc=previous_start_utc
            )
            instance.put()
            self.final_date = instance.end_utc
        self.sync_date = datetime.datetime.today()
        self.put()
        # creating all the instances seems to consume a lot of memory
        context = ndb.get_context()
        context.clear_cache()
        gc.collect()
        return


