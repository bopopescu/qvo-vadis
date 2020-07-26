import webapp2
import logging
from datetime import datetime
from datetime import timedelta
import customer_configuration
import fusion_tables
from google.appengine.api import mail
from lib import DEV


FUSION_TABLE_DATE_TIME_FORMAT = fusion_tables.FUSION_TABLE_DATE_TIME_FORMAT

_start_time = False


class RunningTooLongError(Exception):
    pass


def sync_new_events(configuration, condition, don_t_run_too_long=False):
    new = fusion_tables.select(configuration['main table'], condition=condition)
    logging.info("Syncing %d new rows in %s main %s" % (len(new), configuration['id'], configuration['main table']))
    for row in new:
        # create subordinate dicts
        (subordinates, final_date) = fusion_tables.main_to_subordinate(row)
        # store subordinate dicts
        for subordinate in subordinates:
            fusion_tables.insert_hold(configuration['subordinate table'], subordinate)
            # set main event state to 'public'
        update = {
            'rowid': row['rowid'],
            'state': 'public',
            'sync date': datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT),
            'final date': final_date
        }
        fusion_tables.update_with_implicit_rowid(configuration['main table'], update)
        running_too_long(don_t_run_too_long)
    fusion_tables.insert_go(configuration['subordinate table'])
    logging.info("Done syncing new rows in %s main %s" % (configuration['id'], configuration['main table']))


def sync_updated_events(configuration, condition, don_t_run_too_long=False):
    updated = fusion_tables.select(configuration['main table'], condition=condition)
    logging.info("Syncing %d updated rows in %s main %s" % (len(updated), configuration['id'], configuration['main table']))
    for row in updated:
        # old rows are not deleted! New subordinate rows are just added with incremented sequence number
        # create subordinate dicts
        (subordinates, final_date) = fusion_tables.main_to_subordinate(row)
        # store subordinate dicts
        for subordinate in subordinates:
            fusion_tables.insert_hold(configuration['subordinate table'], subordinate)
        # delete the old main row (the updated row was a copy!)
        condition = "'event slug' = '%s' and 'state' = 'public'" % row['event slug']
        old = fusion_tables.select(configuration['main table'], cols=['rowid'], condition=condition)
        for old_row in old:  # should be only a single row!!
            fusion_tables.delete_with_implicit_rowid(configuration['main table'], old_row)
        # set main event state to 'public'
        update = {
            'rowid': row['rowid'],
            'state': 'public',
            'sync date': datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT),
            'final date': final_date
        }
        fusion_tables.update_with_implicit_rowid(configuration['main table'], update)
        running_too_long(don_t_run_too_long)
    fusion_tables.insert_go(configuration['subordinate table'])
    logging.info("Done syncing updated rows in %s main %s" % (configuration['id'], configuration['main table']))


def sync_cancelled_events(configuration, condition):
    cancelled = fusion_tables.select(configuration['main table'], condition=condition)
    logging.info("Syncing %d cancelled rows in %s main %s" % (len(cancelled), configuration['id'], configuration['main table']))
    for row in cancelled:
        # delete cancelled subordinate rows
        condition = "'event slug' = '%s'" % row['event slug']
        subordinates = fusion_tables.select(configuration['subordinate table'], cols=['rowid'], condition=condition, filter_obsolete_rows=False)
        logging.info("Deleting %d cancelled rows in %s subordinate %s" % (len(subordinates), configuration['id'], configuration['subordinate table']))
        delete_subordinates(configuration['subordinate table'], subordinates)
        # set main event state to 'cancellation'
        update = {
            'rowid': row['rowid'],
            'state': 'cancellation',
            'sync date': datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
        }
        fusion_tables.update_with_implicit_rowid(configuration['main table'], update)
        running_too_long(don_t_run_too_long=True)
    logging.info("Done syncing cancelled rows in %s main %s" % (configuration['id'], configuration['main table']))


def sync_one_month_old_cancellations(configuration, condition):
    cancellation = fusion_tables.select(configuration['main table'], condition=condition)
    logging.info("Syncing %d cancellation rows in %s main %s" % (len(cancellation), configuration['id'], configuration['main table']))
    for row in cancellation:
        # delete cancellation main rows
        fusion_tables.delete_with_implicit_rowid(configuration['main table'], row)
    logging.info("Done syncing cancellation rows in %s main %s" % (configuration['id'], configuration['main table']))
    running_too_long(don_t_run_too_long=True)


