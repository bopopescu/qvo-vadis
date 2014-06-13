from sqlbuilder import SQL
import oauth2_three_legged
from lib import slugify
import logging
from recurrenceinput import calculate_occurrences
from datetime import datetime
from datetime import timedelta
import copy
import json
import StringIO
from apiclient.http import MediaIoBaseUpload
from csv import DictWriter
from random import randint
import re

OAUTH_SCOPE = 'https://www.googleapis.com/auth/fusiontables'
API_CLIENT = 'fusiontables'
VERSION = 'v1'

DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'
ISO_DATE_TIME_FORMAT = '%Y%m%dT%H%M%S'

_SQL = SQL()
_service = oauth2_three_legged.get_service(API_CLIENT, VERSION, OAUTH_SCOPE)
_table_cols = {}  # _table_cols[table_id] gives the list of column names
_inserts = {}  # _inserts[table_id] gives list of dicts to be inserted
_deletes = {}  # idem


def table_cols(table_id):
    # returns a list of column names, stored in global variable
    query = _SQL.select(table_id) + ' LIMIT 1'
    query_result = _service.query().sqlGet(sql=query).execute()
    _table_cols[table_id] = query_result['columns']
    return _table_cols[table_id]


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
    w = DictWriter(csv, cols)
    w.writerows(list_of_dicts)
    return csv


def select(table_id, cols=None, condition=None):
    if not cols:
        cols = table_cols(table_id)
    # make sure you return the rowid, that's useful for later 'updates'
    if not 'rowid' in cols:
        cols.append('rowid')
    query = _SQL.select(table_id, cols, condition)
    query_result = _service.query().sqlGet(sql=query).execute()
    return fusion_table_query_result_as_list_of_dict(query_result)


def select_first(table_id, cols=None, condition=None):
    if not cols:
        cols = table_cols(table_id)
        # make sure you return the rowid, that's useful for later 'updates'
    if not 'rowid' in cols:
        cols.append('rowid')
    query = _SQL.select(table_id, cols, condition) + ' LIMIT 1'
    query_result = _service.query().sqlGet(sql=query).execute()
    return fusion_table_query_result_as_list_of_dict(query_result)


def select_nth(table_id, cols=None, condition=None, n=1):
    if not cols:
        cols = table_cols(table_id)
        # make sure you return the rowid, that's useful for later 'updates'
    if not 'rowid' in cols:
        cols.append('rowid')
    query = _SQL.select(table_id, cols, condition) + ' OFFSET %d LIMIT 1' % n
    query_result = _service.query().sqlGet(sql=query).execute()
    return fusion_table_query_result_as_list_of_dict(query_result)


def insert(table_id, values):
    query = _SQL.insert(table_id, values)
    query_result = _service.query().sql(sql=query).execute()
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
    if len(_inserts[table_id]) >= 250:  # the limit is 500 or 1MB
        insert_go(table_id)
    return


def insert_go(table_id):
    if table_id in _inserts and _inserts[table_id]:
        csv = list_of_dicts_to_csv(table_id, _inserts[table_id])
        media_body = MediaIoBaseUpload(fd=csv, mimetype='application/octet-stream')
        result = _service.table().importRows(tableId=table_id, media_body=media_body).execute()
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
    query_result = _service.query().sql(sql=query).execute()
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
    query_result = _service.query().sql(sql=query).execute()
    if not 'error' in query_result:
        logging.info("Deleted in %s %s" % (table_id, json.dumps(values)))
    else:
        logging.error("Deleted in %s failed on %s with %s" % (table_id, values, query_result['error']))
    return


