from sqlbuilder import SQL
import oauth2_two_legged
from lib import slugify, location_slug, event_slug
import logging
from recurrenceinput import calculate_occurrences
from datetime import datetime
from datetime import timedelta
import copy
import json
import StringIO
from googleapiclient.http import MediaIoBaseUpload
from csv import DictWriter
from random import randint
import re
import time
from google.appengine.runtime import apiproxy_errors
from googleapiclient import errors
import httplib
from google.appengine.api import urlfetch

logging.basicConfig(level=logging.INFO)

#logservice.AUTOFLUSH_EVERY_SECONDS = None
#logservice.AUTOFLUSH_EVERY_BYTES = None
#logservice.AUTOFLUSH_EVERY_LINES = 1
#logservice.AUTOFLUSH_ENABLED = True

OAUTH_SCOPE = 'https://www.googleapis.com/auth/fusiontables'
API_CLIENT = 'fusiontables'
VERSION = 'v2'

FUSION_TABLE_DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'
ISO_DATE_TIME_FORMAT = '%Y%m%dT%H%M%S'

_SQL = SQL()
_table_cols = {}  # _table_cols[table_id] gives the list of column names
_inserts = {}  # _inserts[table_id] gives list of dicts to be inserted
_deletes = {}  # idem


def table_cols(table_id):
    # returns a list of column names, stored in global variable
    global _table_cols
    if table_id not in _table_cols:
        query = _SQL.select(table_id) + ' LIMIT 1'
        sleep = 1
        for attempt in range(10):
            try:
                service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
                logging.debug("Trying to read column names in %s" % table_id)
                query_result = service.query().sqlGet(sql=query).execute()
            except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException) as e:
                time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
                logging.warning("Sleeping %d seconds because of HttpError trying to read column names in %s (%s)" % (sleep, table_id, e))
                sleep = sleep * 2
            else:
                break  # no error caught
        else:
            logging.critical("Retried 10 times reading column names in %s" % table_id)
            raise  # attempts exhausted
        _table_cols[table_id] = query_result['columns']
        logging.info("Read column names in %s: %s" % (table_id, ','.join(_table_cols[table_id])))
    return list(_table_cols[table_id])  # clone it! if they're gonna modify it, the global var is safe


def clean_dict(table_id, dict):
    # removing keys from the dict that are not in the table's list of columns
    cols = table_cols(table_id)
    dict_keys = dict.keys()  # set apart because you can't del while iterating a dict
    for key in dict_keys:
        if not key in cols:
            logging.error("Dirty dict submitted, containing key not in fusion table: " + key)
            del dict[key]


def list_of_dicts_to_csv(table_id, list_of_dicts):
    csv = StringIO.StringIO()
    cols = table_cols(table_id)
    logging.debug("Creating CSV using cols %s" % ','.join(cols))
    w = DictWriter(csv, cols)
    for dict in list_of_dicts:
        for key, value in dict.iteritems():
            if isinstance(value, unicode):
                dict[key] = value.encode('utf8')
    w.writerows(list_of_dicts)
    logging.debug("Created CSV %s" % csv.getvalue())
    return csv


