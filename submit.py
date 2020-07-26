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
        main = json.loads(data)
        # check if the location is in use, if so, reuse it's location slug
        same_location_condition = "ST_INTERSECTS('latitude', CIRCLE(LATLNG(%f,%f),2))" % (round(float(main['latitude']), 5), round(float(main['longitude']), 5))  # 3 meter
        same_location = fusion_tables.select_first(configuration['main table'], condition=same_location_condition)
        if same_location:
            logging.info("Using the location slug of an existing location [%s] instead of [%s]" % (same_location[0]['location slug'], main['location slug']))
            main['location slug'] = same_location[0]['location slug']
        else:
            base_location_slug = location_slug(main)
            logging.info("This is a new location [%s]" % base_location_slug)
            main['location slug'] = base_location_slug
            # add (1) or (2) or etc... to the location slug if it's already in use
            while fusion_tables.select_first(configuration['main table'], condition="'location slug' = '%s'" % main['location slug']):
                logging.info("Adding (1), (2),... to location slug [%s] because it already existed." % main['location slug'])
                counter = 1 if 'counter' not in locals() else counter + 1
                main['location slug'] = base_location_slug + '-(' + str(counter) + ')'
        main['state'] = 'new'
        main['sequence'] = 1
        main['entry date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        main['update date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        main['renewal date'] = (datetime.today() + timedelta(days=30 * 6)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        base_event_slug = event_slug(main)
        main['event slug'] = base_event_slug
        # add (1) or (2) or etc... to the event slug if it's already in use
        while fusion_tables.select_first(configuration['main table'], condition="'event slug' = '%s'" % main['event slug']):
            counter = 1 if 'counter' not in locals() else counter + 1
            main['event slug'] = base_event_slug + '-(' + str(counter) + ')'
        # hashtags
        main['hashtags'] = ','.join(["#%s#" % slugify(tag) for tag in extract_hash_tags(main['description'])])
        fusion_tables.insert(configuration['main table'], main)
        sync.sync_new_events(configuration, condition="'event slug' = '%s'" % main['event slug'])
        logging.info("LIST_OF_ADDED_ROWS [%s] [%s] %s" % (configuration['id'], main['update date'], data))
        sender = 'info@%s.appspotmail.com' % (app_id)
        message = mail.EmailMessage(sender=sender, to="vicmortelmans+maptiming@gmail.com")
        message.subject = "New event added to MapTiming %s" % configuration['title']
        message.body = "http://%s.maptiming.com#event/%s" % (configuration['id'], main['event slug'])
        logging.info("Sending mail from %s: %s - %s" % (sender, message.subject, message.body))
        message.send()
        # return the web-page content
        self.response.out.write(main['event slug'])
        return


class UpdateHandler(BaseHandler):
    def post(self, event_slug=None):
        configuration = customer_configuration.get_configuration(self.request)
        original_main = fusion_tables.select_first(configuration['main table'], condition="'event slug' = '%s'" % event_slug)[0]
        data = self.request.POST['data']
        main = json.loads(data)
        main['location slug'] = location_slug(main)
        # check if the new location is in use, if so, reuse it's location slug
        same_location_condition = "ST_INTERSECTS('latitude', CIRCLE(LATLNG(%f,%f),2))" % (round(float(main['latitude']), 5), round(float(main['longitude']), 5))  # 3 meter
        same_location = fusion_tables.select_first(configuration['main table'], condition=same_location_condition)
        if same_location:
            logging.info("Using the location slug of an existing location [%s] instead of [%s]" % (same_location[0]['location slug'], main['location slug']))
            main['location slug'] = same_location[0]['location slug']
        else:
            base_location_slug = location_slug(main)
            logging.info("This is a new location [%s]" % base_location_slug)
            main['location slug'] = base_location_slug
            # add (1) or (2) or etc... to the location slug if it's already in use
            while fusion_tables.select_first(configuration['main table'], condition="'location slug' = '%s'" % main['location slug']):
                logging.info("Adding (1), (2),... to location slug [%s] because it already existed." % main['location slug'])
                counter = 1 if 'counter' not in locals() else counter + 1
                main['location slug'] = base_location_slug + '-(' + str(counter) + ')'
        if main['location slug'] != original_main['location slug']:
            # otherwise the old location and event remains visible because the FT layer cannot filter them out
            logging.info("Starting task on queue for deleting old versions of moved event %s" % original_main['event slug'])
            taskqueue.add(method="GET", url='/sync/old_version_of_updated_events/%s?id=%s' % (original_main['event slug'], configuration['id']))
        main['state'] = 'updated'
        main['sequence'] = int(original_main['sequence']) + 1
        main['entry date'] = original_main['entry date']
        main['update date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        main['update after sync'] = 'true'  # this will trigger sync_old_version_of_updated_events()
        main['renewal date'] = (datetime.today() + timedelta(days=30 * 6)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        main['event slug'] = original_main['event slug']
        main['hashtags'] = ','.join(["#%s#" % slugify(tag) for tag in extract_hash_tags(main['description'])])
        main['rowid'] = original_main['rowid']
        fusion_tables.update_with_implicit_rowid(configuration['main table'], main)
        sync.sync_updated_events(configuration, condition="'event slug' = '%s'" % main['event slug'])
        logging.info("LIST_OF_UPDATED_ROWS [%s] [%s] %s" % (configuration['id'], main['update date'], data))
        sender = 'info@%s.appspotmail.com' % (app_id)
        message = mail.EmailMessage(sender=sender, to="vicmortelmans@gmail.com")
        message.subject = "Event updated in MapTiming %s" % configuration['title']
        message.body = "http://%s.maptiming.com#event/%s" % (configuration['id'], main['event slug'])
        logging.info("Sending mail from %s: %s - %s" % (sender, message.subject, message.body))
        message.send()
        # return the web-page content
        self.response.out.write(main['event slug'])
        return
