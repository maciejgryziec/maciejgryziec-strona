#!/usr/bin/env python3
"""Run manually over an interactive SSH terminal. Never pass the password in arguments.
Tests OVH authentication and sends one clearly labelled test to the owner's mailbox.
Does not read browser/Keychain passwords or change the OVH mailbox password.
"""
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from getpass import getpass
from pathlib import Path
import json
import os
import smtplib
import ssl
import sys
import tempfile
from datetime import datetime, timezone

MAILBOX='kontakt@maciejgryziec.pl'
DIRECTORY=Path('/opt/maciejgryziec-contact/secrets')

def main():
    if os.geteuid()!=0 or not sys.stdin.isatty():
        print('Uruchom w interaktywnym terminalu: sudo python3 /opt/maciejgryziec-contact/configure_smtp.py')
        return 1
    if not DIRECTORY.is_dir():
        print('Brak katalogu przygotowanej usługi. Nie wprowadzono zmian.')
        return 1
    print('Konfiguracja formularza maciejgryziec.pl')
    print('Skrzynka: '+MAILBOX)
    print('Hasło służy tylko do wysyłki SMTP przez OVH. Nie będzie wyświetlane ani zapisane w repozytorium.')
    print('Po sprawdzeniu zostanie wysłana jedna wiadomość testowa na tę samą skrzynkę.')
    password=getpass('Wpisz hasło skrzynki (znaki pozostaną niewidoczne): ')
    if not password:
        print('Anulowano. Niczego nie zmieniono.')
        return 1
    message=EmailMessage()
    message['From']=MAILBOX;message['To']=MAILBOX
    message['Subject']='[TEST] Formularz na maciejgryziec.pl'
    message['Date']=formatdate(localtime=False)
    message['Message-ID']=make_msgid(domain='maciejgryziec.pl')
    message['Auto-Submitted']='auto-generated'
    message.set_content('To jednorazowy test wysyłki formularza maciejgryziec.pl.\n\nJeżeli wiadomość dotarła, odbiór na nowej skrzynce działa.\nNie trzeba na nią odpowiadać. Test nie zawiera danych klientów.')
    smtp=None
    try:
        smtp=smtplib.SMTP_SSL('smtp.mail.ovh.net',465,context=ssl.create_default_context(),timeout=15)
        smtp.login(MAILBOX,password)
        refused=smtp.send_message(message,from_addr=MAILBOX,to_addrs=[MAILBOX])
        if refused:raise RuntimeError('recipient refused')
    except Exception as exc:
        print('OVH nie potwierdziło przyjęcia testu. Konfiguracji nie zapisano. Rodzaj błędu: '+type(exc).__name__)
        return 1
    finally:
        if smtp:
            try:smtp.close()
            except Exception:pass
    config={'user':MAILBOX,'password':password,'verified':True,'tested_at':datetime.now(timezone.utc).isoformat()}
    fd,name=tempfile.mkstemp(dir=str(DIRECTORY),prefix='.smtp-')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(config,f,ensure_ascii=False)
            f.flush();os.fsync(f.fileno())
        os.chmod(name,0o600);os.chown(name,10001,10001)
        os.replace(name,DIRECTORY/'smtp.json')
    finally:
        if os.path.exists(name):os.unlink(name)
        password='';config.clear()
    print('Serwer SMTP OVH przyjął wiadomość testową. Sprawdź jej odbiór w skrzynce, również w folderze Spam.')
    print('Wysyłka formularza jest aktywna. Odśwież stronę Opisz projekt: przycisk zmieni się na Wyślij.')
    return 0

if __name__=='__main__':raise SystemExit(main())
