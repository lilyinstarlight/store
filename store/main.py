import signal

from store import name, version
from store import log, http, pruner


log.storelog.info(name + ' ' + version + ' starting...')

# start everything
http.start()
pruner.start()


# cleanup function
def exit():
    pruner.stop()
    http.stop()


# use the function for both SIGINT and SIGTERM
for sig in signal.SIGINT, signal.SIGTERM:
    signal.signal(sig, exit)
