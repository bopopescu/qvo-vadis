from lib import BaseHandler
import datetime
import customer_map
import model
import json
import pytz
import logging
from google.appengine.ext import ndb


def datetime_serializer(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


class GeoJSONHandler(BaseHandler):
    """Returns a geojson dataset containing all events for a map on a specified geohash tile

    Parameters:
        tile: geohash id, must match one of the precisions as stored in the tile property of the Event model

    Returns:
        geojson dataset with custom attributes for easy filtering on the client
    """
    def get(self, tile):
        map = customer_map.get_map(self.request)
        # get all events on the active map for the specified tile
        events = ndb.gql("SELECT * FROM Event WHERE tile = :1 AND map = :2", tile, map.key)
        # setup a dict of events, with local timespots for each event (as events can be in different timezones)
        logging.info("Setup timespots dict")
        timespots_dict = {}
        naive_utc_now = datetime.datetime.today()
        utc_now = pytz.utc.localize(naive_utc_now)
        for e in events:
            timespots_dict[e.key.id()] = {}
            ts = timespots_dict[e.key.id()]
            local_now = utc_now.astimezone(pytz.timezone(e.timezone))
            ts["now"] = local_now.replace(tzinfo=None)
            ts["midnight"] = ts["now"].replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
            ts["midnight1"] = ts["midnight"] + datetime.timedelta(days=1)
            ts["midnight7"] = ts["midnight"] + datetime.timedelta(days=7)
        # get all instances on the active map for the specified tile, for the next 8 days
        instances = model.Instance.query(
            model.Instance.tile == tile,
            model.Instance.map == map.key,
            model.Instance.start_utc < naive_utc_now + datetime.timedelta(days=8)
        )
        # iterate all Instances setting up a dict of events, with boolean timeperiod flags for each event
        logging.info("Setup timeperiods dict")
        timeperiods_dict = {}
        for i in instances:
            if i.event_slug.id() not in timeperiods_dict:
                timeperiods_dict[i.event_slug.id()] = {
                    "is_now": False,
                    "is_today": False,
                    "is_tomorrow": False,
                    "is_this_week": False,
                    "passed": True
                }
            tp = timeperiods_dict[i.event_slug.id()]
            ts = timespots_dict[i.event_slug.id()]
            if i.end_local > ts["now"]:
                tp["passed"] = False
                if i.start_local < ts["midnight7"]:
                    tp["is_this_week"] = True
                    if i.start_local < ts["midnight1"] and i.end_local > ts["midnight"]:
                        tp["is_tomorrow"] = True
                    if i.start_local < ts["midnight"]:
                        tp["is_today"] = True
                        if i.start_local < ts["now"]:
                            tp["is_now"] = True
        # convert the results to GeoJSON
        logging.info("Generate geojson")
        features = []
        for e in events:
            logging.info("GeoJSONHandler adding event data to output for %s" % e.key)
            if e.key.id() not in timeperiods_dict:
                timeperiods_dict[e.key.id()] = {
                    "is_now": False,
                    "is_today": False,
                    "is_tomorrow": False,
                    "is_this_week": False,
                    "passed": True
                }
            tp = timeperiods_dict[e.key.id()]
            if not tp["passed"]:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [e.coordinates.lon, e.coordinates.lat]
                    },
                    "properties": {
                        "now": tp["is_now"],
                        "today": tp["is_today"],
                        "tomorrow": tp["is_tomorrow"],
                        "week": tp["is_this_week"],
                        "event slug": e.key.id(),
                        "location slug": e.location_slug,
                        "tags": e.tags,
                        "hashtags": e.hashtags
                    }
                })
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        # return the json dataset
        self.response.headers['Content-Type'] = 'application/json'
        # browser limits to 6 requests to same domain, by allowing dummmy subdomains, sharding is used to prevent queuing
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.out.write(json.dumps(feature_collection, default=datetime_serializer))
        return


class GeoJSONLocationsHandler(BaseHandler):
    """Returns a geojson dataset containing all predefined locations for a map

    Parameters: none (the map is implicit)

    Returns:
        geojson dataset with custom attribute name
    """
    def get(self):
        map = customer_map.get_map(self.request)
        # get all locations on the active map
        locations = ndb.gql("SELECT * FROM Location WHERE map = :1", map.key)
        # convert the results to GeoJSON
        logging.info("Generate geojson locations")
        features = []
        for e in locations:
            logging.info("GeoJSONLocationsHandler adding location data to output for %s" % e.key)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [e.coordinates.lon, e.coordinates.lat]
                },
                "properties": {
                    "name": e.name,
                    "predefined": "yes"
                }
            })
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        # return the json dataset
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(feature_collection, default=datetime_serializer))
        return


class GeoJSONSimpleHandler(BaseHandler):
    """Returns a geojson dataset containing all locations for a map

    Parameters: none (the map is implicit)

    Returns:
        geojson dataset with custom attribute location slug
    """
    def get(self):
        map = customer_map.get_map(self.request)
        # get all locations on the active map
        events = ndb.gql("SELECT DISTINCT location_slug, coordinates FROM Event WHERE map = :1", map.key)
        # convert the results to GeoJSON
        logging.info("Generate geojson simple")
        features = []
        for e in events:
            logging.info("GeoJSONSimpleHandler adding event data to output for %s" % e.key)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [e.coordinates.lon, e.coordinates.lat]
                },
                "properties": {
                    "location_slug": e.location_slug,
                    "predefined": "no"
                }
            })
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        # return the json dataset
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(feature_collection, default=datetime_serializer))
        return


class GeoJSONLocationHandler(BaseHandler):
    """Returns a geojson dataset containing the event for a location
        (if more than one event is stored, it takes the first that is returned)
        Used in the Editor to fetch data for a clicked event

    Parameters: location_slug

    Returns:
        geojson dataset with custom attributes address, location_name, postal_code
    """
    def get(self, location_slug):
        map = customer_map.get_map(self.request)
        # query for Event
        event = model.Event.query(model.Event.location_slug == location_slug, model.Event.map == map.key).fetch(1)[0]
        # convert the results to GeoJSON
        logging.info("Generate geojson simple")
        features = []
        logging.info("GeoJSONEventHandler adding event data to output for %s" % event.key)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [event.coordinates.lon, event.coordinates.lat]
            },
            "properties": {
                "address": event.address,
                "location_name": event.location_name,
                "postal_code": event.postal_code
            }
        })
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        # return the json dataset
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(feature_collection, default=datetime_serializer))
        return
