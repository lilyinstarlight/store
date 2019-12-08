import argparse
import logging
import multiprocessing
import signal
import sys

import fooster.web

from store import config


def main():
    parser = argparse.ArgumentParser(description='serve up a timed storage service')
    parser.add_argument('-a', '--address', dest='address', help='address to bind')
    parser.add_argument('-p', '--port', type=int, dest='port', help='port to bind')
    parser.add_argument('-t', '--template', dest='template', help='template directory to use')
    parser.add_argument('-l', '--log', dest='log', help='log directory to use')
    parser.add_argument('-m', '--minute', dest='minute', help='minute of hour to prune files')
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


    # setup logging
    log = logging.getLogger('store')
    log.setLevel(logging.INFO)
    if config.log:
        log.addHandler(logging.FileHandler(config.log))
    else:
        log.addHandler(logging.StreamHandler(sys.stdout))

    if config.http_log:
        http_log_handler = logging.FileHandler(config.http_log)
        http_log_handler.setFormatter(fooster.web.HTTPLogFormatter())

        logging.getLogger('http').addHandler(http_log_handler)


    from store import name, version
    from store import http, pruner

    log.info(name + ' ' + version + ' starting...')

    # ignore SIGINT in manager
    orig_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
    sync = multiprocessing.Manager()
    signal.signal(signal.SIGINT, orig_sigint)

    # start everything
    http.start(sync=sync)
    pruner.start(sync=sync)


    # cleanup function
    def exit(signum, frame):
        pruner.stop()
        http.stop()


    # use the function for both SIGINT and SIGTERM
    for sig in signal.SIGINT, signal.SIGTERM:
        signal.signal(sig, exit)

    # join against the HTTP server
    http.join()


if __name__ == '__main__':
    main()
