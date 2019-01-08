from lib import BaseHandler
import datetime
import customer_map
import model
import json


def datetime_serializer(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


class GeoJSONHandler(BaseHandler):
    def get(self, tile):
        map = customer_map.get_map(self.request)
        # query on event
        events = model.Event.query(model.Event.tile == tile)
        # convert the results to GeoJSON
        features = []
        for row in events:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row.coordinates.lon, row.coordinates.lat]
                },
                "properties": {
                    "instances": [i.to_dict() for i in row.instances],
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
        # return the web-page content
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(feature_collection, default=datetime_serializer))
        return


