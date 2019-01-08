from google.appengine.ext import ndb
import model
import webapp2

# global variable
_map = {}
_maps = []
_map_limit = {}


def get_map(request):
    # TODO as long as the instance keeps running, the global variable won't be refreshed
    # from the map table, so after adding or modifying a map,
    # there must be made a call to some kind of force_get_map() cal
    global _map
    id = get_id(request)
    if id not in _map:
        map = model.Map.get_by_id(id)
        if not map:
            raise webapp2.abort(404)
        _map[id] = map
    return _map[id]


def get_maps():
    # TODO as long as the instance keeps running, the global variable won't be refreshed
    # from the map table, so after adding or modifying a map,
    # there must be made a call to some kind of force_get_map() cal
    global _maps
    if not _maps:
        _maps = model.Map.query().fetch()
    return _maps


def get_id(request):
    id = request.get('id')
    if not id:
        # otherwise, if the domain is appspot.com, get the subdomain
        domain = request.host
        if domain == 'maptiming.com':
            id = 'www'
        elif 'qvo-vadis.appspot.com' in domain:
            # try fetching this id from the configuration table
            index = domain.index('.qvo-vadis.appspot.com')
            id = domain[:index]
        elif '.maptiming.com' in domain:
            # try fetching this id from the configuration table
            index = domain.index('.maptiming.com')
            id = domain[:index]
        else:
            # TODO what to do for custom domains?
            pass
    if not id:
        raise webapp2.abort(404)
    return id
