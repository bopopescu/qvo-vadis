import webapp2
import customer_map
import logging
from lib import slugify, location_slug, event_slug, extract_hash_tags, BaseHandler
import json
import sync
import fusion_tables
from datetime import datetime
from datetime import timedelta
from google.appengine.api import mail, app_identity
import os
from google.appengine.api import taskqueue
import model
import Geohash
from google.appengine.api.datastore_types import GeoPt
from lib import isfloat, fusion_datetime_string_to_naive_datetime_object


FUSION_TABLE_DATE_TIME_FORMAT = fusion_tables.FUSION_TABLE_DATE_TIME_FORMAT

app_id = app_identity.get_application_id()


class NewHandler(BaseHandler):
    def post(self):
        map = customer_map.get_map(self.request)
        data = json.loads(self.request.POST['data'])
        # set data['geohash', 'coordinates', 'location_slug', 'tile']
        # check if the location is in use, if so, reuse it's location slug
        geohash = Geohash.encode(float(data['latitude']), float(data['longitude']), precision=10)
        same_location_event_list = model.Event.query(model.Event.tile == geohash[:7], model.Event.map == map.key).fetch(1)  # there shouldn't be more than one, in principle
        if same_location_event_list:
            same_location_event = same_location_event_list[0]
            logging.info("Using the geohash of an existing location [%s]: [%s] instead of [%s]" % (same_location_event.location_slug, same_location_event.geohash, geohash))
            data['geohash'] = same_location_event.geohash
            data['coordinates'] = same_location_event.coordinates
            data['location_slug'] = same_location_event.location_slug
            data['tile'] = same_location_event.tile
        else:
            base_location_slug = location_slug(location_name=data['location_name'], address=data['address'], postal_code=data['postal_code'])
            logging.info("This is a new location [%s]" % base_location_slug)
            data['location_slug'] = base_location_slug
            # add (1) or (2) or etc... to the location slug if it's already in use
            while model.Event.query(model.Event.location_slug == data['location_slug'], model.Event.map == map.key).fetch(1):
                logging.info("Adding (1), (2),... to location slug [%s] because it already existed." % data['location slug'])
                counter = 1 if 'counter' not in locals() else counter + 1
                data['location_slug'] = base_location_slug + '-(' + str(counter) + ')'
            data['geohash'] = geohash
            data['coordinates'] = GeoPt(data['latitude'], data['longitude'])
            data['tile'] = [
                geohash[:2],
                geohash[:3],
                geohash[:4],
                geohash[:5],
                geohash[:6],
                geohash[:7],
                geohash[:8],
                geohash[:9]
            ]
        # set data['event_slug']
        base_event_slug = event_slug(event_name=data['event_name'], location_slug=data['location_slug'])
        logging.info("This is a new event [%s]" % base_event_slug)
        data['event_slug'] = base_event_slug
        # add (1) or (2) or etc... to the location slug if it's already in use
        while model.Event.get_by_id(data['event_slug']):  # event_slug is unique over all maps !
            logging.info("Adding (1), (2),... to event slug [%s] because it already existed." % data['event_slug'])
            counter = 1 if 'counter' not in locals() else counter + 1
            data['event_slug'] = base_event_slug + '-(' + str(counter) + ')'
        # set data['hashtags']
        data['hashtags'] = extract_hash_tags(data['description'])
        # create the Event instance based on the data
        event = model.Event(
            id=data['event_slug'],
            map=map.key,
            start=fusion_datetime_string_to_naive_datetime_object(data['start']),
            end=fusion_datetime_string_to_naive_datetime_object(data['end']),
            calendar_rule=data['calendar_rule'],
            event_name=data['event_name'],
            description=data['description'],
            contact=data['contact'],
            website=data['website'],
            registration_required=True if data['registration_required'] == 'true' else False,
            location_name=data['location_name'],
            address=data['address'],
            postal_code=data['postal_code'],
            coordinates=data['coordinates'],
            geohash=data['geohash'],
            tile=data['tile'],
            location_slug=data['location_slug'],
            location_details=data['location_details'],
            tags=[tag.replace('#','') for tag in data['tags'].split(',')],
            hashtags=data['hashtags']
            # timezone is set during syncing
        )
        event.generate_and_store_instances()  # this also puts the event to the datastore
        sender = 'info@%s.appspotmail.com' % (app_id)
        message = mail.EmailMessage(sender=sender, to="vicmortelmans+maptiming@gmail.com")
        message.subject = "New event added to MapTiming %s (datastore)" % map.title
        message.body = "http://%s.maptiming.com#event/%s" % (map.key.id(), data['event_slug'])
        logging.info("Sending mail from %s: %s - %s" % (sender, message.subject, message.body))
        message.send()
        # return the web-page content
        self.response.out.write(data['event_slug'])
        return


