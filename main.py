import webapp2
import logging
import email_logger

logging.basicConfig(level=logging.INFO)
email_logger.register_logger('vicmortelmans+maptiming@gmail.com')


routes = [
    webapp2.Route(r'/card/location/<location_slug:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/<timeframe:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/hash/<hashtags:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/<timeframe:[^/]+>/<tags:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/<timeframe:[^/]+>/hash/<hashtags:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/card/location/<location_slug:[^/]+>/<timeframe:[^/]+>/<tags:[^/]+>/hash/<hashtags:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/card/locations', handler='cards.LocationsHandler'),
    webapp2.Route(r'/qr/location/<location_slug:[^/]+>', handler='qr.LocationHandler'),
    webapp2.Route(r'/card/event/<event_slug:[^/]+>/<datetime_slug:[^/]+>', handler='cards.EventHandler'),
    webapp2.Route(r'/card/event/<event_slug:[^/]+>', handler='cards.EventHandler'),
    webapp2.Route(r'/<edit_mode:new>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new>/<latitude:-?\d+\.\d+>,<longitude:-?\d+\.\d+>,<zoom:\d+>z', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new>/<latitude:-?\d+\.\d+>,<longitude:-?\d+\.\d+>,<zoom:\d+>z/<tags:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new>/<latitude:-?\d+\.\d+>,<longitude:-?\d+\.\d+>,<zoom:\d+>z/hash/<hashtags:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new>/<latitude:-?\d+\.\d+>,<longitude:-?\d+\.\d+>,<zoom:\d+>z/<tags:[^/]+>/hash/<hashtags:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new>/location/<location_slug:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new>/location/<location_slug:[^/]+>/<tags:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new>/location/<location_slug:[^/]+>/hash/<hashtags:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new>/location/<location_slug:[^/]+>/<tags:[^/]+>/hash/<hashtags:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new|update>/<event_slug:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/submit/new', handler='submit.NewHandler'),
    webapp2.Route(r'/submit/update/<event_slug:[^/]+>', handler='submit.UpdateHandler'),
    webapp2.Route(r'/recurrenceinput', handler='recurrenceinput.RecurrenceInputHandler'),
    webapp2.Route(r'/sync', handler='sync.SyncHandler'),
    webapp2.Route(r'/load', handler='sync.LoadHandler'),
    webapp2.Route(r'/ical', handler='ical.ICalHandler'),
    webapp2.Route(r'/oauth2callback', handler='oauth2_three_legged.OauthHandler'),
    webapp2.Route(r'/<:.*>', handler='map.MapHandler')
]

app = webapp2.WSGIApplication(routes, debug=True)