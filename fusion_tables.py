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


# multiple DELETE in one call not supported
"""
def delete_with_implicit_rowid_hold(table_i, values):
    if table_id not in _deletes:
        _deletes[table_id] = []
    _deletes[table_id].append(values)
    if len(_deletes[table_id]) >= 25:  # must fit in an URL
        delete_with_implicit_rowid_go(table_id)
    return


def delete_with_implicit_rowid_go(table_id):
    if table_id in _deletes and _deletes[table_id]:
        query_list = []
        for row in _deletes[table_id]:
            query_list.append(_SQL.delete(table_id, row_id=row['rowid']))
        query = ';'.join(query_list)
        query_result = _service.query().sql(sql=query).execute()
        if not 'error' in query_result:
            logging.info("Deleted %d rows in %s" % (len(_deletes[table_id]), table_id))
            _deletes[table_id] = []
        else:
            logging.error("Insert of %d rows in %s failed with %s" % (len(_deletes[table_id]), table_id, query_result['error']))
    return
"""

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
                    break
            if not done:
                data['start'] += data['batch_size']
            else:
                break
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


