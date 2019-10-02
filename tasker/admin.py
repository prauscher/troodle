from django.contrib import admin
from . import models

admin.site.register(models.Board)
admin.site.register(models.Task)
admin.site.register(models.Handling)
admin.site.register(models.Comment)
admin.site.register(models.Attachment)

