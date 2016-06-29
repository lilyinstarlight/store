from store.lib import web

from store import log, storage


http = None

routes = {}
error_routes = {}


class Page(web.page.PageHandler):
    page = 'html/index.html'


class Root(web.json.JSONHandler):
    def do_get(self):
        return 200, list(storage.iter())

    def do_post(self):
        return 201, storage.create()


class Interface(web.json.JSONHandler):
    def do_get(self):
        return 200, storage.retrieve(self.groups[0])

    def do_put(self):
        return 200, storage.modify(self.groups[0], self.request.body)

    def do_delete(self):
        return 200, storage.remove(self.groups[0])


class Store(web.file.FileHandler):
    def do_put(self):
        if not storage.check(self.groups[0]):
            raise web.HTTPError(404)

        return web.file.ModifyMixIn.do_put(self)


routes.extend({'/': Page, '/api': Root, '/api/([a-zA-Z0-9./_-]*)': Interface})
routes.extend(web.file.new(config.dir + '/upload', '/store', handler=Store))
error_routes.extend(web.json.new_error())


def start():
    global http

    http = web.HTTPServer(config.addr, routes, error_routes, log=log.httplog)
    http.start()


def stop():
    global http

    http.stop()
    http = None
