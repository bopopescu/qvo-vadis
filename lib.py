import webapp2
import logging
import os

DEV = os.environ['SERVER_SOFTWARE'].startswith('Development')


AVAILABLE_LOCALES = ['en', 'es', 'fr', 'nl']


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters
    (except dot, to  make sure the file extension is kept),
    and converts spaces to hyphens.
    """
    import unicodedata
    import re
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s.-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    return value


def location_slug(event):
    location_presentation = ''
    if event['location name']:
        location_presentation += event['location name']
    if event['location name'] and event['address']:
        location_presentation += ', '
    if event['address']:
        location_presentation += event['address']
    if not event['address']:
        location_presentation += event['postal code']
    return slugify(location_presentation)


def event_slug(event):
    # TODO if presentation would ever be needed, this must be refined
    event_presentation = ''
    event_presentation += event['event name']
    # event_presentation += ', '
    # event_presentation += event['start']
    event_presentation += ', '
    event_presentation += event['location slug']
    return slugify(event_presentation)


def extract_hash_tags(s):
    import re
    return set([re.sub(r"(\W+)$", "", j) for j in set([i for i in s.split() if i.startswith("#")])])


def get_localization():
    import csv
    localization_reader = csv.reader(open('localization.csv', 'rb'))
    localization = {}
    header_row = localization_reader.next()
    for column_name in header_row[1:]:
        localization[column_name] = {}
    for row in localization_reader:
        header_with_row = zip(header_row,row)
        for field in header_with_row[1:]:
            localization[field[0]][row[0]] = field[1].decode('utf-8')
    return localization


def get_language(request, configuration):
    header = request.headers.get('Accept-Language', '')  # e.g. en-gb,en;q=0.8,es-es;q=0.5,eu;q=0.3
    locales = [locale.split(';')[0] for locale in header.split(',')]
    for locale in locales:
        if locale in AVAILABLE_LOCALES:
            language = locale
            break
    else:
        language = configuration['language']
    return language


class BaseHandler(webapp2.RequestHandler):
    def handle_exception(self, exception, debug):
        # Log the error.
        logging.exception(exception)

        # Set a custom message.
        self.response.out.write('An error occurred.')

        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
        else:
            self.response.set_status(500)


