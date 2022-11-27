from .utils import func_paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow


def index(request):
    context = func_paginator(Post.objects.all(), request)
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = {
        "group": group,
    }
    context.update(func_paginator(group.posts.all(), request))
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_count = user.posts.count()
    following = user.following.exists()
    context = {
        "author": user,
        "post_count": post_count,
        "following": following,
    }
    context.update(func_paginator(user.posts.all(), request))
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author_posts = post.author.posts.count()
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        "post": post,
        "author_posts": author_posts,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required()
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect("posts:profile", request.user)
        return render(request, "posts/create_post.html", {"form": form})
    form = PostForm()
    return render(request, "posts/create_post.html", {"form": form})


@login_required()
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if request.user != author:
        return redirect("posts:post_detail", post_id)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    context = {
        "form": form,
        "post": post,
        "is_edit": True,
    }
    return render(request, "posts/create_post.html", context)


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
    follower = Follow.objects.filter(user=request.user).values_list(
        "author_id", flat=True
    )
    posts = Post.objects.filter(author_id__in=follower)
    context = func_paginator(posts, request)
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:follow_index")


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect("posts:follow_index")
