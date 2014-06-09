import webapp2
import fusion_tables


CONFIGURATION_TABLE_ID = '16REZHVjob5ah9sdBwuioQl6z8pqi5NXxMx7RzsDG'


# global variable
_customer = {}
_configuration = {}
_configurations = []

"""
def get_customer(request):
    global _customer
    # check if the customer id is provided as URL parameter
    # this overrules the subdomain
    id = request.get('id')
    callback_domain = request.host
    if not id:
        # otherwise, if the domain is appspot.com, get the subdomain
        domain = request.host
        if '.qvo-vadis.appspot.com' in domain:
             # try fetching this id from the configuration table
             index = domain.index('.qvo-vadis.appspot.com')
             id = domain[:index]
             callback_domain = domain[index+1:]
        else:
             # TODO what to do for custom domains?
            pass
    if not id:
        raise webapp2.abort(404)
    if id not in _customer:
        _customer[id] = {
            'id': id,                           # main purpose is to have a domain without the customer id, so
            'callback domain': callback_domain  # only one domain must be registered as callback for the whole app
        }
    return _customer[id]
"""

def get_configuration(request):
    global _configuration
    id = request.get('id')
    if not id:
        # otherwise, if the domain is appspot.com, get the subdomain
        domain = request.host
        if '.qvo-vadis.appspot.com' in domain:
            # try fetching this id from the configuration table
            index = domain.index('.qvo-vadis.appspot.com')
            id = domain[:index]
            callback_domain = domain[index+1:]
        else:
        # TODO what to do for custom domains?
            pass
    if not id:
        raise webapp2.abort(404)
    if id not in _configuration:
        condition = "'id' = '%s'" % id
        configurations = fusion_tables.select(CONFIGURATION_TABLE_ID, condition=condition)
        if not configurations:
            raise webapp2.abort(404)
        _configuration[id] = configurations[0]
    return _configuration[id]


def get_configurations():
    global _configurations
    if not _configurations:
        _configurations = fusion_tables.select(CONFIGURATION_TABLE_ID)
    return _configurations