class UpdateHandler(BaseHandler):
    def post(self, event_slug=None):
        configuration = customer_configuration.get_configuration(self.request)
        original_master = fusion_tables.select_first(configuration['master table'], condition="'event slug' = '%s'" % event_slug)[0]
        data = self.request.POST['data']
        master = json.loads(data)
        master['location slug'] = location_slug(master)
        # check if the new location is in use, if so, reuse it's location slug
        same_location_condition = "ST_INTERSECTS('latitude', CIRCLE(LATLNG(%f,%f),2))" % (round(float(master['latitude']), 5), round(float(master['longitude']), 5))  # 3 meter
        same_location = fusion_tables.select_first(configuration['master table'], condition=same_location_condition)
        if same_location:
            logging.info("Using the location slug of an existing location [%s] instead of [%s]" % (same_location[0]['location slug'], master['location slug']))
            master['location slug'] = same_location[0]['location slug']
        else:
            base_location_slug = location_slug(master)
            logging.info("This is a new location [%s]" % base_location_slug)
            master['location slug'] = base_location_slug
            # add (1) or (2) or etc... to the location slug if it's already in use
            while fusion_tables.select_first(configuration['master table'], condition="'location slug' = '%s'" % master['location slug']):
                logging.info("Adding (1), (2),... to location slug [%s] because it already existed." % master['location slug'])
                counter = 1 if 'counter' not in locals() else counter + 1
                master['location slug'] = base_location_slug + '-(' + str(counter) + ')'
        if master['location slug'] != original_master['location slug']:
            # otherwise the old location and event remains visible because the FT layer cannot filter them out
            logging.info("Starting task on queue for deleting old versions of moved event %s" % original_master['event slug'])
            taskqueue.add(method="GET", url='/sync/old_version_of_updated_events/%s?id=%s' % (original_master['event slug'], configuration['id']))
        master['state'] = 'updated'
        master['sequence'] = int(original_master['sequence']) + 1
        master['entry date'] = original_master['entry date']
        master['update date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        master['update after sync'] = 'true'  # this will trigger sync_old_version_of_updated_events()
        master['renewal date'] = (datetime.today() + timedelta(days=30 * 6)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        master['event slug'] = original_master['event slug']
        master['hashtags'] = ','.join(["#%s#" % slugify(tag) for tag in extract_hash_tags(master['description'])])
        master['rowid'] = original_master['rowid']
        fusion_tables.update_with_implicit_rowid(configuration['master table'], master)
        sync.sync_updated_events(configuration, condition="'event slug' = '%s'" % master['event slug'])
        logging.info("LIST_OF_UPDATED_ROWS [%s] [%s] %s" % (configuration['id'], master['update date'], data))
        sender = 'info@%s.appspotmail.com' % (app_id)
        message = mail.EmailMessage(sender=sender, to="vicmortelmans@gmail.com")
        message.subject = "Event updated in MapTiming %s" % configuration['title']
        message.body = "http://%s.maptiming.com#event/%s" % (configuration['id'], master['event slug'])
        logging.info("Sending mail from %s: %s - %s" % (sender, message.subject, message.body))
        message.send()
        # return the web-page content
        self.response.out.write(master['event slug'])
        return
