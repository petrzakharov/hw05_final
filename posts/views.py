from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def index(request):
    """
    Отображение главной страницы
    """
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html",
                  {"page": page, "paginator": paginator})


def group_posts(request, slug):
    """
    Отображение постов в группе
    """
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group,
                                          "page": page,
                                          "paginator": paginator})


@login_required
def new_post(request):
    """
    Создание нового поста
    """
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        form_instance_updated = form.save(commit=False)
        form_instance_updated.author = request.user
        form_instance_updated.save()
        return redirect("index")
    return render(request, "new.html", {"form": form})


def profile(request, username):
    """
    Просмотр профиля пользователя
    """
    user = get_object_or_404(User, username=username)
    user_posts = user.posts.all()
    paginator = Paginator(user_posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"user_profile": user,
               "page": page,
               "paginator": paginator}
    if (request.user != 'AnonymousUser' or
        Follow.objects.filter(author=user,
                              user=request.user).exists()):
        context["following"] = True
    return render(request, "profile.html", context)


def post_edit(request, username, post_id):
    """
    Редактирование поста
    """
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if post.author != request.user:
        return redirect("post", username, post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", username, post_id)
    return render(request, "new.html", {"form": form,
                                        "is_edit": True,
                                        "post": post})


def post_view(request, username, post_id):
    """
    Просмотр поста
    """
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm()
    comments = post.comments.all()
    context = {"post": post,
               "user_profile": post.author,
               "comments": comments,
               "form": form}
    if (request.user != 'AnonymousUser' or
        Follow.objects.filter(author=post.author,
                              user=request.user).exists()):
        context["following"] = True

    return render(request, "post.html", context)


@login_required
def add_comment(request, username, post_id):
    """
    Добавление комментариев
    """
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if form.is_valid():
        form_instance_updated = form.save(commit=False)
        form_instance_updated.author = request.user
        form_instance_updated.post = post
        form_instance_updated.save()
        return redirect("post", username, post_id)
    return render(request, "post.html", {"form": form,
                                         "user_profile": post.author,
                                         "post": post,
                                         "following": True})


def page_not_found(request, exception=None):
    """
    Отображение 404 ошибки
    """
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    """
    Отображение ошибки сервера
    """
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    """
    Выводит посты авторов, на которых подписан текущий пользователь.
    """
    authors = request.user.follower.all()
    author_posts = Post.objects.select_related("author").filter(
        author__in=authors.values("author"))
    paginator = Paginator(author_posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page,
                                           "paginator": paginator})


@login_required
def profile_follow(request, username):
    """
    Подписка на автора
    """
    author = get_object_or_404(User, username=username)
    if not any([author == request.user,
                Follow.objects.filter(author=author,
                                      user=request.user).exists()]):
        Follow.objects.create(author=author, user=request.user)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    """
    Отписка от автора
    """
    author = get_object_or_404(User, username=username)
    follow_obj = Follow.objects.filter(author=author, user=request.user)
    if follow_obj.exists():
        follow_obj.delete()
    return redirect("profile", username=username)
