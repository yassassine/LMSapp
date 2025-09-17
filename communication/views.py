from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Message, Attachment
from .forms import ComposeForm
from LMSapp.accounts.models import User
from .forms import MessageForm
from django.core.paginator import Paginator
from .models import Notification
from .models import Announcement
from datetime import datetime, timedelta
from django.utils import timezone
# Create your views here. 

@login_required
def inbox(request):
    # Récupérer tous les messages de l'utilisateur
    messages = Message.objects.filter(recipients=request.user).order_by('-sent_at')
    
    # Récupérer les contacts fréquents
    frequent_contacts = User.objects.filter(
        received_messages__sender=request.user
    ).distinct().order_by('?')[:4]
    
    # Marquer un message spécifique comme lu si demandé
    message_id = request.GET.get('message_id')
    selected_message = None
    
    if message_id:
        selected_message = get_object_or_404(Message, id=message_id, recipients=request.user)
        if not selected_message.read:
            selected_message.read = True
            selected_message.save()
    
    context = {
        'messages': messages,
        'frequent_contacts': frequent_contacts,
        'selected_message': selected_message,
        'unread_count': messages.filter(read=False).count(),
    }
    return render(request, 'communication/inbox.html', context)

@login_required
def toggle_message_important(request, message_id):
    message = get_object_or_404(Message, id=message_id, recipients=request.user)
    message.important = not message.important
    message.save()
    return redirect('inbox')

@login_required
def compose_message(request):
    if request.method == 'POST':
        form = ComposeForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            form.save_m2m()  # save recipients (ManyToMany)

            # Save attachments if uploaded
            for file in request.FILES.getlist('attachments'):
                Attachment.objects.create(
                    message=message,
                    file=file,
                    filename=file.name
                )
            return redirect('inbox')
    else:
        form = ComposeForm(user=request.user)

    return render(request, 'communication/compose_message.html', {'form': form})


@login_required
def notifications_view(request):
    # Récupérer les notifications de l'utilisateur
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Appliquer les filtres
    filter_param = request.GET.get('filter', 'all')
    if filter_param == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_param in ['system', 'academic', 'event']:
        notifications = notifications.filter(notification_type=filter_param.upper())
    
    # Pagination (20 notifications par page)
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    total_count = notifications.count()
    
    # Compter les notifications de cette semaine
    one_week_ago = timezone.now() - timedelta(days=7)
    this_week = Notification.objects.filter(
        user=request.user, 
        created_at__gte=one_week_ago
    ).count()
    
    return render(request, 'communication/notifications.html', {
        'notifications': page_obj,
        'unread_count': unread_count,
        'total_count': total_count,
        'this_week': this_week
    })



def announcements_view(request):
    # Récupérer toutes les annonces actives
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(announcements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_announcements = Announcement.objects.count()
    active_announcements = Announcement.objects.filter(is_active=True).count()
    announcements_this_month = Announcement.objects.filter(
        created_at__month=datetime.now().month,
        created_at__year=datetime.now().year
    ).count()
    urgent_announcements = Announcement.objects.filter(is_urgent=True, is_active=True).count()
    
    # Données pour la sidebar
    urgent_announcements_list = Announcement.objects.filter(
        is_urgent=True, 
        is_active=True
    ).order_by('-created_at')[:3]
    
    recent_announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-created_at')[:5]
    
    # Événements pour le calendrier (exemple)
    calendar_events = [
        {'id': 1, 'title': 'Réunion parents', 'date': datetime.now() + timedelta(days=5), 'category': 'event'},
        {'id': 2, 'title': 'Sortie éducative', 'date': datetime.now() + timedelta(days=10), 'category': 'academic'},
    ]
    
    return render(request, 'communication/announcements.html', {
        'announcements': page_obj,
        'total_announcements': total_announcements,
        'active_announcements': active_announcements,
        'announcements_this_month': announcements_this_month,
        'urgent_announcements': urgent_announcements,
        'urgent_announcements_list': urgent_announcements_list,
        'recent_announcements': recent_announcements,
        'calendar_events': calendar_events,
        'upcoming_events': calendar_events  # pour la liste dans la sidebar
    })