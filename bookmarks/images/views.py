# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from .forms import ImageCreateForm
# from django.shortcuts import get_object_or_404
# from .models import Image
# from django.http import JsonResponse
# from django.views.decorators.http import require_POST
# from common.decorators import ajax_required
# from django.http import HttpResponse
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
#
#
#
#
# @login_required
# def image_list(request):
#     images = Image.objects.all()
#     paginator = Paginator(images, 8)
#     page = request.GET.get('page')
#     try:
#         images = paginator.page(page)
#     except PageNotAnInteger:
#         # Если переданная страница не является числом, возвращаем первую.
#         images = paginator.page(1)
#     except EmptyPage:
#         if request.is_ajax():
#             # Если получили AJAX-запрос с номером страницы, большим, чем их количество,
#             # возвращаем пустую страницу.
#             return HttpResponse('')
#         # Если номер страницы больше, чем их количество, возвращаем последнюю.
#         images = paginator.page(paginator.num_pages)
#     if request.is_ajax():
#         return render(request,'images/image/list_ajax.html',{'section': 'images', 'images': images})
#     return render(request,'images/image/list.html',{'section': 'images', 'images': images})
#
#
#
#
#
#
# @ajax_required
# @login_required
# @require_POST
# def image_like(request):
#     image_id = request.POST.get('id')
#     action = request.POST.get('action')
#     if image_id and action:
#         try:
#             image = Image.objects.get(id=image_id)
#             if action == 'like':
#                 image.users_like.add(request.user)
#             else:
#                 image.users_like.remove(request.user)
#             return JsonResponse({'status':'ok'})
#         except:
#             pass
#     return JsonResponse({'status':'ok'})
#
#
#
#
#
#
#
# def image_detail(request, id, slug):
#
#     image = get_object_or_404(Image, id=id, slug=slug)
#     return render(request,'images/image/detail.html',{'section': 'images','image': image})
#
#
#
# @login_required
# def image_create(request):
#     if request.method == 'POST':
#     # Форма отправлена.
#         form = ImageCreateForm(data=request.POST)
#         if form.is_valid():
#         # Данные формы валидны.
#             cd = form.cleaned_data
#             new_item = form.save(commit=False)
#         # Добавляем пользователя к созданному объекту.
#             new_item.user = request.user
#             new_item.save()
#             messages.success(request, 'Image added successfully')
#         # Перенаправляем пользователя на страницу сохраненного изображения.
#             return redirect(new_item.get_absolute_url())
#     else:
#         # Заполняем форму данными из GET-запроса.
#         form = ImageCreateForm(data=request.GET)
#     return render(request,'images/image/create.html',{'section': 'images', 'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import ImageCreateForm
from .models import Image
from common.decorators import ajax_required
from actions.utils import create_action
import redis
from django.conf import settings

# подключение к Redis
r = redis.StrictRedis(host=settings.REDIS_HOST,
                      port=settings.REDIS_PORT,
                      db=settings.REDIS_DB)


@login_required
def image_create(request):
    if request.method == 'POST':
        # form is sent
        form = ImageCreateForm(data=request.POST)
        if form.is_valid():
            # form data is valid
            cd = form.cleaned_data
            new_item = form.save(commit=False)

            # assign current user to the item
            new_item.user = request.user
            new_item.save()
            create_action(request.user, 'bookmarked image', new_item)
            messages.success(request, 'Image added successfully')

            # redirect to new created item detail view
            return redirect(new_item.get_absolute_url())
    else:
        # build form with data provided by the bookmarklet via GET
        form = ImageCreateForm(data=request.GET)

    return render(request,
                  'images/image/create.html',
                  {'section': 'images',
                   'form': form})


def image_detail(request, id, slug):
    image = get_object_or_404(Image, id=id, slug=slug)
    # Увеличиваем количество просмотров картинки на 1.
    total_views = r.incr('image:{}:views'.format(image.id))
    # Увеличиваем рейтинг картинки на 1.
    r.zincrby('image_ranking', 1, image.id)
    return render(request,
                  'images/image/detail.html',
                  {'section': 'images',
                   'image': image,
                   'total_views': total_views})


@ajax_required
@login_required
@require_POST
def image_like(request):
    image_id = request.POST.get('id')
    action = request.POST.get('action')
    if image_id and action:
        try:
            image = Image.objects.get(id=image_id)
            if action == 'like':
                image.users_like.add(request.user)
                create_action(request.user, 'likes', image)
            else:
                image.users_like.remove(request.user)
            return JsonResponse({'status':'ok'})
        except:
            pass
    return JsonResponse({'status':'ko'})


@login_required
def image_list(request):
    images = Image.objects.all()
    paginator = Paginator(images, 8)
    page = request.GET.get('page')
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        images = paginator.page(1)
    except EmptyPage:
        if request.is_ajax():
            # If the request is AJAX and the page is out of range
            # return an empty page
            return HttpResponse('')
        # If page is out of range deliver last page of results
        images = paginator.page(paginator.num_pages)
    if request.is_ajax():
        return render(request,
                      'images/image/list_ajax.html',
                      {'section': 'images', 'images': images})
    return render(request,
                  'images/image/list.html',
                   {'section': 'images', 'images': images})


@login_required
def image_ranking(request):
    #  Получаем набор рейтинга картинок.
    image_ranking = r.zrange('image_ranking', 0, -1, desc=True)[:10]
    image_ranking_ids = [int(id) for id in image_ranking]
    #  Получаем отсортированный список самых популярных картинок.
    most_viewed = list(Image.objects.filter(
                           id__in=image_ranking_ids))
    most_viewed.sort(key=lambda x: image_ranking_ids.index(x.id))
    return render(request,
                  'images/image/ranking.html',
                  {'section': 'images',
                   'most_viewed': most_viewed})