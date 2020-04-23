import os

import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()

env_file = env.str('ENV_FILE', default=os.path.join(BASE_DIR, '.env'))
if os.path.isfile(env_file):
    environ.Env.read_env(env_file=env_file)  # reading .env file

DEBUG = env.bool('DEBUG', default=False)

PLEX_URL = env.str('PLEX_URL')
PLEX_TOKEN = env.str('PLEX_TOKEN')
PLEX_SECTION = env.str('PLEX_SECTION', default='Movies')

SYNO_URL = env.str('SYNO_URL')
SYNO_ACCOUNT = env.str('SYNO_ACCOUNT')
SYNO_PASSWD = env.str('SYNO_PASSWD')

TARGET_DIR = env.str('TARGET_DIR', default=None)

NAME_TEMPLATE = \
    "{{ movie.title|" \
    "replace(':', '.')|" \
    "replace('·', '-')|" \
    "replace('\\\\', '_')|" \
    "replace('/', '_')|" \
    "replace('?', '_')|" \
    "replace('—', '-') }} " \
    "({{ movie.year }})" \
    "{%- if quality|length > 0 %}.{{ quality }}{%- endif %}." \
    "{{ media.videoCodec }}." \
    "{{ media.videoResolution }}{%- if media.videoResolution|int(-1) != -1 %}p{%- endif %}." \
    "{{ media.audioCodec }}." \
    "{{ media.audioChannels }}ch"

QUALITY_MAP = {
    'bluray': 'BluRay',
    'remux': 'Remux',
    'dvdrip': 'DVDRip',
    'web[-_]?dl([-_]?rip)?': 'WEB-DL',
    'hdtv': 'HDTV',
    'webri?p': 'WEBRip',
    'bdscr': 'BDScr',
    'dvdscr': 'DVDScr',
    'sdtv': 'SDTV',
    'dsr': 'Dsr',
    'tvri?p': 'TVRip',
    'preair': 'Preair',
    'ppvri?p': 'PPVRip',
    'hdri?p': 'HDRip',
    'r5': 'R5',
    'tc': 'TC',
    'ts': 'TS',
    'cam': 'Cam',
    'workprint': 'Workprint',
    'bdremux': 'BDRemux',
    'bdri?p': 'BDRip',
    'camri?p': 'CAMRip',
    'dtheari?p': 'DTheaRip',
}
