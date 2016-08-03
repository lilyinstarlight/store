import threading

from store import log


requests = {}

global_lock = threading.Lock()


def autorelease(self):
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
            request.close = autorelease

            # add the alias to the existing list or make a new one
            try:
                requests[request].append((namespace, alias))
            except KeyError:
                requests[request] = [(namespace, alias)]


def release(request, namespace, alias):
    # sanitize namespace
    if not namespace.endswith('/'):
        namespace += '/'

    with global_lock:
        # use resource lock to unlock stuff
        request.server.res_lock.release('/api' + namespace + alias, False)
        request.server.res_lock.release('/store' + namespace + alias, False)
