import webapp2
import logging
from datetime import datetime
from datetime import timedelta
import customer_map
from lib import DEV
import model
from google.appengine.ext import ndb


_start_time = False


class RunningTooLongError(Exception):
    pass

"""
def sync_new_events(configuration, condition, don_t_run_too_long=False):
    new = fusion_tables.select(configuration['master table'], condition=condition)
    logging.info("Syncing %d new rows in %s master %s" % (len(new), configuration['id'], configuration['master table']))
    for row in new:
        # create slave dicts
        (slaves, final_date) = fusion_tables.master_to_slave(row)
        # store slave dicts
        for slave in slaves:
            fusion_tables.insert_hold(configuration['slave table'], slave)
            # set master event state to 'public'
        update = {
            'rowid': row['rowid'],
            'state': 'public',
            'sync date': datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT),
            'final date': final_date
        }
        fusion_tables.update_with_implicit_rowid(configuration['master table'], update)
        running_too_long(don_t_run_too_long)
    fusion_tables.insert_go(configuration['slave table'])
    logging.info("Done syncing new rows in %s master %s" % (configuration['id'], configuration['master table']))
"""
"""
def sync_updated_events(configuration, condition, don_t_run_too_long=False):
    updated = fusion_tables.select(configuration['master table'], condition=condition)
    logging.info("Syncing %d updated rows in %s master %s" % (len(updated), configuration['id'], configuration['master table']))
    for row in updated:
        # old rows are not deleted! New slave rows are just added with incremented sequence number
        # create slave dicts
        (slaves, final_date) = fusion_tables.master_to_slave(row)
        # store slave dicts
        for slave in slaves:
            fusion_tables.insert_hold(configuration['slave table'], slave)
        # delete the old master row (the updated row was a copy!)
        condition = "'event slug' = '%s' and 'state' = 'public'" % row['event slug']
        old = fusion_tables.select(configuration['master table'], cols=['rowid'], condition=condition)
        for old_row in old:  # should be only a single row!!
            fusion_tables.delete_with_implicit_rowid(configuration['master table'], old_row)
        # set master event state to 'public'
        update = {
            'rowid': row['rowid'],
            'state': 'public',
            'sync date': datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT),
            'final date': final_date
        }
        fusion_tables.update_with_implicit_rowid(configuration['master table'], update)
        running_too_long(don_t_run_too_long)
    fusion_tables.insert_go(configuration['slave table'])
    logging.info("Done syncing updated rows in %s master %s" % (configuration['id'], configuration['master table']))
"""
"""
def sync_cancelled_events(configuration, condition):
    cancelled = fusion_tables.select(configuration['master table'], condition=condition)
    logging.info("Syncing %d cancelled rows in %s master %s" % (len(cancelled), configuration['id'], configuration['master table']))
    for row in cancelled:
        # delete cancelled slave rows
        condition = "'event slug' = '%s'" % row['event slug']
        slaves = fusion_tables.select(configuration['slave table'], cols=['rowid'], condition=condition, filter_obsolete_rows=False)
        logging.info("Deleting %d cancelled rows in %s slave %s" % (len(slaves), configuration['id'], configuration['slave table']))
        delete_slaves(configuration['slave table'], slaves)
        # set master event state to 'cancellation'
        update = {
            'rowid': row['rowid'],
            'state': 'cancellation',
            'sync date': datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        }
        fusion_tables.update_with_implicit_rowid(configuration['master table'], update)
        running_too_long(don_t_run_too_long=True)
    logging.info("Done syncing cancelled rows in %s master %s" % (configuration['id'], configuration['master table']))
"""
"""
def sync_one_month_old_cancellations(configuration, condition):
    cancellation = fusion_tables.select(configuration['master table'], condition=condition)
    logging.info("Syncing %d cancellation rows in %s master %s" % (len(cancellation), configuration['id'], configuration['master table']))
    for row in cancellation:
        # delete cancellation master rows
        fusion_tables.delete_with_implicit_rowid(configuration['master table'], row)
    logging.info("Done syncing cancellation rows in %s master %s" % (configuration['id'], configuration['master table']))
    running_too_long(don_t_run_too_long=True)
"""

