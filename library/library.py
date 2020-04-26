import logging
import os
import re

import jinja2
from django.db import transaction
from plexapi.server import PlexServer
from pytz import utc

from library.syno import Syno
from movies import settings
from movies.models import LibrarySection, Movie, Media, MediaPart

logger = logging.getLogger(__name__)


class Library(object):
    @staticmethod
    def parse_quality(title):
        for pattern, source in settings.QUALITY_MAP.items():
            item_regex = re.compile(r'[\W_]{0}'.format(pattern), flags=re.IGNORECASE)
            match = item_regex.search(title)
            if match:
                return source

        return ''

    @staticmethod
    def sync(force=False):
        logger.debug('Sync library...')

        plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)
        plex_section = plex.library.section(settings.PLEX_SECTION)
        if plex_section.refreshing:
            logger.warning('"%s" library is being refreshed now', plex_section.title)
            return

        changed_at = int(plex_section._data.attrib.get('contentChangedAt'))
        # scanned_at = utils.toDatetime(plex_section._data.attrib.get('scannedAt'))

        section = LibrarySection.objects.filter(uuid=plex_section.uuid).first()
        if not force and section and changed_at <= section.changed_at:
            logger.debug('"%s" library is up-to-date', plex_section.title)
            return

        shares = Syno.list_share()

        shares_map = dict()
        for share in shares:
            shares_map[share['additional']['real_path']] = share['path']

        jinja_env = jinja2.Environment()
        template = jinja_env.from_string(settings.NAME_TEMPLATE)

        count = 0
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

                        quality = Library.parse_quality(file_name)
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

                count += 1

        logger.info('%i record(s) have been synced', count)
