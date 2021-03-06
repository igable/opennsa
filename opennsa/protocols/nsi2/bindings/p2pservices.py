## Generated by pyxsdgen

from xml.etree import ElementTree as ET

# types

class P2PServiceBaseType(object):
    def __init__(self, capacity, directionality, symmetricPath, sourceSTP, destSTP, ero):
        self.capacity = capacity  # long
        self.directionality = directionality  # DirectionalityType -> string
        self.symmetricPath = symmetricPath  # boolean
        self.sourceSTP = sourceSTP  # StpType
        self.destSTP = destSTP  # StpType
        self.ero = ero  # [ OrderedStpType ]

    @classmethod
    def build(self, element):
        return P2PServiceBaseType(
                int(element.findtext('capacity')),
                element.findtext('directionality'),
                True if element.findtext('symmetricPath') == 'true' else False if element.find('symmetricPath') is not None else None,
                StpType.build(element.find('sourceSTP')),
                StpType.build(element.find('destSTP')),
                [ OrderedStpType.build(e) for e in element.find('ero') ] if element.find('ero') is not None else None
               )

    def xml(self, elementName):
        r = ET.Element(elementName)
        ET.SubElement(r, 'capacity').text = str(self.capacity)
        ET.SubElement(r, 'directionality').text = self.directionality
        if self.symmetricPath is not None:
            ET.SubElement(r, 'symmetricPath').text = 'true' if self.symmetricPath else 'false'
        r.append(self.sourceSTP.xml('sourceSTP'))
        r.append(self.destSTP.xml('destSTP'))
        if self.ero is not None:
            ET.SubElement(r, 'ero').extend( [ e.xml('ero') for e in self.ero ] )
        return r


class StpType(object):
    def __init__(self, networkId, localId, labels):
        self.networkId = networkId  # string
        self.localId = localId  # string
        self.labels = labels  # [ TypeValuePairType ]

    @classmethod
    def build(self, element):
        return StpType(
                element.findtext('networkId'),
                element.findtext('localId'),
                [ TypeValuePairType.build(e) for e in element.find('labels') ] if element.find('labels') is not None else None
               )

    def xml(self, elementName):
        r = ET.Element(elementName)
        ET.SubElement(r, 'networkId').text = self.networkId
        ET.SubElement(r, 'localId').text = self.localId
        if self.labels is not None:
            ET.SubElement(r, 'labels').extend( [ e.xml('labels') for e in self.labels ] )
        return r


class TypeValuePairType(object):
    def __init__(self, type, namespace, value):
        self.type = type  # string
        self.namespace = namespace  # anyURI
        self.value = value  # [ string ]

    @classmethod
    def build(self, element):
        return TypeValuePairType(
                element.get('type'),
                element.get('namespace'),
                element.findtext('value') if element.find('value') is not None else None
               )

    def xml(self, elementName):
        r = ET.Element(elementName, attrib={'type' : str(self.type), 'namespace' : str(self.namespace)})
        if self.value is not None:
            for el in self.value:
                ET.SubElement(r, 'value').text = el
        return r


class ServiceExceptionType(object):
    def __init__(self, nsaId, connectionId, serviceType, errorId, text, variables, childException):
        self.nsaId = nsaId  # NsaIdType -> anyURI
        self.connectionId = connectionId  # ConnectionIdType -> string
        self.serviceType = serviceType  # string
        self.errorId = errorId  # string
        self.text = text  # string
        self.variables = variables  # [ TypeValuePairType ]
        self.childException = childException  # [ ServiceExceptionType ]

    @classmethod
    def build(self, element):
        return ServiceExceptionType(
                element.findtext('nsaId'),
                element.findtext('connectionId') if element.find('connectionId') is not None else None,
                element.findtext('serviceType') if element.find('serviceType') is not None else None,
                element.findtext('errorId'),
                element.findtext('text'),
                [ TypeValuePairType.build(e) for e in element.find('variables') ] if element.find('variables') is not None else None,
                [ ServiceExceptionType.build(e) for e in element.findall('childException') ] if element.find('childException') is not None else None
               )

    def xml(self, elementName):
        r = ET.Element(elementName)
        ET.SubElement(r, 'nsaId').text = str(self.nsaId)
        if self.connectionId is not None:
            ET.SubElement(r, 'connectionId').text = self.connectionId
        if self.serviceType is not None:
            ET.SubElement(r, 'serviceType').text = self.serviceType
        ET.SubElement(r, 'errorId').text = self.errorId
        ET.SubElement(r, 'text').text = self.text
        if self.variables is not None:
            ET.SubElement(r, 'variables').extend( [ e.xml('variables') for e in self.variables ] )
        if self.childException is not None:
            for el in self.childException:
                ET.SubElement(r, 'childException').extend( el.xml('childException') )
        return r


