from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ChildEnrollment
from datetime import date
from django import forms
from django.shortcuts import render, get_object_or_404
from .models import Child, ClassGroup, Activity, Observation

# Create your views here.

@login_required
def enrollment_view(request):
    class EnrollmentForm(forms.ModelForm):
        class Meta:
            model = ChildEnrollment
            fields = [
                'child_first_name', 'child_last_name', 'birth_date', 'gender', 
                'grade_level', 'allergies', 'medical_conditions', 'schedule_type', 
                'start_date', 'special_requirements', 'emergency_contact_name', 
                'emergency_contact_phone', 'emergency_contact_relation'
            ]
            widgets = {
                'birth_date': forms.DateInput(attrs={'type': 'date'}),
                'start_date': forms.DateInput(attrs={'type': 'date'}),
                'special_requirements': forms.Textarea(attrs={'rows': 3}),
                'medical_conditions': forms.Textarea(attrs={'rows': 3}),
            }
        
        def clean_birth_date(self):
            birth_date = self.cleaned_data['birth_date']
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 2 or age > 6:
                raise forms.ValidationError("L'enfant doit avoir entre 2 et 6 ans")
            return birth_date

    if request.method == 'POST':
        form = EnrollmentForm(request.POST, request.FILES)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.parent = request.user
            enrollment.save()
            
            # Gérer le fichier médical séparément
            if 'medical_certificate' in request.FILES:
                enrollment.medical_certificate = request.FILES['medical_certificate']
                enrollment.save()
            
            messages.success(
                request,
                "Inscription soumise avec succès! "
                "Vous recevrez une confirmation par email après validation."
            )
            return redirect('dashboard')
    else:
        form = EnrollmentForm()
    
    return render(request, 'enrollment/enroll_form.html', {'form': form})

@login_required
def enrollment_status(request):
    enrollments = ChildEnrollment.objects.filter(parent=request.user).order_by('-created_at')
    return render(request, 'enrollment/enroll_status.html', {'enrollments': enrollments})

def enrollment_detail(request, enrollment_id):
    enrollment = get_object_or_404(
        ChildEnrollment, 
        id=enrollment_id, 
        parent=request.user
    )
    return render(request, 'enrollment/enroll_detail.html', {'enrollment': enrollment})

def child_management(request):
    children = Child.objects.filter(parent=request.user)
    
    # Derniers paiements (exemple simplifié)
    payments = [
        {'description': 'Mai 2023', 'amount': 150, 'date': '2023-05-01', 'child': children.first()} 
    ] if children else []
    
    # Événements à venir (exemple simplifié)
    events = [
        {'title': 'Sortie au zoo', 'date': '2023-06-15', 'time': '09:00', 'child': children.first()}
    ] if children else []
    
    return render(request, 'enrollment/child_management.html', {
        'children': children,
        'payments': payments,
        'events': events
    })

@login_required
def child_detail(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    return render(request, 'enrollment/child_detail.html', {'child': child})

@login_required
def update_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    # Logique de mise à jour à implémenter
    return redirect('enrollment:child_management')

@login_required
def deactivate_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        child.is_active = False
        child.save()
        messages.success(request, f"{child.first_name} a été désinscrit avec succès.")
    return redirect('enrollment:child_management')

@login_required
def activate_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        child.is_active = True
        child.save()
        messages.success(request, f"{child.first_name} a été réinscrit avec succès.")
    return redirect('enrollment:child_management')
def class_groups(request):
    # Récupérer les groupes de l'enseignant connecté
    groups = ClassGroup.objects.filter(teacher=request.user)
    
    # Calculer les indicateurs pour le tableau de bord
    groups_count = groups.count()
    children_count = sum(group.children.count() for group in groups)
    
    # Récupérer les activités et observations récentes
    activities = Activity.objects.filter(group__teacher=request.user).order_by('-date')[:5]
    observations = Observation.objects.filter(group__teacher=request.user).order_by('-date')[:5]
    activity_count = Activity.objects.filter(group__teacher=request.user).count()
    observation_count = Observation.objects.filter(group__teacher=request.user).count()
    
    # Tous les enfants (pour la création de groupe)
    all_children = Child.objects.all().order_by('first_name')
    
    context = {
        'groups': groups,
        'groups_count': groups_count,
        'children_count': children_count,
        'activity_count': activity_count,
        'observation_count': observation_count,
        'activities': activities,
        'observations': observations,
        'all_children': all_children,
    }
    
    return render(request, 'enrollment/class_groups.html', context)