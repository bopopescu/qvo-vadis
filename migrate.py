import model
import webapp2
import customer_configuration
from lib import get_localization, get_language, BaseHandler
import fusion_tables
import logging
import datetime
import pytz
from google.appengine.api.datastore_types import GeoPt
import Geohash
from google.appengine.ext import ndb


def fusion_datetime_string_to_naive_datetime_object(fusion):
    """ conversion assuming that the fusion datetime string is in Europe/Brussels timezone """
    naive_datetime = datetime.datetime.strptime(fusion, '%Y-%m-%d %H:%M:%S')
    return naive_datetime


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


class MigrateConfigurationHandler(BaseHandler):
    def get(self):
        configurations = fusion_tables.select(customer_configuration.CONFIGURATION_TABLE_ID)
        if not configurations:
            raise webapp2.abort(404)
        for row in configurations:
            map = model.Map(
                id=row['id'],
                title=row['title'],
                tags=row['tags'].split(','),
                qr_code_string=row['qr code string'],
                language=row['language'],
                plan=row['plan'],
                help=row['help'],
                latitude=float(row['latitude']) if isfloat(row['latitude']) else None,
                longitude=float(row['longitude']) if isfloat(row['longitude']) else None,
                zoom=int(row['zoom']) if row['zoom'].isdigit() else None
            )
            map.put()
        # return the web-page content
        self.response.out.write("Migrated configurations")
        return


class MigrateLocationsHandler(BaseHandler):
    def get(self):
        # get the data from the fusion table
        configuration = customer_configuration.get_configuration(self.request)
        data = fusion_tables.select(configuration['predefined locations table'])
        if not data:
            logging.error("No predefined locations found for configuration (%s)" % configuration['id'])
            raise webapp2.abort(404)
        # flush the data from the datastore
        model.Map.get_by_id(configuration['id']).flush_locations()
        # transfer the data to the datastore
        for row in data:
            if row['latitude']:  # some rows in the fusion table have empty coordinate values
                location = model.Location(
                    map=ndb.Key(model.Map, configuration['id']),
                    name=row['name'],
                    coordinates=GeoPt(row['latitude'], row['longitude']),
                    geohash=Geohash.encode(row['latitude'], row['longitude']),
                    tile=[
                        Geohash.encode(row['latitude'], row['longitude'], precision=2),
                        Geohash.encode(row['latitude'], row['longitude'], precision=3),
                        Geohash.encode(row['latitude'], row['longitude'], precision=4),
                        Geohash.encode(row['latitude'], row['longitude'], precision=5),
                        Geohash.encode(row['latitude'], row['longitude'], precision=6)
                    ]
                )
                location.put()
        # return the web-page content
        self.response.out.write("Migrated predefined locations (%s)" % configuration['id'])
        return


class MigrateHandler(BaseHandler):
    def get(self):
        # get the data from the fusion table
        configuration = customer_configuration.get_configuration(self.request)
        data = fusion_tables.select(configuration['master table'])
        if not data:
            logging.error("No events found for configuration (%s)" % configuration['id'])
            raise webapp2.abort(404)
        # flush the data from the datastore
        model.Map.get_by_id(configuration['id']).flush_events_and_instances()
        # transfer the data to the datastore
        for row in data:
            event = model.Event(
                id=row['event slug'],
                map=ndb.Key(model.Map, configuration['id']),
                start=fusion_datetime_string_to_naive_datetime_object(row['start']),
                end=fusion_datetime_string_to_naive_datetime_object(row['end']),
                calendar_rule=row['calendar rule'],
                event_name=row['event name'],
                description=row['description'],
                contact=row['contact'],
                website=row['website'],
                registration_required=True if row['registration required'] == 'true' else False,
                owner=row['owner'],
                moderator=row['moderator'],
                sync_date=fusion_datetime_string_to_naive_datetime_object('2018-01-01 00:00:00'),  # sync will be needed after migration
                final_date=fusion_datetime_string_to_naive_datetime_object(row['final date']),
                location_name=row['location name'],
                address=row['address'],
                postal_code=row['postal code'],
                coordinates=GeoPt(row['latitude'], row['longitude']),
                geohash=Geohash.encode(row['latitude'], row['longitude']),
                tile=[
                    Geohash.encode(row['latitude'], row['longitude'], precision=2),
                    Geohash.encode(row['latitude'], row['longitude'], precision=3),
                    Geohash.encode(row['latitude'], row['longitude'], precision=4),
                    Geohash.encode(row['latitude'], row['longitude'], precision=5),
                    Geohash.encode(row['latitude'], row['longitude'], precision=6)
                ],
                location_slug=row['location slug'],
                location_details=row['location details'],
                tags=[tag.replace('#','') for tag in row['tags'].split(',')],
                hashtags=[tag.replace('#','') for tag in row['hashtags'].split(',')]
                # timezone is set during syncing
            )
            event.generate_and_store_instances()  # this also puts the event to the datastore
        # return the web-page content
        self.response.out.write("Migrated events and regenerated instances (%s)" % configuration['id'])
        return


