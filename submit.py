import webapp2
import customer_configuration
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


FUSION_TABLE_DATE_TIME_FORMAT = fusion_tables.FUSION_TABLE_DATE_TIME_FORMAT

app_id = app_identity.get_application_id()


class NewHandler(BaseHandler):
    def post(self):
        configuration = customer_configuration.get_configuration(self.request)
        data = self.request.POST['data']
        master = json.loads(data)
        # check if the location is in use, if so, reuse it's location slug
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
        master['state'] = 'new'
        master['sequence'] = 1
        master['entry date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        master['update date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        master['renewal date'] = (datetime.today() + timedelta(days=30 * 6)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        base_event_slug = event_slug(master)
        master['event slug'] = base_event_slug
        # add (1) or (2) or etc... to the event slug if it's already in use
        while fusion_tables.select_first(configuration['master table'], condition="'event slug' = '%s'" % master['event slug']):
            counter = 1 if 'counter' not in locals() else counter + 1
            master['event slug'] = base_event_slug + '-(' + str(counter) + ')'
        # hashtags
        master['hashtags'] = ','.join(["#%s#" % slugify(tag) for tag in extract_hash_tags(master['description'])])
        fusion_tables.insert(configuration['master table'], master)
        sync.sync_new_events(configuration, condition="'event slug' = '%s'" % master['event slug'])
        logging.info("LIST_OF_ADDED_ROWS [%s] [%s] %s" % (configuration['id'], master['update date'], data))
        sender = 'info@%s.appspotmail.com' % (app_id)
        message = mail.EmailMessage(sender=sender, to="vicmortelmans+maptiming@gmail.com")
        message.subject = "New event added to MapTiming %s" % configuration['title']
        message.body = "http://%s.maptiming.com#event/%s" % (configuration['id'], master['event slug'])
        logging.info("Sending mail from %s: %s - %s" % (sender, message.subject, message.body))
        message.send()
        # return the web-page content
        self.response.out.write(master['event slug'])
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
