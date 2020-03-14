from django import forms
from django.utils.translation import gettext as _


class EnterNickForm(forms.Form):
    subscription_info = forms.CharField(widget=forms.HiddenInput)
    nick = forms.CharField(label=_('Nickname'), min_length=3, max_length=30)
