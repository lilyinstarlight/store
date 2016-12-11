import argparse
import signal

from store import config


parser = argparse.ArgumentParser(description='serve up a timed storage service')
parser.add_argument('-a', '--address', dest='address', help='address to bind')
parser.add_argument('-p', '--port', type=int, dest='port', help='port to bind')
parser.add_argument('-t', '--template', dest='template', help='template directory to use')
parser.add_argument('-l', '--log', dest='log', help='log directory to use')
parser.add_argument('dir', nargs='?', help='directory to store information')

args = parser.parse_args()

if args.address:
    config.addr = (args.address, config.addr[1])

if args.port:
    config.addr = (config.addr[0], args.port)

if args.template:
    config.template = args.template

if args.log:
    if args.log == 'none':
        config.log = None
        config.httplog = None
    else:
        config.log = args.log + '/store.log'
        config.httplog = args.log + '/http.log'

if args.dir:
    config.dir = args.dir


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
