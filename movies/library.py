import logging
import os
import re

import jinja2
import requests
from django.db import transaction
from plexapi import utils
from plexapi.server import PlexServer
from pytz import utc

from movies import settings
from movies.models import SynoSession, LibrarySection, Movie, Media, MediaPart

logger = logging.getLogger(__name__)


def parse_quality(title):
    for pattern, source in settings.QUALITY_MAP.items():
        item_regex = re.compile(r'[\W_]{0}'.format(pattern), flags=re.IGNORECASE)
        match = item_regex.search(title)
        if match:
            return source

    return ''


def raise_syno_error(response):
    response.raise_for_status()

    content = response.json()
    if not content.get('success'):
        error = content.get('error')
        raise Exception('SYNO.ErrorCode: {0}'.format(error.get('code')))

    return content


def get_syno_data(response):
    content = raise_syno_error(response)
    return content.get('data')


def get_syno_sid(session):
    credentials = SynoSession.objects.filter(account=settings.SYNO_ACCOUNT).first()
    if credentials:
        return credentials.sid

    response = session.get(
        settings.SYNO_URL + 'auth.cgi',
        params={
            'api': 'SYNO.API.Auth',
            'version': 6,
            'method': 'login',
            'account': 'butik',
            'passwd': 'v0hr0drf',
            'session': 'FileStation',
            'format': 'sid',
        })

    data = get_syno_data(response)

    credentials = SynoSession(account=settings.SYNO_ACCOUNT, sid=data['sid'])
    credentials.save()

    return credentials.sid


def sync_library(force=False):
    plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)
    plex_section = plex.library.section(settings.PLEX_SECTION)
    if plex_section.refreshing:
        logger.info('"{0}" library is being refreshed now'.format(plex_section.title))
        return

    changed_at = int(plex_section._data.attrib.get('contentChangedAt'))
    # scanned_at = utils.toDatetime(plex_section._data.attrib.get('scannedAt'))

    section = LibrarySection.objects.filter(uuid=plex_section.uuid).first()
    if not force and section and changed_at <= section.changed_at:
        logger.info('"{0}" library is up-to-date'.format(plex_section.title))
        return

    syno_session = requests.Session()
    syno_session.headers['Accept'] = 'application/json'

    syno_sid = get_syno_sid(syno_session)

    response = syno_session.get(
        settings.SYNO_URL + 'entry.cgi',
        params={
            'api': 'SYNO.FileStation.List',
            'version': 2,
            'method': 'list_share',
            'additional': 'real_path',
            '_sid': syno_sid,
        })

    data = get_syno_data(response)
    shares = data['shares']

    shares_map = dict()
    for share in shares:
        shares_map[share['additional']['real_path']] = share['path']

    jinja_env = jinja2.Environment()
    template = jinja_env.from_string(settings.NAME_TEMPLATE)

    with transaction.atomic():
        if section:
            section.delete()

        section = LibrarySection(
            uuid=plex_section.uuid,
            title=plex_section.title,
            changed_at=changed_at
        )

        section.save()

        for plex_item in plex_section.search():
            item_guid = plex_item.guid
            if item_guid.startswith('local://'):
                continue

            movie = Movie(
                guid=item_guid,
                title=plex_item.title,
                year=plex_item.year,
                thumb=plex_item.thumbUrl,
                added_at=plex_item.addedAt.replace(tzinfo=utc),
                updated_at=plex_item.updatedAt.replace(tzinfo=utc),
                section=section
            )

            movie.save()

            for plex_media in plex_item.media:
                media = Media(
                    id=plex_media.id,
                    movie=movie
                )

                media.save()

                parts_count = len(plex_media.parts)
                for i, plex_part in enumerate(plex_media.parts):
                    file_path = plex_part.file

                    _, file_extension = os.path.splitext(file_path)
                    file_name = os.path.basename(file_path)

                    dir_name = os.path.dirname(file_path)
                    for key, value in shares_map.items():
                        if dir_name.startswith(key):
                            dir_name = value + dir_name[len(key):]
                            break

                    file_path = os.path.join(dir_name, file_name)

                    quality = parse_quality(file_name)
                    render_context = {
                        'movie': plex_item,
                        'media': plex_media,
                        'part': plex_part,
                        'quality': quality,
                    }

                    best_file_name = template.render(render_context)
                    if parts_count > 1:
                        best_file_name = '{0}.part{1}'.format(best_file_name, i + 1)

                    best_file_name = '{0}{1}'.format(best_file_name, file_extension)
                    best_file_path = os.path.join(dir_name, best_file_name)

                    part = MediaPart(
                        id=plex_part.id,
                        path=file_path,
                        best_path=best_file_path,
                        media=media
                    )

                    part.save()