class EthernetVlanType(object):
    def __init__(self, capacity, directionality, symmetricPath, sourceSTP, destSTP, ero, mtu, burstsize, sourceVLAN, destVLAN):
        self.capacity = capacity  # long
        self.directionality = directionality  # DirectionalityType -> string
        self.symmetricPath = symmetricPath  # boolean
        self.sourceSTP = sourceSTP  # StpType
        self.destSTP = destSTP  # StpType
        self.ero = ero  # [ OrderedStpType ]
        self.mtu = mtu  # int
        self.burstsize = burstsize  # long
        self.sourceVLAN = sourceVLAN  # vlanIdType -> int
        self.destVLAN = destVLAN  # vlanIdType -> int

    @classmethod
    def build(self, element):
        return EthernetVlanType(
                int(element.findtext('capacity')),
                element.findtext('directionality'),
                True if element.findtext('symmetricPath') == 'true' else False if element.find('symmetricPath') is not None else None,
                StpType.build(element.find('sourceSTP')),
                StpType.build(element.find('destSTP')),
                [ OrderedStpType.build(e) for e in element.find('ero') ] if element.find('ero') is not None else None,
                int(element.findtext('mtu')) if element.find('mtu') is not None else None,
                int(element.findtext('burstsize')) if element.find('burstsize') is not None else None,
                int(element.findtext('sourceVLAN')),
                int(element.findtext('destVLAN'))
               )

    def xml(self, elementName):
        r = ET.Element(elementName)
        ET.SubElement(r, 'capacity').text = str(self.capacity)
        ET.SubElement(r, 'directionality').text = self.directionality
        if self.symmetricPath is not None:
            ET.SubElement(r, 'symmetricPath').text = 'true' if self.symmetricPath else 'false'
        r.append(self.sourceSTP.xml('sourceSTP'))
        r.append(self.destSTP.xml('destSTP'))
        if self.ero is not None:
            ET.SubElement(r, 'ero').extend( [ e.xml('ero') for e in self.ero ] )
        if self.mtu is not None:
            ET.SubElement(r, 'mtu').text = str(self.mtu)
        if self.burstsize is not None:
            ET.SubElement(r, 'burstsize').text = str(self.burstsize)
        ET.SubElement(r, 'sourceVLAN').text = str(self.sourceVLAN)
        ET.SubElement(r, 'destVLAN').text = str(self.destVLAN)
        return r


class OrderedStpType(object):
    def __init__(self, order, stp):
        self.order = order  # int
        self.stp = stp  # StpType

    @classmethod
    def build(self, element):
        return OrderedStpType(
                element.get('order'),
                StpType.build(element.find('stp'))
               )

    def xml(self, elementName):
        r = ET.Element(elementName, attrib={'order' : str(self.order)})
        r.append(self.stp.xml('stp'))
        return r


class EthernetBaseType(object):
    def __init__(self, capacity, directionality, symmetricPath, sourceSTP, destSTP, ero, mtu, burstsize):
        self.capacity = capacity  # long
        self.directionality = directionality  # DirectionalityType -> string
        self.symmetricPath = symmetricPath  # boolean
        self.sourceSTP = sourceSTP  # StpType
        self.destSTP = destSTP  # StpType
        self.ero = ero  # [ OrderedStpType ]
        self.mtu = mtu  # int
        self.burstsize = burstsize  # long

    @classmethod
    def build(self, element):
        return EthernetBaseType(
                int(element.findtext('capacity')),
                element.findtext('directionality'),
                True if element.findtext('symmetricPath') == 'true' else False if element.find('symmetricPath') is not None else None,
                StpType.build(element.find('sourceSTP')),
                StpType.build(element.find('destSTP')),
                [ OrderedStpType.build(e) for e in element.find('ero') ] if element.find('ero') is not None else None,
                int(element.findtext('mtu')) if element.find('mtu') is not None else None,
                int(element.findtext('burstsize')) if element.find('burstsize') is not None else None
               )

    def xml(self, elementName):
        r = ET.Element(elementName)
        ET.SubElement(r, 'capacity').text = str(self.capacity)
        ET.SubElement(r, 'directionality').text = self.directionality
        if self.symmetricPath is not None:
            ET.SubElement(r, 'symmetricPath').text = 'true' if self.symmetricPath else 'false'
        r.append(self.sourceSTP.xml('sourceSTP'))
        r.append(self.destSTP.xml('destSTP'))
        if self.ero is not None:
            ET.SubElement(r, 'ero').extend( [ e.xml('ero') for e in self.ero ] )
        if self.mtu is not None:
            ET.SubElement(r, 'mtu').text = str(self.mtu)
        if self.burstsize is not None:
            ET.SubElement(r, 'burstsize').text = str(self.burstsize)
        return r


p2ps = ET.QName('http://schemas.ogf.org/nsi/2013/07/services/point2point', 'p2ps')
ets = ET.QName('http://schemas.ogf.org/nsi/2013/07/services/point2point', 'ets')
stpList = ET.QName('http://schemas.ogf.org/nsi/2013/07/services/types', 'stpList')
evts = ET.QName('http://schemas.ogf.org/nsi/2013/07/services/point2point', 'evts')
stp = ET.QName('http://schemas.ogf.org/nsi/2013/07/services/types', 'stp')
capacity = ET.QName('http://schemas.ogf.org/nsi/2013/07/services/point2point', 'capacity')
serviceException = ET.QName('http://schemas.ogf.org/nsi/2013/07/framework/types', 'serviceException')

def parse(input_):

    root = ET.fromstring(input_)

    return parseElement(root)


def parseElement(element):

    type_map = {
        '{http://schemas.ogf.org/nsi/2013/07/services/point2point}p2ps' : P2PServiceBaseType,
        '{http://schemas.ogf.org/nsi/2013/07/services/point2point}ets' : EthernetBaseType,
        '{http://schemas.ogf.org/nsi/2013/07/services/point2point}evts' : EthernetVlanType,
        '{http://schemas.ogf.org/nsi/2013/07/services/types}stp' : StpType,
        '{http://schemas.ogf.org/nsi/2013/07/framework/types}serviceException' : ServiceExceptionType
    }

    if not element.tag in type_map:
        raise ValueError('No type mapping for tag %s' % element.tag)

    type_ = type_map[element.tag]
    return type_.build(element)
