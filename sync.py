import webapp2
import logging
from datetime import datetime
from datetime import timedelta
import customer_configuration
import fusion_tables
import time
from apiclient.errors import HttpError

logging.basicConfig(level=logging.INFO)

FUSION_TABLE_DATE_TIME_FORMAT = fusion_tables.FUSION_TABLE_DATE_TIME_FORMAT


def sync_new_events(configuration, condition):
    new = fusion_tables.select(configuration['master table'], condition=condition)
    logging.info("Syncing %d new rows in %s" % (len(new), configuration['master table']))
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
    fusion_tables.insert_go(configuration['slave table'])
    logging.info("Done syncing new rows in %s" % configuration['master table'])


def sync_updated_events(configuration, condition):
    updated = fusion_tables.select(configuration['master table'], condition=condition)
    logging.info("Syncing %d updated rows in %s" % (len(updated), configuration['master table']))
    for row in updated:
        # delete old slave rows
        condition = "'event slug' = '%s'" % row['event slug']  # assuming that 'event slug' was not updated !!!
        slaves = fusion_tables.select(configuration['slave table'], cols=['rowid'], condition=condition)
        for slave in slaves:
            for attempt in range(3):
                try:
                    fusion_tables.delete_with_implicit_rowid(configuration['slave table'], slave)
                except HttpError:
                    time.sleep(5)  # arbitrary pause to avoid "Rate Limit Exceeded" error
                else:
                    break
            else:
                raise
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
    fusion_tables.insert_go(configuration['slave table'])
    logging.info("Done syncing updated rows in %s" % configuration['master table'])



class SyncHandler(webapp2.RequestHandler):
    def get(self):
        configurations = customer_configuration.get_configurations()
        for configuration in configurations:

            # in the master table, find all new events
            condition = "'state' = 'new'"
            sync_new_events(configuration, condition)

            # in the master table, find all updated events
            condition = "'state' = 'updated'"
            sync_updated_events(configuration, condition)

            # in the master table, find all cancelled events
            condition = "'state' = 'cancelled'"
            cancelled = fusion_tables.select(configuration['master table'], condition=condition)
            logging.info("Syncing %d cancelled rows in %s" % (len(cancelled), configuration['master table']))
            for row in cancelled:
                # delete cancelled slave rows
                condition = "'event slug' = '%s'" % row['event slug']
                slaves = fusion_tables.select(configuration['slave table'], cols=['rowid'], condition=condition)
                for slave in slaves:
                    fusion_tables.delete_with_implicit_rowid(configuration['slave table'], slave)
                # set master event state to 'cancellation'
                update = {
                    'rowid': row['rowid'],
                    'state': 'cancellation',
                    'sync date': datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
                }
                fusion_tables.update_with_implicit_rowid(configuration['master table'], update)
            logging.info("Done syncing cancelled rows in %s" % configuration['master table'])

            # in the master table, find all cancellations older than one month
            today_minus_one_month = (datetime.today() - timedelta(days=30)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
            condition = "'state' = 'cancellation' and 'update date' < '%s'" % today_minus_one_month
            cancellation = fusion_tables.select(configuration['master table'], condition=condition)
            logging.info("Syncing %d cancellation rows in %s" % (len(cancellation), configuration['master table']))
            for row in cancellation:
                # delete cancellation master rows
                fusion_tables.delete_with_implicit_rowid(configuration['master table'], row)
            logging.info("Done syncing cancellation rows in %s" % configuration['master table'])

            # in the master table, find all events with outdated sync
            today_minus_one_month = (datetime.today() - timedelta(days=30)).strftime(FUSION_TABLE_DATE_TIME_FORMAT)
            condition = "'state' = 'public' and 'sync date' < '%s'" % today_minus_one_month
            updated = fusion_tables.select(configuration['master table'], condition=condition)
            logging.info("Syncing outdated public rows in %s" % configuration['master table'])
            for row in updated:
                # delete old slave rows
                condition = "'event slug' = '%s'" % row['event slug']
                slaves = fusion_tables.select(configuration['slave table'], cols=['rowid'], condition=condition)
                for slave in slaves:
                    fusion_tables.delete_with_implicit_rowid(configuration['slave table'], slave)
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
                    'final_date': final_date
                }
                fusion_tables.update_with_implicit_rowid(configuration['master table'], update)
            fusion_tables.insert_go(configuration['slave table'])
            logging.info("Done syncing outdated public rows in %s" % configuration['master table'])

            # in the master table, find all events with final date in the past
            today = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
            condition = "'final date' < '%s'" % today
            outdated = fusion_tables.select(configuration['master table'], condition=condition)
            logging.info("Deleting %d past events in master (and slave) %s" % (len(outdated), configuration['master table']))
            for row in outdated:
                # delete old slave rows
                condition = "'event slug' = '%s'" % row['event slug']
                slaves = fusion_tables.select(configuration['slave table'], cols=['rowid'], condition=condition)
                for slave in slaves:
                    fusion_tables.delete_with_implicit_rowid(configuration['slave table'], slave)
                # delete cancellation master rows
                fusion_tables.delete_with_implicit_rowid(configuration['master table'], row)
            logging.info("Done deleting past events in master (and slave) %s" % configuration['master table'])

            # in the slave table, find all events with end date in the past
            today = datetime.today().strftime(FUSION_TABLE_DATE_TIME_FORMAT)
            condition = "'end' < '%s'" % today
            outdated = fusion_tables.select(configuration['slave table'], condition=condition)
            logging.info("Deleting %d past events in slave %s" % (len(outdated), configuration['slave table']))
            for row in outdated:
                # delete slave row
                fusion_tables.delete_with_implicit_rowid(configuration['slave table'], row)
            logging.info("Done deleting past events in slave %s" % configuration['master table'])

            # return the web-page content
            self.response.out.write("SyncHandler finished")
            return


class LoadHandler(webapp2.RequestHandler):
    def get(self):
        configuration = customer_configuration.get_configuration(self.request)
        count = self.request.get('count')
        for i in xrange(0, int(count)):
            master = fusion_tables.random_master(configuration)
            fusion_tables.insert_hold(configuration['master table'], master)
        fusion_tables.insert_go(configuration['master table'])

        # return the web-page content
        self.response.out.write("LoadHandler finished")
        return
