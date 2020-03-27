from django.shortcuts import render
from plexapi.server import PlexServer

from movies import settings
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

    if movie['state'] != 0:
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
                'path': movie['source_file']['path'],
                'name': movie['target_file']['name'],
                'additional': 'real_path',
                '_sid': syno_sid,
            })

        raise_syno_error(response)

    movie['source_file'] = movie['target_file']
    movie['state'] = 1

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
        if movie['state'] != 0:
            index += 1
            continue

        paths.append(movie['source_file']['path'])
        names.append(movie['target_file']['name'])

        movie['source_file'] = movie['target_file']
        movie['state'] = 1

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

    return render(request, 'movies/cards.html', {'items': movies})


def movies(request):
    filter = request.GET.get('filter')

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

    items = list()

    section = plex.library.section(settings.PLEX_SECTION)
    for movie in section.search():
        for media in movie.media:
            parts_count = len(media.parts)
            for i, part in enumerate(media.parts):
                real_file_path = part.file

                _, file_extension = os.path.splitext(real_file_path)
                file_name = os.path.basename(real_file_path)

                real_dir_name = os.path.dirname(real_file_path)
                dir_name = real_dir_name
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
                    'movie': movie,
                    'media': media,
                    'part': part,
                    'quality': quality,
                }

                new_file_name = template.render(render_context)
                if parts_count > 1:
                    new_file_name = '{0}.part{1}'.format(new_file_name, i + 1)

                new_file_name = '{0}{1}'.format(new_file_name, file_extension)
                new_real_file_path = os.path.join(real_dir_name, new_file_name)

                state = 0
                if new_real_file_path == real_file_path:
                    state = 1
                    if filter != 'all':
                        continue

                item = {
                    'id': part.id,
                    'thumb': movie.thumbUrl,
                    'title': movie.title,
                    'year': movie.year,
                    'quality': quality,
                    'state': state,
                    'source_file': {
                        'real_path': real_file_path,
                        'real_dir': real_dir_name,
                        'path': file_path,
                        'dir': dir_name,
                        'name': file_name,
                    },
                    'target_file': {
                        'real_path': new_real_file_path,
                        'real_dir': real_dir_name,
                        'path': os.path.join(dir_name, new_file_name),
                        'dir': dir_name,
                        'name': new_file_name,
                    },
                    'warnings': warnings
                }

                items.append(item)

    request.session['movies'] = items

    return render(request, 'movies/index.html', {'items': items})
