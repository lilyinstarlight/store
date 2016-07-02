import time

from store.lib import cron

from store import config, log, storage


scheduler = None


def prune():
    date = time.time()

    for entry in storage.values():
        if entry.expire <= date:
            # ignore errors and keep going
            try:
                storage.remove(entry.alias)
            except:
                pass


def start():
    global scheduler

    scheduler = cron.Scheduler(log=log.storelog)
    scheduler.add(cron.Job(prune, minute=config.minute))
    scheduler.start()


def stop():
    global scheduler

    scheduler.stop()
    scheduler = None
