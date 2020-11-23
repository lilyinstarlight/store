import json as _json
import logging as _logging
import os as _os
import os.path as _path
import sys as _sys

import fooster.web as _web


# address to listen on
addr = ('', 8000)

# directory to store information
dir = '/var/lib/store'

# log locations
log = '/var/log/store/store.log'
http_log = '/var/log/store/http.log'

# template directory to use
template = _path.dirname(__file__) + '/html'

# maximum file size
max_size = 33554432  # 32 MB

# minute of hour to prune files
minute = 9

# number of random characters to use
random = 6


# store config in env var
def _store():
    config = {key: val for key, val in globals().items() if not key.startswith('_')}

    _os.environ['STORE_CONFIG'] = _json.dumps(config)


# load config from env var
def _load():
    config = _json.loads(_os.environ['STORE_CONFIG'])

    globals().update(config)

    # automatically apply
    _apply()


# apply special config-specific logic after changes
def _apply():
    # setup logging
    if log:
        _logging.getLogger('store').addHandler(_logging.FileHandler(log))
    else:
        _logging.getLogger('store').addHandler(_logging.StreamHandler(_sys.stdout))

    _logging.getLogger('store').setLevel(_logging.INFO)

    if http_log:
        http_log_handler = _logging.FileHandler(http_log)
        http_log_handler.setFormatter(_web.HTTPLogFormatter())

        _logging.getLogger('http').addHandler(http_log_handler)

    # automatically store if not already serialized
    if 'STORE_CONFIG' not in _os.environ:
        _store()


# load if config already serialized in env var
if 'STORE_CONFIG' in _os.environ:
    _load()