def select(table_id, cols=None, condition=None, filter_obsolete_rows=True):
    """
     condition can contain GROUP BY and LIMIT statements, but there must be at least one WHERE statement!!
     filter_obsolete_rows: only has effect on subordinate table queries (by testing on 'datetime slug' field)
     filter_repeating_rows: only has effect on subordinate table queries, returns the next upcoming (or ongoing) event
    """
    if not cols:
        cols = table_cols(table_id)
    # make sure you return the rowid, that's useful for later 'updates'
    if not 'rowid' in cols and not 'GROUP BY' in condition:
        cols.append('rowid')
    query = _SQL.select(table_id, cols, condition)
    sleep = 1
    urlfetch.set_default_fetch_deadline(60)
    for attempt in range(10):
        try:
            service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
            logging.debug("Trying to select rows in %s" % table_id)
            query_result = service.query().sqlGet(sql=query).execute()
        except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException) as e:
            time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
            logging.warning("Sleeping %d seconds because of HttpError trying to select rows in %s (%s)" % (sleep, table_id, e))
            sleep = sleep * 2
        else:
            break  # no error caught
    else:
        logging.critical("Retried 10 times selecting rows in %s" % table_id)
        raise  # attempts exhausted
    rows = fusion_table_query_result_as_list_of_dict(query_result)
    for row in rows:  # this is an intermediate fix for data entered before se quence field was added to subordinate tables
        if 'sequence' in row and row['sequence'] == 'NaN':
            row['sequence'] = 1
    # for each event only return the row(s) with the highest 'sequence'
    if filter_obsolete_rows and rows and 'datetime slug' in rows[0]:
        # for each event slug, find the maximum sequence
        maximum_sequence = {}
        for row in rows:
            event_slug = row['event slug']
            sequence = row['sequence']
            if event_slug not in maximum_sequence or maximum_sequence[event_slug] < sequence:
                maximum_sequence[event_slug] = sequence
        # filter the rows with sequence lower than the maximum sequence for that event slug
        rows[:] = [row for row in rows if row['sequence'] == maximum_sequence[row['event slug']]]
#    # for each event only return the row(s) with the earliest TWO 'datetime slug' values
#    if filter_repeating_rows and rows and 'datetime slug' in rows[0]:
#        # for each event slug, find the TWO minimum datetime values
#        maximum_datetime = {}
#        maximum2_datetime = {}
#        for row in rows:
#            event_slug = row['event slug']
#            datetime = row['datetime slug']
#            if event_slug not in maximum_datetime or maximum_datetime[event_slug] > datetime:
#                maximum_datetime[event_slug] = datetime
#            elif event_slug not in maximum2_datetime or maximum2_datetime[event_slug] > datetime:
#                maximum2_datetime[event_slug] = datetime
#        # filter the rows with two lowest datetime values for that event slug
#        rows[:] = [row for row in rows if row['datetime slug'] in (maximum_datetime[row['event slug']], maximum2_datetime[row['event slug']])]
    return rows


def count(table_id, condition=None):
    """
     condition can contain GROUP BY and LIMIT statements, but there must be at least one WHERE statement!!
     filter_obsolete_rows: only has effect on subordinate table queries (by testing on 'datetime slug' field)
    """
    query = _SQL.count(table_id, condition)
    sleep = 1
    for attempt in range(10):
        try:
            service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
            logging.debug("Trying to count rows in %s" % table_id)
            query_result = service.query().sqlGet(sql=query).execute()
        except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException) as e:
            time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
            logging.warning("Sleeping %d seconds because of HttpError trying to count rows in %s (%s)" % (sleep, table_id, e))
            sleep = sleep * 2
        else:
            break  # no error caught
    else:
        logging.critical("Retried 10 times counting rows in %s" % table_id)
        raise  # attempts exhausted
    rows = fusion_table_query_result_as_list_of_dict(query_result)
    count = int(rows[0]['count()'])
    return count


def select_first(table_id, cols=None, condition=None):
    """
    cols: a list of strings identifying the columns to be returned
    condition: e.g. "'name' = 'John Cleese' and 'group' = 'The Rolling Stones'"
    """
    if not cols:
        cols = table_cols(table_id)
        # make sure you return the rowid, that's useful for later 'updates'
    if not 'rowid' in cols:
        cols.append('rowid')
    query = _SQL.select(table_id, cols, condition) + ' LIMIT 1'
    sleep = 1
    for attempt in range(10):
        try:
            service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
            logging.debug("Trying to select first row in %s" % table_id)
            query_result = service.query().sqlGet(sql=query).execute()
        except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException) as e:
            time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
            logging.warning("Sleeping %d seconds because of HttpError trying to select first row in %s (%s)" % (sleep, table_id, e))
            sleep = sleep * 2
        else:
            break  # no error caught
    else:
        logging.critical("Retried 10 times selecting first row in %s" % table_id)
        raise  # attempts exhausted
    rows = fusion_table_query_result_as_list_of_dict(query_result)
    for row in rows:  # this is an intermediate fix for data entered before sequence field was added to subordinate tables
        if 'sequence' in row and row['sequence'] == 'NaN':
            row['sequence'] = 1
    return rows


