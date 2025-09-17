from django import forms
from .models import Message
from LMSapp.accounts.models import User

class ComposeForm(forms.ModelForm):
    attachments = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'multiple': False})
    )
    
    class Meta:
        model = Message
        fields = ['recipients', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'recipients': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrer les destinataires selon le rôle de l'utilisateur
            if user.role == 'parent':
                self.fields['recipients'].queryset = User.objects.filter(
                    role__in=['teacher', 'admin']
                )
            elif user.role == 'teacher':
                self.fields['recipients'].queryset = User.objects.filter(
                    role__in=['parent', 'admin']
                )
            else:  # admin
                self.fields['recipients'].queryset = User.objects.exclude(
                    id=user.id
                )
                
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'subject', 'body']