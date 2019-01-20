# -*- coding: utf-8 -*-
"""DIDL-Lite (Digital Item Declaration Language) tools for Python."""

# Useful links:
#  http://upnp.org/specs/av/UPnP-av-ContentDirectory-v2-Service.pdf
#  http://www.upnp.org/schemas/av/didl-lite-v2.xsd
#  http://xml.coverpages.org/mpeg21-didl.html

import re

from typing import Any, Dict  # noqa: F401 pylint: disable=unused-import
from typing import cast, List, Optional, Sequence, Tuple, Type, TypeVar, Union
from xml.etree import ElementTree as ET

import defusedxml.ElementTree  # type: ignore


NAMESPACES = {
    'didl_lite': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'upnp': 'urn:schemas-upnp-org:metadata-1-0/upnp/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}


def _ns_tag(tag: str) -> str:
    """
    Expand namespace-alias to url.

    E.g.,
        _ns_tag('didl_lite:item') -> '{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'
    """
    if ':' not in tag:
        return tag

    namespace, tag = tag.split(':')
    namespace_uri = NAMESPACES[namespace]
    return '{{{0}}}{1}'.format(namespace_uri, tag)


def _namespace_tag(namespaced_tag: str) -> Tuple[Optional[str], str]:
    """
    Extract namespace and tag from namespaced-tag.

    E.g., _namespace_tag('{urn:schemas-upnp-org:metadata-1-0/upnp/}class') ->
        'urn:schemas-upnp-org:metadata-1-0/upnp/', 'class'
    """
    if '}' not in namespaced_tag:
        return None, namespaced_tag

    idx = namespaced_tag.index('}')
    namespace = namespaced_tag[1:idx]
    tag = namespaced_tag[idx + 1:]
    return namespace, tag


def _to_camel_case(name: str) -> str:
    sub1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', sub1).lower()


def _didl_property_def_key(didl_property_def: Tuple[str, ...]) -> str:
    """Get Python property key for didl_property_def."""
    if didl_property_def[1].startswith('@'):
        return _to_camel_case(didl_property_def[1].replace('@', ''))

    return _to_camel_case(didl_property_def[1].replace('@', '_'))


# region: DidlObjects


TDO = TypeVar('TDO', bound='DidlObject')


class DidlObject:
    """DIDL Ojbect."""

    tag = None  # type: Optional[str]
    upnp_class = 'object'
    didl_properties_defs = [
        ('didl_lite', '@id', 'R'),
        ('didl_lite', '@parentID', 'R'),
        ('didl_lite', '@restricted', 'R'),
        ('dc', 'title', 'R'),
        ('upnp', 'class', 'R'),
        ('dc', 'creator', 'O'),
        ('didl_lite', 'res', 'O'),
        ('upnp', 'writeStatus', 'O'),
    ]

    def __init__(self, id: str = "", parent_id: str = "",
                 descriptors: Optional[Sequence['Descriptor']] = None, **properties: Any):
        """Initializer."""
        # pylint: disable=invalid-name,redefined-builtin
        properties['id'] = id
        properties['parent_id'] = parent_id
        properties['class'] = self.upnp_class
        self._ensure_required_properties(**properties)
        self._set_properties(**properties)

        self.resources = properties.get('resources') or []
        self.descriptors = descriptors if descriptors else []

    def _ensure_required_properties(self, **properties: Any) -> None:
        """Check if all required properties are given."""
        for property_def in self.didl_properties_defs:
            key = _didl_property_def_key(property_def)
            if property_def[2] == 'R' and key not in properties:
                raise Exception(key + ' is mandatory')

    def _set_properties(self, **properties: Any) -> None:
        """Set attributes from properties."""
        # ensure we have default/known slots
        for property_def in self.didl_properties_defs:
            key = _didl_property_def_key(property_def)
            setattr(self, key, None)

        for key, value in properties.items():
            setattr(self, key, value)

    @classmethod
    def from_xml(cls: Type[TDO], xml_el: ET.Element) -> TDO:
        """
        Initialize from an XML node.

        I.e., parse XML and return instance.
        """
        # pylint: disable=too-many-locals
        properties = {}  # type: Dict[str, Any]

        # attributes
        for attr_key, attr_value in xml_el.attrib.items():
            key = _to_camel_case(attr_key)
            properties[key] = attr_value

        # child-nodes
        for xml_child_node in xml_el:
            if xml_child_node.tag == _ns_tag('didl_lite:res'):
                continue

            _, tag = _namespace_tag(xml_child_node.tag)
            key = _to_camel_case(tag)
            value = xml_child_node.text
            properties[key] = value

            # attributes of child nodes
            parent_key = key
            for attr_key, attr_value in xml_child_node.attrib.items():
                key = parent_key + '_' + _to_camel_case(attr_key)
                properties[key] = attr_value

        # resources
        resources = []
        for res_el in xml_el.findall('./didl_lite:res', NAMESPACES):
            resource = Resource.from_xml(res_el)
            resources.append(resource)
        properties['resources'] = resources

        # descriptors
        descriptors = []
        for desc_el in xml_el.findall('./didl_lite:desc', NAMESPACES):
            descriptor = Descriptor.from_xml(desc_el)
            descriptors.append(descriptor)

        return cls(descriptors=descriptors, **properties)

    def to_xml(self) -> ET.Element:
        """Convert self to XML Element."""
        assert self.tag is not None
        item_el = ET.Element(_ns_tag(self.tag))
        elements = {'': item_el}

        # properties
        for property_def in self.didl_properties_defs:
            if '@' in property_def[1]:
                continue
            key = _didl_property_def_key(property_def)

            if getattr(self, key) is None or \
               key == 'res':  # no resources, handled later on
                continue

            tag = property_def[0] + ':' + property_def[1]
            property_el = ET.Element(_ns_tag(tag), {})
            property_el.text = getattr(self, key)
            item_el.append(property_el)
            elements[property_def[1]] = property_el

        # attributes and property@attributes
        for property_def in self.didl_properties_defs:
            if '@' not in property_def[1]:
                continue

            key = _didl_property_def_key(property_def)
            value = getattr(self, key)
            if value is None:
                continue

            el_name, attr_name = property_def[1].split('@')
            property_el = elements[el_name]
            property_el.attrib[attr_name] = value

        # resource
        for resource in self.resources:
            res_el = resource.to_xml()
            item_el.append(res_el)

        # descriptor
        for descriptor in self.descriptors:
            desc_el = descriptor.to_xml()
            item_el.append(desc_el)

        return item_el


# region: items
class Item(DidlObject):
    """DIDL Item."""

    # pylint: disable=too-few-public-methods

    tag = 'item'
    upnp_class = 'object.item'
    didl_properties_defs = DidlObject.didl_properties_defs + [
        ('didl_lite', '@refID', 'O'),  # actually, R, but ignore for now
        ('upnp', 'bookmarkID', 'O'),
    ]


class ImageItem(Item):
    """DIDL Image Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.imageItem'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'longDescription', 'O'),
        ('upnp', 'storageMedium', 'O'),
        ('upnp', 'rating', 'O'),
        ('dc', 'description', 'O'),
        ('dc', 'publisher', 'O'),
        ('dc', 'date', 'O'),
        ('dc', 'rights', 'O'),
    ]


class Photo(ImageItem):
    """DIDL Photo."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.imageItem.photo'
    didl_properties_defs = ImageItem.didl_properties_defs + [
        ('upnp', 'album', 'O'),
    ]


class AudioItem(Item):
    """DIDL Audio Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.audioItem'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'genre', 'O'),
        ('dc', 'description', 'O'),
        ('upnp', 'longDescription', 'O'),
        ('dc', 'publisher', 'O'),
        ('dc', 'language', 'O'),
        ('dc', 'relation', 'O'),
        ('dc', 'rights', 'O'),
    ]


class MusicTrack(AudioItem):
    """DIDL Music Track."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.audioItem.musicTrack'
    didl_properties_defs = AudioItem.didl_properties_defs + [
        ('upnp', 'artist', 'O'),
        ('upnp', 'album', 'O'),
        ('upnp', 'originalTrackNumber', 'O'),
        ('upnp', 'playlist', 'O'),
        ('upnp', 'storageMedium', 'O'),
        ('dc', 'contributor', 'O'),
        ('dc', 'date', 'O'),
    ]


class AudioBroadcast(AudioItem):
    """DIDL Audio Broadcast."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.audioItem.audioBroadcast'
    didl_properties_defs = AudioItem.didl_properties_defs + [
        ('upnp', 'region', 'O'),
        ('upnp', 'radioCallSign', 'O'),
        ('upnp', 'radioStationID', 'O'),
        ('upnp', 'radioBand', 'O'),
        ('upnp', 'channelNr', 'O'),
        ('upnp', 'signalStrength', 'O'),
        ('upnp', 'signalLocked', 'O'),
        ('upnp', 'tuned', 'O'),
        ('upnp', 'recordable', 'O'),
    ]


class AudioBook(AudioItem):
    """DIDL Audio Book."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.audioItem.audioBook'
    didl_properties_defs = AudioItem.didl_properties_defs + [
        ('upnp', 'storageMedium', 'O'),
        ('upnp', 'producer', 'O'),
        ('dc', 'contributor', 'O'),
        ('dc', 'date', 'O'),
    ]


class VideoItem(Item):
    """DIDL Video Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.videoItem'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'genre', 'O'),
        ('upnp', 'genre@id', 'O'),
        ('upnp', 'genre@type', 'O'),
        ('upnp', 'longDescription', 'O'),
        ('upnp', 'producer', 'O'),
        ('upnp', 'rating', 'O'),
        ('upnp', 'actor', 'O'),
        ('upnp', 'director', 'O'),
        ('dc', 'description', 'O'),
        ('dc', 'publisher', 'O'),
        ('dc', 'language', 'O'),
        ('dc', 'relation', 'O'),
        ('upnp', 'playbackCount', 'O'),
        ('upnp', 'lastPlaybackTime', 'O'),
        ('upnp', 'lastPlaybackPosition', 'O'),
        ('upnp', 'recordedDayOfWeek', 'O'),
        ('upnp', 'srsRecordScheduleID', 'O'),
    ]


class Movie(VideoItem):
    """DIDL Movie."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.videoItem.movie'
    didl_properties_defs = VideoItem.didl_properties_defs + [
        ('upnp', 'storageMedium', 'O'),
        ('upnp', 'DVDRegionCode', 'O'),
        ('upnp', 'channelName', 'O'),
        ('upnp', 'scheduledStartTime', 'O'),
        ('upnp', 'scheduledEndTime', 'O'),
        ('upnp', 'programTitle', 'O'),
        ('upnp', 'seriesTitle', 'O'),
        ('upnp', 'episodeCount', 'O'),
        ('upnp', 'episodeNr', 'O'),
    ]


class VideoBroadcast(VideoItem):
    """DIDL Video Broadcast."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.videoItem.videoBroadcast'
    didl_properties_defs = VideoItem.didl_properties_defs + [
        ('upnp', 'icon', 'O'),
        ('upnp', 'region', 'O'),
        ('upnp', 'channelNr', 'O'),
        ('upnp', 'signalStrength', 'O'),
        ('upnp', 'signalLocked', 'O'),
        ('upnp', 'tuned', 'O'),
        ('upnp', 'recordable', 'O'),
        ('upnp', 'callSign', 'O'),
        ('upnp', 'price', 'O'),
        ('upnp', 'payPerView', 'O'),
    ]


class MusicVideoClip(VideoItem):
    """DIDL Music Video Clip."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.videoItem.musicVideoClip'
    didl_properties_defs = VideoItem.didl_properties_defs + [
        ('upnp', 'artist', 'O'),
        ('upnp', 'storageMedium', 'O'),
        ('upnp', 'album', 'O'),
        ('upnp', 'scheduledStartTime', 'O'),
        ('upnp', 'scheduledStopTime', 'O'),
        # ('upnp', 'director', 'O'),  # duplicate in standard
        ('dc', 'contributor', 'O'),
        ('dc', 'date', 'O'),
    ]


class PlaylistItem(Item):
    """DIDL Playlist Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.playlistItem'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'artist', 'O'),
        ('upnp', 'genre', 'O'),
        ('upnp', 'longDescription', 'O'),
        ('upnp', 'storageMedium', 'O'),
        ('dc', 'description', 'O'),
        ('dc', 'date', 'O'),
        ('dc', 'language', 'O'),
    ]


class TextItem(Item):
    """DIDL Text Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.textItem'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'author', 'O'),
        ('upnp', 'res@protection', 'O'),
        ('upnp', 'longDescription', 'O'),
        ('upnp', 'storageMedium', 'O'),
        ('upnp', 'rating', 'O'),
        ('dc', 'description', 'O'),
        ('dc', 'publisher', 'O'),
        ('dc', 'contributor', 'O'),
        ('dc', 'date', 'O'),
        ('dc', 'relation', 'O'),
        ('dc', 'language', 'O'),
        ('dc', 'rights', 'O'),
    ]


