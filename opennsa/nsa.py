"""
Core abstractions used in OpenNSA.

In design pattern terms, these would be Data Transfer Objects (DTOs).
Though some of them do actually have some functionality methods.

Author: Henrik Thostrup Jensen <htj@nordu.net>
Copyright: NORDUnet (2011-2013)
"""


import uuid
import random
import urlparse
import itertools

from opennsa import error, constants as cnt



LOG_SYSTEM = 'opennsa.nsa'

OGF_PREFIX = 'urn:ogf:network:'
URN_UUID_PREFIX = 'urn:uuid:'

BIDIRECTIONAL   = 'Bidirectional'



class NSIHeader(object):

    def __init__(self, requester_nsa, provider_nsa, session_security_attrs=None, correlation_id=None, reply_to=None):
        self.requester_nsa          = requester_nsa
        self.provider_nsa           = provider_nsa
        self.session_security_attrs = session_security_attrs
        self.reply_to               = reply_to
        self.correlation_id = correlation_id or self._createCorrelationId()

    def _createCorrelationId(self):
        return URN_UUID_PREFIX + str(uuid.uuid1())

    def newCorrelationId(self):
        self.correlation_id = self._createCorrelationId()


    def __repr__(self):
        return '<NSIHeader: %s, %s, %s, %s, %s>' % (self.requester_nsa, self.provider_nsa, self.session_security_attrs, self.reply_to, self.correlation_id)



class EmptyLabelSet(Exception):
    pass



class Label(object):

    def __init__(self, type_, values=None):

        assert type(values) in (None, str, list), 'Type of Label values must be a None, str, or list. Was given %s' % type(values)

        self.type_ = type_
        self.values = self._parseLabelValues(values) if values is not None else None


    def _parseLabelValues(self, values):

        def createValue(value):
            try:
                if '-' in value:
                    v1, v2 = value.split('-', 1)
                    i1, i2 = int(v1), int(v2)
                    if i1 > i2:
                        raise error.PayloadError('Label value %s is in descending order, which is not allowed.' % value)
                else:
                    i1 = int(value)
                    i2 = i1
                return i1, i2
            except ValueError:
                raise error.PayloadError('Label %s is not an integer or an integer range.' % value)

        if type(values) is str:
            values = values.split(',')

        parsed_values = sorted( [ createValue(value) for value in values ] )

        # detect any overlap and remove it - remember that the list is sorted

        nv = [] # normalized values
        for v1, v2 in parsed_values:
            if len(nv) == 0:
                nv.append( (v1,v2) )
                continue

            l = nv[-1] # last
            if v1 <= l[1] + 1: # merge
                nv = nv[:-1] + [ (l[0], max(l[1],v2)) ]
            else:
                nv.append( (v1,v2) )

        return nv


    def intersect(self, other):
        # get the common labels between two label set - I hate you nml
        assert type(other) is Label, 'Cannot intersect label with something that is not a label (other was %s)' % type(other)
        assert self.type_ == other.type_, 'Cannot insersect label of different types'

        label_values = []
        i = iter(other.values)
        o1, o2 = i.next()

        for v1, v2 in self.values:
            while True:
                if v2 < o1:
                    break
                elif o2 < v1:
                    try:
                        o1, o2 = i.next()
                    except StopIteration:
                        break
                    continue
                label_values.append( ( max(v1,o1), min(v2,o2)) )
                if v2 <= o2:
                    break
                elif o2 <= v2:
                    try:
                        o1, o2 = i.next()
                    except StopIteration:
                        break

        if len(label_values) == 0:
            raise EmptyLabelSet('Label intersection produced empty label set')

        ls = ','.join( [ '%i-%s' % (nv[0], nv[1]) for nv in label_values ] )
        return Label(self.type_, ls)


    def labelValue(self):
        vs = [ str(v1) if v1 == v2 else str(v1) + '-' + str(v2) for v1,v2 in self.values ]
        return ','.join(vs)

    def singleValue(self):
        return len(self.values) == 1 and self.values[0][0] == self.values[0][1]

    def enumerateValues(self):
        lv = [ range(lr[0], lr[1]+1) for lr in self.values ]
        return list(itertools.chain.from_iterable( lv ) )

    def randomLabel(self):
        # not evenly distributed, but that isn't promised anyway
        label_range = random.choice(self.values)
        return random.randint(label_range[0], label_range[1]+1)


    def __eq__(self, other):
        if not type(other) is Label:
            return False
        return self.type_ == other.type_ and sorted(self.values) == sorted(other.values)


    def __repr__(self):
        return '<Label %s:%s>' % (self.type_, self.labelValue())



class STP(object): # Service Termination Point

    def __init__(self, network, port, labels=None):
        assert type(network) is str, 'Invalid network type provided for STP'
        assert type(port) is str, 'Invalid port type provided for STP'
        self.network = network
        self.port = port
        self.labels = labels or []


    def __eq__(self, other):
        if not type(other) is STP:
            return False
        return self.network == other.network and self.port == other.port and self.labels == other.labels


    def __repr__(self):
        base = '<STP %s %s' % (self.network, self.port)
        if self.labels:
            base += ' ' + ','.join( [ label.type_.split('#')[-1] + '=' + label.labelValue() for label in self.labels ] )
        return base + '>'



