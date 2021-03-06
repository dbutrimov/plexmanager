from django.core.paginator import Paginator
from django.db import models, transaction
from django.shortcuts import render

from library.syno import Syno
from library.library import Library
from movies.models import MediaPart
from movies.templatetags import movie_extras
import logging

logger = logging.getLogger(__name__)
page_size = 20


def rename(request, id):
    part = MediaPart.objects.get(id=id)

    if part.path == part.best_path:
        return render(request, 'movies/card.html', {'item': part})

    Syno.rename(part.path, movie_extras.filename(part.best_path))

    part.path = part.best_path
    part.save()

    return render(request, 'movies/card.html', {'item': part})


def rename_all(request):
    parts = MediaPart.objects.exclude(path=models.F('best_path'))
    if len(parts) > 0:
        with transaction.atomic():
            paths = list()
            names = list()

            for part in parts:
                paths.append(part.path)
                names.append(movie_extras.filename(part.best_path))

                part.path = part.best_path
                part.save()

            paths = ','.join(paths)
            names = ','.join(names)

            Syno.rename(paths, names)

    items_filter = request.GET.get('filter')
    page_number = request.GET.get('page', 1)

    items = MediaPart.objects.order_by('-media__movie__added_at')
    if items_filter == 'invalid':
        items = items.exclude(path=models.F('best_path'))
    else:
        items = items.all()

    paginator = Paginator(items, page_size)
    page = paginator.get_page(page_number)

    context = {
        'items': page,
    }

    return render(request, 'movies/cards.html', context)


def sync(request):
    items_filter = request.GET.get('filter')
    page_number = request.GET.get('page', 1)

    Library.sync(force=True)

    items = MediaPart.objects.order_by('-media__movie__added_at')
    if items_filter == 'invalid':
        items = items.exclude(path=models.F('best_path'))
    else:
        items = items.all()

    paginator = Paginator(items, page_size)
    page = paginator.get_page(page_number)

    context = {
        'items': page,
    }

    return render(request, 'movies/cards.html', context)


def movies(request):
    items_filter = request.GET.get('filter')
    page_number = request.GET.get('page', 1)

    Library.sync()

    items = MediaPart.objects.order_by('-media__movie__added_at')
    if items_filter == 'invalid':
        items = items.exclude(path=models.F('best_path'))
    else:
        items = items.all()

    paginator = Paginator(items, page_size)
    page = paginator.get_page(page_number)

    context = {
        'items': page,
    }

    return render(request, 'movies/index.html', context)
