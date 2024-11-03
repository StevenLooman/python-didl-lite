# -*- coding: utf-8 -*-
"""Unit tests for didl_lite."""

import pytest
from defusedxml import ElementTree as ET

from didl_lite import didl_lite

NAMESPACES = {
    "didl_lite": "urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "upnp": "urn:schemas-upnp-org:metadata-1-0/upnp/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


class TestDidlLite:
    """Tests for didl_lite."""

    # pylint: disable=too-many-public-methods

    def test_item_from_xml(self) -> None:
        """Test item from XML."""
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
        <upnp:longDescription>Long description</upnp:longDescription>
    </item>
</DIDL-Lite>"""
        items = didl_lite.from_xml_string(didl_string)
        assert len(items) == 1

        item = items[0]
        assert item.xml_el is not None
        assert getattr(item, "title") == "Audio Item Title"
        assert getattr(item, "upnp_class") == "object.item.audioItem"
        assert getattr(item, "language") == "English"
        assert getattr(item, "longDescription") == "Long description"
        assert getattr(item, "long_description") == "Long description"
        assert isinstance(item, didl_lite.AudioItem)
        assert not hasattr(item, "non_existing")

        resources = item.res
        assert len(resources) == 1
        resource = resources[0]
        assert resource.xml_el is not None
        assert resource.protocol_info == "protocol_info"
        assert resource.uri == "url"
        assert not hasattr(item, "non_existing")
        assert item.res == item.resources

    def test_item_bad_class(self) -> None:
        """Test item from XML that has a badly-cased upnp:class."""
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <item id="0" parentID="0" restricted="1">
        <dc:title>Audio Item Title</dc:title>
        <upnp:class>Object.Item.AudioItem</upnp:class>
        <dc:language>English</dc:language>
        <res protocolInfo="protocol_info">url</res>
        <upnp:longDescription>Long description</upnp:longDescription>
    </item>
</DIDL-Lite>"""
        with pytest.raises(
            didl_lite.DidlLiteException,
            match="upnp:class Object.Item.AudioItem is unknown",
        ):
            didl_lite.from_xml_string(didl_string)

        items = didl_lite.from_xml_string(didl_string, strict=False)
        assert len(items) == 1

        item = items[0]
        assert isinstance(item, didl_lite.AudioItem)

    def test_item_from_xml_not_strict(self) -> None:
        """Test item from XML."""
        didl_string = """
<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
           xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:sec="http://www.sec.co.kr/">
    <item id="0" parentID="0" restricted="1">
        <dc:title>Audio Item Title</dc:title>
        <upnp:class>object.item.audioItem</upnp:class>
        <dc:language>English</dc:language>
        <res>url</res>
    </item>
</DIDL-Lite>"""
        items = didl_lite.from_xml_string(didl_string, strict=False)
        assert len(items) == 1

        item = items[0]
        assert item.xml_el is not None
        assert getattr(item, "title") == "Audio Item Title"
        assert getattr(item, "upnp_class") == "object.item.audioItem"
        assert getattr(item, "language") == "English"
        assert isinstance(item, didl_lite.AudioItem)
        assert not hasattr(item, "non_existing")

        resources = item.res
        assert len(resources) == 1
        resource = resources[0]
        assert resource.xml_el is not None
        assert resource.protocol_info is None  # This is now allowed with strict=False
        assert resource.uri == "url"
        assert not hasattr(item, "non_existing")
        assert item.res == item.resources

    def test_item_to_xml(self) -> None:
        """Test item to XML."""
        resource = didl_lite.Resource("url", "protocol_info")
        items = [
            didl_lite.AudioItem(
                id="0",
                parent_id="0",
                title="Audio Item Title",
                restricted="1",
                resources=[resource],
                language="English",
                longDescription="Long description",
            ),
        ]
        didl_string = didl_lite.to_xml_string(*items).decode("utf-8")

        assert 'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"' in didl_string
        assert 'xmlns:dc="http://purl.org/dc/elements/1.1/"' in didl_string
        assert 'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"' in didl_string
        assert 'xmlns:sec="http://www.sec.co.kr/"' in didl_string
        assert 'xmlns:ns1="urn:schemas-upnp-org:metadata-1-0/upnp/"' not in didl_string

        didl_el = ET.fromstring(didl_string)

        item_el = didl_el.find("./didl_lite:item", NAMESPACES)
        assert item_el is not None
        assert item_el.attrib["id"] == "0"
        assert item_el.attrib["parentID"] == "0"
        assert item_el.attrib["restricted"] == "1"

        title_el = item_el.find("./dc:title", NAMESPACES)
        assert title_el is not None
        assert title_el.text == "Audio Item Title"

        class_el = item_el.find("./upnp:class", NAMESPACES)
        assert class_el is not None
        assert class_el.text == "object.item.audioItem"

        language_el = item_el.find("./dc:language", NAMESPACES)
        assert language_el is not None
        assert language_el.text == "English"

        long_description_el = item_el.find("./upnp:longDescription", NAMESPACES)
        assert long_description_el is not None
        assert long_description_el.text == "Long description"

        res_el = item_el.find("./didl_lite:res", NAMESPACES)
        assert res_el is not None
        assert res_el.attrib["protocolInfo"] == "protocol_info"
        assert res_el.text == "url"

    def test_item_repr(self) -> None:
        """Test item's repr can convert back to an equivalent item."""
        # pylint: disable=import-outside-toplevel
        # repr method doesn't know how package was imported, so only uses class names
        from didl_lite.didl_lite import AudioItem, Resource

        item = AudioItem(
            id="0",
            parent_id="0",
            title="Audio Item Title",
            restricted="1",
            res=[
                Resource("url", "protocol_info"),
                Resource("url2", "protocol_info2"),
            ],
            language="English",
        )

        item_repr = repr(item)
        item_remade = eval(item_repr)  # pylint: disable=eval-used
        assert ET.tostring(item.to_xml()) == ET.tostring(item_remade.to_xml())

    def test_container_from_xml(self) -> None:
        """Test container from XML."""
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
        assert container.xml_el is not None
        assert isinstance(container, didl_lite.Container)
        assert getattr(container, "title") == "Album Container Title"
        assert getattr(container, "upnp_class") == "object.container.album"

        item = container[0]
        assert item.xml_el is not None
        assert item.title == "Audio Item Title"
        assert item.upnp_class == "object.item.audioItem"
        assert item.language == "English"

        resources = item.res
        assert len(resources) == 1
        resource = resources[0]
        assert resource.xml_el is not None
        assert resource.protocol_info == "protocol_info"
        assert resource.uri == "url"
        assert item.res == item.resources

    def test_container_to_xml(self) -> None:
        """Test container to XML."""
        container = didl_lite.Album(
            id="0", parent_id="0", title="Audio Item Title", restricted="1"
        )
        resource = didl_lite.Resource("url", "protocol_info")
        item = didl_lite.AudioItem(
            id="0",
            parent_id="0",
            title="Audio Item Title",
            restricted="1",
            resources=[resource],
            language="English",
        )
        container.append(item)

        didl_string = didl_lite.to_xml_string(container).decode("utf-8")
        didl_el = ET.fromstring(didl_string)

        container_el = didl_el.find("./didl_lite:container", NAMESPACES)
        assert container_el is not None
        assert container_el.attrib["id"] == "0"
        assert container_el.attrib["parentID"] == "0"
        assert container_el.attrib["restricted"] == "1"

        item_el = container_el.find("./didl_lite:item", NAMESPACES)
        assert item_el is not None
        assert item_el.attrib["id"] == "0"
        assert item_el.attrib["parentID"] == "0"
        assert item_el.attrib["restricted"] == "1"

        title_el = item_el.find("./dc:title", NAMESPACES)
        assert title_el is not None
        assert title_el.text == "Audio Item Title"

        class_el = item_el.find("./upnp:class", NAMESPACES)
        assert class_el is not None
        assert class_el.text == "object.item.audioItem"

        language_el = item_el.find("./dc:language", NAMESPACES)
        assert language_el is not None
        assert language_el.text == "English"

        res_el = item_el.find("./didl_lite:res", NAMESPACES)
        assert res_el is not None
        assert res_el.attrib["protocolInfo"] == "protocol_info"
        assert res_el.text == "url"

    def test_container_repr(self) -> None:
        """Test containers's repr can convert back to an equivalent container."""
        # pylint: disable=import-outside-toplevel
        from didl_lite.didl_lite import Album, AudioItem, Resource

        container = Album(
            id="0", parent_id="0", title="Audio Item Title", restricted="1"
        )
        resource = Resource("url", "protocol_info")
        item = AudioItem(
            id="0",
            parent_id="0",
            title="Audio Item Title",
            restricted="1",
            resources=[resource],
            language="English",
        )
        container.append(item)

        container_repr = repr(container)
        container_remade = eval(container_repr)  # pylint: disable=eval-used
        assert ET.tostring(container.to_xml()) == ET.tostring(container_remade.to_xml())

    def test_descriptor_from_xml_root(self) -> None:
        """Test root descriptor from XML."""
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
        assert descriptor.xml_el is not None
        assert getattr(descriptor, "id") == "1"
        assert getattr(descriptor, "name_space") == "ns"
        assert getattr(descriptor, "type") == "type"
        assert getattr(descriptor, "text") == "Text"

    def test_descriptor_from_xml_item(self) -> None:
        """Test item descriptor from XML."""
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
        assert descriptor.xml_el is not None
        assert descriptor.id == "1"
        assert descriptor.name_space == "ns"
        assert descriptor.type == "type"
        assert descriptor.text == "Text"

    def test_descriptor_from_xml_container(self) -> None:
        """Test container descriptor from XML."""
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
        assert container.xml_el is not None
        assert isinstance(container, didl_lite.Container)

        descriptor = container.descriptors[0]
        assert descriptor is not None
        assert descriptor.xml_el is not None
        assert descriptor.id == "1"
        assert descriptor.name_space == "ns"
        assert descriptor.type == "type"
        assert descriptor.text == "Text"

    def test_descriptor_from_xml_container_item(self) -> None:
        """Test item descriptor in container from XML."""
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
        assert descriptor.xml_el is not None
        assert descriptor.id == "1"
        assert descriptor.name_space == "ns"
        assert descriptor.type == "type"
        assert descriptor.text == "Text"

    def test_descriptor_to_xml(self) -> None:
        """Test descriptor to XML."""
        descriptor = didl_lite.Descriptor(
            id="1", name_space="ns", type="type", text="Text"
        )
        item = didl_lite.AudioItem(
            id="0",
            parent_id="0",
            title="Audio Item Title",
            restricted="1",
            language="English",
            descriptors=[descriptor],
        )
        didl_string = didl_lite.to_xml_string(item).decode("utf-8")
        didl_el = ET.fromstring(didl_string)

        item_el = didl_el.find("./didl_lite:item", NAMESPACES)
        assert item_el is not None

        descriptor_el = item_el.find("./didl_lite:desc", NAMESPACES)
        assert descriptor_el is not None
        assert len(descriptor_el.attrib) == 3
        assert descriptor_el.attrib["id"] == "1"
        assert descriptor_el.attrib["nameSpace"] == "ns"
        assert descriptor_el.attrib["type"] == "type"
        assert descriptor_el.text == "Text"

        descriptor = didl_lite.Descriptor(id="2", name_space="ns2")
        descriptor_el = descriptor.to_xml()
        assert descriptor_el is not None
        assert len(descriptor_el.attrib) == 2
        assert descriptor_el.attrib["id"] == "2"
        assert descriptor_el.attrib["nameSpace"] == "ns2"

    def test_descriptor_repr(self) -> None:
        """Test descriptor's repr can convert back to an equivalent descriptorb."""
        # pylint: disable=import-outside-toplevel
        from didl_lite.didl_lite import Descriptor

        descriptor = Descriptor(id="1", name_space="ns", type="type", text="Text")

        descriptor_repr = repr(descriptor)
        descriptor_remade = eval(descriptor_repr)  # pylint: disable=eval-used
        assert ET.tostring(descriptor.to_xml()) == ET.tostring(
            descriptor_remade.to_xml()
        )

    def test_item_order(self) -> None:
        """Test item ordering."""
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
        """Test item property from XML attribute."""
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
        assert getattr(item, "genre") == "Action"
        assert getattr(item, "genre_id") == "genreId"

    def test_item_property_attribute_to_xml(self) -> None:
        """Test item property to XML."""
        item = didl_lite.VideoItem(
            id="0",
            parent_id="0",
            title="Video Item Title",
            restricted="1",
            genre="Action",
            genre_id="genreId",
        )
        didl_string = didl_lite.to_xml_string(item).decode("utf-8")
        didl_el = ET.fromstring(didl_string)

        item_el = didl_el.find("./didl_lite:item", NAMESPACES)
        assert item_el is not None

        genre_el = item_el.find("./upnp:genre", NAMESPACES)
        assert genre_el is not None
        assert genre_el.text == "Action"
        assert genre_el.attrib["id"] == "genreId"

    def test_item_missing_id(self) -> None:
        """Test item missing ID from XML."""
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
        """Test item attribute from XML."""
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
        assert getattr(item, "title") == "Video Item Title"
        assert hasattr(item, "rating")
        assert getattr(item, "rating") is None
        assert isinstance(item, didl_lite.VideoItem)
        assert len(item.res) == 0
        assert item.res == item.resources

    def test_extra_properties(self) -> None:
        """Test extra item properties from XML."""
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
        assert hasattr(item, "album_art_uri")
        assert getattr(item, "album_art_uri") == "extra_property"
        assert getattr(item, "albumArtURI") == "extra_property"

    def test_default_properties_set(self) -> None:
        """Test defaults for item properties."""
        item = didl_lite.VideoItem(
            id="0", parent_id="0", title="Video Item Title", restricted="1"
        )
        assert hasattr(item, "genre_type")  # property is set

    def test_property_case(self) -> None:
        """Test item properties can be accessed using snake_case or camelCase."""
        item = didl_lite.MusicTrack(
            id="0",
            parent_id="0",
            title="Audio Item Title",
            restricted="1",
            language="English",
            originalTrackNumber="1",
            storage_medium="HDD",
        )
        assert hasattr(item, "original_track_number")
        assert hasattr(item, "originalTrackNumber")
        assert item.original_track_number is item.originalTrackNumber
        assert item.original_track_number == "1"

        assert hasattr(item, "storage_medium")
        assert hasattr(item, "storageMedium")
        assert item.storage_medium is item.storageMedium
        assert item.storage_medium == "HDD"

        assert hasattr(item, "long_description")
        assert hasattr(item, "longDescription")
        assert item.long_description is item.longDescription
        assert item.long_description is None

        assert not hasattr(item, "otherItem")
        assert not hasattr(item, "other_item")

        item.storageMedium = "CD"
        assert item.storage_medium is item.storageMedium
        assert item.storage_medium == "CD"

        item.long_description = "Long description"
        assert item.long_description is item.longDescription
        assert item.long_description == "Long description"

        item.otherItem = "otherItem"
        assert hasattr(item, "otherItem")
        assert not hasattr(item, "other_item")
        assert item.otherItem == "otherItem"

    def test_item_improper_class_nesting(self) -> None:
        """
        Test item from XML that has upnp_class element above item.

        Cater for WiiM Pro and possibly other Linkplay devices that
        emit upnp_class above the item element instead of inside it
        """
        didl_string = """
<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
    xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">
    <upnp:class>object.item.audioItem.musicTrack</upnp:class>
    <item id="0">
        <res protocolInfo="protocol_info"></res>
        <dc:title>Music Track Title</dc:title>
        <dc:creator>Music Track Creator</dc:creator>
        <upnp:artist>Artist</upnp:artist>
        <upnp:album>Album</upnp:album>
    </item>
</DIDL-Lite>"""
        items = didl_lite.from_xml_string(didl_string, strict=False)
        assert len(items) == 1

        item = items[0]
        assert isinstance(item, didl_lite.MusicTrack)
