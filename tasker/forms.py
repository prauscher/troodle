from django import forms


class EnterNickForm(forms.Form):
    nick = forms.CharField(label='Nickname', min_length=3, max_length=30)