"""
def sync_events_with_final_date_passed(configuration, condition):
    outdated = fusion_tables.select(configuration['master table'], condition=condition)
    logging.info("Deleting %d finally past events in %s master (and slave) %s" % (len(outdated), configuration['id'], configuration['master table']))
    for row in outdated:
        # delete old slave rows
        condition = "'event slug' = '%s'" % row['event slug']
        slaves = fusion_tables.select(configuration['slave table'], cols=['rowid'], condition=condition, filter_obsolete_rows=False)
        logging.info("Deleting %d finally past events in %s slave %s" % (len(slaves), configuration['id'], configuration['slave table']))
        delete_slaves(configuration['slave table'], slaves)
        # delete cancellation master rows
        fusion_tables.delete_with_implicit_rowid(configuration['master table'], row)
        running_too_long(don_t_run_too_long=True)
    logging.info("Done deleting finally past events in %s master (and slave) %s" % (configuration['id'], configuration['master table']))
"""

"""
def sync_passed_events(configuration, condition):
    outdated = fusion_tables.select(configuration['slave table'], condition=condition, filter_obsolete_rows=False)
    logging.info("Deleting %d past events in %s slave %s" % (len(outdated), configuration['id'], configuration['slave table']))
    delete_slaves(configuration['slave table'], outdated)
    logging.info("Done deleting past events in %s slave %s" % (configuration['id'], configuration['master table']))
    running_too_long(don_t_run_too_long=True)
"""

"""
def sync_old_version_of_updated_events(configuration, condition):
    updated_master = fusion_tables.select(configuration['master table'], condition=condition)
    logging.info("Deleting old slave rows for %d updated events in %s master %s" % (len(updated_master), configuration['id'], configuration['master table']))
    for updated_master_row in updated_master:
        # find the old slave row(s)
        condition = "'event slug' = '%s' AND 'sequence' < %s" % (updated_master_row['event slug'], updated_master_row['sequence'])
        old_slave = fusion_tables.select(configuration['slave table'], condition=condition, filter_obsolete_rows=False)
        # delete the old row(s)
        logging.info("Deleting %d old event rows in %s slave %s" % (len(old_slave), configuration['id'], configuration['slave table']))
        delete_slaves(configuration['slave table'], old_slave)
        logging.info("Deleted %d old rows in %s slave %s" % (len(old_slave), configuration['id'], configuration['slave table']))
        # unflag the updated master row
        unflagged_row = {}
        unflagged_row['rowid'] = updated_master_row['rowid']
        unflagged_row['update after sync'] = 'false'
        fusion_tables.update_with_implicit_rowid(configuration['master table'], unflagged_row)
        logging.info("Unflagged updated row %s in %s master %s" % (updated_master_row['rowid'], configuration['id'], configuration['master table']))
        running_too_long(don_t_run_too_long=True)
    logging.info("Done deleting old slave rows in %s slave %s" % (configuration['id'], configuration['slave table']))
"""

"""
def delete_slaves(tableId, slaves):
    for slave in slaves:
        fusion_tables.delete_with_implicit_rowid(tableId, slave)
"""

def running_too_long(initialize=False, don_t_run_too_long=False):
    global _start_time
    if initialize or not _start_time:
        _start_time = datetime.now()
    elif don_t_run_too_long:
        minutes_running = (datetime.now() - _start_time).total_seconds() / 60
        if not DEV and minutes_running > 40:
            # running 12 times a day, this will give at max 9 instance hours
            # debugger can run as long as he wants, no quota :)
            logging.warning("Sync running for %d minutes now... going to quit!" % minutes_running)
            raise RunningTooLongError()
        else:
            logging.debug("Sync running for %d minutes now..." % minutes_running)


class SyncHandler(webapp2.RequestHandler):
    def get(self):
        if self.request.get('id'):
            # for debugging, to limit sync to specific table
            maps = [customer_map.get_map(self.request)]
        else:
            maps = customer_map.get_maps()

        running_too_long(initialize=True)  # initialize

        try:
            logging.info("Start syncing")

            for map in [m for m in maps if m.key.id() != 'www']:
                # www is a fake configuration!
                logging.info("Start syncing %s" % map.key.id())
                yesterday = datetime.today() - timedelta(days=1)
                today_minus_one_month = datetime.today() - timedelta(days=30)

                # find all events with outdated sync
                query = model.Event.query(model.Event.sync_date < today_minus_one_month, model.Event.map == map.key)
                logging.info("Syncing outdated events in %s" % map.key.id())
                for event in query:
                    logging.info("Syncing event %s" % event.key.id())
                    event.generate_and_store_instances(start_from_final_date=True)
                    if event.final_date < yesterday:
                        # the event is passed
                        logging.info("Deleting event %s as it is passed" % event.key.id())
                        event.key.delete()
                logging.info("Done syncing outdated events in %s" % map.key.id())

                # find all instances with end date in the past (*)
                # (*) yesterday, because this is running server time, and other timezones in the world
                # still need the event, while for the server it's already 'past'
                logging.info("Deleting passed instances in %s" % map.key.id())
                instance_keys = model.Instance.query(model.Instance.end_utc < yesterday, model.Instance.map == map.key).fetch(keys_only=True)
                ndb.delete_multi(instance_keys)
                logging.info("Done deleting passed instances in %s" % map.key.id())


            logging.info("Done syncing")

            # return the web-page content
            self.response.out.write("SyncHandler for qvo-vadis version datastore done")

            return

        except RunningTooLongError:
            self.response.out.write("SyncHandler finished with leftovers")
            return