class BookmarkItem(Item):
    """DIDL Bookmark Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.bookmarkItem'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'bookmarkedObjectID', 'R'),
        ('upnp', 'neverPlayable', 'O'),
        ('upnp', 'deviceUDN', 'R'),
        ('upnp', 'serviceType', 'R'),
        ('upnp', 'serviceId', 'R'),
        ('dc', 'date', 'O'),
        ('dc', 'stateVariableCollection', 'R'),
    ]


class EpgItem(Item):
    """DIDL EPG Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.epgItem'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'channelGroupName', 'O'),
        ('upnp', 'channelGroupName@id', 'O'),
        ('upnp', 'epgProviderName', 'O'),
        ('upnp', 'serviceProvider', 'O'),
        ('upnp', 'channelName', 'O'),
        ('upnp', 'channelNr', 'O'),
        ('upnp', 'programTitle', 'O'),
        ('upnp', 'seriesTitle', 'O'),
        ('upnp', 'programID', 'O'),
        ('upnp', 'programID@type', 'O'),
        ('upnp', 'seriesID', 'O'),
        ('upnp', 'seriesID@type', 'O'),
        ('upnp', 'channelID', 'O'),
        ('upnp', 'channelID@type', 'O'),
        ('upnp', 'episodeCount', 'O'),
        ('upnp', 'episodeNumber', 'O'),
        ('upnp', 'programCode', 'O'),
        ('upnp', 'programCode_type', 'O'),
        ('upnp', 'rating', 'O'),
        ('upnp', 'rating@type', 'O'),
        ('upnp', 'episodeType', 'O'),
        ('upnp', 'genre', 'O'),
        ('upnp', 'genre@id', 'O'),
        ('upnp', 'genre@extended', 'O'),
        ('upnp', 'artist', 'O'),
        ('upnp', 'artist@role', 'O'),
        ('upnp', 'actor', 'O'),
        ('upnp', 'actor@role', 'O'),
        ('upnp', 'author', 'O'),
        ('upnp', 'author@role', 'O'),
        ('upnp', 'producer', 'O'),
        ('upnp', 'director', 'O'),
        ('dc', 'publisher', 'O'),
        ('dc', 'contributor', 'O'),
        ('upnp', 'networkAffiliation', 'O'),
        # ('upnp', 'serviceProvider', 'O'),  # duplicate in standard
        ('upnp', 'price', 'O'),
        ('upnp', 'price@currency', 'O'),
        ('upnp', 'payPerView', 'O'),
        # ('upnp', 'epgProviderName', 'O'),  # duplicate in standard
        ('dc', 'description', 'O'),
        ('upnp', 'longDescription', 'O'),
        ('upnp', 'icon', 'O'),
        ('upnp', 'region', 'O'),
        ('dc', 'language', 'O'),
        ('dc', 'relation', 'O'),
        ('upnp', 'scheduledStartTime', 'O'),
        ('upnp', 'scheduledEndTime', 'O'),
        ('upnp', 'recordable', 'O'),
    ]


