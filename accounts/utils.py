from django.core.mail import send_mail
from django.urls import reverse

def send_parental_consent_email(parent_email, parent_name, player, token, request):
    link = request.build_absolute_uri(reverse('accounts:consent_verify', args=[str(token)]))
    subject = f"Parental Consent Request for {player.get_full_name()}"
    message = f"Dear {parent_name},\n\nYour child {player.get_full_name()} has registered as a player. Please review and provide your consent by clicking the link below:\n\n{link}\n\nIf you did not expect this email, you can ignore it.\n\nThank you."
    send_mail(subject, message, None, [parent_email]) 