"""
        if self.request.get('id'):
            # for debugging, to limit sync to specific table
            configurations = [customer_configuration.get_configuration(self.request)]
        else:
            configurations = customer_configuration.get_configurations()
        running_too_long(initialize=True)  # initialize

        try:
            logging.info("Start syncing")

            for configuration in [c for c in configurations if c['id'] != 'www']:
                # www is a fake configuration!
                logging.info("Start syncing %s" % configuration['id'])

                # in the master table, find all new events
                condition = "'state' = 'new'"
                sync_new_events(configuration, condition, don_t_run_too_long=True)

                # in the master table, find all updated events
                condition = "'state' = 'updated'"
                sync_updated_events(configuration, condition, don_t_run_too_long=True)

                # in the master table, find all cancelled events
                condition = "'state' = 'cancelled'"
                sync_cancelled_events(configuration, condition)

                # in the master table, find all cancellations older than one month
                today_minus_one_month = (datetime.today() - timedelta(days=30)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                condition = "'state' = 'cancellation' and 'update date' < '%s'" % today_minus_one_month
                sync_one_month_old_cancellations(configuration, condition)

                # in the master table, find all events with outdated sync
                today_minus_one_month = (datetime.today() - timedelta(days=30)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                condition = "'state' = 'public' and 'sync date' < '%s'" % today_minus_one_month
                sync_outdated_events(configuration, condition)

                # in the master table, find all events with final date in the past (*)
                yesterday = (datetime.today() - timedelta(days=1)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                condition = "'final date' < '%s'" % yesterday
                sync_events_with_final_date_passed(configuration, condition)

                # in the slave table, find all events with end date in the past (*)
                yesterday = (datetime.today() - timedelta(days=1)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                condition = "'end' < '%s'" % yesterday
                sync_passed_events(configuration, condition)

                # in the master table, find all events flagged as updated (flag is set in submit.py)
                condition = "'update after sync' = 'true'"
                sync_old_version_of_updated_events(configuration, condition)

                # (*) yesterday, because this is running server time, and other timezones in the world
                # still need the event, while for the server it's already 'past'

            logging.info("Done syncing")

            # return the web-page content
            self.response.out.write("SyncHandler finished")
            return

        except RunningTooLongError:
            # first release pending inserts!
            fusion_tables.insert_go(configuration['slave table'])
            # then quit
            self.response.out.write("SyncHandler finished with leftovers")
            return
"""

"""
class SyncOldVersionOfUpdatedEventsHandler(webapp2.RequestHandler):
    def get(self, event_slug=None):
        logging.info("Start deleting old version of updated events (probably a queued request from submit.py")

        configuration = customer_configuration.get_configuration(self.request)

        # in the master table, find all events flagged as updated for the submitted event
        condition = "'event slug' = '%s'" % event_slug
        sync_old_version_of_updated_events(configuration, condition)

        logging.info("Done deleting old version of updated events.")

        # return the web-page content
        self.response.out.write("SyncOldVersionOfUpdatedEventsHandler finished")
        return

"""

"""
class SyncAllHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("Start syncing all by force. For this operation to have effect, you have to delete the slave rows manually first!")
        if self.request.get('id'):
            # for debugging, to limit sync to specific table
            configurations = [customer_configuration.get_configuration(self.request)]
        else:
            configurations = customer_configuration.get_configurations()
        running_too_long(initialize=True)  # initialize

        try:
            logging.info("Start syncing by force")

            for configuration in [c for c in configurations if c['id'] != 'www']:
                # www is a fake configuration!
                logging.info("Start syncing %s by force" % configuration['id'])

                # in the master table, find all events with outdated sync
                condition = "'state' = 'public' ORDER BY 'sync date'"
                sync_outdated_events(configuration, condition)

            logging.info("Done syncing by force")

            # return the web-page content
            self.response.out.write("SyncHandler by force finished")
            return

        except RunningTooLongError:
            # first release pending inserts!
            fusion_tables.insert_go(configuration['slave table'])
            # then quit
            self.response.out.write("SyncHandler by force finished with leftovers")
            return
"""

class StartHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("Starting instance")
        self.response.out.write("Instance started")