class AudioProgram(EpgItem):
    """DIDL Audio Program."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.epgItem.audioProgram'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'radioCallSign', 'O'),
        ('upnp', 'radioStationID', 'O'),
        ('upnp', 'radioBand', 'O'),
    ]


class VideoProgram(EpgItem):
    """DIDL Video Program."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.epgItem.videoProgram'
    didl_properties_defs = Item.didl_properties_defs + [
        ('upnp', 'price', 'O'),
        ('upnp', 'price@currency', 'O'),
        ('upnp', 'payPerView', 'O'),
    ]
# endregion


# region: containers
TC = TypeVar('TC', bound='Container')


class Container(DidlObject, list):
    """DIDL Container."""

    # pylint: disable=too-few-public-methods

    tag = 'container'
    upnp_class = 'object.container'
    didl_properties_defs = DidlObject.didl_properties_defs + [
        ('didl_lite', '@childCount', 'O'),
        ('upnp', 'createClass', 'O'),
        ('upnp', 'searchClass', 'O'),
        ('didl_lite', '@searchable', 'O'),
        ('didl_lite', '@neverPlayable', 'O'),
    ]

    @classmethod
    def from_xml(cls: Type[TC], xml_el: ET.Element) -> TC:
        """
        Initialize from an XML node.

        I.e., parse XML and return instance.
        """
        instance = super().from_xml(xml_el)

        # add all children
        didl_objects = from_xml_el(xml_el)
        instance.extend(didl_objects)  # pylint: disable=no-member

        return instance

    def to_xml(self) -> ET.Element:
        """Convert self to XML Element."""
        container_el = super().to_xml()

        for didl_object in self:
            didl_object_el = didl_object.to_xml()
            container_el.append(didl_object_el)

        return container_el


