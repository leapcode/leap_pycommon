from twisted.internet import reactor
from leap.common.events.server import ensure_server
reactor.callWhenRunning(ensure_server)
reactor.run()
