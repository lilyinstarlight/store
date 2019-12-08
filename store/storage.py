import logging
import os
import os.path
import random
import string

import fooster.db

from store import config


log = logging.getLogger('store')

trunk = config.dir + '/'
path = trunk + 'upload'
lib = trunk + 'db'

max_tries = 10

ns_db = None


def nsfile(namespace):
    if namespace == '/':
        return trunk + 'root.db'
    else:
        return lib + namespace + '.db'


def open(namespace):
    if namespace not in ns_db:
        raise KeyError(namespace)
    return fooster.db.Database(nsfile(namespace), ['alias', 'filename', 'type', 'size', 'date', 'expire', 'locked'])


def namespaces():
    return ns_db.keys()


def values(namespace):
    return iter(open(namespace))


def rand():
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(config.random))


def create(namespace, alias=None):
    if namespace not in ns_db:
        ns_db.add(namespace)
    db = open(namespace)

    if alias is None:
        alias = rand()
        count = 1
        while alias in db:
            alias = rand()
            count += 1

            if count > max_tries:
                raise RuntimeError('max tries for random alias generation exceeded')

    return db.add(alias, '', '', 0, 0, 0)


def retrieve(namespace, alias):
    db = open(namespace)

    return db[alias]


def remove(namespace, alias):
    db = open(namespace)

    if namespace == '/':
        storepath = path + namespace
    else:
        storepath = path + namespace + '/'

    try:
        os.remove(storepath + alias)
    except Exception:
        log.exception('Caught exception while trying to remove stored file at "' + storepath + alias + '"')

    del db[alias]

    if len(db) == 0:
        storedir = os.path.dirname(storepath)
        if not os.path.samefile(storedir, path):
            try:
                while not os.path.samefile(storedir, path) and len(os.listdir(storedir)) == 0:
                    os.rmdir(storedir)
                    storedir = os.path.dirname(storedir)
            except Exception:
                log.exception('Caught exception while trying to remove storage directory at "' + storedir + '"')

        del ns_db[namespace]

        dbfile = nsfile(namespace)

        os.remove(dbfile)

        dbdir = os.path.dirname(dbfile)
        if not os.path.samefile(dbdir, trunk):
            try:
                while not os.path.samefile(dbdir, lib) and len(os.listdir(dbdir)) == 0:
                    os.rmdir(dbdir)
                    dbdir = os.path.dirname(dbdir)
            except Exception:
                log.exception('Caught exception while trying to remove database directory at "' + dbdir + '"')


ns_db = fooster.db.Database(trunk + 'ns.db', ['namespace'])