class Person(Container):
    """DIDL Person."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.person'
    didl_properties_defs = Container.didl_properties_defs + [
        ('dc', 'language', 'O'),
    ]


class MusicArtist(Person):
    """DIDL Music Artist."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.person.musicArtist'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'genre', 'O'),
        ('upnp', 'artistDiscographyURI', 'O'),
    ]


class PlaylistContainer(Container):
    """DIDL Playlist Container."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.playlistContainer'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'artist', 'O'),
        ('upnp', 'genre', 'O'),
        ('upnp', 'longDescription', 'O'),
        ('upnp', 'producer', 'O'),
        ('upnp', 'storageMedium', 'O'),
        ('dc', 'description', 'O'),
        ('dc', 'contributor', 'O'),
        ('dc', 'date', 'O'),
        ('dc', 'language', 'O'),
        ('dc', 'rights', 'O'),
    ]


class Album(Container):
    """DIDL Album."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.album'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'storageMedium', 'O'),
        ('dc', 'longDescription', 'O'),
        ('dc', 'description', 'O'),
        ('dc', 'publisher', 'O'),
        ('dc', 'contributor', 'O'),
        ('dc', 'date', 'O'),
        ('dc', 'relation', 'O'),
        ('dc', 'rights', 'O'),
    ]


class MusicAlbum(Album):
    """DIDL Music Album."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.album.musicAlbum'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'artist', 'O'),
        ('upnp', 'genre', 'O'),
        ('upnp', 'producer', 'O'),
        ('upnp', 'albumArtURI', 'O'),
        ('upnp', 'toc', 'O'),
    ]


class PhotoAlbum(Album):
    """DIDL Photo Album."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.album.photoAlbum'
    didl_properties_defs = Container.didl_properties_defs + [
    ]


