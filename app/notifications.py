"""Notification par e-mail à la réception d'un message (facultative).

Si SMTP_HOST n'est pas configuré, la fonction ne fait rien : les messages restent
consultables dans l'espace d'administration.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.config import Settings

journal = logging.getLogger("roubil.notifications")


def notifier_nouveau_message(settings: Settings, nom: str, telephone: str, contenu: str) -> None:
    if not (settings.smtp_host and settings.notify_to):
        return

    mail = EmailMessage()
    mail["Subject"] = "Nouveau message depuis le site ROUBIL CONTROLE"
    mail["From"] = settings.smtp_user or settings.notify_to
    mail["To"] = settings.notify_to
    # Les champs viennent d'un visiteur : ils sont placés dans le CORPS du mail, jamais
    # dans un en-tête (sinon risque d'injection d'en-têtes SMTP via des retours à la ligne).
    mail.set_content(f"Nom : {nom}\nTéléphone : {telephone}\n\nMessage :\n{contenu}\n")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as serveur:
            serveur.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                serveur.login(settings.smtp_user, settings.smtp_password)
            serveur.send_message(mail)
    except (OSError, smtplib.SMTPException) as erreur:
        # Un problème d'e-mail ne doit jamais faire perdre le message : il est déjà en base.
        journal.warning("Notification e-mail impossible : %s", erreur)
