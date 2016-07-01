import time

from store.lib import web

from store import log, storage


http = None

routes = {}
error_routes = {}


def create(body, date, alias=None):
    entry = storage.create(alias)

    entry.alias = body['alias']
    entry.filename = body['filename']
    entry.type = body['type']

    entry.size = body['size']
    entry.date = date

    entry.expire = body['expire']

    return entry


def ouput(entry):
    return {'alias': entry.alias, 'filename': entry.filename, 'type': entry.type, 'size': entry.size, 'date': entry.date, 'expire': entry.expire}


class Page(web.page.PageHandler):
    page = 'html/index.html'


class Root(web.json.JSONHandler):
    def do_get(self):
        return 200, list(storage.iter())

    def do_post(self):
        entry = create(self.request.body, time.asctime())

        return 201, output(entry)


class Interface(web.json.JSONHandler):
    def do_get(self):
        try:
            return 200, output(storage.retrieve(self.groups[0]))
        except KeyError:
            raise web.HTTPError(404)

    def do_put(self):
        try:
            entry = storage.retrieve(self.groups[0])

            entry.expire = self.request.body['expire']

            return 204, ''
        except KeyError:
            entry = create(self.request.body, time.asctime(), self.groups[0])

            return 201, output(entry)

    def do_delete(self):
        try:
            storage.remove(self.groups[0])

            return 204, ''
        except KeyError:
            raise web.HTTPError(404)


class Store(web.file.FileHandler):
    def do_put(self):
        try:
            entry = storage.retrieve(self.groups[0])

            if self.request.headers['Content-Length'] != entry.size:
                raise web.HTTPError(400, status_message='Content-Length Does Not Match Database Size')
        except KeyError:
            raise web.HTTPError(404)

        return web.file.ModifyMixIn.do_put(self)


routes.update({'/': Page, '/api': Root, '/api/([a-zA-Z0-9./_-]*)': Interface})
routes.update(web.file.new(config.dir + '/upload', '/store', handler=Store))
error_routes.update(web.json.new_error())


def start():
    global http

    http = web.HTTPServer(config.addr, routes, error_routes, log=log.httplog)
    http.start()


def stop():
    global http

    http.stop()
    http = None