def select_nth(table_id, cols=None, condition=None, n=1):
    if not cols:
        cols = table_cols(table_id)
        # make sure you return the rowid, that's useful for later 'updates'
    if not 'rowid' in cols:
        cols.append('rowid')
    query = _SQL.select(table_id, cols, condition) + ' OFFSET %d LIMIT 1' % n
    sleep = 1
    for attempt in range(10):
        try:
            service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
            logging.debug("Trying to select nth row in %s" % table_id)
            query_result = service.query().sqlGet(sql=query).execute()
        except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException) as e:
            time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
            logging.warning("Sleeping %d seconds because of HttpError trying to select nth row in %s (%s)" % (sleep, table_id, e))
            sleep = sleep * 2
        else:
            break  # no error caught
    else:
        logging.critical("Retried 10 times selecting nth row in %s" % table_id)
        raise  # attempts exhausted
    rows = fusion_table_query_result_as_list_of_dict(query_result)
    for row in rows:  # this is an intermediate fix for data entered before sequence field was added to subordinate tables
        if 'sequence' in row and row['sequence'] == 'NaN':
            row['sequence'] = 1
    return rows


def insert(table_id, values):
    query = _SQL.insert(table_id, values)
    sleep = 1
    for attempt in range(10):
        try:
            service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
            logging.debug("Trying to insert row in %s" % table_id)
            query_result = service.query().sql(sql=query).execute()
        except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException) as e:
            time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
            logging.warning("Sleeping %d seconds because of HttpError trying to insert row in %s (%s)" % (sleep, table_id, e))
            sleep = sleep * 2
        else:
            break  # no error caught
    else:
        logging.critical("Retried 10 times inserting row in %s" % table_id)
        raise  # attempts exhausted
    if not 'error' in query_result:
        logging.info("Inserted in %s %s" % (table_id, json.dumps(values)))
    else:
        logging.error("Insert in %s failed on %s with %s" % (table_id, values, query_result['error']))
    return


def insert_hold(table_id, values):
    if table_id not in _inserts:
        _inserts[table_id] = []
    _inserts[table_id].append(values)
    logging.info("Insert ON HOLD in %s %s" % (table_id, json.dumps(values)))
    if len(_inserts[table_id]) >= 100:  # the limit is 500 or 1MB, so ~250 is maximum here!
        insert_go(table_id)
    return


def insert_go(table_id):
    if table_id in _inserts and _inserts[table_id]:
        csv = list_of_dicts_to_csv(table_id, _inserts[table_id])
        media_body = MediaIoBaseUpload(fd=csv, mimetype='application/octet-stream')
        sleep = 1
        for attempt in range(10):
            try:
                service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
                logging.debug("Trying to insert %d rows in subordinate %s" % (len(_inserts[table_id]), table_id))
                csv.seek(0)  # rewind the StringIO object
                logging.debug("First row: %s" % csv.readline())
                result = service.table().importRows(tableId=table_id, media_body=media_body).execute()
            except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException) as e:
                time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
                logging.warning("Sleeping %d seconds because of HttpError trying to insert %d rows in subordinate %s (%s)" % (sleep, len(_inserts[table_id]), table_id, e))
                sleep = sleep * 2
            else:
                break  # no error caught
        else:
            logging.critical("Retried 10 times inserting %d rows in subordinate %s" % (len(_inserts[table_id]), table_id))
            raise  # attempts exhausted
        if not 'error' in result:
            logging.info("Inserted %d rows in %s" % (len(_inserts[table_id]), table_id))
            _inserts[table_id] = []
        else:
            logging.error("Insert of %d rows in %s failed with %s" % (len(_inserts[table_id]), table_id, result['error']))
    return


