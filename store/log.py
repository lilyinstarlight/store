import log

from store import config


storelog = log.Log(config.log)
httplog = log.HTTPLog(config.log, config.httplog)
