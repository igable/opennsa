"""
Connection abstraction.

Author: Henrik Thostrup Jensen <htj@nordu.net>
Copyright: NORDUnet (2011)
"""


from twisted.python import log
from twisted.internet import defer

from opennsa import error, nsa



# connection states
INITIAL             = 'Initial'

RESERVING           = 'Reserving'
RESERVED            = 'Reserved'

AUTO_PROVISION      = 'Auto-Provision'
PROVISIONING        = 'Provisioning'
PROVISIONED         = 'Provisioned'

RELEASING           = 'Releasing'

TERMINATING         = 'Terminateing' # John can't spell
TERMINATED          = 'Terminated'

# allowed state transitions
TRANSITIONS = {
    INITIAL         : [ RESERVING                                   ],
    RESERVING       : [ RESERVED,       TERMINATED                  ],
    RESERVED        : [ AUTO_PROVISION, PROVISIONING, TERMINATING   ],
    AUTO_PROVISION  : [ PROVISIONING,   TERMINATED                  ],
    PROVISIONING    : [ PROVISIONED,    TERMINATED                  ],
    PROVISIONED     : [ RELEASING,      TERMINATING                 ],
    RELEASING       : [ RESERVED,       TERMINATED                  ],
    TERMINATING     : [ TERMINATED,                                 ],
    TERMINATED      : [ ]
}



class ConnectionState:

    def __init__(self, state=INITIAL):
        self._state = state


    def state(self):
        return self._state


    def switchState(self, new_state):
        if new_state in TRANSITIONS[self._state]:
            self._state = new_state
        else:
            raise error.ConnectionStateTransitionError('Transition from state %s to %s not allowed' % (self._state, new_state))



class SubConnection(ConnectionState):

    def __init__(self, parent_connection, connection_id, network, source_stp, dest_stp, proxy=None):
        ConnectionState.__init__(self)
        self.parent_connection  = parent_connection
        self.connection_id      = connection_id
        self.network            = network
        self.source_stp         = source_stp
        self.dest_stp           = dest_stp

        # the one should not be persistent, but should be set when re-created at startup
        self._proxy = proxy


    def reservation(self, service_parameters):

        assert self._proxy is not None, 'Proxy not set for SubConnection, cannot invoke method'

        def reservationDone(int_res_id):
            log.msg('Sub-connection for network %s (%s -> %s) reserved' % (self.network, self.source_stp.endpoint, self.dest_stp.endpoint), system='opennsa.Connection')
            self.switchState(RESERVED)
            return self

        def reservationFailed(err):
            self.switchState(TERMINATED)
            return err

        sub_service_params  = nsa.ServiceParameters(service_parameters.start_time, service_parameters.end_time, self.source_stp, self.dest_stp,
                                                    directionality=service_parameters.directionality, bandwidth_params=service_parameters.bandwidth_params)
        self.switchState(RESERVING)
        d = self._proxy.reservation(self.network, None, self.parent_connection.global_reservation_id, self.parent_connection.description, self.connection_id, sub_service_params)
        d.addCallbacks(reservationDone, reservationFailed)
        return d


    def cancelReservation(self):

        assert self._proxy is not None, 'Proxy not set for SubConnection, cannot invoke method'

        def cancelDone(_):
            self.switchState(TERMINATED)
            return self

        def cancelFailed(err):
            self.switchState(TERMINATED)
            return err

        self.switchState(TERMINATING)
        d = self._proxy.terminateReservation(self.network, None, self.connection_id)
        d.addCallbacks(cancelDone, cancelFailed)
        return d


    def provision(self):

        assert self._proxy is not None, 'Proxy not set for SubConnection, cannot invoke method'

        def provisionDone(conn_id):
            assert conn_id == self.connection_id
            self.switchState(PROVISIONED)
            return self

        def provisionFailed(err):
            self.switchState(TERMINATED)
            return err

        self.switchState(PROVISIONING)
        d = self._proxy.provision(self.network, None, self.connection_id)
        d.addCallbacks(provisionDone, provisionFailed)
        return d


    def releaseProvision(self):

        assert self._proxy is not None, 'Proxy not set for SubConnection, cannot invoke method'

        def releaseDone(conn_id):
            assert conn_id == self.connection_id
            self.switchState(RESERVED)
            return self

        def releaseFailed(err):
            self.switchState(TERMINATED)
            return err

        self.switchState(RELEASING)
        d = self._proxy.releaseProvision(self.network, None, self.connection_id)
        d.addCallbacks(releaseDone, releaseFailed)
        return d



