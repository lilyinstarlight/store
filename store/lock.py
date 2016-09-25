import threading

from store import log


requests = {}

global_lock = threading.Lock()


def close(self):
    try:
        # release all locks
        for namespace, alias in requests[self]:
            try:
                release(self, namespace, alias)
            except Exception:
                # do not worry about failures since
                # they were probably already released
                # when the file was successfully uploaded
                pass

        # remove now unnecessary requests list
        del requests[self]
    except KeyError:
        # do not worry about not being found (NOTE: might leave dangling locks)
        self.storelog.exception()

    type(self).close(self)


def acquire(request, namespace, alias, autorelease=False):
    # sanitize namespace
    if not namespace.endswith('/'):
        namespace += '/'

    with global_lock:
        # use resource lock to lock stuff
        request.server.res_lock.acquire(request, '/api' + namespace + alias, False)
        request.server.res_lock.acquire(request, '/store' + namespace + alias, False)

        # if this lock should autorelease
        if autorelease:
            # set the handler
            request.close = close.__get__(request, request.__class__)

            # add the alias to the existing list or make a new one
            try:
                requests[request].append((namespace, alias))
            except KeyError:
                requests[request] = [(namespace, alias)]


def release(request, namespace, alias, store=False):
    # sanitize namespace
    if not namespace.endswith('/'):
        namespace += '/'

    with global_lock:
        try:
            # use resource lock to unlock stuff
            request.server.res_lock.release('/api' + namespace + alias, False)
        except KeyError:
            # ignore
            pass

        try:
            request.server.res_lock.release('/store' + namespace + alias, False, not store)
        except KeyError:
            # ignore
            pass
