from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def _get_page_obj(request, post_list):
    paginator = Paginator(post_list, settings.NUMBER_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    template = "posts/index.html"
    post_list = Post.objects.all()
    page_obj = _get_page_obj(request, post_list)
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = _get_page_obj(request, posts)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    number_posts = posts.count()
    page_obj = _get_page_obj(request, posts)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists()
    )
    context = {
        "number_posts": number_posts,
        "author": author,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = "posts/post_detail.html"
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    number_posts = Post.objects.filter(author=author).count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        "number_posts": number_posts,
        "post": post,
        "form": form,
        "comments": comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    is_edit = False
    template = "posts/create_post.html"
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    template = "posts/create_post.html"
    context = {
        "is_edit": is_edit,
        "form": form,
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", request.user)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    template = "posts/create_post.html"
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    context = {
        "post": post,
        "is_edit": is_edit,
        "form": form,
    }
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post_id)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = _get_page_obj(request, posts)
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    condition = not Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    if author.id != request.user.id:
        if condition:
            Follow.objects.create(
                user=request.user,
                author=author,
            )
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author,
    ).delete()
    return redirect("posts:profile", author.username)
