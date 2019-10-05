from django.utils.http import is_safe_url


def get_redirect_url(request, get_parameter='next', default=''):
    redirect_to = request.GET.get(get_parameter, default)
    url_is_safe = is_safe_url(redirect_to, [])
    return redirect_to if url_is_safe else default