def update_with_implicit_rowid(table_id, values):
    # get row id
    row_id = values['rowid']
    # get rid of row id
    del values['rowid']
    # update row
    query = _SQL.update(table_id, values, row_id=row_id)
    sleep = 1
    for attempt in range(10):
        try:
            service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
            logging.debug("Trying to insert a row in subordinate %s" % table_id)
            query_result = service.query().sql(sql=query).execute()
        except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException, httplib.error) as e:
            time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
            logging.warning("Sleeping %d seconds because of HttpError trying to insert a row in subordinate %s (%s)" % (sleep, table_id, e))
            sleep = sleep * 2
        else:
            break  # no error caught
    else:
        logging.critical("Retried 10 times updating a row in %s" % (table_id))
        raise  # attempts exhausted
    if not 'error' in query_result:
        logging.info("Updated in %s %s" % (table_id, json.dumps(values)))
    else:
        logging.error("Update in %s failed on %s with %s" % (table_id, values, query_result['error']))
    return


def delete_with_implicit_rowid(table_id, values):
    # get row id
    row_id = values['rowid']
    # delete row
    query = _SQL.delete(table_id, row_id=row_id)
    sleep = 1
    for attempt in range(10):
        try:
            service = oauth2_two_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
            logging.debug("Trying to delete row from subordinate %s" % table_id)
            query_result = service.query().sql(sql=query).execute()
        except (errors.HttpError, apiproxy_errors.DeadlineExceededError, httplib.HTTPException) as e:
            time.sleep(sleep)  # pause to avoid "Rate Limit Exceeded" error
            logging.warning("Sleeping %d seconds because of HttpError trying to delete row from subordinate %s (%s)" % (sleep, table_id, e))
            sleep = sleep * 2
        else:
            break  # no error caught
    else:
        logging.critical("Retried 10 times deleting row from subordinate %s" % table_id)
        raise  # attempts exhausted
    if not 'error' in query_result:
        logging.info("Deleted in %s %s" % (table_id, json.dumps(values)))
    else:
        logging.error("Deleted in %s failed on %s with %s" % (table_id, values, query_result['error']))
    return


def main_to_subordinate(main):
    # returns a tuple of a list of subordinate dicts
    # ('list' because a recurring date will produce multiple rows)
    # and the final date as second tuple element
    # first create a dict with the copied attributes
    subordinate = {}
    for key in [
        'event slug',
        'event name',
        'description',
        'contact',
        'website',
        'registration required',
        'sequence',
        'location name',
        'address',
        'postal code',
        'latitude',
        'longitude',
        'location slug',
        'location details',
        'tags',
        'hashtags'
    ]:
        subordinate[key] = main[key]

    previous_start = "1970-01-01 00:00:00"
    # then calculate the date occurrences
    if main['calendar rule']:
        # start field holds the start date for the recurrence rule
        start_date = datetime.strptime(main['start'], FUSION_TABLE_DATE_TIME_FORMAT).date()
        end_date = datetime.strptime(main['end'], FUSION_TABLE_DATE_TIME_FORMAT).date()
        days = end_date - start_date
        today_date = datetime.today().date()
        if start_date <= today_date:
            start_date = today_date
        data = {
            'year': start_date.year,
            'month': start_date.month,
            'day': start_date.day,
            'rrule': main['calendar rule'],
            'format': DATE_FORMAT,
            'batch_size': 10,
            'start': 0
        }
        start = datetime.strptime(main['start'], FUSION_TABLE_DATE_TIME_FORMAT).time()
        end = datetime.strptime(main['end'], FUSION_TABLE_DATE_TIME_FORMAT).time()
        today_plus_13_months_date = today_date + timedelta(days=13*30)  # naive, don't care
        subordinates = []
        done = False
        final_date = ''
        while True:
            occurrences = [o for o in calculate_occurrences(data)['occurrences'] if o['type'] != 'exdate']
            for occurrence in occurrences:
                start_date = datetime.strptime(occurrence['date'], ISO_DATE_TIME_FORMAT).date()
                if today_date <= start_date < today_plus_13_months_date:
                    # only add events within one year timeframe from now
                    new_subordinate = copy.deepcopy(subordinate)
                    new_subordinate['start'] = datetime.combine(start_date, start).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                    new_subordinate['end'] = datetime.combine(start_date + days, end).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                    new_subordinate['datetime slug'] = slugify(new_subordinate['start'])
                    new_subordinate['previous start'] = previous_start
                    previous_start = new_subordinate['start']
                    if final_date < new_subordinate['end']:
                        final_date = new_subordinate['end']
                    subordinates.append(new_subordinate)
                else:
                    done = True
                    break  # for
            if occurrences and not done:
                data['start'] += data['batch_size']
            else:
                break  # while
        return (subordinates, final_date)
    else:  # not recurring, can span multiple days
        subordinate['start'] = main['start']
        subordinate['end'] = main['end']
        subordinate['datetime slug'] = slugify(subordinate['start'])
        subordinate['previous start'] = previous_start
        return ([subordinate], subordinate['end'])