def sync_outdated_events(configuration, condition):
    outdated = fusion_tables.select(configuration['main table'], condition=condition)
    logging.info("Syncing %d outdated public rows in %s main %s" % (len(outdated), configuration['id'], configuration['main table']))
    for row in outdated:
        # select old subordinate rows
        condition = "'event slug' = '%s'" % row['event slug']
        subordinates = fusion_tables.select(configuration['subordinate table'], cols=['datetime slug'], condition=condition, filter_obsolete_rows=False)
        # create subordinate dicts
        datetime_slugs = [subordinate['datetime slug'] for subordinate in subordinates]
        (new_subordinates, final_date) = fusion_tables.main_to_subordinate(row)
        # store subordinate dicts
        logging.info("Inserting approx. %d future rows in %s subordinate %s" % (len(new_subordinates) - len(subordinates), configuration['id'], configuration['subordinate table']))
        for new_subordinate in new_subordinates:
            if new_subordinate['datetime slug'] not in datetime_slugs:
                fusion_tables.insert_hold(configuration['subordinate table'], new_subordinate)
            # set main event state to 'public'
        update = {
            'rowid': row['rowid'],
            'state': 'public',
            'sync date': datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT),
            'final date': final_date
        }
        logging.info("Updated sync timestamp and final date in regenerated row in %s main %s" % (configuration['id'], configuration['main table']))
        fusion_tables.update_with_implicit_rowid(configuration['main table'], update)
        running_too_long(don_t_run_too_long=True)
    fusion_tables.insert_go(configuration['subordinate table'])
    logging.info("Done syncing outdated public rows in %s main %s" % (configuration['id'], configuration['main table']))


def sync_events_with_final_date_passed(configuration, condition):
    outdated = fusion_tables.select(configuration['main table'], condition=condition)
    logging.info("Deleting %d finally past events in %s main (and subordinate) %s" % (len(outdated), configuration['id'], configuration['main table']))
    for row in outdated:
        # delete old subordinate rows
        condition = "'event slug' = '%s'" % row['event slug']
        subordinates = fusion_tables.select(configuration['subordinate table'], cols=['rowid'], condition=condition, filter_obsolete_rows=False)
        logging.info("Deleting %d finally past events in %s subordinate %s" % (len(subordinates), configuration['id'], configuration['subordinate table']))
        delete_subordinates(configuration['subordinate table'], subordinates)
        # delete cancellation main rows
        fusion_tables.delete_with_implicit_rowid(configuration['main table'], row)
        running_too_long(don_t_run_too_long=True)
    logging.info("Done deleting finally past events in %s main (and subordinate) %s" % (configuration['id'], configuration['main table']))


def sync_passed_events(configuration, condition):
    outdated = fusion_tables.select(configuration['subordinate table'], condition=condition, filter_obsolete_rows=False)
    logging.info("Deleting %d past events in %s subordinate %s" % (len(outdated), configuration['id'], configuration['subordinate table']))
    delete_subordinates(configuration['subordinate table'], outdated)
    logging.info("Done deleting past events in %s subordinate %s" % (configuration['id'], configuration['main table']))
    running_too_long(don_t_run_too_long=True)


def sync_old_version_of_updated_events(configuration, condition):
    updated_main = fusion_tables.select(configuration['main table'], condition=condition)
    logging.info("Deleting old subordinate rows for %d updated events in %s main %s" % (len(updated_main), configuration['id'], configuration['main table']))
    for updated_main_row in updated_main:
        # find the old subordinate row(s)
        condition = "'event slug' = '%s' AND 'sequence' < %s" % (updated_main_row['event slug'], updated_main_row['sequence'])
        old_subordinate = fusion_tables.select(configuration['subordinate table'], condition=condition, filter_obsolete_rows=False)
        # delete the old row(s)
        logging.info("Deleting %d old event rows in %s subordinate %s" % (len(old_subordinate), configuration['id'], configuration['subordinate table']))
        delete_subordinates(configuration['subordinate table'], old_subordinate)
        logging.info("Deleted %d old rows in %s subordinate %s" % (len(old_subordinate), configuration['id'], configuration['subordinate table']))
        # unflag the updated main row
        unflagged_row = {}
        unflagged_row['rowid'] = updated_main_row['rowid']
        unflagged_row['update after sync'] = 'false'
        fusion_tables.update_with_implicit_rowid(configuration['main table'], unflagged_row)
        logging.info("Unflagged updated row %s in %s main %s" % (updated_main_row['rowid'], configuration['id'], configuration['main table']))
        running_too_long(don_t_run_too_long=True)
    logging.info("Done deleting old subordinate rows in %s subordinate %s" % (configuration['id'], configuration['subordinate table']))


