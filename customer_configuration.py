import webapp2
import fusion_tables


CONFIGURATION_TABLE_ID = '16REZHVjob5ah9sdBwuioQl6z8pqi5NXxMx7RzsDG'


# global variable
_configuration = {}
_configurations = []
_limit = {}


def get_configuration(request):
    global _configuration
    id = get_id(request)
    if id not in _configuration:
        condition = "'id' = '%s'" % id
        configurations = fusion_tables.select(CONFIGURATION_TABLE_ID, condition=condition)
        if not configurations:
            raise webapp2.abort(404)
        _configuration[id] = configurations[0]
    return _configuration[id]


def get_limit(request):
    """
    returns a datetime if a limit must be applied or False if no limit must be applied,
    i.e. if the 'commercial limit' is set to 0 or if the number of rows in the slave table is
    lower than the 'commercial limit'
    """
    global _limit
    id = get_id(request)
    if id not in _limit:
        configuration = get_configuration(request)
        try:
            limit = int(configuration["commercial limit"])
        except ValueError:
            return False
        if not limit:
            return False
        threshold_slave = fusion_tables.select_nth(configuration['slave table'], cols=['start'], n=limit)
        if not threshold_slave:
            return False
        _limit[id] = threshold_slave[0]['start']
    return _limit[id]


def get_configurations():
    global _configurations
    if not _configurations:
        _configurations = fusion_tables.select(CONFIGURATION_TABLE_ID)
    return _configurations


def get_id(request):
    id = request.get('id')
    if not id:
        # otherwise, if the domain is appspot.com, get the subdomain
        domain = request.host
        if '.qvo-vadis.appspot.com' in domain:
            # try fetching this id from the configuration table
            index = domain.index('.qvo-vadis.appspot.com')
            id = domain[:index]
        else:
        # TODO what to do for custom domains?
            pass
    if not id:
        raise webapp2.abort(404)
    return id