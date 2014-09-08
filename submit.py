import webapp2
import customer_configuration
import logging
from lib import slugify, get_localization, location_slug, event_slug, extract_hash_tags, BaseHandler
import json
import sync
import fusion_tables
from datetime import datetime
from datetime import timedelta
from google.appengine.api import mail
import os


FUSION_TABLE_DATE_TIME_FORMAT = fusion_tables.FUSION_TABLE_DATE_TIME_FORMAT

app_id = os.environ.get('APPLICATION_ID')


class NewHandler(BaseHandler):
    def post(self):
        configuration = customer_configuration.get_configuration(self.request)
        localization = get_localization()
        data = self.request.POST['data']
        master = json.loads(data)
        # check if the location is in use, if so, reuse it's location slug
        same_location_condition = "ST_INTERSECTS('latitude', CIRCLE(LATLNG(%f,%f),2))" % (round(float(master['latitude']), 5), round(float(master['longitude']), 5))  # 3 meter
        same_location = fusion_tables.select_first(configuration['master table'], condition=same_location_condition)
        if same_location:
            master['location slug'] = same_location[0]['location slug']
        else:
            master['location slug'] = location_slug(master)
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
        master['location slug'] = original_master['location slug']
        master['state'] = 'updated'
        master['sequence'] = int(original_master['sequence']) + 1
        master['entry date'] = original_master['entry date']
        master['update date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        master['update after sync'] = 'true'
        master['renewal date'] = (datetime.today() + timedelta(days=30 * 6)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        master['event slug'] = original_master['event slug']
        master['hashtags'] = ','.join(["#%s#" % slugify(tag) for tag in extract_hash_tags(master['description'])])
        master['rowid'] = original_master['rowid']
        fusion_tables.update_with_implicit_rowid(configuration['master table'], master)
        sync.sync_updated_events(configuration, condition="'event slug' = '%s'" % master['event slug'])
        logging.info("LIST_OF_UPDATED_ROWS [%s] [%s] %s" % (configuration['id'], master['update date'], data))
        sender = 'info@%s.appspotmail.com' % (app_id)
        message = mail.EmailMessage(sender=sender, to="vicmortelmans+maptiming@gmail.com")
        message.subject = "Event updated in MapTiming %s" % configuration['title']
        message.body = "http://%s.maptiming.com#event/%s" % (configuration['id'], master['event slug'])
        message.send()
        # return the web-page content
        self.response.out.write(master['event slug'])
        return
