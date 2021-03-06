"""
Web Service Resource for OpenNSA.

Author: Henrik Thostrup Jensen <htj@nordu.net>
Copyright: NORDUnet (2011)
"""

from twisted.python import failure

from opennsa import constants as cnt, nsa, error

from opennsa.protocols.nsi2 import helper
from opennsa.protocols.nsi2.bindings import actions, p2pservices



class RequesterService:

    def __init__(self, soap_resource, requester):

        self.requester = requester

        # consider moving this to __init__ (soap_resource only used in setup)
        soap_resource.registerDecoder(actions.RESERVE_CONFIRMED,        self.reserveConfirmed)
        soap_resource.registerDecoder(actions.RESERVE_FAILED,           self.reserveFailed)
        soap_resource.registerDecoder(actions.RESERVE_COMMIT_CONFIRMED, self.reserveCommitConfirmed)
        soap_resource.registerDecoder(actions.RESERVE_COMMIT_FAILED,    self.reserveCommitFailed)
        soap_resource.registerDecoder(actions.RESERVE_ABORT_CONFIRMED,  self.reserveAbortConfirmed)

        soap_resource.registerDecoder(actions.PROVISION_CONFIRMED,      self.provisionConfirmed)
        soap_resource.registerDecoder(actions.RELEASE_CONFIRMED,        self.releaseConfirmed)
        soap_resource.registerDecoder(actions.TERMINATE_CONFIRMED,      self.terminateConfirmed)

        soap_resource.registerDecoder(actions.QUERY_SUMMARY_CONFIRMED,  self.querySummaryConfirmed)
        soap_resource.registerDecoder(actions.QUERY_SUMMARY_FAILED,     self.querySummaryFailed)

