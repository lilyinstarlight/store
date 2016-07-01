def iter():
    return iter(storage_db)


def create(alias=None):
    if alias is None:
        pass

    return storage_db.Entry(alias)


def retrieve(alias):
    return storage_db[alias]


def remove(alias):
    os.remove(config.dir + '/upload/' + alias)

    del storage_db[alias]


storage_db = db.Database(config.dir + 'storage.db', ['alias', 'filename', 'type', 'size', 'date', 'expire'])
