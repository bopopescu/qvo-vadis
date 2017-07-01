import webapp2
from jinja_templates import jinja_environment
import customer_configuration
import logging
import datetime
import fusion_tables
from lib import get_localization, get_language, BaseHandler
import json

DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class LocationHandler(BaseHandler):
    def get(self, location_slug=None, timeframe=None, tags=None, hashtags=None):
        now = self.request.get("now")
        if not now:
            now = datetime.datetime.strftime(datetime.datetime.now(), DATE_TIME_FORMAT)  # fallback to server time
        configuration = customer_configuration.get_configuration(self.request)
        localization = get_localization()
        # detect language and use configuration as default
        language = get_language(self.request, configuration)
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
            localization=localization[language]
        )

        # return the web-page content
        self.response.out.write(content)
        return


class EventHandler(BaseHandler):
    def get(self, event_slug=None, datetime_slug=None):
        configuration = customer_configuration.get_configuration(self.request)
        # detect language and use configuration as default
        language = get_language(self.request, configuration)
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
        data = data[0] if data else {}
        # if data has no address, fetch it
        if not data['address']:
            data['address'] = address(data['latitude'], data['longitude'], language)
        template = jinja_environment.get_template('event.html')
        content = template.render(
            configuration=configuration,
            data=data,
            date_time_reformat=date_time_reformat,
            date_time_reformat_iso=date_time_reformat_iso,
            no_results_message=no_results_message,
            localization=localization[language]
        )
        # return the web-page content
        self.response.out.write(content)
        return


class LocationsHandler(BaseHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        # detect language and use configuration as default
        language = get_language(self.request, configuration)
        localization = get_localization()
        offset = self.request.get("offset")
        condition = "'state' = 'public'"
        # apply commercial limit
        limit = customer_configuration.get_limit(self.request)
        if limit:
            condition += " AND 'start' < '%s'" % limit

        if offset:
            condition += " OFFSET %s" % offset

        # at least for debugging, limit to 100 results
        condition += " LIMIT 100"
        no_results_message = ''
        data = fusion_tables.select(configuration['master table'], condition=condition)
        if not data:
            no_results_message = localization[configuration['language']]['no-results']
        # remove duplicates
        unique_data = []
        location_slugs = []
        for d in data:
            location_slug = d['location slug']
            if location_slug not in location_slugs:
                unique_data.append(d)
                location_slugs.append(location_slug)
        next_url = self.request.path_url + "?offset=%s" % str(int(offset if offset else 0) + 100)
        # for debugging, the id must be added to an url as parameter
        id_appendix = ""
        if self.request.get("id"):
            id_appendix = "?id=%s" % self.request.get("id")
            next_url += "&id=%s" % self.request.get("id")
        template = jinja_environment.get_template('locations.html')
        content = template.render(
            configuration=configuration,
            data=unique_data,
            date_time_reformat=date_time_reformat,
            no_results_message=no_results_message,
            localization=localization[language],
            id_appendix=id_appendix,
            offset=offset,
            next_url=next_url
        )
        # return the web-page content
        self.response.out.write(content)
        return



class GeoJSONHandler(BaseHandler):
    def get(self):
        now = self.request.get("now")
        if not now:
            now = datetime.datetime.strftime(datetime.datetime.now(), DATE_TIME_FORMAT)  # fallback to server time
        condition = "'previous start' <= '" + now + "' and 'end' >= '" + now + "'"
        cols = ['datetime slug', 'event slug', 'sequence', 'latitude', 'longitude', 'location slug', 'tags', 'hashtags']
        configuration = customer_configuration.get_configuration(self.request)
        # query on event
        data = fusion_tables.select(configuration['slave table'], condition=condition, cols=cols)
        # convert the results to GeoJSON
        features = []
        for row in data:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['longitude'], row['latitude']]
                },
                "properties": {
                    "datetime slug": row['datetime slug'],
                    "event slug": row['event slug'],
                    "sequence": row['sequence'],
                    "location slug": row['location slug'],
                    "tags": row['tags'],
                    "hashtags": row['hashtags']
                }
            })
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        # return the web-page content
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(feature_collection))
        return


