from django.db.models import Count
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist as DoesNotExist

from blog.models import Post, Tag


def serialize_post(post):
    return {
        "title": post.title,
        "teaser_text": post.text[:200],
        "author": post.author.username,
        "comments_amount": post.comments_count,
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.first().title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def index(request):

    most_popular_posts = Post.objects.popular().prefetch_related('author')[:5] \
                                               .fetch_tags().fetch_with_comments()

    most_fresh_posts = Post.objects.annotate(comments_count=Count('comments')) \
                                   .order_by('-published_at').prefetch_related('author').fetch_tags()[:5]

    most_popular_tags = Tag.objects.popular().prefetch_related('posts')[:5].annotate(posts_count=Count("posts"))

    context = {
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    posts = Post.objects.popular().fetch_tags()\
        .prefetch_related('author') # при использовании select_related скорость загрузки страницы сильно снижается

    try:
        main_post = posts.get(slug=slug)
    except DoesNotExist:
        return redirect('index')

    comments = main_post.comments.prefetch_related('author')
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    related_tags = main_post.tags.annotate(posts_count=Count("posts"))

    serialized_post = {
        "title": main_post.title,
        "text": main_post.text,
        "author": main_post.author.username,
        "comments": serialized_comments,
        'likes_amount': main_post.likes_count,
        "image_url": main_post.image.url if main_post.image else None,
        "published_at": main_post.published_at,
        "slug": main_post.slug,
        "tags": [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = Tag.objects.annotate(posts_count=Count("posts")).popular()[5:]

    most_popular_posts = posts[:5].fetch_with_comments()

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    try:
        tag = Tag.objects.get(title=tag_title)
    except DoesNotExist:
        return redirect('index')

    most_popular_tags = Tag.objects.annotate(posts_count=Count("posts")).popular()[:5]
    most_popular_posts = Post.objects.popular() \
                                     .fetch_tags().prefetch_related('author')[:5] \
                                     .fetch_with_comments()

    related_posts = tag.posts \
                            .prefetch_related('author').fetch_tags() \
                            .fetch_with_comments()[:20]

    context = {
        "tag": tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        "posts": [serialize_post(post) for post in related_posts],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
