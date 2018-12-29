# -*- coding: utf-8 -*-
"""Unit tests for didl_lite."""

from defusedxml import ElementTree as ET  # type: ignore

from didl_lite import didl_lite


NAMESPACES = {
    'didl_lite': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'upnp': 'urn:schemas-upnp-org:metadata-1-0/upnp/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}


class TestDidlLite:

    def test_item_from_xml(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <item id="0" parentID="0" restricted="1">
        <dc:title>Audio Item Title</dc:title>
        <upnp:class>object.item.audioItem</upnp:class>
        <dc:language>English</dc:language>
        <res protocolInfo="protocol_info">url</res>
    </item>
</DIDL-Lite>"""
        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        item = items[0]
        assert getattr(item, 'title') == 'Audio Item Title'
        assert getattr(item, 'upnp_class') == 'object.item.audioItem'
        assert getattr(item, 'language') == 'English'
        assert isinstance(item, didl_lite.AudioItem)

        resources = item.resources
        assert len(resources) == 1
        resource = resources[0]
        assert resource.protocol_info == 'protocol_info'
        assert resource.uri == 'url'

    def test_item_to_xml(self) -> None:
        resource = didl_lite.Resource('url', 'protocol_info')
        items = [
            didl_lite.AudioItem(id='0',
                                parent_id='0',
                                title='Audio Item Title',
                                restricted='1',
                                resources=[resource],
                                language='English'),
        ]
        didl_string = didl_lite.to_xml_string(*items).decode('utf-8')
        didl_el = ET.fromstring(didl_string)
        assert didl_el is not None

        item_el = didl_el.find('./didl_lite:item', NAMESPACES)
        assert item_el is not None
        assert item_el.attrib['id'] == '0'
        assert item_el.attrib['parentID'] == '0'
        assert item_el.attrib['restricted'] == '1'

        title_el = item_el.find('./dc:title', NAMESPACES)
        assert title_el is not None
        assert title_el.text == 'Audio Item Title'

        class_el = item_el.find('./upnp:class', NAMESPACES)
        assert class_el is not None
        assert class_el.text == 'object.item.audioItem'

        language_el = item_el.find('./dc:language', NAMESPACES)
        assert language_el is not None
        assert language_el.text == 'English'

        res_el = item_el.find('./didl_lite:res', NAMESPACES)
        assert res_el is not None
        assert res_el.attrib['protocolInfo'] == 'protocol_info'
        assert res_el.text == 'url'

    def test_container_from_xml(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <container id="0" parentID="0" restricted="1">
        <dc:title>Album Container Title</dc:title>
        <upnp:class>object.container.album</upnp:class>

        <item id="1" parentID="0" restricted="1">
            <dc:title>Audio Item Title</dc:title>
            <upnp:class>object.item.audioItem</upnp:class>
            <dc:language>English</dc:language>
            <res protocolInfo="protocol_info">url</res>
        </item>
    </container>
</DIDL-Lite>"""
        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        container = items[0]
        assert isinstance(container, didl_lite.Container)
        assert getattr(container, 'title') == 'Album Container Title'
        assert getattr(container, 'upnp_class') == 'object.container.album'

        item = container[0]
        assert item.title == 'Audio Item Title'
        assert item.upnp_class == 'object.item.audioItem'
        assert item.language == 'English'

        resources = item.resources
        assert len(resources) == 1
        resource = resources[0]
        assert resource.protocol_info == 'protocol_info'
        assert resource.uri == 'url'

    def test_container_to_xml(self) -> None:
        container = didl_lite.Album(id='0', parent_id='0',
                                    title='Audio Item Title',
                                    restricted='1')
        resource = didl_lite.Resource('url', 'protocol_info')
        item = didl_lite.AudioItem(id='0', parent_id='0',
                                   title='Audio Item Title',
                                   restricted='1', resources=[resource],
                                   language='English')
        container.append(item)

        didl_string = didl_lite.to_xml_string(container).decode('utf-8')
        didl_el = ET.fromstring(didl_string)
        assert didl_el is not None

        container_el = didl_el.find('./didl_lite:container', NAMESPACES)
        assert container_el is not None
        assert container_el.attrib['id'] == '0'
        assert container_el.attrib['parentID'] == '0'
        assert container_el.attrib['restricted'] == '1'

        item_el = container_el.find('./didl_lite:item', NAMESPACES)
        assert item_el is not None
        assert item_el.attrib['id'] == '0'
        assert item_el.attrib['parentID'] == '0'
        assert item_el.attrib['restricted'] == '1'

        title_el = item_el.find('./dc:title', NAMESPACES)
        assert title_el is not None
        assert title_el.text == 'Audio Item Title'

        class_el = item_el.find('./upnp:class', NAMESPACES)
        assert class_el is not None
        assert class_el.text == 'object.item.audioItem'

        language_el = item_el.find('./dc:language', NAMESPACES)
        assert language_el is not None
        assert language_el.text == 'English'

        res_el = item_el.find('./didl_lite:res', NAMESPACES)
        assert res_el is not None
        assert res_el.attrib['protocolInfo'] == 'protocol_info'
        assert res_el.text == 'url'

    def test_descriptor_from_xml_root(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <desc id="1" nameSpace="ns" type="type">Text</desc>
</DIDL-Lite>"""

        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        descriptor = items[0]
        assert descriptor is not None
        assert getattr(descriptor, 'id') == '1'
        assert getattr(descriptor, 'name_space') == 'ns'
        assert getattr(descriptor, 'type') == 'type'
        assert getattr(descriptor, 'text') == 'Text'

    def test_descriptor_from_xml_item(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <item id="1" parentID="0" restricted="1">
        <dc:title>Audio Item Title</dc:title>
        <upnp:class>object.item.audioItem</upnp:class>
        <dc:language>English</dc:language>
        <res protocolInfo="protocol_info">url</res>
        <desc id="1" nameSpace="ns" type="type">Text</desc>
    </item>
</DIDL-Lite>"""

        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        item = items[0]
        assert item is not None
        assert isinstance(item, didl_lite.AudioItem)

        descriptor = item.descriptors[0]
        assert descriptor is not None
        assert descriptor.id == '1'
        assert descriptor.name_space == 'ns'
        assert descriptor.type == 'type'
        assert descriptor.text == 'Text'

    def test_descriptor_from_xml_container(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <container id="0" parentID="0" restricted="1">
        <dc:title>Album Container Title</dc:title>
        <upnp:class>object.container.album</upnp:class>

        <desc id="1" nameSpace="ns" type="type">Text</desc>
    </container>
</DIDL-Lite>"""

        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        container = items[0]
        assert container is not None
        assert isinstance(container, didl_lite.Container)

        descriptor = container.descriptors[0]
        assert descriptor is not None
        assert descriptor.id == '1'
        assert descriptor.name_space == 'ns'
        assert descriptor.type == 'type'
        assert descriptor.text == 'Text'

    def test_descriptor_from_xml_container_item(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <container id="0" parentID="0" restricted="1">
        <dc:title>Album Container Title</dc:title>
        <upnp:class>object.container.album</upnp:class>

        <item id="1" parentID="0" restricted="1">
            <dc:title>Audio Item Title</dc:title>
            <upnp:class>object.item.audioItem</upnp:class>
            <dc:language>English</dc:language>
            <res protocolInfo="protocol_info">url</res>
            <desc id="1" nameSpace="ns" type="type">Text</desc>
        </item>
    </container>
</DIDL-Lite>"""

        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        container = items[0]
        assert container is not None
        assert isinstance(container, didl_lite.Container)

        item = container[0]
        assert item is not None

        descriptor = item.descriptors[0]
        assert descriptor is not None
        assert descriptor.id == '1'
        assert descriptor.name_space == 'ns'
        assert descriptor.type == 'type'
        assert descriptor.text == 'Text'

    def test_descriptor_to_xml(self) -> None:
        descriptor = didl_lite.Descriptor(id='1', name_space='ns',
                                          type='type', text='Text')
        item = didl_lite.AudioItem(id='0', parent_id='0',
                                   title='Audio Item Title',
                                   restricted='1', language='English',
                                   descriptors=[descriptor])
        didl_string = didl_lite.to_xml_string(item).decode('utf-8')
        didl_el = ET.fromstring(didl_string)
        assert didl_el is not None

        item_el = didl_el.find('./didl_lite:item', NAMESPACES)
        assert item_el is not None

        descriptor_el = item_el.find('./didl_lite:desc', NAMESPACES)
        assert descriptor_el is not None
        assert len(descriptor_el.attrib) == 3
        assert descriptor_el.attrib['id'] == '1'
        assert descriptor_el.attrib['nameSpace'] == 'ns'
        assert descriptor_el.attrib['type'] == 'type'
        assert descriptor_el.text == 'Text'

        descriptor = didl_lite.Descriptor(id='2', name_space='ns2')
        descriptor_el = descriptor.to_xml()
        assert descriptor_el is not None
        assert len(descriptor_el.attrib) == 2
        assert descriptor_el.attrib['id'] == '2'
        assert descriptor_el.attrib['nameSpace'] == 'ns2'

    def test_item_order(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <item id="0" parentID="0" restricted="1">
        <dc:title>Audio Item Title 1</dc:title>
        <upnp:class>object.item.audioItem</upnp:class>
        <dc:language>English</dc:language>
    </item>
    <container id="1" parentID="0" restricted="1">
        <dc:title>Album Container Title</dc:title>
        <upnp:class>object.container.album</upnp:class>
    </container>
    <item id="2" parentID="0" restricted="1">
        <dc:title>Audio Item Title 1</dc:title>
        <upnp:class>object.item.audioItem</upnp:class>
        <dc:language>English</dc:language>
    </item>
</DIDL-Lite>"""

        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 3

        assert isinstance(items[0], didl_lite.AudioItem)
        assert isinstance(items[1], didl_lite.Album)
        assert isinstance(items[2], didl_lite.AudioItem)

    def test_item_property_attribute_from_xml(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <item id="0" parentID="0" restricted="1">
        <dc:title>Video Item Title</dc:title>
        <upnp:class>object.item.videoItem</upnp:class>
        <upnp:genre id="genreId">Action</upnp:genre>
    </item>
</DIDL-Lite>"""

        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        item = items[0]
        assert item is not None
        assert getattr(item, 'genre') == 'Action'
        assert getattr(item, 'genre_id') == 'genreId'

    def test_item_property_attribute_to_xml(self) -> None:
        item = didl_lite.VideoItem(id='0', parent_id='0',
                                   title='Video Item Title',
                                   restricted='1',
                                   genre='Action', genre_id='genreId')
        didl_string = didl_lite.to_xml_string(item).decode('utf-8')
        didl_el = ET.fromstring(didl_string)
        assert didl_el is not None

        item_el = didl_el.find('./didl_lite:item', NAMESPACES)
        assert item_el is not None

        genre_el = item_el.find('./upnp:genre', NAMESPACES)
        assert genre_el is not None
        assert genre_el.text == 'Action'
        assert genre_el.attrib['id'] == 'genreId'

    def test_item_missing_id(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <item restricted="1">
        <dc:title>Video Item Title</dc:title>
        <upnp:class>object.item</upnp:class>
    </item>
</DIDL-Lite>"""

        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

    def test_item_set_attributes(self) -> None:
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <item restricted="1">
        <dc:title>Video Item Title</dc:title>
        <upnp:class>object.item.videoItem</upnp:class>
    </item>
</DIDL-Lite>"""

        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        item = items[0]
        assert getattr(item, 'title') == 'Video Item Title'
        assert hasattr(item, 'rating')
        assert getattr(item, 'rating') is None
        assert isinstance(item, didl_lite.VideoItem)
        assert len(item.resources) == 0

    def test_extra_properties(self) -> None:
        didl_string = """
        <DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
                   xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:sec="http://www.sec.co.kr/">
            <item restricted="1">
                <dc:title>Video Item Title</dc:title>
                <upnp:class>object.item.videoItem</upnp:class>
                <upnp:albumArtURI>extra_property</upnp:albumArtURI>
            </item>
        </DIDL-Lite>"""
        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        item = items[0]
        assert hasattr(item, 'album_art_uri')
        assert getattr(item, 'album_art_uri') == 'extra_property'

    def test_default_properties_set(self) -> None:
        item = didl_lite.VideoItem(id='0', parent_id='0',
                                   title='Video Item Title',
                                   restricted='1')
        assert hasattr(item, 'genre_type')  # property is set
