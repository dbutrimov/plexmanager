FROM python:3.7-alpine

ENV PYTHONUNBUFFERED 1

RUN mkdir /plexmanager

WORKDIR /plexmanager

COPY requirements.txt /plexmanager/
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt
COPY . /plexmanager/

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/plexmanager/entrypoint.sh"]

VOLUME /config