def master_to_slave(master):
    # returns a tuple of slave dicts, 'list' because a recurring date will produce multiple rows
    # and the final date as second tuple element
    # first create a dict with the copied attributes
    slave = {}
    for key in [
        'event slug',
        'event name',
        'description',
        'contact',
        'website',
        'registration required',
        'organization',
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
        slave[key] = master[key]

    # then calculate the date occurrences
    if master['calendar rule']:
        # start (and end) fields hold the start date for the recurrence rule
        start_date = datetime.strptime(master['start'], DATE_TIME_FORMAT).date()
        today_date = datetime.today().date()
        if start_date <= today_date:
            start_date = today_date
        data = {
            'year': start_date.year,
            'month': start_date.month,
            'day': start_date.day,
            'rrule': master['calendar rule'],
            'format': DATE_FORMAT,
            'batch_size': 10,
            'start': 0
        }
        start = datetime.strptime(master['start'], DATE_TIME_FORMAT).time()
        end = datetime.strptime(master['end'], DATE_TIME_FORMAT).time()
        today_plus_13_months_date = today_date + timedelta(days=13*30)  # naive, don't care
        slaves = []
        done = False
        final_date = ''
        while True:
            occurrences = calculate_occurrences(data)['occurrences']
            for occurrence in occurrences:
                date = datetime.strptime(occurrence['date'], ISO_DATE_TIME_FORMAT).date()
                if today_date <= date < today_plus_13_months_date:
                    # only add events within one year timeframe from now
                    new_slave = copy.deepcopy(slave)
                    new_slave['start'] = datetime.combine(date, start).strftime(DATE_TIME_FORMAT)
                    new_slave['end'] = datetime.combine(date, end).strftime(DATE_TIME_FORMAT)
                    new_slave['datetime slug'] = slugify(new_slave['start'])
                    if final_date < new_slave['end']:
                        final_date = new_slave['end']
                    slaves.append(new_slave)
                else:
                    done = True
                    break  # for
            if occurrences and not done:
                data['start'] += data['batch_size']
            else:
                break  # while
        return (slaves, final_date)
    else:  # not recurring, can span multiple days
        slave['start'] = master['start']
        slave['end'] = master['end']
        slave['datetime slug'] = slugify(slave['start'])
        return ([slave], slave['end'])


def fusion_table_query_result_as_list_of_dict(data):
    list = []
    if 'rows' in data:
        for row in data['rows']:
            list.append(dict(zip(data['columns'],row)))
    return list


def location_slug(event):
    return slugify(event['location name'] + ' ' + event['address'])


def random_master(configuration=None):
    master = {}
    start = datetime(2014, randint(1, 12), randint(1, 28), randint(8, 20), 0, 0)
    master['start'] = start.strftime(DATE_TIME_FORMAT)
    master['description'] = random_text(sentences=1)
    master['contact'] = "vicmortelmans+%s@gmail.com" % random_text(words=1)
    master['website'] = "http://www.%s.com" % random_text(words=1)
    master['registration required'] = 'true' if randint(0, 1) == 1 else 'false'
    master['organization'] = random_text(words=randint(0, 4))
    master['owner'] = "vicmortelmans+%s@gmail.com" % random_text(words=1)
    master['moderator'] = "vicmortelmans+%s@gmail.com" % random_text(words=1)
    master['state'] = "new"
    master['sequence'] = "0"
    master['entry date'] = datetime.today().strftime(DATE_TIME_FORMAT)
    master['update date'] = datetime.today().strftime(DATE_TIME_FORMAT)
    master['renewal date'] = (datetime.today() + timedelta(days=30 * 6)).strftime(DATE_TIME_FORMAT)
    master['location name'] = random_text(words=randint(1, 4))
    postal_code = randint(1000,9999)
    master['address'] = "%s %d, %d %s" % (random_text(words=1), randint(1,100), postal_code, random_text(words=1))
    master['postal code'] = postal_code
    master['latitude'] = float(randint(50734, 51444)) / 1000
    master['longitude'] = float(randint(2547, 5840)) / 1000
    master['location slug'] = location_slug(master)
    master['location details'] = random_text(words=randint(0,4))
    if configuration:
        master['tags'] = random_tags(configuration['tags'])
    else:
        master['tags'] = ''
    master['hashtags'] = random_text(words=randint(0, 1))
    # second
    multi_day = True if randint(1, 10) < 2 else False
    if multi_day:
        master['end'] = (start + timedelta(hours=randint(0, 3), days=randint(1, 7))).strftime(DATE_TIME_FORMAT)
        master['calendar rule'] = ''
    else:
        master['end'] = (start + timedelta(hours=randint(1, 3))).strftime(DATE_TIME_FORMAT)
        chance = randint(1, 10)
        if chance < 3:
            master['calendar rule'] = "RRULE:FREQ=DAILY;UNTIL=%s" % (start + timedelta(days=30 * 6)).strftime(ISO_DATE_TIME_FORMAT)
        elif chance < 7:
            master['calendar rule'] = "RRULE:FREQ=WEEKLY;BYDAY=%s;COUNT=16" % {0: 'MO', 1: 'TU', 2: 'WE', 3: 'TH', 4: 'FR', 5: 'SA', 6: 'SU'}[start.weekday()]
        else:
            master['calendar rule'] = "RRULE:FREQ=MONTHLY;BYMONTHDAY=%d" % start.day
    master['event name'] = "%s %s" % (master['location name'], master['calendar rule'])
    master['event slug'] = slugify("%s %s" % (master['location slug'], master['event name']))
    return master


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

