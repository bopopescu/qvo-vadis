import webapp2

routes = [
    webapp2.Route(r'/', handler='map.MapHandler'),
    webapp2.Route(r'/location/<location_slug:.+>/<timeframe:.+>/<now:%d{4}-%d{2}-%d{2} %d{2}:%d{2}:%d{2}>', handler='cards.LocationHandler'),
    webapp2.Route(r'/location/<location_slug:.+>/<timeframe:.+>/<tags:.+>/<now:%d{4}-%d{2}-%d{2} %d{2}:%d{2}:%d{2}>', handler='cards.LocationHandler'),
    webapp2.Route(r'/location/<location_slug:.+>/<timeframe:.+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/location/<location_slug:.+>/<timeframe:.+>/<tags:.+>', handler='cards.LocationHandler'),
    webapp2.Route(r'/ical', handler='ical.ICalHandler'),
    webapp2.Route(r'/oauth2callback', handler='oauth2_three_legged.OauthHandler')
]

app = webapp2.WSGIApplication(routes, debug=True)