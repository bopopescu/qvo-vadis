import webapp2

routes = [
    webapp2.Route(r'/', handler='map.MapHandler'),
    webapp2.Route(r'/map', handler='map.MapHandler'),
    webapp2.Route(r'/map/@\d+.\d+,\d+.\d+>,\d+z,\d+px', handler='map.MapHandler'),
    webapp2.Route(r'/map/@\d+.\d+,\d+.\d+>,\d+z,\d+px/\w+', handler='map.MapHandler'),
    webapp2.Route(r'/map/@\d+.\d+,\d+.\d+>,\d+z,\d+px/\w+/[\w,]+', handler='map.MapHandler')
]

app = webapp2.WSGIApplication(routes, debug=True)