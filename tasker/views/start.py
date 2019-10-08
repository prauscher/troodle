from django.shortcuts import render


def error_404(request, exception):
    return render(request, 'meta/error_404.html')
