# -*- coding: utf-8 -*-
"""DIDL-Lite (Digital Item Declaration Language) tools for Python."""

# Useful links:
#  http://upnp.org/specs/av/UPnP-av-ContentDirectory-v2-Service.pdf
#  http://www.upnp.org/schemas/av/didl-lite-v2.xsd
#  http://xml.coverpages.org/mpeg21-didl.html

from xml.etree import ElementTree as ET


NAMESPACES = {
    'didl_lite': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'upnp': 'urn:schemas-upnp-org:metadata-1-0/upnp/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}


def _ns_tag(tag: str) -> str:
    """Expand namespace-alias to url."""
    if ':' not in tag:
        return tag

    namespace, tag = tag.split(':')
    namespace_uri = NAMESPACES[namespace]
    return '{{{0}}}{1}'.format(namespace_uri, tag)


# region: DidlObjects
class DidlObject:
    """DIDL Ojbect."""

    tag = None
    upnp_class = 'object'
    didl_properties = {
        'id': ('didl_lite', '@id', 'R'),
        'parent_id': ('didl_lite', '@parentID', 'R'),
        'restricted': ('didl_lite', '@restricted', 'R'),
        'title': ('dc', 'title', 'R'),
        'class': ('upnp', 'class', 'R'),
        'creator': ('dc', 'creator', 'O'),
        'resources': ('didl_lite', 'res', 'O'),
        'write_status': ('upnp', 'writeStatus', 'O'),
    }

    def __init__(self, id="", parent_id="", descriptors=None, **properties):
        """Initializer."""
        # pylint: disable=invalid-name,redefined-builtin
        properties['id'] = id
        properties['parent_id'] = parent_id
        properties['class'] = self.upnp_class
        self._ensure_required_properties(**properties)
        self._ensure_known_properties(**properties)
        self._set_properties(**properties)

        self.descriptors = descriptors if descriptors else []

    def _ensure_required_properties(self, **properties):
        """Check if all required properties are given."""
        for key, value in self.didl_properties.items():
            if value[2] == 'R' and key not in properties:
                raise Exception(key + ' is mandatory')

    def _ensure_known_properties(self, **properties):
        """Check if all given properties are known."""
        for key in properties:
            if key not in self.didl_properties:
                raise Exception(key + ' is not a known property')

    def _set_properties(self, **properties):
        """Set attributes from properties."""
        for key, value in properties.items():
            setattr(self, key, value)

    @classmethod
    def from_xml(cls, xml_node: ET.Element):
        """
        Initialize from an XML node.

        I.e., parse XML and return instance.
        """
        # pylint: disable=too-many-locals
        properties = {}

        # properties
        for key, value in cls.didl_properties.items():
            if '@' in value[1] or key == 'resources':
                continue

            query = './' + value[0] + ':' + value[1]
            property_el = xml_node.find(query, NAMESPACES)
            if property_el is not None:
                properties[key] = property_el.text

        # property@attributes
        for key, value in cls.didl_properties.items():
            if '@' not in value[1]:
                continue

            el_name, attr_name = value[1].split('@')
            if el_name:
                query = './' + value[0] + ':' + el_name
                property_el = xml_node.find(query, NAMESPACES)
            else:
                property_el = xml_node
            if property_el is None:
                continue

            if attr_name in property_el.attrib:
                attr_value = property_el.attrib[attr_name]
                properties[key] = attr_value

        # resources
        resources = []
        for res_el in xml_node.findall('./didl_lite:res', NAMESPACES):
            resource = Resource.from_xml(res_el)
            resources.append(resource)
        if resources:
            properties['resources'] = resources

        # descriptors
        descriptors = []
        for desc_el in xml_node.findall('./didl_lite:desc', NAMESPACES):
            descriptor = Descriptor.from_xml(desc_el)
            descriptors.append(descriptor)

        return cls(descriptors=descriptors, **properties)

    def to_xml(self) -> str:
        """Convert self to XML Element."""
        item_el = ET.Element(_ns_tag(self.tag))
        elements = {'': item_el}

        # properties
        for key, value in self.didl_properties.items():
            if '@' in value[1] or not hasattr(self, key) or key == 'resources':
                continue

            tag = value[0] + ':' + value[1]
            property_el = ET.Element(_ns_tag(tag), {})
            property_el.text = getattr(self, key)
            item_el.append(property_el)
            elements[value[1]] = property_el

        # attributes and property@attributes
        for key, value in self.didl_properties.items():
            if '@' not in value[1] or not hasattr(self, key):
                continue

            el_name, attr_name = value[1].split('@')
            property_el = elements[el_name]
            property_el.attrib[attr_name] = getattr(self, key)

        # resource
        for resource in getattr(self, 'resources', []):  # pylint: disable=no-member
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
    didl_properties = dict(**DidlObject.didl_properties, **{
        'ref_id': ('didl_lite', '@refID', 'O'),  # actually, R, but ignore for now
        'bookmark_id': ('upnp', 'bookmarkID', 'O'),
    })


class ImageItem(Item):
    """DIDL Image Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.imageItem'
    didl_properties = dict(**Item.didl_properties, **{
        'long_description': ('upnp', 'longDescription', 'O'),
        'storage_medium': ('upnp', 'storageMedium', 'O'),
        'rating': ('upnp', 'rating', 'O'),
        'description': ('dc', 'description', 'O'),
        'publisher': ('dc', 'publisher', 'O'),
        'date': ('dc', 'date', 'O'),
        'rights': ('dc', 'rights', 'O'),
    })


class Photo(ImageItem):
    """DIDL Photo."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.imageItem.photo'
    didl_properties = dict(**ImageItem.didl_properties, **{
        'album': ('upnp', 'album', 'O'),
    })


class AudioItem(Item):
    """DIDL Audio Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.audioItem'
    didl_properties = dict(**Item.didl_properties, **{
        'genre': ('upnp', 'genre', 'O'),
        'description': ('dc', 'description', 'O'),
        'long_description': ('upnp', 'longDescription', 'O'),
        'publisher': ('dc', 'publisher', 'O'),
        'language': ('dc', 'language', 'O'),
        'relation': ('dc', 'relation', 'O'),
        'rights': ('dc', 'rights', 'O'),
    })


class MusicTrack(AudioItem):
    """DIDL Music Track."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.audioItem.musicTrack'
    didl_properties = dict(**AudioItem.didl_properties, **{
        'artist': ('upnp', 'artist', 'O'),
        'album': ('upnp', 'album', 'O'),
        'original_track_number': ('upnp', 'originalTrackNumber', 'O'),
        'playlist': ('upnp', 'playlist', 'O'),
        'storage_medium': ('upnp', 'storageMedium', 'O'),
        'contributor': ('dc', 'contributor', 'O'),
        'date': ('dc', 'date', 'O'),
    })


class AudioBroadcast(AudioItem):
    """DIDL Audio Broadcast."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.audioItem.audioBroadcast'
    didl_properties = dict(**AudioItem.didl_properties, **{
        'region': ('upnp', 'region', 'O'),
        'radio_call_sign': ('upnp', 'radioCallSign', 'O'),
        'radio_station_id': ('upnp', 'radioStationID', 'O'),
        'radio_band': ('upnp', 'radioBand', 'O'),
        'channel_nr': ('upnp', 'channelNr', 'O'),
        'signal_strength': ('upnp', 'signalStrength', 'O'),
        'signal_locked': ('upnp', 'signalLocked', 'O'),
        'tuned': ('upnp', 'tuned', 'O'),
        'recordable': ('upnp', 'recordable', 'O'),
    })


class AudioBook(AudioItem):
    """DIDL Audio Book."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.audioItem.audioBook'
    didl_properties = dict(**AudioItem.didl_properties, **{
        'storage_medium': ('upnp', 'storageMedium', 'O'),
        'producer': ('upnp', 'producer', 'O'),
        'contributor': ('dc', 'contributor', 'O'),
        'date': ('dc', 'date', 'O'),
    })


class VideoItem(Item):
    """DIDL Video Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.videoItem'
    didl_properties = dict(**Item.didl_properties, **{
        'genre': ('upnp', 'genre', 'O'),
        'genre_id': ('upnp', 'genre@id', 'O'),
        'genre_type': ('upnp', 'genre@type', 'O'),
        'long_description': ('upnp', 'longDescription', 'O'),
        'producer': ('upnp', 'producer', 'O'),
        'rating': ('upnp', 'rating', 'O'),
        'actor': ('upnp', 'actor', 'O'),
        'director': ('upnp', 'director', 'O'),
        'description': ('dc', 'description', 'O'),
        'publisher': ('dc', 'publisher', 'O'),
        'language': ('dc', 'language', 'O'),
        'relation': ('dc', 'relation', 'O'),
        'playback_count': ('upnp', 'playbackCount', 'O'),
        'last_playback_time': ('upnp', 'lastPlaybackTime', 'O'),
        'last_playback_position': ('upnp', 'lastPlaybackPosition', 'O'),
        'recorded_day_of_week': ('upnp', 'recordedDayOfWeek', 'O'),
        'srsRecordScheduleID': ('upnp', 'srsRecordScheduleID', 'O'),
    })


class Movie(VideoItem):
    """DIDL Movie."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.videoItem.movie'
    didl_properties = dict(**VideoItem.didl_properties, **{
        'storage_medium': ('upnp', 'storageMedium', 'O'),
        'dvd_region_code': ('upnp', 'DVDRegionCode', 'O'),
        'channel_name': ('upnp', 'channelName', 'O'),
        'scheduled_start_time': ('upnp', 'scheduledStartTime', 'O'),
        'scheduled_end_time': ('upnp', 'scheduledEndTime', 'O'),
        'program_title': ('upnp', 'programTitle', 'O'),
        'series_title': ('upnp', 'seriesTitle', 'O'),
        'episode_count': ('upnp', 'episodeCount', 'O'),
        'episode_nr': ('upnp', 'episodeNr', 'O'),
    })


class VideoBroadcast(VideoItem):
    """DIDL Video Broadcast."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.videoItem.videoBroadcast'
    didl_properties = dict(**VideoItem.didl_properties, **{
        'icon': ('upnp', 'icon', 'O'),
        'region': ('upnp', 'region', 'O'),
        'channel_nr': ('upnp', 'channelNr', 'O'),
        'signal_strength': ('upnp', 'signalStrength', 'O'),
        'signal_locked': ('upnp', 'signalLocked', 'O'),
        'tuned': ('upnp', 'tuned', 'O'),
        'recordable': ('upnp', 'recordable', 'O'),
        'call_sign': ('upnp', 'callSign', 'O'),
        'price': ('upnp', 'price', 'O'),
        'pay_per_view': ('upnp', 'payPerView', 'O'),
    })


class MusicVideoClip(VideoItem):
    """DIDL Music Video Clip."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.videoItem.musicVideoClip'
    didl_properties = dict(**VideoItem.didl_properties, **{
        'artist': ('upnp', 'artist', 'O'),
        'storage_medium': ('upnp', 'storageMedium', 'O'),
        'album': ('upnp', 'album', 'O'),
        'scheduled_start_time': ('upnp', 'scheduledStartTime', 'O'),
        'scheduled_stop_time': ('upnp', 'scheduledStopTime', 'O'),
        # 'director': ('upnp', 'director', 'O'),  # duplicate in standard
        'contributor': ('dc', 'contributor', 'O'),
        'date': ('dc', 'date', 'O'),
    })


class PlaylistItem(Item):
    """DIDL Playlist Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.playlistItem'
    didl_properties = dict(**Item.didl_properties, **{
        'artist': ('upnp', 'artist', 'O'),
        'genre': ('upnp', 'genre', 'O'),
        'long_description': ('upnp', 'longDescription', 'O'),
        'storage_medium': ('upnp', 'storageMedium', 'O'),
        'description': ('dc', 'description', 'O'),
        'date': ('dc', 'date', 'O'),
        'language': ('dc', 'language', 'O'),
    })


class TextItem(Item):
    """DIDL Text Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.textItem'
    didl_properties = dict(**Item.didl_properties, **{
        'author': ('upnp', 'author', 'O'),
        'res_protection': ('upnp', 'res@protection', 'O'),
        'long_description': ('upnp', 'longDescription', 'O'),
        'storage_medium': ('upnp', 'storageMedium', 'O'),
        'rating': ('upnp', 'rating', 'O'),
        'description': ('dc', 'description', 'O'),
        'publisher': ('dc', 'publisher', 'O'),
        'contributor': ('dc', 'contributor', 'O'),
        'date': ('dc', 'date', 'O'),
        'relation': ('dc', 'relation', 'O'),
        'language': ('dc', 'language', 'O'),
        'rights': ('dc', 'rights', 'O'),
    })


class BookmarkItem(Item):
    """DIDL Bookmark Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.bookmarkItem'
    didl_properties = dict(**Item.didl_properties, **{
        'bookmarkedObjectID': ('upnp', 'bookmarkedObjectID', 'R'),
        'neverPlayable': ('upnp', 'neverPlayable', 'O'),
        'deviceUDN': ('upnp', 'deviceUDN', 'R'),
        'serviceType': ('upnp', 'serviceType', 'R'),
        'serviceId': ('upnp', 'serviceId', 'R'),
        'date': ('dc', 'date', 'O'),
        'stateVariableCollection': ('dc', 'stateVariableCollection', 'R'),
    })


class EpgItem(Item):
    """DIDL EPG Item."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.epgItem'
    didl_properties = dict(**Item.didl_properties, **{
        'channel_group_name': ('upnp', 'channelGroupName', 'O'),
        'channel_group_name_id': ('upnp', 'channelGroupName@id', 'O'),
        'epg_provider_name': ('upnp', 'epgProviderName', 'O'),
        'service_provider': ('upnp', 'serviceProvider', 'O'),
        'channel_name': ('upnp', 'channelName', 'O'),
        'channel_nr': ('upnp', 'channelNr', 'O'),
        'program_title': ('upnp', 'programTitle', 'O'),
        'series_title': ('upnp', 'seriesTitle', 'O'),
        'program_id': ('upnp', 'programID', 'O'),
        'program_id_type': ('upnp', 'programID@type', 'O'),
        'series_id': ('upnp', 'seriesID', 'O'),
        'series_id_type': ('upnp', 'seriesID@type', 'O'),
        'channel_id': ('upnp', 'channelID', 'O'),
        'channel_id_type': ('upnp', 'channelID@type', 'O'),
        'episode_count': ('upnp', 'episodeCount', 'O'),
        'episode_number': ('upnp', 'episodeNumber', 'O'),
        'program_code': ('upnp', 'programCode', 'O'),
        'program_code_type': ('upnp', 'programCode_type', 'O'),
        'rating': ('upnp', 'rating', 'O'),
        'rating_type': ('upnp', 'rating@type', 'O'),
        'episode_type': ('upnp', 'episodeType', 'O'),
        'genre': ('upnp', 'genre', 'O'),
        'genre_id': ('upnp', 'genre@id', 'O'),
        'genre_extended': ('upnp', 'genre@extended', 'O'),
        'artist': ('upnp', 'artist', 'O'),
        'artist_role': ('upnp', 'artist@role', 'O'),
        'actor': ('upnp', 'actor', 'O'),
        'actor_role': ('upnp', 'actor@role', 'O'),
        'author': ('upnp', 'author', 'O'),
        'author_role': ('upnp', 'author@role', 'O'),
        'producer': ('upnp', 'producer', 'O'),
        'director': ('upnp', 'director', 'O'),
        'publisher': ('dc', 'publisher', 'O'),
        'contributor': ('dc', 'contributor', 'O'),
        'network_affiliation': ('upnp', 'networkAffiliation', 'O'),
        # 'service_provider': ('upnp', 'serviceProvider', 'O'),  # duplicate in standard
        'price': ('upnp', 'price', 'O'),
        'price_currency': ('upnp', 'price@currency', 'O'),
        'pay_per_view': ('upnp', 'payPerView', 'O'),
        # 'epg_provider_name': ('upnp', 'epgProviderName', 'O'),  # duplicate in standard
        'description': ('dc', 'description', 'O'),
        'long_description': ('upnp', 'longDescription', 'O'),
        'icon': ('upnp', 'icon', 'O'),
        'region': ('upnp', 'region', 'O'),
        'language': ('dc', 'language', 'O'),
        'relation': ('dc', 'relation', 'O'),
        'scheduled_start_time': ('upnp', 'scheduledStartTime', 'O'),
        'scheduled_end_time': ('upnp', 'scheduledEndTime', 'O'),
        'recordable': ('upnp', 'recordable', 'O'),
    })


class AudioProgram(EpgItem):
    """DIDL Audio Program."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.epgItem.audioProgram'
    didl_properties = dict(**Item.didl_properties, **{
        'radio_call_sign': ('upnp', 'radioCallSign', 'O'),
        'radio_station_id': ('upnp', 'radioStationID', 'O'),
        'radio_band': ('upnp', 'radioBand', 'O'),
    })


class VideoProgram(EpgItem):
    """DIDL Video Program."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.item.epgItem.videoProgram'
    didl_properties = dict(**Item.didl_properties, **{
        'price': ('upnp', 'price', 'O'),
        'price_currency': ('upnp', 'price@currency', 'O'),
        'payPerView': ('upnp', 'payPerView', 'O'),
    })
# endregion


# region: containers
class Container(DidlObject, list):
    """DIDL Container."""

    # pylint: disable=too-few-public-methods

    tag = 'container'
    upnp_class = 'object.container'
    didl_properties = dict(**DidlObject.didl_properties, **{
        'child_count': ('didl_lite', '@childCount', 'O'),
        'create_class': ('upnp', 'createClass', 'O'),
        'search_class': ('upnp', 'searchClass', 'O'),
        'searchable': ('didl_lite', '@searchable', 'O'),
        'never_playable': ('didl_lite', '@neverPlayable', 'O'),
    })

    @classmethod
    def from_xml(cls, xml_node: ET.Element):
        """
        Initialize from an XML node.

        I.e., parse XML and return instance.
        """
        instance = super().from_xml(xml_node)

        # add all children
        didl_objects = from_xml_el(xml_node)
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
    didl_properties = dict(**Container.didl_properties, **{
        'language': ('dc', 'language', 'O'),
    })


class MusicArtist(Person):
    """DIDL Music Artist."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.person.musicArtist'
    didl_properties = dict(**Container.didl_properties, **{
        'genre': ('upnp', 'genre', 'O'),
        'artist_discography_uri': ('upnp', 'artistDiscographyURI', 'O'),
    })


class PlaylistContainer(Container):
    """DIDL Playlist Container."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.playlistContainer'
    didl_properties = dict(**Container.didl_properties, **{
        'artist': ('upnp', 'artist', 'O'),
        'genre': ('upnp', 'genre', 'O'),
        'longDescription': ('upnp', 'longDescription', 'O'),
        'producer': ('upnp', 'producer', 'O'),
        'storageMedium': ('upnp', 'storageMedium', 'O'),
        'description': ('dc', 'description', 'O'),
        'contributor': ('dc', 'contributor', 'O'),
        'date': ('dc', 'date', 'O'),
        'language': ('dc', 'language', 'O'),
        'rights': ('dc', 'rights', 'O'),
    })


class Album(Container):
    """DIDL Album."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.album'
    didl_properties = dict(**Container.didl_properties, **{
        'storageMedium': ('upnp', 'storageMedium', 'O'),
        'longDescription': ('dc', 'longDescription', 'O'),
        'description': ('dc', 'description', 'O'),
        'publisher': ('dc', 'publisher', 'O'),
        'contributor': ('dc', 'contributor', 'O'),
        'date': ('dc', 'date', 'O'),
        'relation': ('dc', 'relation', 'O'),
        'rights': ('dc', 'rights', 'O'),
    })


class MusicAlbum(Album):
    """DIDL Music Album."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.album.musicAlbum'
    didl_properties = dict(**Container.didl_properties, **{
        'artist': ('upnp', 'artist', 'O'),
        'genre': ('upnp', 'genre', 'O'),
        'producer': ('upnp', 'producer', 'O'),
        'album_art_uri': ('upnp', 'albumArtURI', 'O'),
        'toc': ('upnp', 'toc', 'O'),
    })


class PhotoAlbum(Album):
    """DIDL Photo Album."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.album.photoAlbum'
    didl_properties = dict(**Container.didl_properties, **{
    })


class Genre(Container):
    """DIDL Genre."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.genre'
    didl_properties = dict(**Container.didl_properties, **{
        'genre': ('upnp', 'genre', 'O'),
        'long_description': ('upnp', 'longDescription', 'O'),
        'description': ('dc', 'description', 'O'),
    })


class MusicGenre(Genre):
    """DIDL Music Genre."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.genre.musicGenre'
    didl_properties = dict(**Container.didl_properties, **{
    })


class MovieGenre(Genre):
    """DIDL Movie Genre."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.genre.movieGenre'
    didl_properties = dict(**Container.didl_properties, **{
    })


class ChannelGroup(Container):
    """DIDL Channel Group."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.channelGroup'
    didl_properties = dict(**Container.didl_properties, **{
        'channelGroupName': ('upnp', 'channelGroupName', 'O'),
        'channelGroupName_id': ('upnp', 'channelGroupName@id', 'O'),
        'epgProviderName': ('upnp', 'epgProviderName', 'O'),
        'serviceProvider': ('upnp', 'serviceProvider', 'O'),
        'icon': ('upnp', 'icon', 'O'),
        'region': ('upnp', 'region', 'O'),
    })


class AudioChannelGroup(ChannelGroup):
    """DIDL Audio Channel Group."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.channelGroup.audioChannelGroup'
    didl_properties = dict(**Container.didl_properties, **{
    })


class VideoChannelGroup(ChannelGroup):
    """DIDL Video Channel Group."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.channelGroup.videoChannelGroup'
    didl_properties = dict(**Container.didl_properties, **{
    })


class EpgContainer(Container):
    """DIDL EPG Container."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.epgContainer'
    didl_properties = dict(**Container.didl_properties, **{
        'channel_group_name': ('upnp', 'channelGroupName', 'O'),
        'channel_group_name_id': ('upnp', 'channelGroupName@id', 'O'),
        'epg_provider_name': ('upnp', 'epgProviderName', 'O'),
        'service_provider': ('upnp', 'serviceProvider', 'O'),
        'channel_name': ('upnp', 'channelName', 'O'),
        'channel_nr': ('upnp', 'channelNr', 'O'),
        'channel_id': ('upnp', 'channelID', 'O'),
        'channel_id_type': ('upnp', 'channelID@type', 'O'),
        'radio_call_sign': ('upnp', 'radioCallSign', 'O'),
        'radio_station_id': ('upnp', 'radioStationID', 'O'),
        'radio_band': ('upnp', 'radioBand', 'O'),
        'call_sign': ('upnp', 'callSign', 'O'),
        'network_affiliation': ('upnp', 'networkAffiliation', 'O'),
        # 'service_provider': ('upnp', 'serviceProvider', 'O'),  # duplicate in standard
        'price': ('upnp', 'price', 'O'),
        'price_currency': ('upnp', 'price@currency', 'O'),
        'pay_per_view': ('upnp', 'payPerView', 'O'),
        # 'epg_provider_name': ('upnp', 'epgProviderName', 'O'),  # duplicate in standard
        'icon': ('upnp', 'icon', 'O'),
        'region': ('upnp', 'region', 'O'),
        'language': ('dc', 'language', 'O'),
        'relation': ('dc', 'relation', 'O'),
        'date_time_range': ('upnp', 'dateTimeRange', 'O'),
    })


class StorageSystem(Container):
    """DIDL Storage System."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.storageSystem'
    didl_properties = dict(**Container.didl_properties, **{
        'storage_total': ('upnp', 'storageTotal', 'R'),
        'storage_used': ('upnp', 'storageUsed', 'R'),
        'storage_free': ('upnp', 'storageFree', 'R'),
        'storage_max_partition': ('upnp', 'storageMaxPartition', 'R'),
        'storage_medium': ('upnp', 'storageMedium', 'R'),
    })


class StorageVolume(Container):
    """DIDL Storage Volume."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.storageVolume'
    didl_properties = dict(**Container.didl_properties, **{
        'storage_total': ('upnp', 'storageTotal', 'R'),
        'storage_used': ('upnp', 'storageUsed', 'R'),
        'storage_free': ('upnp', 'storageFree', 'R'),
        'storage_medium': ('upnp', 'storageMedium', 'R'),
    })


class StorageFolder(Container):
    """DIDL Storage Folder."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.storageFolder'
    didl_properties = dict(**Container.didl_properties, **{
        'storage_used': ('upnp', 'storageUsed', 'R'),
    })


class BookmarkFolder(Container):
    """DIDL Bookmark Folder."""

    # pylint: disable=too-few-public-methods

    upnp_class = 'object.container.bookmarkFolder'
    didl_properties = dict(**Container.didl_properties, **{
        'genre': ('upnp', 'genre', 'O'),
        'long_description': ('upnp', 'longDescription', 'O'),
        'description': ('dc', 'description', 'O'),
    })
# endregion


class Resource:
    """DIDL Resource."""

    # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(self, uri, protocol_info, import_uri=None, size=None, duration=None,
                 bitrate=None, sample_frequency=None, bits_per_sample=None,
                 nr_audio_channels=None, resolution=None, color_depth=None, protection=None):
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
    def from_xml(cls, xml_node: ET.Element):
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

    def to_xml(self) -> str:
        """Convert self to XML."""
        attribs = {
            'protocolInfo': self.protocol_info,
        }
        res_el = ET.Element(_ns_tag('res'), attribs)
        res_el.text = self.uri
        return res_el


class Descriptor:
    """DIDL Descriptor."""

    def __init__(self, id, name_space, type=None, text=None):
        """Initializer."""
        # pylint: disable=invalid-name,redefined-builtin
        self.id = id
        self.name_space = name_space
        self.type = type
        self.text = text

    @classmethod
    def from_xml(cls, xml_node: ET.Element):
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
            'type': self.type,
        }
        desc_el = ET.Element(_ns_tag('desc'), attribs)
        desc_el.text = self.text
        return desc_el
# endregion


def to_xml_string(*objects) -> str:
    """Convert items to DIDL-Lite XML string."""
    root_el = ET.Element(_ns_tag('DIDL-Lite'), {})
    root_el.attrib['xmlns'] = NAMESPACES['didl_lite']

    for didl_object in objects:
        didl_object_el = didl_object.to_xml()
        root_el.append(didl_object_el)

    return ET.tostring(root_el)


def from_xml_string(xml_string) -> DidlObject:
    """Convert XML string to DIDL Objects."""
    xml_el = ET.fromstring(xml_string)
    return from_xml_el(xml_el)


def from_xml_el(xml_el: ET.Element) -> DidlObject:
    """Convert XML Element to DIDL Objects."""
    didl_objects = []

    # items and containers, in order
    for child_el in xml_el:
        if child_el.tag != _ns_tag('didl_lite:item') and \
           child_el.tag != _ns_tag('didl_lite:container'):
            continue

        # construct item
        upnp_class = child_el.find('./upnp:class', NAMESPACES).text
        didl_object_type = type_by_upnp_class(upnp_class)
        didl_object = didl_object_type.from_xml(child_el)
        didl_objects.append(didl_object)

    # descriptors
    for desc_el in xml_el.findall('./didl_lite:desc', NAMESPACES):
        desc = Descriptor.from_xml(desc_el)
        didl_objects.append(desc)

    return didl_objects


# upnp_class to python type mapping
def type_by_upnp_class(upnp_class: str) -> DidlObject:
    """Get DidlObject-type by upnp_class."""
    queue = DidlObject.__subclasses__()
    while queue:
        type_ = queue.pop()
        queue.extend(type_.__subclasses__())

        if type_.upnp_class == upnp_class:
            return type_
