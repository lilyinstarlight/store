from store.lib import web

from store import log, storage


http = None

routes = {}
error_routes = {}


class Page(web.page.PageHandler):
    page = 'html/index.html'


class Root(web.json.JSONHandler):
    def do_get(self):
        return 200, status

    def do_post(self):
        return 201, status


class Interface(web.json.JSONHandler):
    def do_get(self):
        return 200, status

    def do_put(self):
        return 200, status

    def do_delete(self):
        return 200, status


class Store(web.HTTPHandler):
    def get_body(self):
        return False

    def do_get(self):
        try:
            return 200, storage.file(self.groups[0])
        except KeyError:
            raise web.HTTPError(404)

    def do_put(self):
        try:
            return 200, storage.store(self.groups[0], self.request.rfile)
        except KeyError:
            raise web.HTTPError(404)


routes.extend({'/': Page, '/api/': Root, '/api/([a-zA-Z0-9._-]+)': Interface, '/store/([a-zA-Z0-9._-]+)': Store})
error_routes.extend(web.json.new_error())


def start():
    global http

    http = web.HTTPServer(config.addr, routes, error_routes, log=log.httplog)
    http.start()


def stop():
    global http

    http.stop()
    http = None
