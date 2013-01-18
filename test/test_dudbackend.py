import time, datetime

from twisted.trial import unittest
from twisted.internet import defer

from dateutil.tz import tzutc

from opennsa import nsa
from opennsa.backends import dud




class DUDBackendTest(unittest.TestCase):

    def setUp(self):
        self.backend = dud.DUDNSIBackend('TestDUD')

        source_stp  = nsa.STP('Aruba', 'A1' )
        dest_stp    = nsa.STP('Aruba', 'A3' )
        start_time = datetime.datetime.fromtimestamp(time.time() + 0.1, tzutc() )
        end_time   = datetime.datetime.fromtimestamp(time.time() + 10,  tzutc() )
        bandwidth = 200

        self.service_params  = nsa.ServiceParameters(start_time, end_time, source_stp, dest_stp, bandwidth)


    @defer.inlineCallbacks
    def testBasicUsage(self):
        conn = self.backend.createConnection('A1', 'A3', self.service_params)
        yield conn.reserve()
        yield conn.provision()
        yield conn.release()
        yield conn.terminate()

