import random
import string


from store import config

from store.lib import db


def values():
    return iter(storage_db)


def create(alias=None):
    if alias is None:
        alias = ''.join(random.choice(string.ascii_lowercase) for _ in range(config.random))

    return storage_db.add(alias, '', '', 0, 0, 0)


def retrieve(alias):
    return storage_db[alias]


def remove(alias):
    # ignore errors deleting file
    try:
        os.remove(config.dir + '/upload/' + alias)
    except:
        pass

    del storage_db[alias]


storage_db = db.Database(config.dir + 'storage.db', ['alias', 'filename', 'type', 'size', 'date', 'expire'])
