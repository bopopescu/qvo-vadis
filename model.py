from google.appengine.ext import ndb


class Map(ndb.Model):
    """ models the configuration data for a map
        The key contains the id of the map configuration """
    title = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    qr_code_string = ndb.TextProperty()
    commercial_limit = ndb.IntegerProperty()
    language = ndb.StringProperty()
    plan = ndb.StringProperty()
    help = ndb.TextProperty()
    latitude = ndb.FloatProperty()
    longitude = ndb.FloatProperty()
    zoom = ndb.IntegerProperty()


class Location(ndb.Model):
    """ models a predefined location """
    name = ndb.TextProperty()
    coordinates = ndb.GeoPtProperty()
    geohash = ndb.StringProperty()
    tile = ndb.StringProperty(repeated=True)
    map = ndb.KeyProperty(repeated=True, kind=Map)


class Instance(ndb.Model):
    date_time_slug = ndb.StringProperty()
    previous_start = ndb.DateTimeProperty()
    start = ndb.DateTimeProperty()
    end = ndb.DateTimeProperty()


class Event(ndb.Model):
    """ models an event, including the recurring instances as a structured property
        The key contains the event slug """
    map = ndb.KeyProperty()
    start = ndb.DateTimeProperty()
    end = ndb.DateTimeProperty()
    calendar_rule = ndb.TextProperty()
    event_name = ndb.TextProperty()
    description = ndb.TextProperty()
    contact = ndb.TextProperty()
    website = ndb.TextProperty()
    registration_required = ndb.BooleanProperty()
    owner = ndb.StringProperty()
    moderator = ndb.StringProperty()
    state = ndb.StringProperty()
    update_after_sync = ndb.BooleanProperty()
    sync_date = ndb.DateTimeProperty()
    final_date = ndb.DateTimeProperty()
    location_name = ndb.TextProperty()
    address = ndb.TextProperty()
    postal_code = ndb.StringProperty()
    coordinates = ndb.GeoPtProperty()
    geohash = ndb.StringProperty()
    tile = ndb.StringProperty(repeated=True)
    location_slug = ndb.StringProperty()
    location_details = ndb.TextProperty()
    tags = ndb.StringProperty(repeated=True)
    hashtags = ndb.StringProperty(repeated=True)
    instances = ndb.StructuredProperty(Instance, repeated=True)