def fusion_table_query_result_as_list_of_dict(data):
    list = []
    if 'rows' in data:
        for row in data['rows']:
            list.append(dict(zip(data['columns'],row)))
    return list


def random_main(configuration=None):
    main = {}
    start = datetime(2014, randint(1, 12), randint(1, 28), randint(8, 20), 0, 0)
    main['start'] = start.strftime(FUSION_TABLE_DATE_TIME_FORMAT)
    main['description'] = random_text(sentences=1)
    main['contact'] = "vicmortelmans+%s@gmail.com" % random_text(words=1)
    main['website'] = "http://www.%s.com" % random_text(words=1)
    main['registration required'] = 'true' if randint(0, 1) == 1 else 'false'
    main['owner'] = "vicmortelmans+%s@gmail.com" % random_text(words=1)
    main['moderator'] = "vicmortelmans+%s@gmail.com" % random_text(words=1)
    main['state'] = "new"
    main['sequence'] = "0"
    main['entry date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
    main['update date'] = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
    main['renewal date'] = (datetime.today() + timedelta(days=30 * 6)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
    main['location name'] = random_text(words=randint(1, 4))
    postal_code = randint(1000,9999)
    main['address'] = "%s %d, %d %s" % (random_text(words=1), randint(1,100), postal_code, random_text(words=1))
    main['postal code'] = postal_code
    main['latitude'] = float(randint(50734, 51444)) / 1000
    main['longitude'] = float(randint(2547, 5840)) / 1000
    main['location slug'] = location_slug(main)
    main['location details'] = random_text(words=randint(0,4))
    if configuration:
        main['tags'] = random_tags(configuration['tags'])
    else:
        main['tags'] = ''
    main['hashtags'] = random_text(words=randint(0, 1))
    # second
    multi_day = True if randint(1, 10) < 2 else False
    if multi_day:
        main['end'] = (start + timedelta(hours=randint(0, 3), days=randint(1, 7))).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        main['calendar rule'] = ''
    else:
        main['end'] = (start + timedelta(hours=randint(1, 3))).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        chance = randint(1, 10)
        if chance < 3:
            main['calendar rule'] = "RRULE:FREQ=DAILY;UNTIL=%s" % (start + timedelta(days=30 * 6)).strftime(ISO_DATE_TIME_FORMAT)
        elif chance < 7:
            main['calendar rule'] = "RRULE:FREQ=WEEKLY;BYDAY=%s;COUNT=16" % {0: 'MO', 1: 'TU', 2: 'WE', 3: 'TH', 4: 'FR', 5: 'SA', 6: 'SU'}[start.weekday()]
        else:
            main['calendar rule'] = "RRULE:FREQ=MONTHLY;BYMONTHDAY=%d" % start.day
    main['event name'] = "%s %s" % (main['location name'], main['calendar rule'])
    main['event slug'] = event_slug(main)
    return main


def random_text(words=None, sentences=None):
    text = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    words_list = re.split('[,. ]+', text)
    sentences_list = re.split('\. ', text)
    if words:
        start = randint(1, len(words_list) - words)
        return ' '.join(words_list[start:start + words])
    elif sentences:
        start = randint(1, len(sentences_list) - sentences)
        return '. '.join(sentences_list[start:start + sentences])
    else:
        return ''


def random_tags(tags_comma_separated):
    tags = re.split(',', tags_comma_separated)
    selected = []
    for tag in tags:
        chance = randint(1,10)
        if chance > 7:
            selected.append("#%s#" % slugify(tag))
    return ','.join(selected)

