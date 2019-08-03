import webapp2
import logging
import email_logger

logging.basicConfig(level=logging.INFO)
email_logger.register_logger('vicmortelmans+maptiming@gmail.com')


routes = [
    webapp2.Route(r'/_ah/start', handler='sync.StartHandler'),
    webapp2.Route(r'/flush_events_and_instances', handler='migrate.FlushEventsAndInstancesHandler'),
    webapp2.Route(r'/geojson/<tile:[^/]+>', handler='geojson.GeoJSONHandler'),
    webapp2.Route(r'/geojsonsimple', handler='geojson.GeoJSONSimpleHandler'),
    webapp2.Route(r'/geojsonlocations', handler='geojson.GeoJSONLocationsHandler'),
    webapp2.Route(r'/geojsonlocation/<location_slug:[^/]+>', handler='geojson.GeoJSONLocationHandler'),
    webapp2.Route(r'/card/location/<location_slug:[^/]+>', handler='cards.LocationHandler'),  # TODO
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/<timeframe:[^/]+>', handler='cards.LocationHandler'),  # TODO
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/hash/<hashtags:[^/]+>', handler='cards.LocationHandler'),  # TODO
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/<timeframe:[^/]+>/<tags:[^/]+>', handler='cards.LocationHandler'),  # TODO
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/<timeframe:[^/]+>/hash/<hashtags:[^/]+>', handler='cards.LocationHandler'),  # TODO
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/<timeframe:[^/]+>/<tags:[^/]+>/hash/<hashtags:[^/]+>', handler='cards.LocationHandler'),  # TODO
    webapp2.Route(r'/card/locations', handler='cards.LocationsHandler'),  # TODO
    webapp2.Route(r'/card/indexbybatches', handler='cards.IndexHandler'),  # obsolete  # TODO
    webapp2.Route(r'/card/index', handler='cards.IndexByLocationHandler'),  # TODO
    webapp2.Route(r'/card/sitemap', handler='cards.SitemapHandler'),  # obsolete  # TODO
    webapp2.Route(r'/card/sitemapbylocation', handler='cards.SitemapByLocationHandler'),  # TODO
    webapp2.Route(r'/qr/location/<location_slug:[^/]+>', handler='qr.LocationHandler'),  # TODO
    webapp2.Route(r'/card/event/<event_slug:[^/]+>/<date_time_slug:[^/]+>', handler='cards.EventHandler'),  # TODO
    webapp2.Route(r'/card/event/<event_slug:[^/]+>', handler='cards.EventHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>/<latitude:-?\d+\.\d+>,<longitude:-?\d+\.\d+>,<zoom:\d+>z', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>/<latitude:-?\d+\.\d+>,<longitude:-?\d+\.\d+>,<zoom:\d+>z/<tags:[^/]+>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>/<latitude:-?\d+\.\d+>,<longitude:-?\d+\.\d+>,<zoom:\d+>z/hash/<hashtags:[^/]+>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>/<latitude:-?\d+\.\d+>,<longitude:-?\d+\.\d+>,<zoom:\d+>z/<tags:[^/]+>/hash/<hashtags:[^/]+>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>/location/<location_slug:[^/]+>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>/location/<location_slug:[^/]+>/<tags:[^/]+>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>/location/<location_slug:[^/]+>/hash/<hashtags:[^/]+>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new>/location/<location_slug:[^/]+>/<tags:[^/]+>/hash/<hashtags:[^/]+>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/<edit_mode:new|update>/<event_slug:[^/]+>', handler='edit.EditHandler'),  # TODO
    webapp2.Route(r'/submit/new', handler='submit.NewHandler'),  # TODO
    webapp2.Route(r'/submit/update/<event_slug:[^/]+>', handler='submit.UpdateHandler'),  # TODO
    webapp2.Route(r'/recurrenceinput', handler='recurrenceinput.RecurrenceInputHandler'),  # TODO
    webapp2.Route(r'/sync/old_version_of_updated_events/<event_slug:[^/]+>', handler='sync.SyncOldVersionOfUpdatedEventsHandler'),  # TODO
    webapp2.Route(r'/sync/all', handler='sync.SyncAllHandler'),  # TODO
    webapp2.Route(r'/sync', handler='sync.SyncHandler'),
    webapp2.Route(r'/load', handler='sync.LoadHandler'),  # TODO
    webapp2.Route(r'/ical', handler='ical.ICalHandler'),  # TODO
    webapp2.Route(r'/oauth2callback', handler='oauth2_three_legged.OauthHandler'),  # TODO
    webapp2.Route(r'/migrateconfiguration', handler='migrate.MigrateConfigurationHandler'),
    webapp2.Route(r'/migratelocations', handler='migrate.MigrateLocationsHandler'),
    webapp2.Route(r'/migrate', handler='migrate.MigrateHandler'),
    webapp2.Route(r'/<:.*>', handler='map.MapHandler')
]

app = webapp2.WSGIApplication(routes, debug=True)