def delete_subordinates(tableId, subordinates):
    for subordinate in subordinates:
        fusion_tables.delete_with_implicit_rowid(tableId, subordinate)


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
            configurations = [customer_configuration.get_configuration(self.request)]
        else:
            configurations = customer_configuration.get_configurations()
        running_too_long(initialize=True)  # initialize

        try:
            logging.info("Start syncing")

            for configuration in [c for c in configurations if c['id'] != 'www']:
                # www is a fake configuration!
                logging.info("Start syncing %s" % configuration['id'])

                # in the main table, find all new events
                condition = "'state' = 'new'"
                sync_new_events(configuration, condition, don_t_run_too_long=True)

                # in the main table, find all updated events
                condition = "'state' = 'updated'"
                sync_updated_events(configuration, condition, don_t_run_too_long=True)

                # in the main table, find all cancelled events
                condition = "'state' = 'cancelled'"
                sync_cancelled_events(configuration, condition)

                # in the main table, find all cancellations older than one month
                today_minus_one_month = (datetime.today() - timedelta(days=30)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                condition = "'state' = 'cancellation' and 'update date' < '%s'" % today_minus_one_month
                sync_one_month_old_cancellations(configuration, condition)

                # in the main table, find all events with outdated sync
                today_minus_one_month = (datetime.today() - timedelta(days=30)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                condition = "'state' = 'public' and 'sync date' < '%s'" % today_minus_one_month
                sync_outdated_events(configuration, condition)

                # in the main table, find all events with final date in the past (*)
                yesterday = (datetime.today() - timedelta(days=1)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                condition = "'final date' < '%s'" % yesterday
                sync_events_with_final_date_passed(configuration, condition)

                # in the subordinate table, find all events with end date in the past (*)
                yesterday = (datetime.today() - timedelta(days=1)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                condition = "'end' < '%s'" % yesterday
                sync_passed_events(configuration, condition)

                # in the main table, find all events flagged as updated (flag is set in submit.py)
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
            fusion_tables.insert_go(configuration['subordinate table'])
            # then quit
            self.response.out.write("SyncHandler finished with leftovers")
            return


class SyncOldVersionOfUpdatedEventsHandler(webapp2.RequestHandler):
    def get(self, event_slug=None):
        logging.info("Start deleting old version of updated events (probably a queued request from submit.py")

        configuration = customer_configuration.get_configuration(self.request)

        # in the main table, find all events flagged as updated for the submitted event
        condition = "'event slug' = '%s'" % event_slug
        sync_old_version_of_updated_events(configuration, condition)

        logging.info("Done deleting old version of updated events.")

        # return the web-page content
        self.response.out.write("SyncOldVersionOfUpdatedEventsHandler finished")
        return


class SyncAllHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("Start syncing all by force. For this operation to have effect, you have to delete the subordinate rows manually first!")
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

                # in the main table, find all events with outdated sync
                condition = "'state' = 'public' ORDER BY 'sync date'"
                sync_outdated_events(configuration, condition)

            logging.info("Done syncing by force")

            # return the web-page content
            self.response.out.write("SyncHandler by force finished")
            return

        except RunningTooLongError:
            # first release pending inserts!
            fusion_tables.insert_go(configuration['subordinate table'])
            # then quit
            self.response.out.write("SyncHandler by force finished with leftovers")
            return


class LoadHandler(webapp2.RequestHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        count = self.request.get('count')
        for i in xrange(0, int(count)):
            main = fusion_tables.random_main(configuration)
            fusion_tables.insert_hold(configuration['main table'], main)
        fusion_tables.insert_go(configuration['main table'])

        # return the web-page content
        self.response.out.write("LoadHandler finished")
        return


class StartHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("Starting instance")
        self.response.out.write("Instance started")
