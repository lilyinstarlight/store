import logging


log = logging.getLogger('store')


def close(self):
    try:
        # release all locks
        for namespace, alias in self.store_locks:
            try:
                release(self, namespace, alias)
            except Exception:
                # do not worry about failures since
                # they were probably already released
                # when the file was successfully uploaded
                pass
    except KeyError:
        # do not worry about not being found (NOTE: might leave dangling locks)
        log.exception('ResLock Not Found')

    type(self).close(self)


def acquire(request, namespace, alias, autorelease=False):
    # sanitize namespace
    if not namespace.endswith('/'):
        namespace += '/'

    with request.handler.global_lock:
        # use resource lock to lock stuff
        request.server.res_lock.acquire(request, '/api' + namespace + alias, True)
        request.server.res_lock.acquire(request, '/store' + namespace + alias, True)

        # if this lock should autorelease
        if autorelease:
            # set the handler
            request.close = close.__get__(request, request.__class__)

            # add the alias to the existing list or make a new one
            try:
                request.store_locks.append((namespace, alias))
            except AttributeError:
                request.store_locks = [(namespace, alias)]


def release(request, namespace, alias):
    # sanitize namespace
    if not namespace.endswith('/'):
        namespace += '/'

    with request.handler.global_lock:
        # use resource lock to unlock stuff
        try:
            request.server.res_lock.release('/api' + namespace + alias, True)
        except RuntimeError:
            # ignore
            pass

        try:
            request.server.res_lock.release('/store' + namespace + alias, True)
        except RuntimeError:
            # ignore
            pass
