import logging
import os
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

namespace_dbs = {}


def nsfile(namespace):
    if namespace == '/':
        return trunk + 'root.db'
    else:
        return lib + namespace + '.db'


def open(namespace):
    return fooster.db.Database(nsfile(namespace), ['alias', 'filename', 'type', 'size', 'date', 'expire', 'locked'])


def namespaces():
    return iter(namespace_dbs)


def values(namespace):
    return iter(namespace_dbs[namespace])


def create(namespace, alias=None):
    if namespace not in namespace_dbs:
        if namespace not in ns_db:
            ns_db.add(namespace)
        namespace_dbs[namespace] = open(namespace)

    if alias is None:
        rand = lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(config.random))

        alias = rand()
        count = 1
        while alias in namespace_dbs[namespace]:
            alias = rand()
            count += 1

            if count > max_tries:
                raise RuntimeError('max tries for random alias generation exceeded')

    return namespace_dbs[namespace].add(alias, '', '', 0, 0, 0)


def retrieve(namespace, alias):
    if namespace not in namespace_dbs and namespace in ns_db:
        namespace_dbs[namespace] = open(namespace)
    elif namespace not in ns_db and namespace in namespace_dbs:
        del namespace_dbs[namespace]

    return namespace_dbs[namespace][alias]


def remove(namespace, alias):
    if namespace == '/':
        storepath = path + namespace
    else:
        storepath = path + namespace + '/'

    try:
        os.remove(storepath + alias)
    except:
        log.exception()

    del namespace_dbs[namespace][alias]

    if len(namespace_dbs[namespace]) == 0:
        try:
            os.removedirs(storepath)
        except:
            log.exception()

        del namespace_dbs[namespace]
        del ns_db[namespace]

        dbfile = nsfile(namespace)

        os.remove(dbfile)

        try:
            os.removedirs(os.path.dirname(dbfile))
        except:
            log.exception()


ns_db = fooster.db.Database(trunk + 'ns.db', ['namespace'])

for entry in ns_db:
    namespace_dbs[entry.namespace] = open(entry.namespace)
