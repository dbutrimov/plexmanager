import logging
from datetime import datetime, timedelta

import requests
from pytz import utc

from movies import settings
from movies.models import SynoSession

logger = logging.getLogger(__name__)


class Syno(object):
    @staticmethod
    def _raise_syno_error(response):
        response.raise_for_status()

        content = response.json()
        if not content.get('success'):
            error = content.get('error')
            raise Exception('SYNO.ErrorCode: {0}'.format(error.get('code')))

        return content

    @staticmethod
    def _get_syno_data(response):
        content = Syno._raise_syno_error(response)
        return content.get('data')

    @staticmethod
    def _get_syno_sid(session):
        credentials = SynoSession.objects.filter(account=settings.SYNO_ACCOUNT).first()
        if credentials:
            elapsed = datetime.now(tz=utc) - credentials.timestamp.replace(tzinfo=utc)
            if elapsed < timedelta(hours=3):
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

        data = Syno._get_syno_data(response)

        credentials = SynoSession(account=settings.SYNO_ACCOUNT, sid=data['sid'])
        credentials.save()

        return credentials.sid

    @staticmethod
    def _create_session():
        session = requests.Session()
        session.headers['Accept'] = 'application/json'

        return session

    @staticmethod
    def list_share():
        session = Syno._create_session()
        sid = Syno._get_syno_sid(session)

        response = session.get(
            settings.SYNO_URL + 'entry.cgi',
            params={
                'api': 'SYNO.FileStation.List',
                'version': 2,
                'method': 'list_share',
                'additional': 'real_path',
                '_sid': sid,
            })

        data = Syno._get_syno_data(response)
        return data['shares']

    @staticmethod
    def rename(paths, names):
        logger.debug('Rename: %s -> %s', paths, names)

        session = Syno._create_session()
        sid = Syno._get_syno_sid(session)

        if settings.DEBUG:
            logger.warning('Skip critical section in Debug mode: %s', 'rename')
            return

        response = session.get(
            settings.SYNO_URL + 'entry.cgi',
            params={
                'api': 'SYNO.FileStation.Rename',
                'version': 2,
                'method': 'rename',
                'path': paths,
                'name': names,
                'additional': 'real_path',
                '_sid': sid,
            })

        Syno._raise_syno_error(response)
