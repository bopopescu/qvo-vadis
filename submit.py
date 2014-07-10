import webapp2
import customer_configuration
import logging
from lib import slugify, get_localization, location_slug, event_slug, extract_hash_tags
import json
import sync
import fusion_tables
from datetime import datetime
from datetime import timedelta



FUSION_TABLE_DATE_TIME_FORMAT = fusion_tables.FUSION_TABLE_DATE_TIME_FORMAT


logging.basicConfig(level=logging.INFO)


class NewHandler(webapp2.RequestHandler):
    def post(self, edit_mode='new'):
        configuration = customer_configuration.get_configuration(self.request)
        localization = get_localization()
        data = self.request.POST['data']
        master = json.loads(data)
        # location slug
        master['location slug'] = location_slug(master)
        # entry date
        master['entry date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        # update date
        master['update date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        # renewal date
        master['renewal date'] = (datetime.today() + timedelta(days=30 * 6)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        # event slug
        base_event_slug = event_slug(master)
        master['event slug'] = base_event_slug
        while fusion_tables.select_first(configuration['master table'], condition="'event slug' = '%s'" % master['event slug']):
            counter = 1 if 'counter' not in locals() else counter + 1
            master['event slug'] = base_event_slug + '-(' + str(counter) + ')'
        # hashtags
        master['hashtags'] = ','.join(["#%s#" % slugify(tag) for tag in extract_hash_tags(master['description'])])
        fusion_tables.insert(configuration['master table'], master)
        sync.sync_new_events(configuration, condition="'event slug' = '%s'" % master['event slug'])
        # return the web-page content
        self.response.out.write(master['event slug'])
        return
