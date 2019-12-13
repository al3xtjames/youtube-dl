# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    unified_timestamp,
    unified_strdate
)


class MatterIE(InfoExtractor):
    IE_NAME = 'matter.online'
    _VALID_URL = r'(?:https?://)app\.matter\.online/tracks/(?P<track_id>\w+)'
    _API_BASE = 'https://api.matter.online/api/v1/'
    _APP_BASE = 'https://app.matter.online/'

    _NETRC_MACHINE = 'matter.online'
    _TOKEN = None

    _FORMAT_BITRATES = {
        'high': 320
    }

    _INCLUDE_TYPES = ['files', 'users', 'tags', 'tracklists_tracks', 'tracks']

    _TESTS = [{
        'url': 'https://app.matter.online/tracks/3079',
        'md5': '667d365ff42828070f6a5ba9e3dade07',
        'info_dict': {
            'id': '3079',
            'ext': 'wav',
            'title': 'dream of you',
            'description': 'ft miku',
            'uploader': 'yandere',
            'uploader_id': '1842',
            'timestamp': 1575338869,
            'upload_date': '20191203',
            'release_date': '20191202',
            'duration': 164.308,
            'view_count': int,
            'like_count': int,
            'comment_count': int
        }
    }, {
        'url': 'https://app.matter.online/tracks/4296',
        'md5': '2439f1d331b695332c7fa7798ce0fb41',
        'info_dict': {
            'id': '4296',
            'ext': 'wav',
            'title': 'intimate ft. lilac ',
            'uploader': 'acounta',
            'uploader_id': '1818',
            'timestamp': 1575406876,
            'upload_date': '20191203',
            'release_date': '20191203',
            'duration': 107.116,
            'view_count': int,
            'like_count': int,
            'comment_count': int
        }
    }]

    def _real_initialize(self):
        email, password = self._get_login_info()
        if email is None:
            self.raise_login_required()

        login_data = {
            'email': email,
            'password': password
        }

        post_url = self._API_BASE + 'authentication/login'
        response = self._download_json(post_url, None, 'Logging in', 'Login failed',
                                       data=json.dumps(login_data).encode(),
                                       headers={'Content-Type': 'application/json'})

        self._TOKEN = response.get('jwtToken')

    def _extract_info_dict(self, data, include_dict):
        artwork_id = data.get('relationships').get('artwork').get('data').get('id')
        author_id = data.get('relationships').get('author').get('data').get('id')
        file_id = data.get('relationships').get('file').get('data').get('id')

        artwork_info = include_dict.get(artwork_id)
        author_info = include_dict.get(author_id)
        file_info = include_dict.get(file_id)

        thumbnails = []
        for variant, url in artwork_info.get('attributes').get('variants').items():
            thumbnails.append({
                'id': variant,
                'url': url
            })

        thumbnails.append({
            'id': 'original',
            'url': artwork_info.get('attributes').get('file_uri'),
            'preference': 10
        })

        formats = []
        for variant, url in file_info.get('attributes').get('variants').items():
            if variant != 'preview':
                formats.append({
                    'format_id': variant,
                    'ext': 'mp3',
                    'abr': self._FORMAT_BITRATES.get(variant),
                    'url': url,
                    'vcodec': 'none'
                })

        formats.append({
            'format_id': 'original',
            'ext': file_info.get('attributes').get('metadata').get('format_name'),
            'filesize': file_info.get('attributes').get('metadata').get('size'),
            'url': file_info.get('attributes').get('file_uri'),
            'vcodec': 'none'
        })

        return {
            'id': str(data.get('id')),
            'uploader': author_info.get('attributes').get('display_name'),
            'uploader_id': str(author_id),
            'uploader_url': self._APP_BASE + 'artists/@' + author_info.get('attributes').get('login'),
            'timestamp': unified_timestamp(data.get('attributes').get('created_at')),
            'release_date': unified_strdate(data.get('attributes').get('release_date')),
            'title': data.get('attributes').get('title'),
            'description': data.get('attributes').get('description'),
            'thumbnails': thumbnails,
            'duration': file_info.get('attributes').get('metadata').get('duration'),
            'view_count': data.get('attributes').get('streams_count'),
            'like_count': data.get('attributes').get('likes_count'),
            'comment_count': data.get('attributes').get('comments_count'),
            'formats': formats
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        track_id = mobj.group('track_id')

        info_json_url = self._API_BASE + 'tracks/' + track_id
        headers = {
            'authorization': 'Bearer %s' % self._TOKEN
        }

        info = self._download_json(info_json_url, track_id, 'Downloading info JSON',
                                   headers=headers)

        include_dict = {}
        if info.get('included') is not None:
            for include in info.get('included'):
                include_dict[include.get('id')] = include

        return self._extract_info_dict(info.get('data'), include_dict)


class MatterPlaylistIE(MatterIE):
    IE_NAME = 'matter.online:playlist'
    _VALID_URL = r'(?:https?://)app\.matter\.online/(albums|playlists)/(?P<playlist_id>\w+)'

    _TESTS = [{
        'url': 'https://app.matter.online/albums/296',
        'info_dict': {
            'id': '296',
            'uploader': 'acounta',
            'uploader_id': '1818',
            'title': 'A​.​777 [TOKYOGHOST X ACOUNTA]',
        },
        'playlist_count': 5,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('playlist_id')

        info_json_url = self._API_BASE + mobj.group(1) + '/' + playlist_id
        headers = {
            'authorization': 'Bearer %s' % self._TOKEN
        }

        info = self._download_json(info_json_url, playlist_id, 'Downloading info JSON',
                                   headers=headers)
        author_id = info.get('data').get('relationships').get('author').get('data').get('id')

        include_dict = {}
        if info.get('included') is not None:
            for include in info.get('included'):
                if include.get('type') in self._INCLUDE_TYPES:
                    include_dict[include.get('id')] = include

        tracks = [None] * info.get('data').get('attributes').get('tracks_count')
        for tracklist in info.get('data').get('relationships').get('tracklists_tracks').get('data'):
            tracklist_info = include_dict.get(tracklist.get('id'))
            track_pos = tracklist_info.get('attributes').get('position')
            track_info = include_dict.get(tracklist_info.get('relationships').get('track').get('data').get('id'))
            tracks[track_pos] = self._extract_info_dict(track_info, include_dict)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'uploader': include_dict.get(author_id).get('attributes').get('display_name'),
            'uploader_id': str(author_id),
            'title': info.get('data').get('attributes').get('title'),
            'entries': tracks
        }


class MatterUserBaseIE(MatterIE):
    def _extract_playlist(self, info, resource):
        include_dict = {}
        if info.get('included') is not None:
            for include in info.get('included'):
                if include.get('type') in self._INCLUDE_TYPES:
                    include_dict[include.get('id')] = include

        entries = []
        for entry in info.get('data'):
            if resource == 'tracks':
                entries.append(self._extract_info_dict(entry, include_dict))
            else:
                entries.append({
                    '_type': 'url',
                    'id': entry.get('id'),
                    'title': entry.get('attributes').get('title'),
                    'ie_key': MatterPlaylistIE.ie_key(),
                    'url': self._APP_BASE + entry.get('type') + '/' + str(entry.get('id'))
                })

        return entries


class MatterArtistIE(MatterUserBaseIE):
    IE_NAME = 'matter.online:artist'
    _VALID_URL = r'(?:https?://)app\.matter\.online/artists/@(?P<artist_username>\w+)(?:/(?P<resource>albums|playlists|tracks))?'

    _TESTS = [{
        'url': 'https://app.matter.online/artists/@harmful_logic',
        'info_dict': {
            'id': '2270',
            'uploader': 'Harmful Logic',
            'uploader_id': '2270',
            'title': 'Harmful Logic - Tracks'
        },
        'playlist_mincount': 4,
    }, {
        'url': 'https://app.matter.online/artists/@acounta/albums',
        'info_dict': {
            'id': '1818',
            'uploader': 'acounta',
            'uploader_id': '1818',
            'title': 'acounta - Albums'
        },
        'playlist_mincount': 7,
    }, {
        'url': 'https://app.matter.online/artists/@melanite/tracks',
        'info_dict': {
            'id': '2641',
            'uploader': 'melanite',
            'uploader_id': '2641',
            'title': 'melanite - Tracks'
        },
        'playlist_mincount': 3,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        artist_username = mobj.group('artist_username')
        resource = mobj.group('resource') or 'tracks'

        info_json_url = self._API_BASE + 'users/@' + artist_username
        headers = {
            'authorization': 'Bearer %s' % self._TOKEN
        }

        info = self._download_json(info_json_url, artist_username, 'Downloading info JSON',
                                   headers=headers)
        artist_id = info.get('data').get('id')
        artist_name = info.get('data').get('attributes').get('display_name')

        info_json_url = self._API_BASE + 'users/' + str(artist_id) + '/' + resource + '?sort=release_date&dir=desc&limit=9999'
        info = self._download_json(info_json_url, artist_id, 'Downloading info JSON',
                                   headers=headers)
        entries = self._extract_playlist(info, resource)

        return {
            '_type': 'playlist',
            'id': str(artist_id),
            'uploader': artist_name,
            'uploader_id': str(artist_id),
            'title': artist_name + ' - ' + resource.capitalize(),
            'entries': entries
        }


class MatterLibraryIE(MatterUserBaseIE):
    IE_NAME = 'matter.online:library'
    _VALID_URL = r'(?:https?://)app\.matter\.online/library(?:/(?P<resource>albums|playlists|tracks|))?'

    _TESTS = []

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        resource = mobj.group('resource') or 'tracks'

        info_json_url = self._API_BASE + 'library/' + resource
        headers = {
            'authorization': 'Bearer %s' % self._TOKEN
        }

        info = self._download_json(info_json_url, 'library', 'Downloading info JSON',
                                   headers=headers)
        entries = self._extract_playlist(info, resource)

        return {
            '_type': 'playlist',
            'title': 'Library - ' + resource.capitalize(),
            'entries': entries
        }
