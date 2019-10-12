from django.utils.http import is_safe_url


def get_redirect_url(request, get_parameter='next', post_parameter='next', default=''):
    if post_parameter in request.POST and is_safe_url(request.POST[post_parameter], []):
        return request.POST[post_parameter]

    if get_parameter in request.GET and is_safe_url(request.GET[get_parameter], []):
        return request.GET[get_parameter]

    return default
