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



class StartHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("Starting instance")
        self.response.out.write("Instance started")