class Genre(Container):
    """DIDL Genre."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.genre'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'genre', 'O'),
        ('upnp', 'longDescription', 'O'),
        ('dc', 'description', 'O'),
    ]


class MusicGenre(Genre):
    """DIDL Music Genre."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.genre.musicGenre'
    didl_properties_defs = Container.didl_properties_defs + [
    ]


class MovieGenre(Genre):
    """DIDL Movie Genre."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.genre.movieGenre'
    didl_properties_defs = Container.didl_properties_defs + [
    ]


class ChannelGroup(Container):
    """DIDL Channel Group."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.channelGroup'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'channelGroupName', 'O'),
        ('upnp', 'channelGroupName@id', 'O'),
        ('upnp', 'epgProviderName', 'O'),
        ('upnp', 'serviceProvider', 'O'),
        ('upnp', 'icon', 'O'),
        ('upnp', 'region', 'O'),
    ]


class AudioChannelGroup(ChannelGroup):
    """DIDL Audio Channel Group."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.channelGroup.audioChannelGroup'
    didl_properties_defs = Container.didl_properties_defs + [
    ]


class VideoChannelGroup(ChannelGroup):
    """DIDL Video Channel Group."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.channelGroup.videoChannelGroup'
    didl_properties_defs = Container.didl_properties_defs + [
    ]


