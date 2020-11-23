import argparse
import logging
import signal

from store import config


def main():
    parser = argparse.ArgumentParser(description='serve up a timed storage service')
    parser.add_argument('-a', '--address', dest='address', help='address to bind')
    parser.add_argument('-p', '--port', type=int, dest='port', help='port to bind')
    parser.add_argument('-t', '--template', dest='template', help='template directory to use')
    parser.add_argument('-l', '--log', dest='log', help='log directory to use')
    parser.add_argument('-m', '--minute', type=int, dest='minute', help='minute of hour to prune files')
    parser.add_argument('-r', '--random', dest='random', help='number of random characters for auto-generated aliases')
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
            config.http_log = None
        else:
            config.log = args.log + '/store.log'
            config.http_log = args.log + '/http.log'

    if args.minute:
        config.minute = args.minute

    if args.random:
        config.random = args.random

    if args.dir:
        config.dir = args.dir

    config._apply()


    from store import __version__
    from store import http, pruner


    log = logging.getLogger('store')

    log.info('store ' + __version__ + ' starting...')

    # start everything
    http.start()
    pruner.start()

    # cleanup function
    def exit(signum, frame):
        http.stop()

    # use the function for both SIGINT and SIGTERM
    for sig in signal.SIGINT, signal.SIGTERM:
        signal.signal(sig, exit)

    # join against the HTTP server
    http.join()

    # stop pruner
    pruner.stop()


if __name__ == '__main__':
    main()
