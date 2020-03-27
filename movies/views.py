from datetime import timezone

from django.shortcuts import render
from plexapi.server import PlexServer

from movies import settings
from movies.templatetags import movie_extras
import os
import jinja2
import re
import logging
import requests

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


def syno_auth(session):
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

    return data['sid']


def rename(request, id):
    movies = request.session.get('movies')
    if not movies:
        raise FileNotFoundError('id: ' + id)

    movie = None
    index = -1
    for i, item in enumerate(movies):
        if item['id'] == id:
            index = i
            movie = item
            break

    if index < 0 or not movie:
        raise FileNotFoundError('id: ' + id)

    if movie_extras.validate_movie(movie):
        return render(request, 'movies/card.html', {'item': movie})

    syno_session = requests.Session()
    syno_session.headers['Accept'] = 'application/json'

    syno_sid = request.session.get('syno_sid')
    if not syno_sid or len(syno_sid) <= 0:
        syno_sid = syno_auth(syno_session)
        request.session['syno_sid'] = syno_sid

    if not settings.DEBUG:
        response = syno_session.get(
            settings.SYNO_URL + 'entry.cgi',
            params={
                'api': 'SYNO.FileStation.Rename',
                'version': 2,
                'method': 'rename',
                'path': movie['path'],
                'name': movie_extras.filename(movie['valid_path']),
                'additional': 'real_path',
                '_sid': syno_sid,
            })

        raise_syno_error(response)

    movie['path'] = movie['valid_path']

    movies.pop(index)

    request.session['movies'] = movies

    return render(request, 'movies/card.html', {'item': movie})


def rename_all(request):
    movies = request.session.get('movies')
    if not movies:
        return render(request, 'movies/cards.html', {'items': movies})

    paths = list()
    names = list()

    index = 0
    while index < len(movies):
        movie = movies[index]
        if movie_extras.validate_movie(movie):
            index += 1
            continue

        paths.append(movie['path'])
        names.append(movie_extras.filename(movie['valid_path']))

        movie['path'] = movie['valid_path']

        movies.pop(index)

    if len(paths) <= 0:
        return render(request, 'movies/cards.html', {'items': movies})

    paths = ','.join(paths)
    names = ','.join(names)

    syno_session = requests.Session()
    syno_session.headers['Accept'] = 'application/json'

    syno_sid = request.session.get('syno_sid')
    if not syno_sid or len(syno_sid) <= 0:
        syno_sid = syno_auth(syno_session)
        request.session['syno_sid'] = syno_sid

    if not settings.DEBUG:
        response = syno_session.get(
            settings.SYNO_URL + 'entry.cgi',
            params={
                'api': 'SYNO.FileStation.Rename',
                'version': 2,
                'method': 'rename',
                'path': paths,
                'name': names,
                'additional': 'real_path',
                '_sid': syno_sid,
            })

        raise_syno_error(response)

    request.session['movies'] = movies

    context = {
        'items': movies,
        'invalid_count': len([m for m in movies if not movie_extras.validate_movie(m)])
    }

    return render(request, 'movies/cards.html', context)


def movies(request):
    items_filter = request.GET.get('filter')

    syno_session = requests.Session()
    syno_session.headers['Accept'] = 'application/json'

    syno_sid = request.session.get('syno_sid')
    if not syno_sid or len(syno_sid) <= 0:
        syno_sid = syno_auth(syno_session)
        request.session['syno_sid'] = syno_sid

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

    plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)

    invalid_count = 0
    movies = list()

    section = plex.library.section(settings.PLEX_SECTION)
    for item in section.search(sort='addedAt:desc'):
        for media in item.media:
            parts_count = len(media.parts)
            for i, part in enumerate(media.parts):
                file_path = part.file

                _, file_extension = os.path.splitext(file_path)
                file_name = os.path.basename(file_path)

                dir_name = os.path.dirname(file_path)
                for key, value in shares_map.items():
                    if dir_name.startswith(key):
                        dir_name = value + dir_name[len(key):]
                        break

                file_path = os.path.join(dir_name, file_name)

                warnings = list()

                quality = parse_quality(file_name)
                if len(quality) <= 0:
                    warnings.append('no_quality')

                render_context = {
                    'movie': item,
                    'media': media,
                    'part': part,
                    'quality': quality,
                }

                valid_file_name = template.render(render_context)
                if parts_count > 1:
                    valid_file_name = '{0}.part{1}'.format(valid_file_name, i + 1)

                valid_file_name = '{0}{1}'.format(valid_file_name, file_extension)
                valid_file_path = os.path.join(dir_name, valid_file_name)

                movie = {
                    'id': part.id,
                    'thumb': item.thumbUrl,
                    'title': item.title,
                    'year': item.year,
                    'added': item.addedAt.replace(tzinfo=timezone.utc).timestamp(),
                    'quality': quality,
                    'path': file_path,
                    'valid_path': valid_file_path,
                    'warnings': warnings
                }

                is_valid = movie_extras.validate_movie(movie)
                if items_filter and items_filter == 'invalid' and is_valid:
                    continue

                if not is_valid:
                    invalid_count += 1

                movies.append(movie)

    request.session['movies'] = movies

    context = {
        'items': movies,
        'invalid_count': invalid_count
    }

    return render(request, 'movies/index.html', context)