class EpgContainer(Container):
    """DIDL EPG Container."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.epgContainer'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'channelGroupName', 'O'),
        ('upnp', 'channelGroupName@id', 'O'),
        ('upnp', 'epgProviderName', 'O'),
        ('upnp', 'serviceProvider', 'O'),
        ('upnp', 'channelName', 'O'),
        ('upnp', 'channelNr', 'O'),
        ('upnp', 'channelID', 'O'),
        ('upnp', 'channelID@type', 'O'),
        ('upnp', 'radioCallSign', 'O'),
        ('upnp', 'radioStationID', 'O'),
        ('upnp', 'radioBand', 'O'),
        ('upnp', 'callSign', 'O'),
        ('upnp', 'networkAffiliation', 'O'),
        # ('upnp', 'serviceProvider', 'O'),  # duplicate in standard
        ('upnp', 'price', 'O'),
        ('upnp', 'price@currency', 'O'),
        ('upnp', 'payPerView', 'O'),
        # ('upnp', 'epgProviderName', 'O'),  # duplicate in standard
        ('upnp', 'icon', 'O'),
        ('upnp', 'region', 'O'),
        ('dc', 'language', 'O'),
        ('dc', 'relation', 'O'),
        ('upnp', 'dateTimeRange', 'O'),
    ]


class StorageSystem(Container):
    """DIDL Storage System."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.storageSystem'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'storageTotal', 'R'),
        ('upnp', 'storageUsed', 'R'),
        ('upnp', 'storageFree', 'R'),
        ('upnp', 'storageMaxPartition', 'R'),
        ('upnp', 'storageMedium', 'R'),
    ]


class StorageVolume(Container):
    """DIDL Storage Volume."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.storageVolume'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'storageTotal', 'R'),
        ('upnp', 'storageUsed', 'R'),
        ('upnp', 'storageFree', 'R'),
        ('upnp', 'storageMedium', 'R'),
    ]


class StorageFolder(Container):
    """DIDL Storage Folder."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.storageFolder'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'storageUsed', 'R'),
    ]