class LocalConnection(ConnectionState):

    def __init__(self, parent_connection, source_endpoint, dest_endpoint, internal_reservation_id=None, internal_connection_id=None, backend=None):
        ConnectionState.__init__(self)
        self.parent_connection          = parent_connection
        self.source_endpoint            = source_endpoint
        self.dest_endpoint              = dest_endpoint
        # the two latter are usually not available at creation time
        self.internal_reservation_id    = internal_reservation_id
        self.internal_connection_id     = internal_connection_id

        # the one should not be persistent, but should be set when re-created at startup
        self._backend = backend


    def reservation(self, service_parameters):

        assert self._backend is not None, 'Backend not set for LocalConnection, cannot invoke method'

        def reservationDone(int_res_id):
            self.internal_reservation_id = int_res_id
            self.switchState(RESERVED)
            return self

        def reservationFailed(err):
            self.switchState(TERMINATED)
            return err

        self.switchState(RESERVING)
        d = self._backend.reserve(self.source_endpoint, self.dest_endpoint, service_parameters)
        d.addCallbacks(reservationDone, reservationFailed)
        return d


    def cancelReservation(self):

        assert self._backend is not None, 'Backend not set for LocalConnection, cannot invoke method'

        def cancelDone(_):
            self.switchState(TERMINATED)
            return self

        def cancelFailed(err):
            self.switchState(TERMINATED)
            return err

        self.switchState(TERMINATING)
        d = self._backend.cancelReservation(self.internal_reservation_id)
        d.addCallbacks(cancelDone, cancelFailed)
        return d


    def provision(self):

        assert self._backend is not None, 'Backend not set for LocalConnection, cannot invoke method'

        def provisionDone(int_conn_id):
            self.internal_connection_id = int_conn_id
            self.switchState(PROVISIONED)
            return self

        def provisionFailed(err):
            self.switchState(TERMINATED)
            return err

        self.switchState(PROVISIONING)
        d = self._backend.provision(self.internal_reservation_id)
        d.addCallbacks(provisionDone, provisionFailed)
        return d


    def releaseProvision(self):

        assert self._backend is not None, 'Backend not set for LocalConnection, cannot invoke method'

        def releaseDone(int_res_id):
            self.internal_reservation_id = int_res_id
            self.internal_connection_id = None
            self.switchState(RESERVED)
            return self

        def releaseFailed(err):
            self.switchState(TERMINATED)
            return err

        self.switchState(RELEASING)
        d = self._backend.releaseProvision(self.internal_connection_id)
        d.addCallbacks(releaseDone, releaseFailed)
        return d



class Connection(ConnectionState):

    def __init__(self, requester_nsa, connection_id, source_stp, dest_stp, global_reservation_id=None, description=None, local_connection=None, sub_connections=None):
        ConnectionState.__init__(self)
        self.requester_nsa              = requester_nsa
        self.connection_id              = connection_id
        self.source_stp                 = source_stp
        self.dest_stp                   = dest_stp
        self.global_reservation_id      = global_reservation_id
        self.description                = description
        self.local_connection           = local_connection
        self.sub_connections            = sub_connections or []
        self.service_parameters         = None


    def hasLocalConnection(self):
        return self.local_connection is not None


    def connections(self):
        if self.local_connection is not None:
            return [ self.local_connection ] + self.sub_connections
        else:
            return self.sub_connections


    def reservation(self, service_parameters, nsa_identity=None):

        def reservationRequestsDone(results):
            successes = [ r[0] for r in results ]
            if all(successes):
                self.switchState(RESERVED)
                return self
            else:
                self.switchState(TERMINATED)
                if any(successes):
                    failure_msg = ' # '.join( [ f.getErrorMessage() for success,f in results if success is False ] )
                    error_msg = 'Partial failure in reservation, may require manual cleanup (%s)' % failure_msg
                else:
                    failure_msg = ' # '.join( [ f.getErrorMessage() for _,f in results ] )
                    error_msg = 'Reservation failed for all local/sub connections (%s)' % failure_msg
                return defer.fail( error.ReserveError(error_msg) )

        self.service_parameters = service_parameters
        self.switchState(RESERVING)

        defs = []
        for sc in self.connections():
            d = sc.reservation(service_parameters)
            defs.append(d)

        dl = defer.DeferredList(defs, consumeErrors=True)
        dl.addCallbacks(reservationRequestsDone) # never errbacks
        return dl


    def cancelReservation(self):

        def connectionCancelled(results):
            successes = [ r[0] for r in results ]
            if all(successes):
                self.switchState(TERMINATED)
                if len(successes) > 1:
                    log.msg('Connection %s and all sub connections(%i) cancelled' % (self.connection_id, len(results)-1), system='opennsa.NSIService')
                return self
            if any(successes):
                self.switchState(TERMINATED)
                raise error.CancelReservationError('Cancel partially failed (may require manual cleanup)')
            else:
                self.switchState(TERMINATED)
                raise error.CancelReservationError('Cancel failed for all local/sub connections')

        self.switchState(TERMINATING)

        defs = []
        for sc in self.connections():
            d = sc.cancelReservation()
            defs.append(d)

        dl = defer.DeferredList(defs)
        dl.addCallback(connectionCancelled)
        return dl


    def provision(self):

        def provisionComplete(results):
            successes = [ r[0] for r in results ]
            if all(successes):
                self.switchState(PROVISIONED)
                if len(results) > 1:
                    log.msg('Connection %s and all sub connections(%i) provisioned' % (self.connection_id, len(results)-1), system='opennsa.NSIService')
                return self
            if any(successes):
                self.switchState(TERMINATED)
                raise error.ProvisionError('Provision partially failed (may require manual cleanup)')
            else:
                self.switchState(TERMINATED)
                raise error.ProvisionError('Provision failed for all local/sub connections')

        self.switchState(PROVISIONING)

        defs = []
        for sc in self.connections():
            d = sc.provision()
            defs.append(d)

        dl = defer.DeferredList(defs)
        dl.addCallback(provisionComplete)
        return dl


    def releaseProvision(self):

        def connectionReleased(results):
            successes = [ r[0] for r in results ]
            if all(successes):
                self.switchState(RESERVED)
                if len(results) > 1:
                    log.msg('Connection %s and all sub connections(%i) released' % (self.connection_id, len(results)-1), system='opennsa.NSIService')
                return self
            if any(successes):
                self.switchState(TERMINATED)
                raise error.ReleaseError('Release partially failed (may require manual cleanup)')
            else:
                self.switchState(TERMINATED)
                raise error.ReleaseError('Release failed for all local/sub connection')

        self.switchState(RELEASING)

        defs = []
        for sc in self.connections():
            d = sc.releaseProvision()
            defs.append(d)

        dl = defer.DeferredList(defs)
        dl.addCallback(connectionReleased)
        return dl