class SitemapByLocationHandler(BaseHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        location = self.request.get("location")
        condition = "'sequence' > 0"
        # apply commercial limit
        limit = customer_configuration.get_limit(self.request)
        if limit:
            condition += " AND 'start' < '%s'" % limit
        if location:
            condition += " AND 'location slug' = '%s'" % location
        condition += " ORDER BY 'datetime slug'"
        no_results_message = ''
        data = fusion_tables.select(configuration['slave table'], condition=condition, cols=[
            'event slug',
            'datetime slug',
            'sequence',
            'start'
        ])
        if not data:
            no_results_message = '# No results'
        template = jinja_environment.get_template('sitemap.txt')
        content = template.render(
            configuration=configuration,
            data=data,
            no_results_message=no_results_message
        )
        # return the web-page content
        self.response.headers['Content-Type'] = "text/plain"
        self.response.out.write(content)
        return


class SitemapHandler(BaseHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        offset = self.request.get("offset")
        batch = self.request.get("batch")
        condition = "'sequence' > 0"
        # apply commercial limit
        limit = customer_configuration.get_limit(self.request)
        if limit:
            condition += " AND 'start' < '%s'" % limit
        if offset:
            condition += " OFFSET %s" % offset
        # at least for debugging, limit to 100 results
        if batch:
            condition += " LIMIT %s" % batch
        no_results_message = ''
        data = fusion_tables.select(configuration['slave table'], condition=condition, cols=[
            'event slug',
            'datetime slug',
            'sequence',
            'start'
        ])
        if not data:
            no_results_message = '# No results'
        template = jinja_environment.get_template('sitemap.txt')
        content = template.render(
            configuration=configuration,
            data=data,
            no_results_message=no_results_message
        )
        # return the web-page content
        self.response.headers['Content-Type'] = "text/plain"
        self.response.out.write(content)
        return


class IndexByLocationHandler(BaseHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        count = fusion_tables.count(configuration['slave table'])
        template = jinja_environment.get_template('sitemapindexbylocation.xml')
        # get a list of all locations (location slug)
        condition = "'sequence' > 0"
        # apply commercial limit
        limit = customer_configuration.get_limit(self.request)
        if limit:
            condition += " AND 'start' < '%s'" % limit
        condition += " GROUP BY 'location slug'"
        no_results_message = ''
        locations = fusion_tables.select(configuration['slave table'], condition=condition, cols=[
            'location slug'
        ])
        if not locations:
            no_results_message = '# No results'
        content = template.render(
            configuration=configuration,
            locations=locations
        )
        # return the web-page content
        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(content)
        return


class IndexHandler(BaseHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        count = fusion_tables.count(configuration['slave table'])
        template = jinja_environment.get_template('sitemapindex.xml')
        # render the series of offsets
        batch = 1000
        offsets = [0]
        while offsets[-1] < count - batch:
            offsets.append(offsets[-1] + batch)
        content = template.render(
            configuration=configuration,
            batch=batch,
            offsets=offsets
        )
        # return the web-page content
        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(content)
        return


def date_time_reformat(date, format='full', lang='en'):
    from babel.dates import format_date, format_datetime, format_time
    date_p = datetime.datetime.strptime(date, DATE_TIME_FORMAT)
    return format_datetime(date_p, format=format, locale=lang)


from google.appengine.ext import ndb
from google.appengine.api import urlfetch


def date_time_reformat_iso(date, latitude, longitude):
    # caching timezone doesn't make much sense, because it will depend on the actual date because of daylight saving
    date_p = datetime.datetime.strptime(date, DATE_TIME_FORMAT)
    key = "%.4f,%.4f" % (latitude, longitude)
    api_key = "AIzaSyAObYcVpywvDwFBZqDxU6PIRvVji9vM9TQ"
    timestamp = (date_p - datetime.datetime(1970, 1, 1)).total_seconds()  # actually shouldn't do this, because date_p isn't UTC
    url = "https://maps.googleapis.com/maps/api/timezone/json?location=%.6f,%.6f&timestamp=%d&key=%s" % (latitude, longitude, timestamp, api_key)
    try:
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            timezone_json = result.content
        else:
            logging.exception("HTTP error fetching url %s" % url)
            timezone_json = ''
    except urlfetch.Error:
        logging.exception("Caught exception fetching url %s" % url)
    timezone = json.loads(timezone_json)
    (offset_hours, offset_minutes) = divmod((timezone["dstOffset"] + timezone["rawOffset"]) / 60, 60)
    iso = date_p.isoformat() + '+' + "%02d:%02d" % (offset_hours, offset_minutes)
    return iso


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