class BookmarkFolder(Container):
    """DIDL Bookmark Folder."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.bookmarkFolder'
    didl_properties_defs = Container.didl_properties_defs + [
        ('upnp', 'genre', 'O'),
        ('upnp', 'longDescription', 'O'),
        ('dc', 'description', 'O'),
    ]
# endregion


TR = TypeVar('TR', bound='Resource')


class Resource:
    """DIDL Resource."""

    # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(self, uri: Optional[str], protocol_info: str, import_uri: Optional[str] = None,
                 size: Optional[str] = None, duration: Optional[str] = None,
                 bitrate: Optional[str] = None, sample_frequency: Optional[str] = None,
                 bits_per_sample: Optional[str] = None, nr_audio_channels: Optional[str] = None,
                 resolution: Optional[str] = None, color_depth: Optional[str] = None,
                 protection: Optional[str] = None):
        """Initializer."""
        # pylint: disable=too-many-arguments
        self.uri = uri
        self.protocol_info = protocol_info
        self.import_uri = import_uri
        self.size = size
        self.duration = duration
        self.bitrate = bitrate
        self.sample_frequency = sample_frequency
        self.bits_per_sample = bits_per_sample
        self.nr_audio_channels = nr_audio_channels
        self.resolution = resolution
        self.color_depth = color_depth
        self.protection = protection

    @classmethod
    def from_xml(cls: Type[TR], xml_node: ET.Element) -> TR:
        """Initialize from an XML node."""
        uri = xml_node.text
        protocol_info = xml_node.attrib["protocolInfo"]
        import_uri = xml_node.attrib.get('importUri')
        size = xml_node.attrib.get('size')
        duration = xml_node.attrib.get('duration')
        bitrate = xml_node.attrib.get('bitrate')
        sample_frequency = xml_node.attrib.get('sampleFrequency')
        bits_per_sample = xml_node.attrib.get('bitsPerSample')
        nr_audio_channels = xml_node.attrib.get('nrAudioChannels')
        resolution = xml_node.attrib.get('resolution')
        color_depth = xml_node.attrib.get('colorDepth')
        protection = xml_node.attrib.get('protection')
        return cls(uri, protocol_info,
                   import_uri=import_uri, size=size, duration=duration,
                   bitrate=bitrate, sample_frequency=sample_frequency,
                   bits_per_sample=bits_per_sample,
                   nr_audio_channels=nr_audio_channels,
                   resolution=resolution, color_depth=color_depth,
                   protection=protection)

    def to_xml(self) -> ET.Element:
        """Convert self to XML."""
        attribs = {
            'protocolInfo': self.protocol_info,
        }
        res_el = ET.Element(_ns_tag('res'), attribs)
        res_el.text = self.uri
        return res_el


TD = TypeVar('TD', bound='Descriptor')


class Descriptor:
    """DIDL Descriptor."""

    def __init__(self, id: str, name_space: str, type: Optional[str] = None,
                 text: Optional[str] = None):
        """Initializer."""
        # pylint: disable=invalid-name,redefined-builtin
        self.id = id
        self.name_space = name_space
        self.type = type
        self.text = text

    @classmethod
    def from_xml(cls: Type[TD], xml_node: ET.Element) -> TD:
        """Initialize from an XML node."""
        id_ = xml_node.attrib['id']
        name_space = xml_node.attrib['nameSpace']
        type_ = xml_node.attrib.get('type')
        return cls(id_, name_space, type_, xml_node.text)

    def to_xml(self) -> ET.Element:
        """Convert self to XML."""
        attribs = {
            'id': self.id,
            'nameSpace': self.name_space,
        }
        if self.type is not None:
            attribs['type'] = self.type
        desc_el = ET.Element(_ns_tag('desc'), attribs)
        desc_el.text = self.text
        return desc_el
# endregion


def to_xml_string(*objects: DidlObject) -> bytes:
    """Convert items to DIDL-Lite XML string."""
    root_el = ET.Element(_ns_tag('DIDL-Lite'), {})
    root_el.attrib['xmlns'] = NAMESPACES['didl_lite']

    for didl_object in objects:
        didl_object_el = didl_object.to_xml()
        root_el.append(didl_object_el)

    return cast(bytes, ET.tostring(root_el))


def from_xml_string(xml_string: str) -> List[Union[DidlObject, Descriptor]]:
    """Convert XML string to DIDL Objects."""
    xml_el = defusedxml.ElementTree.fromstring(xml_string)
    return from_xml_el(xml_el)


def from_xml_el(xml_el: ET.Element) -> List[Union[DidlObject, Descriptor]]:
    """Convert XML Element to DIDL Objects."""
    didl_objects = []  # type: List[Union[DidlObject, Descriptor]]

    # items and containers, in order
    for child_el in xml_el:
        if child_el.tag != _ns_tag('didl_lite:item') and \
           child_el.tag != _ns_tag('didl_lite:container'):
            continue

        # construct item
        upnp_class = child_el.find('./upnp:class', NAMESPACES)
        if upnp_class is None or not upnp_class.text:
            continue
        didl_object_type = type_by_upnp_class(upnp_class.text)
        if didl_object_type is None:
            continue
        didl_object = didl_object_type.from_xml(child_el)
        didl_objects.append(didl_object)

    # descriptors
    for desc_el in xml_el.findall('./didl_lite:desc', NAMESPACES):
        desc = Descriptor.from_xml(desc_el)
        didl_objects.append(desc)

    return didl_objects


# upnp_class to python type mapping
def type_by_upnp_class(upnp_class: str) -> Optional[Type[DidlObject]]:
    """Get DidlObject-type by upnp_class."""
    queue = DidlObject.__subclasses__()
    while queue:
        type_ = queue.pop()
        queue.extend(type_.__subclasses__())

        if type_.upnp_class == upnp_class:
            return type_
    return None
