import threading

from store import log


locks = {}
requests = {}

global_lock = threading.Lock()


def autorelease(self):
    try:
        # release all locks
        for alias in requests[self]:
            try:
                release(alias)
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


def acquire(request, alias, autorelease=False):
    with global_lock:
        try:
            # get the lock and request
            lock, lock_request = locks[alias]
        except KeyError:
            # create the lock
            lock = threading.Lock()
            lock_request = request

            # if this lock should autorelease
            if autorelease:
                # set the handler
                lock_request.close = autorelease

                # add the alias to the existing list or make a new one
                try:
                    requests[lock_request].append(alias)
                except KeyError:
                    requests[lock_request] = [alias]

            # store the new lock
            locks[alias] = (lock, lock_request)

        # bypass current requests
        if lock_request == request:
            return

    # acquire the appropriate lock like normal
    lock.acquire()


def release(alias):
    with global_lock:
        # get the lock and request (let upstream handle KeyError's)
        lock, lock_request = locks[alias]

    # release the appropriate lock like normal
    lock.release()
