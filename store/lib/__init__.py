import importlib
import os
import sys


sys.path.append(os.path.dirname(__file__) + '/cron.py')
sys.path.append(os.path.dirname(__file__) + '/db.py')
sys.path.append(os.path.dirname(__file__) + '/web.py')


cron = importlib.import_module('cron')
db = importlib.import_module('db')
web = importlib.import_module('web')


sys.path.remove(os.path.dirname(__file__) + '/cron.py')
sys.path.remove(os.path.dirname(__file__) + '/db.py')
sys.path.remove(os.path.dirname(__file__) + '/web.py')


__all__ = ['cron', 'db', 'web']
