from django.utils.http import url_has_allowed_host_and_scheme


def get_redirect_url(request, get_parameter='next', post_parameter='next', default=''):
    if post_parameter in request.POST and url_has_allowed_host_and_scheme(request.POST[post_parameter], []):
        return request.POST[post_parameter]

    if get_parameter in request.GET and url_has_allowed_host_and_scheme(request.GET[get_parameter], []):
        return request.GET[get_parameter]

    return default
