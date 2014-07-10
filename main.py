import webapp2

routes = [
    webapp2.Route(r'/', handler='map.MapHandler'),
    webapp2.Route(r'/location/<location_slug:[^/]+>/<timeframe:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/location/<location_slug:[^/]+>/<timeframe:[^/]+>/<tags:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/location/<location_slug:[^/]+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/qr/location/<location_slug:[^/]+>', handler='qr.LocationHandler'),
    webapp2.Route(r'/event/<event_slug:[^/]+>/<datetime_slug:[^/]+>', handler='cards.EventHandler'),
    webapp2.Route(r'/event/<event_slug:[^/]+>', handler='cards.EventHandler'),
    webapp2.Route(r'/<edit_mode:new>', handler='edit.EditHandler'),
    webapp2.Route(r'/<edit_mode:new|update>/<event_slug:[^/]+>', handler='edit.EditHandler'),
    webapp2.Route(r'/submit/<edit_mode:new|update>', handler='submit.NewHandler'),
    webapp2.Route(r'/recurrenceinput', handler='recurrenceinput.RecurrenceInputHandler'),
    webapp2.Route(r'/sync', handler='sync.SyncHandler'),
    webapp2.Route(r'/load', handler='sync.LoadHandler'),
    webapp2.Route(r'/ical', handler='ical.ICalHandler'),
    webapp2.Route(r'/oauth2callback', handler='oauth2_three_legged.OauthHandler'),
    webapp2.Route(r'/status.appcache', handler='appcache.AppCacheHandler')
]

app = webapp2.WSGIApplication(routes, debug=True)