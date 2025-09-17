from django.apps import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        label='Nom complet',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Votre nom complet'
        })
    )
    
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Votre adresse email'
        })
    )
    
    phone = forms.CharField(
        label='Téléphone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Votre numéro de téléphone'
        })
    )
    
    subject = forms.ChoiceField(
        label='Sujet',
        choices=[
            ('', 'Sélectionnez un sujet...'),
            ('general', 'Demande générale'),
            ('enrollment', 'Inscription'),
            ('schedule', 'Horaires et disponibilités'),
            ('activities', 'Activités et programmes'),
            ('billing', 'Facturation et paiement'),
            ('other', 'Autre demande'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        })
    )
    
    message = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Décrivez votre demande en détail...',
            'rows': 5
        })
    )