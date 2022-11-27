from django.core.paginator import Paginator

LIMIT_POSTS_ON_BOARD: int = 10


def func_paginator(queryset, request):
    paginator = Paginator(queryset, LIMIT_POSTS_ON_BOARD)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return context
