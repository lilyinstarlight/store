import os
import random
import string


from store import config, log

from store.lib import db


path = config.dir + 'upload'
lib = config.dir + 'db'
trunk = config.dir

ns_db = None

namespace_dbs = {}


def open(namespace):
    return db.Database(lib + namespace + '.db', ['alias', 'filename', 'type', 'size', 'date', 'expire'])


def namespaces():
    return iter(namespace_dbs)


def values(namespace):
    return iter(namespace_dbs[namespace])


def create(namespace, alias=None):
    if namespace not in namespace_dbs:
        ns_db.add(namespace)
        namespace_dbs[namespace] = open(namespace)

    if alias is None:
        alias = ''.join(random.choice(string.ascii_lowercase) for _ in range(config.random))

    return namespace_dbs[namespace].add(alias, '', '', 0, 0, 0)


def retrieve(namespace, alias):
    return namespace_dbs[namespace][alias]


def remove(namespace, alias):
    try:
        os.remove(path + namespace + '/' + alias)
    except:
        log.storelog.exception()

    del namespace_dbs[namespace][alias]

    if len(namespace_dbs[namespace]) == 0:
        try:
            os.removedirs(path + namespace + '/')
        except:
            log.storelog.exception()

        del namespace_dbs[namespace]
        del ns_db[namespace]

        os.remove(lib + namespace + '.db')
        os.removedirs(os.path.dirname(lib + namespace))


ns_db = db.Database(trunk + 'ns.db', ['namespace'])

for entry in ns_db:
    namespace_dbs[entry.namespace] = open(entry.namespace)
