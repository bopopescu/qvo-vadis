from lib import BaseHandler
import datetime
import customer_map
import model
import json
import pytz


def datetime_serializer(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


class GeoJSONHandler(BaseHandler):
    """Returns a geojson dataset containing all events on a specified geohash tile

    Parameters:
        tile: geohash id, must match one of the precisions as stored in the tile property of the Event model

    Returns:
        geojson dataset with custom attributes for easy filtering on the client
    """
    def get(self, tile):
        map = customer_map.get_map(self.request)
        # query on event
        events = model.Event.query(model.Event.tile == tile)
        # convert the results to GeoJSON
        features = []
        for row in events:
            naive_utc_now = datetime.datetime.today()
            utc_now = pytz.utc.localize(naive_utc_now)
            local_now = utc_now.astimezone(pytz.timezone(row.timezone))
            now = local_now.replace(tzinfo=None)
            midnight = now.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
            midnight1 = midnight + datetime.timedelta(days=1)
            midnight7 = midnight + datetime.timedelta(days=7)
            is_now = False
            is_today = False
            is_tomorrow = False
            is_this_week = False
            for i in row.instances:
                if i.start_local < now and i.end_local > now:
                    is_now = True
                if i.start_local < midnight and i.end_local > now:
                    is_today = True
                if i.start_local < midnight1 and i.end_local > midnight:
                    is_tomorrow = True
                if i.start_local < midnight7 and i.end_local > now:
                    is_this_week = True
                if i.start_local > midnight7:
                    # all following intances will be later
                    break
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row.coordinates.lon, row.coordinates.lat]
                },
                "properties": {
                    "now": is_now,
                    "today": is_today,
                    "tomorrow": is_tomorrow,
                    "week": is_this_week,
                    "event slug": row.key.id(),
                    "location slug": row.location_slug,
                    "tags": row.tags,
                    "hashtags": row.hashtags
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


