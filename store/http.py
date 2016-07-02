import os
import time

from store.lib import web
from store.lib.web import file, json, page

from store import log, storage


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
        entry.expire = float(self.request.body['expire'])
    except ValueError:
        raise web.HTTPError(400, status_message='Time Must Be In Seconds Since The Epoch')


def ouput(entry):
    return {'alias': entry.alias, 'filename': entry.filename, 'type': entry.type, 'size': entry.size, 'date': entry.date, 'expire': entry.expire}


class Page(page.PageHandler):
    directory = os.path.dirname(__file__) + 'html'
    page = 'index.html'


class Root(json.JSONHandler):
    def do_get(self):
        return 200, list(storage.iter())

    def do_post(self):
        entry = storage.create()
        create(entry, self.request.body, time.time())

        return 201, output(entry)


class Interface(json.JSONHandler):
    def do_get(self):
        try:
            return 200, output(storage.retrieve(self.groups[0]))
        except KeyError:
            raise web.HTTPError(404)

    def do_put(self):
        try:
            entry = storage.retrieve(self.groups[0])

            update(entry, body)

            return 204, ''
        except KeyError:
            entry = storage.create(self.groups[0])
            create(entry, self.request.body, time.time())

            return 201, output(entry)

    def do_delete(self):
        try:
            storage.remove(self.groups[0])

            return 204, ''
        except KeyError:
            raise web.HTTPError(404)


class Store(file.FileHandler):
    def do_get(self):
        try:
            entry = storage.retrieve(self.groups[0])
        except KeyError:
            raise web.HTTPError(404)

        self.response.headers['Content-Type'] = entry.type
        self.response.headers['Content-Filename'] = entry.filename
        self.response.headers['Last-Modified'] = web.mktime(time.gmtime(entry.date))
        self.response.headers['Expires'] = web.mktime(time.gmtime(entry.expire))

        return super().do_get()

    def do_put(self):
        try:
            entry = storage.retrieve(self.groups[0])
        except KeyError:
            raise web.HTTPError(404)

        if self.request.headers['Content-Length'] != entry.size:
            raise web.HTTPError(400, status_message='Content-Length Does Not Match Database Size')

        if 'Content-Type' in self.request.headers and self.request.headers['Content-Type'] != entry.type:
            raise web.HTTPError(400, status_message='Content-Type Does Not Match Database Type')

        return file.ModifyMixIn.do_put(self)


routes.update({'/': Page, '/api': Root, '/api/([a-zA-Z0-9./_-]*)': Interface})
routes.update(file.new(config.dir + '/upload', '/store', handler=Store))
error_routes.update(json.new_error())


def start():
    global http

    http = web.HTTPServer(config.addr, routes, error_routes, log=log.httplog)
    http.start()


def stop():
    global http

    http.stop()
    http = None