#        actions.QUERY_RECURSIVE_CONFIRMED
#        actions.QUERY_RECURSIVE_FAILED
#        actions.QUERY_NOTIFICATION_CONFIRMED
#        actions.QUERY_NOTIFICATION_FAILED

        # notifications
        soap_resource.registerDecoder(actions.ERROR_EVENT,              self.errorEvent)
        soap_resource.registerDecoder(actions.DATA_PLANE_STATE_CHANGE,  self.dataPlaneStateChange)
        soap_resource.registerDecoder(actions.RESERVE_TIMEOUT,          self.reserveTimeout)
        soap_resource.registerDecoder(actions.MESSAGE_DELIVERY_TIMEOUT, self.messageDeliveryTimeout)


    def _parseGenericFailure(self, soap_data):

        header, generic_failure = helper.parseRequest(soap_data)

        rc = generic_failure.connectionStates
        rd = rc.dataPlaneStatus

        dps = (rd.active, rd.version, rd.versionConsistent)
        cs = (rc.reservationState, rc.provisionState, rc.lifecycleState, dps)

        se = generic_failure.serviceException

        exception_type = error.lookup(se.errorId)
        err = exception_type(se.text)

        return header, generic_failure.connectionId, cs, err



    def reserveConfirmed(self, soap_data):

        header, reservation = helper.parseRequest(soap_data)

        criteria = reservation.criteria

        # Create DTOs - this overlaps heavily with the parsing done in providerservice - unify sometime

        start_time = helper.parseXMLTimestamp(criteria.schedule.startTime)
        end_time   = helper.parseXMLTimestamp(criteria.schedule.endTime)
        schedule   = nsa.Schedule(start_time, end_time)

        evts = criteria.serviceDefinitions.values()[0] # add check later
        if type(evts) is not p2pservices.EthernetVlanType:
            raise ValueError('Only EVTS service supported for now')

        # (ERO missing)
        src_stp = helper.createSTP(evts.sourceSTP)
        dst_stp = helper.createSTP(evts.destSTP)

        # for evts in r99, STPs are without labels, but this will change in the future, so we set them here
        src_stp.labels = [ nsa.Label(cnt.ETHERNET_VLAN, str(evts.sourceVLAN)) ]
        dst_stp.labels = [ nsa.Label(cnt.ETHERNET_VLAN, str(evts.destVLAN))   ]

        if evts.ero:
            print "ERO parsing in reserveConfirmed not implemented yet, full path will not be available"

        sd = nsa.EthernetVLANService(src_stp, dst_stp, evts.capacity, evts.mtu, evts.burstsize, evts.directionality, evts.symmetricPath, None)
        crt = nsa.Criteria(criteria.version, schedule, sd)

        self.requester.reserveConfirmed(header, reservation.connectionId,  reservation.globalReservationId, reservation.description, crt)

        return helper.createGenericAcknowledgement(header)


    def reserveFailed(self, soap_data):
        header, connection_id, cs, err = self._parseGenericFailure(soap_data)
        self.requester.reserveFailed(header, connection_id, cs, err)
        return helper.createGenericAcknowledgement(header)


    def reserveCommitConfirmed(self, soap_data):
        header, generic_confirm = helper.parseRequest(soap_data)
        self.requester.reserveCommitConfirmed(header, generic_confirm.connectionId)
        return helper.createGenericAcknowledgement(header)


    def reserveCommitFailed(self, soap_data):
        header, connection_id, cs, err = self._parseGenericFailure(soap_data)
        self.requester.reserveCommitFailed(header, connection_id, cs, err)
        return helper.createGenericAcknowledgement(header)


    def reserveAbortConfirmed(self, soap_data):
        header, generic_confirm = helper.parseRequest(soap_data)
        self.requester.reserveAbortConfirmed(header, generic_confirm.connectionId)
        return helper.createGenericAcknowledgement(header)


    def provisionConfirmed(self, soap_data):
        header, generic_confirm = helper.parseRequest(soap_data)
        self.requester.provisionConfirmed(header, generic_confirm.connectionId)
        return helper.createGenericAcknowledgement(header)


    def releaseConfirmed(self, soap_data):
        header, generic_confirm = helper.parseRequest(soap_data)
        self.requester.releaseConfirmed(header, generic_confirm.connectionId)
        return helper.createGenericAcknowledgement(header)


    def terminateConfirmed(self, soap_data):
        header, generic_confirm = helper.parseRequest(soap_data)
        self.requester.terminateConfirmed(header, generic_confirm.connectionId)
        return helper.createGenericAcknowledgement(header)


    def terminateFailed(self, soap_data):
        header, connection_id, cs, err = self._parseGenericFailure(soap_data)
        self.requester.terminateFailed(header, connection_id, cs, err)
        return helper.createGenericAcknowledgement(header)


    def querySummaryConfirmed(self, soap_data):

        header, query_confirmed = helper.parseRequest(soap_data)

        if query_confirmed is None: # handle no connection case
            reservations = []
        elif type(query_confirmed) is list:
            reservations = helper.buildQuerySummaryResult(query_confirmed)
        else:
            reservations = [ helper.buildQuerySummaryResult(query_confirmed) ]

        self.requester.querySummaryConfirmed(header, reservations)

        return helper.createGenericAcknowledgement(header)


    def querySummaryFailed(self, soap_data):

        header, connection_id, cs, err = self._parseGenericFailure(soap_data)

        self.requester.queryFailed(header, connection_id, cs, err)

        return helper.createGenericAcknowledgement(header)


    def errorEvent(self, soap_data):

        header, error_event = helper.parseRequest(soap_data)

        #connection_id, notification_id, timestamp, event, info, service_ex = 
        ee = error_event
        if ee.serviceException:
            se = ee.serviceException
            service_ex = (se.nsaId, se.connectionId, se.errorId, se.text, se.variables, se.childException)
        else:
            service_ex = None

        self.requester.errorEvent(header, ee.connectionId, ee.notificationId, ee.timeStamp, ee.event, ee.additionalInfo, service_ex)

        return helper.createGenericAcknowledgement(header)



    def dataPlaneStateChange(self, soap_data):

        header, data_plane_state_change = helper.parseRequest(soap_data)

        dpsc = data_plane_state_change
        dps = dpsc.dataPlaneStatus

        self.requester.dataPlaneStateChange(header, dpsc.connectionId, dpsc.notificationId, dpsc.timeStamp, (dps.active, dps.version, dps.versionConsistent) )

        return helper.createGenericAcknowledgement(header)


    def reserveTimeout(self, soap_data):

        header, reserve_timeout = helper.parseRequest(soap_data)
        rt = reserve_timeout
        self.requester.reserveTimeout(header, rt.connectionId, rt.notificationId, rt.timeStamp, rt.timeoutValue, rt.originatingConnectionId, rt.originatingNSA)

        return helper.createGenericAcknowledgement(header)


    def messageDeliveryTimeout(self, soap_data):
        raise NotImplementedError('messageDeliveryTimeout not yet implemented in requester service')