class Link(object): # intra network link

    def __init__(self, network, src_port, dst_port, src_labels=None, dst_labels=None):
        if src_labels is None:
            assert dst_labels is None, 'Source and destination labels must either both be None, or both specified'
        else:
            assert dst_labels is not None, 'Source and destination labels must either both be None, or both specified'
            assert type(src_labels) is list, 'Source labels must be a list'
            assert type(dst_labels) is list, 'Dest labels must be a list'
        self.network = network
        self.src_port = src_port
        self.dst_port = dst_port
        self.src_labels = src_labels
        self.dst_labels = dst_labels


    def sourceSTP(self):
        return STP(self.network, self.src_port, None, self.src_labels)


    def destSTP(self):
        return STP(self.network, self.dst_port, None, self.dst_labels)


    def __eq__(self, other):
        if not type(other) is Link:
            return False
        return (self.network, self.src_port, self.dst_port, self.src_labels, self.dst_labels) == \
               (other.network, other.src_port, other.dst_port, other.src_labels, other.dst_labels)


    def __repr__(self):
        if self.src_labels:
            src_label_type = self.src_labels[0].type_.split('#')[-1]
            dst_label_type = self.dst_labels[0].type_.split('#')[-1]
            return '<Link %s::%s#%s=%s--%s#%s=%s>' % (self.network, self.src_port, src_label_type, self.src_labels[0].labelValue(), self.dst_port, dst_label_type, self.dst_labels[0].labelValue())
        else:
            return '<Link %s::%s=%s>' % (self.network, self.src_port, self.dst_port)



class Path(object):
    """
    Represent a path from a source and destitionation STP, with the endpoint pairs between them.
    """
    def __init__(self, network_links):
        self.network_links = network_links


    def links(self):
        return self.network_links


    def sourceEndpoint(self):
        return self.network_links[0].sourceSTP()


    def destEndpoint(self):
        return self.network_links[-1].destSTP()


    def __str__(self):
        return '<Path: ' + ' '.join( [ str(nl) for nl in self.network_links ] ) + '>'



class NetworkServiceAgent(object):

    def __init__(self, identity, endpoint, service_type=None):
        assert type(identity) is str, 'NSA identity type must be string (type: %s, value %s)' % (type(identity), identity)
        assert type(endpoint) is str, 'NSA endpoint type must be string (type: %s, value %s)' % (type(endpoint), endpoint)
        self.identity = identity
        self.endpoint = endpoint.strip()
        self.service_type = service_type


    def getHostPort(self):
        url = urlparse.urlparse(self.endpoint)
        host, port = url.netloc.split(':',2)
        port = int(port)
        return host, port


    def urn(self):
        return OGF_PREFIX + self.identity


    def getServiceType(self):
        if self.service_type is None:
            raise ValueError('NSA with identity %s is not constructed with a type' % self.identity)
        return self.service_type


    def __str__(self):
        return '<NetworkServiceAgent %s>' % self.identity



class Criteria(object):

    def __init__(self, revision, schedule, service_def):
        self.revision    = revision
        self.schedule    = schedule
        self.service_def = service_def



class Schedule(object):

    def __init__(self, start_time, end_time):
        # Must be datetime instances without tzinfo
        assert start_time.tzinfo is None, 'Start time must NOT have time zone'
        assert end_time.tzinfo   is None, 'End time must NOT have time zone'

        self.start_time = start_time
        self.end_time   = end_time


    def __str__(self):
        return '<Schedule: %s-%s>' % (self.start_time, self.end_time)



class EthernetService(object):

    def __init__(self, source_stp, dest_stp, capacity, mtu, burst_size,  directionality=BIDIRECTIONAL, symmetric=False, ero=None):

        self._verifySTPs(source_stp, dest_stp)

        self.source_stp     = source_stp
        self.dest_stp       = dest_stp
        self.capacity       = capacity
        self.mtu            = mtu
        self.burst_size     = burst_size
        self.directionality = directionality
        self.symmetric      = symmetric
        self.ero            = ero


    def _verifySTPs(self, source_stp, dest_stp):

        assert source_stp.labels == [], 'Source STP must not specify labels in EthernetService'
        assert dest_stp.labels == [],   'Destination STP must not specify labels in EthernetService'



class EthernetVLANService(EthernetService):

    def _verifySTPs(self, source_stp, dest_stp):

        assert source_stp.labels and len(source_stp.labels) == 1,  'Source STP must specify label and exactly one for EthernetVLANService'
        assert dest_stp.labels and len(dest_stp.labels) == 1, 'Destination STP must specify label and exactly one for EthernetVLANService'

        assert source_stp.labels[0].type_ == cnt.ETHERNET_VLAN, 'Source STP label type must be %s for EthernetVLANService' % cnt.ETHERNET_VLAN
        assert dest_stp.labels[0].type_   == cnt.ETHERNET_VLAN, 'Destination STP label type must be %s for EthernetVLANService' % cnt.ETHERNET_VLAN

