import environ

env = environ.Env()
environ.Env.read_env()  # reading .env file

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
    'webrip': 'WEBRip',
    'bdscr': 'BDScr',
    'dvdscr': 'DVDScr',
    'sdtv': 'SDTV',
    'dsr': 'Dsr',
    'tvrip': 'TVRip',
    'preair': 'Preair',
    'ppvrip': 'PPVRip',
    'hdrip': 'HDRip',
    'r5': 'R5',
    'tc': 'TC',
    'ts': 'TS',
    'cam': 'Cam',
    'workprint': 'Workprint',
    'bdremux': 'BDRemux',
    'bdrip': 'BDRip',
    'camrip': 'CAMRip',
    'dthearip': 'DTheaRip',
}
