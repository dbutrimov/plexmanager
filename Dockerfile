FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
RUN mkdir /plexmanager
WORKDIR /plexmanager
COPY requirements.txt /plexmanager/
RUN pip install -r requirements.txt
COPY . /plexmanager/
RUN python manage.py migrate
