import os
import time

import web, web.file, web.json, web.page

from store import config, log, storage


alias = '([a-zA-Z0-9._-]+)'
namespace = '([a-zA-Z0-9._/-]*)/'

http = None

routes = {}
error_routes = {}


def create(entry, body, date):
    entry.filename = body['filename']
    entry.type = body['type']

    try:
        entry.size = int(body['size'])
    except ValueError:
        raise web.HTTPError(400, status_message='Size Must Be In Bytes')

    entry.date = date

    update(entry, body)

    return entry


def update(entry, body):
    try:
        entry.expire = float(body['expire'])
    except ValueError:
        raise web.HTTPError(400, status_message='Time Must Be In Seconds Since The Epoch')

    if not isinstance(body['locked'], bool):
        raise web.HTTPError(400, status_message='Locked Must Be A Bool')

    entry.locked = body['locked']


def output(entry):
    return {'alias': entry.alias, 'filename': entry.filename, 'type': entry.type, 'size': entry.size, 'date': entry.date, 'expire': entry.expire, 'locked': entry.locked}


class Page(web.page.PageHandler):
    directory = os.path.dirname(__file__) + '/html'
    page = 'index.html'


class Namespace(web.json.JSONHandler):
    def respond(self):
        if not self.request.resource.endswith('/'):
            self.response.headers['Location'] = self.request.resource + '/'

            return 307, ''

        self.namespace = self.groups[0]

        if self.namespace == '':
            self.namespace = '/'

        return super().respond()

    def do_get(self):
        try:
            return 200, list(output(value) for value in storage.values(self.namespace))
        except KeyError:
            raise web.HTTPError(404)

    def do_post(self):
        if self.request.headers.get('Content-Type') != 'application/json':
            raise web.HTTPError(400, status_message='Body Must Be JSON')

        entry = storage.create(self.namespace)

        try:
            create(entry, self.request.body, time.time())
        except KeyError:
            storage.remove(self.namespace, entry.alias)
            raise web.HTTPError(400, status_message='Not Enough Fields')

        self.response.headers['Location'] = self.request.resource + entry.alias

        return 201, output(entry)


class Interface(web.json.JSONHandler):
    def respond(self):
        self.namespace = self.groups[0]
        self.alias = self.groups[1]

        if self.namespace == '':
            self.namespace = '/'

        return super().respond()

    def do_get(self):
        try:
            return 200, output(storage.retrieve(self.namespace, self.alias))
        except KeyError:
            raise web.HTTPError(404)

    def do_put(self):
        if self.request.headers.get('Content-Type') != 'application/json':
            raise web.HTTPError(400, status_message='Body Must Be JSON')

        try:
            entry = storage.retrieve(self.namespace, self.alias)

            if entry.locked:
                raise web.HTTPError(403)

            try:
                update(entry, self.request.body)
            except KeyError:
                raise web.HTTPError(400, status_message='Not Enough Fields')

            return 200, output(entry)
        except KeyError:
            entry = storage.create(self.namespace, self.alias)

            try:
                create(entry, self.request.body, time.time())
            except KeyError:
                storage.remove(self.namespace, self.alias)
                raise web.HTTPError(400, status_message='Not Enough Fields')

            return 201, output(entry)

    def do_delete(self):
        try:
            entry = storage.retrieve(self.namespace, self.alias)

            if entry.locked:
                raise web.HTTPError(403)

            storage.remove(self.namespace, self.alias)

            return 204, ''
        except KeyError:
            raise web.HTTPError(404)


class Store(web.HTTPHandler):
    def get_body(self):
        return False

    def respond(self):
        if len(self.groups) == 0:
            self.response.headers['Location'] = self.request.resource + '/'

            return 307, ''

        self.namespace = self.groups[0]
        self.alias = self.groups[1]

        self.filename = storage.path + self.namespace + '/' + self.alias

        if self.namespace == '':
            self.namespace = '/'

        return super().respond()

    def do_get(self):
        try:
            entry = storage.retrieve(self.namespace, self.alias)
        except KeyError:
            raise web.HTTPError(404)

        self.response.headers['Content-Type'] = entry.type
        self.response.headers['Content-Filename'] = entry.filename
        self.response.headers['Last-Modified'] = web.mktime(time.gmtime(entry.date))
        self.response.headers['Expires'] = web.mktime(time.gmtime(entry.expire))

        return web.file.ModifyFileHandler.do_get(self)

    def do_put(self):
        try:
            entry = storage.retrieve(self.namespace, self.alias)
        except KeyError:
            raise web.HTTPError(404)

        if entry.locked and os.path.isfile(self.filename):
            raise web.HTTPError(403)

        if self.request.headers['Content-Length'] != str(entry.size):
            raise web.HTTPError(400, status_message='Content-Length Does Not Match Database Size')

        if 'Content-Type' in self.request.headers and self.request.headers['Content-Type'] != entry.type:
            raise web.HTTPError(400, status_message='Content-Type Does Not Match Database Type')

        return web.file.ModifyFileHandler.do_put(self)


routes.update({'/': Page, '/api': Namespace, '/api' + namespace: Namespace, '/api' + namespace + alias: Interface, '/store': Store, '/store' + namespace + alias: Store})
error_routes.update(web.json.new_error())


def start():
    global http

    http = web.HTTPServer(config.addr, routes, error_routes, log=log.httplog)
    http.start()


def stop():
    global http

    http.stop()
    http = None
