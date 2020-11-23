import multiprocessing
import os
import sys
import time

import fooster.web
import fooster.web.file
import fooster.web.json
import fooster.web.page

from store import config, lock, storage


fooster.web.file.max_file_size = config.max_size


alias = '(?P<alias>[a-zA-Z0-9._-]+)'
namespace = '(?P<namespace>/[a-zA-Z0-9._/-]*)/'

http = None
global_lock = None

routes = {}
error_routes = {}


def create(entry, body, date):
    entry.filename = body['filename']
    entry.type = body['type']

    try:
        entry.size = int(body['size'])
    except ValueError:
        raise fooster.web.HTTPError(400, status_message='Size Must Be In Bytes')

    if entry.size > config.max_size:
        raise fooster.web.HTTPError(413, status_message='Object Too Large')

    entry.date = date

    update(entry, body)

    return entry


def update(entry, body):
    if 'expire' in body:
        try:
            entry.expire = float(body['expire'])
        except ValueError:
            raise fooster.web.HTTPError(400, status_message='Time Must Be In Seconds Since The Epoch')

    if 'locked' in body:
        if not isinstance(body['locked'], bool):
            raise fooster.web.HTTPError(400, status_message='Locked Must Be A Bool')

        entry.locked = body['locked']


def output(entry):
    return {'alias': entry.alias, 'filename': entry.filename, 'type': entry.type, 'size': entry.size, 'date': entry.date, 'expire': entry.expire, 'locked': entry.locked}


class GlobalLockMixIn:
    def __init__(self, *args, **kwargs):
        self.global_lock = kwargs.pop('global_lock', None)
        super().__init__(*args, **kwargs)


class Page(fooster.web.page.PageHandler):
    directory = config.template
    page = 'index.html'


class Namespace(GlobalLockMixIn, fooster.web.json.JSONHandler):
    def respond(self):
        if not self.request.resource.endswith('/'):
            self.response.headers['Location'] = self.request.resource + '/'

            return 307, ''

        self.namespace = self.groups['namespace']

        norm_request = fooster.web.file.normpath(self.namespace)
        if self.namespace != norm_request:
            self.response.headers.set('Location', '/api' + norm_request)

            return 307, ''

        return super().respond()

    def do_get(self):
        try:
            return 200, list(output(value) for value in storage.values(self.namespace))
        except KeyError:
            raise fooster.web.HTTPError(404)

    def do_post(self):
        if self.request.headers.get('Content-Type') != 'application/json':
            raise fooster.web.HTTPError(400, status_message='Body Must Be JSON')

        entry = storage.create(self.namespace)

        try:
            create(entry, self.request.body, time.time())
        except KeyError:
            storage.remove(self.namespace, entry.alias)
            raise fooster.web.HTTPError(400, status_message='Not Enough Fields')
        except fooster.web.HTTPError:
            storage.remove(self.namespace, entry.alias)
            raise

        if entry.locked:
            lock.acquire(self.request, self.namespace, entry.alias, True)

        self.response.headers['Location'] = self.request.resource + entry.alias

        return 201, output(entry)


class Interface(GlobalLockMixIn, fooster.web.json.JSONHandler):
    def respond(self):
        self.namespace = self.groups['namespace']
        self.alias = self.groups['alias']

        norm_request = fooster.web.file.normpath(self.namespace + '/' + self.alias)
        if self.namespace + '/' + self.alias != norm_request:
            self.response.headers.set('Location', '/api' + norm_request)

            return 307, ''

        return super().respond()

    def do_get(self):
        try:
            return 200, output(storage.retrieve(self.namespace, self.alias))
        except KeyError:
            raise fooster.web.HTTPError(404)

    def do_put(self):
        if self.request.headers.get('Content-Type') != 'application/json':
            raise fooster.web.HTTPError(400, status_message='Body Must Be JSON')

        try:
            entry = storage.retrieve(self.namespace, self.alias)

            if entry.locked:
                raise fooster.web.HTTPError(403)

            try:
                update(entry, self.request.body)
            except KeyError:
                raise fooster.web.HTTPError(400, status_message='Not Enough Fields')

            return 200, output(entry)
        except KeyError:
            entry = storage.create(self.namespace, self.alias)

            try:
                create(entry, self.request.body, time.time())
            except KeyError:
                storage.remove(self.namespace, entry.alias)
                raise fooster.web.HTTPError(400, status_message='Not Enough Fields')
            except fooster.web.HTTPError:
                storage.remove(self.namespace, entry.alias)
                raise

            if entry.locked:
                lock.acquire(self.request, self.namespace, entry.alias, True)

            return 201, output(entry)

    def do_delete(self):
        try:
            entry = storage.retrieve(self.namespace, self.alias)

            if entry.locked:
                raise fooster.web.HTTPError(403)

            storage.remove(self.namespace, entry.alias)

            return 204, ''
        except KeyError:
            raise fooster.web.HTTPError(404)


class Store(GlobalLockMixIn, fooster.web.file.ModifyMixIn, fooster.web.file.PathHandler):
    local = storage.path
    remote = '/store'

    def get_body(self):
        return False

    def respond(self):
        if 'namespace' not in self.groups or 'alias' not in self.groups:
            self.response.headers['Location'] = self.request.resource + '/'

            return 307, ''

        self.namespace = self.groups['namespace']
        self.alias = self.groups['alias']

        self.pathstr = self.namespace + '/' + self.alias

        return super().respond()

    def do_get(self):
        try:
            entry = storage.retrieve(self.namespace, self.alias)
        except KeyError:
            raise fooster.web.HTTPError(404)

        if entry.type is not None:
            self.response.headers['Content-Type'] = entry.type
        if entry.filename is not None:
            self.response.headers['Content-Filename'] = entry.filename.encode(fooster.web.http_encoding, 'ignore').decode()
        self.response.headers['Last-Modified'] = fooster.web.mktime(time.gmtime(entry.date))
        self.response.headers['Expires'] = fooster.web.mktime(time.gmtime(entry.expire))

        return super().do_get()

    def do_put(self):
        try:
            entry = storage.retrieve(self.namespace, self.alias)
        except KeyError:
            raise fooster.web.HTTPError(404)

        if entry.locked and os.path.isfile(self.filename):
            raise fooster.web.HTTPError(403)

        if self.request.headers.get('Content-Length') != str(entry.size):
            raise fooster.web.HTTPError(400, status_message='Content-Length Does Not Match Database Size')

        if 'Content-Type' in self.request.headers and self.request.headers['Content-Type'] != entry.type:
            raise fooster.web.HTTPError(400, status_message='Content-Type Does Not Match Database Type')

        response = super().do_put()

        return response


routes.update({'/': Page, '/api': Namespace, '/api' + namespace: Namespace, '/api' + namespace + alias: Interface, '/store': Store, '/store' + namespace + alias: Store})
error_routes.update(fooster.web.json.new_error())


def start():
    global http, global_lock

    if sys.version_info >= (3, 7):
        global_lock = multiprocessing.get_context('spawn').Lock()
    else:
        global_lock = multiprocessing.get_context('fork').Lock()

    run_routes = {}
    for route, handler in routes.items():
        if issubclass(handler, GlobalLockMixIn):
            run_routes[route] = fooster.web.HTTPHandlerWrapper(handler, global_lock=global_lock)
        else:
            run_routes[route] = handler

    http = fooster.web.HTTPServer(config.addr, run_routes, error_routes, timeout=60, keepalive=60)
    http.start()


def stop():
    global http, global_lock

    http.stop()
    http = None
    global_lock = None


def join():
    global http

    http.join()
