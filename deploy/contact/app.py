"""Private WSGI service for the portfolio contact form.
Fixed sender/recipient; no attachments, open relay, automatic replies or stored messages.
Public access is through the portfolio nginx /api/contact routes only.
"""
from contextlib import closing
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formatdate, make_msgid
from pathlib import Path
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import smtplib
import socket
import sqlite3
import ssl
import time
import uuid

ORIGIN = 'https://maciejgryziec.pl'
MAILBOX = 'kontakt@maciejgryziec.pl'
MAX_BYTES = 32768
FIELDS = {'imie':120,'email':180,'firma':180,'telefon':50,'typ':200,
          'dzis':2500,'problem':1500,'narzedzia':500,'uzytkownicy':100,'budzet':100,'efekt':1000}
REQUIRED = {'imie','email','typ','dzis','problem'}
LABELS = {'imie':'Imię i nazwisko','email':'E-mail','firma':'Firma','telefon':'Telefon',
          'typ':'Typ projektu','dzis':'Obecny sposób pracy','problem':'Największy problem',
          'narzedzia':'Używane programy','uzytkownicy':'Liczba użytkowników',
          'budzet':'Orientacyjny budżet','efekt':'Oczekiwany efekt'}
EMAIL_RE = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}\Z")
log = logging.getLogger('contact')

class Invalid(Exception):
    pass

class DeliveryUnknown(Exception):
    pass


def validate(body):
    if not isinstance(body, dict) or set(body) - set(FIELDS) - {'token','request_id','website'}:
        raise Invalid('Nieprawidłowy format formularza.')
    data = {}
    for name, limit in FIELDS.items():
        value = body.get(name, '')
        if not isinstance(value, str) or len(value) > limit or any(ord(c)<32 and c not in '\n\t\r' for c in value):
            raise Invalid('Sprawdź długość i treść pól formularza.')
        value = value.strip()
        if name in REQUIRED and not value:
            raise Invalid('Uzupełnij wymagane pola.')
        data[name] = value
    if '\r' in data['email'] or '\n' in data['email'] or not EMAIL_RE.fullmatch(data['email']):
        raise Invalid('Podaj prawidłowy adres e-mail.')
    local, domain = data['email'].rsplit('@', 1)
    if len(local)>64 or local.startswith('.') or local.endswith('.') or '..' in local or '..' in domain or any(x.startswith('-') or x.endswith('-') for x in domain.split('.')):
        raise Invalid('Podaj prawidłowy adres e-mail.')
    if not isinstance(body.get('website', ''), str) or body.get('website', '').strip():
        raise Invalid('Nie udało się zweryfikować formularza.')
    try:
        request_id = str(uuid.UUID(body['request_id']))
    except (KeyError, ValueError, TypeError, AttributeError):
        raise Invalid('Odśwież formularz i spróbuj ponownie.')
    if request_id != body.get('request_id'):
        raise Invalid('Nieprawidłowy identyfikator formularza.')
    return data, request_id


def smtp_config(path):
    try:
        cfg = json.loads(Path(path).read_text())
        if cfg.get('verified') is not True or cfg.get('user') != MAILBOX or not isinstance(cfg.get('password'), str) or not cfg['password']:
            return None
        return cfg
    except (OSError, ValueError, TypeError):
        return None


def deliver(data, request_id, cfg):
    """Only an SMTP 250 acceptance is reported as sent. No automatic retry."""
    message = EmailMessage(policy=SMTP)
    message['From'] = 'Formularz maciejgryziec.pl <' + MAILBOX + '>'
    message['To'] = MAILBOX
    message['Reply-To'] = data['email']
    message['Subject'] = 'Nowe zapytanie ze strony maciejgryziec.pl'
    message['Date'] = formatdate(localtime=False)
    message['Message-ID'] = make_msgid(idstring=request_id, domain='maciejgryziec.pl')
    message['Auto-Submitted'] = 'auto-generated'
    lines = ['Zapytanie z formularza na maciejgryziec.pl', 'Identyfikator: '+request_id, '']
    for key in FIELDS:
        lines.extend([LABELS[key]+':', data[key] or 'nie podano', ''])
    lines.append('Odpowiedz na tę wiadomość, aby napisać do zgłaszającego. Nie otwieraj niezaufanych odnośników z treści.')
    message.set_content('\n'.join(lines))
    # Host and port are fixed; form data cannot change SMTP or recipient.
    sending = False
    accepted = False
    server = None
    try:
        server = smtplib.SMTP_SSL('smtp.mail.ovh.net', 465, context=ssl.create_default_context(), timeout=12)
        server.login(MAILBOX, cfg['password'])
        sending = True
        refused = server.send_message(message, from_addr=MAILBOX, to_addrs=[MAILBOX])
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)
        accepted = True
    except (smtplib.SMTPRecipientsRefused, smtplib.SMTPDataError, smtplib.SMTPSenderRefused, smtplib.SMTPAuthenticationError):
        raise
    except (socket.timeout, TimeoutError, ConnectionError, OSError, smtplib.SMTPServerDisconnected) as exc:
        if sending and not accepted:
            raise DeliveryUnknown() from exc
        raise
    finally:
        if server is not None:
            # A failed QUIT must never turn an accepted message into a retry.
            try:
                server.close()
            except Exception:
                pass


class Contact:
    def __init__(self, database, signing_key, config, sender=deliver, clock=time.time):
        self.database, self.key, self.config, self.sender, self.clock = str(database), signing_key, config, sender, clock
        if len(self.key)<32:
            raise ValueError('A private signing key of at least 32 bytes is required.')
        Path(database).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.database)) as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                client TEXT NOT NULL, created REAL NOT NULL, status TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS attempts_client ON attempts(client,created);
            CREATE TABLE IF NOT EXISTS tokens(client TEXT NOT NULL, created REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS tokens_client ON tokens(client,created);
            ''')
        os.chmod(self.database, 0o600)

    def digest(self, text):
        return hmac.new(self.key, text.encode('utf-8'), hashlib.sha256).hexdigest()

    def token(self, client):
        data = str(int(self.clock()))+'.'+secrets.token_hex(16)
        return data+'.'+self.digest('token:'+client+':'+data)

    def verify_token(self, client, token):
        if not isinstance(token,str) or len(token)>180:
            return False
        try:
            ts, nonce, signature = token.split('.')
            age = self.clock()-int(ts)
            return 2 <= age <= 3600 and bool(re.fullmatch('[a-f0-9]{32}',nonce)) and hmac.compare_digest(signature,self.digest('token:'+client+':'+ts+'.'+nonce))
        except (ValueError,TypeError):
            return False

    def respond(self, start, status, data, extra=()):
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        start(status, [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(payload))),
                      ('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('X-Robots-Tag','noindex')]+list(extra))
        return [payload]

    def __call__(self, environ, start):
        try:
            return self.handle(environ, start)
        except Exception as exc:
            # Never log form contents, email, raw IP or credentials.
            log.error('contact_internal_error type=%s', type(exc).__name__)
            return self.respond(start,'503 Service Unavailable',{'ok':False,'code':'unavailable','message':'Wysyłka jest chwilowo niedostępna. Zachowaj opis i napisz na '+MAILBOX+'.'})

    def handle(self, env, start):
        method, path = env.get('REQUEST_METHOD',''), env.get('PATH_INFO','')
        config = smtp_config(self.config)
        if path == '/healthz' and method == 'GET':
            with closing(sqlite3.connect(self.database, timeout=5)) as db:
                db.execute('DELETE FROM attempts WHERE created<?', (self.clock()-172800,))
                db.execute('DELETE FROM tokens WHERE created<?', (self.clock()-3600,))
                db.commit()
            return self.respond(start,'200 OK',{'ok':True,'ready':config is not None})
        if path not in ('/api/contact/session','/api/contact'):
            return self.respond(start,'404 Not Found',{'ok':False})
        if env.get('HTTP_SEC_FETCH_SITE') not in (None,'same-origin','none'):
            return self.respond(start,'403 Forbidden',{'ok':False,'message':'Otwórz formularz na maciejgryziec.pl.'})
        if method == 'POST' and (env.get('HTTP_ORIGIN') != ORIGIN or env.get('HTTP_X_CONTACT_FORM') != '1'):
            return self.respond(start,'403 Forbidden',{'ok':False,'message':'Otwórz formularz na maciejgryziec.pl.'})
        if method == 'GET' and env.get('HTTP_ORIGIN') not in (None, ORIGIN):
            return self.respond(start,'403 Forbidden',{'ok':False})
        # nginx overwrites this header using a trusted client address, never form input.
        raw_ip = env.get('HTTP_X_CONTACT_CLIENT_IP') or env.get('REMOTE_ADDR','')
        try:
            ip = str(ipaddress.ip_address(raw_ip))
        except ValueError:
            return self.respond(start,'400 Bad Request',{'ok':False})
        client = self.digest('ip:'+ip)
        now = self.clock()
        if path == '/api/contact/session' and method == 'GET':
            if config is None:
                return self.respond(start,'200 OK',{'ready':False})
            with closing(sqlite3.connect(self.database, timeout=5)) as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('DELETE FROM tokens WHERE created<?',(now-3600,))
                if db.execute('SELECT count(*) FROM tokens WHERE client=?',(client,)).fetchone()[0]>=40:
                    db.rollback()
                    return self.respond(start,'429 Too Many Requests',{'ok':False,'message':'Odczekaj chwilę przed kolejną próbą.'},[('Retry-After','300')])
                db.execute('INSERT INTO tokens VALUES (?,?)',(client,now));db.commit()
            return self.respond(start,'200 OK',{'ready':True,'token':self.token(client),'expires_in':3600})
        if path != '/api/contact' or method != 'POST':
            return self.respond(start,'405 Method Not Allowed',{'ok':False},[('Allow','POST' if path=='/api/contact' else 'GET')])
        if config is None:
            return self.respond(start,'503 Service Unavailable',{'ok':False,'code':'unavailable','message':'Wysyłka jest chwilowo niedostępna. Napisz na '+MAILBOX+'.'})
        if env.get('CONTENT_TYPE','').split(';')[0].strip().lower() != 'application/json':
            return self.respond(start,'415 Unsupported Media Type',{'ok':False})
        try:
            length = int(env.get('CONTENT_LENGTH','0'))
        except ValueError:
            length = 0
        if not 0 < length <= MAX_BYTES:
            return self.respond(start,'413 Payload Too Large',{'ok':False,'message':'Wiadomość jest zbyt długa.'})
        raw = env['wsgi.input'].read(length)
        if len(raw) != length:
            return self.respond(start,'400 Bad Request',{'ok':False})
        try:
            body = json.loads(raw.decode('utf-8'))
            data, request_id = validate(body)
        except (ValueError, UnicodeError, Invalid) as exc:
            message = str(exc) if isinstance(exc,Invalid) else 'Sprawdź formularz i spróbuj ponownie.'
            return self.respond(start,'400 Bad Request',{'ok':False,'code':'validation','message':message})
        if not self.verify_token(client,body.get('token')):
            return self.respond(start,'400 Bad Request',{'ok':False,'code':'token','message':'Odśwież weryfikację formularza i spróbuj za kilka sekund.'})
        fingerprint = self.digest('data:'+json.dumps(data,sort_keys=True,ensure_ascii=False))
        with closing(sqlite3.connect(self.database,timeout=5)) as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM attempts WHERE created<?',(now-172800,))
            old = db.execute('SELECT fingerprint,status FROM attempts WHERE id=?',(request_id,)).fetchone()
            if old:
                db.rollback()
                if old[0] != fingerprint:
                    return self.respond(start,'409 Conflict',{'ok':False,'code':'changed','message':'Treść formularza zmieniła się. Przygotuj nową próbę.'})
                if old[1] == 'sent':
                    return self.respond(start,'200 OK',{'ok':True,'status':'sent','request_id':request_id})
                return self.respond(start,'409 Conflict',{'ok':False,'code':'previous_attempt','message':'Ta próba była już obsługiwana. Nie wysyłaj duplikatu. W razie wątpliwości napisz bezpośrednio na '+MAILBOX+'.'})
            recent = db.execute('SELECT count(*) FROM attempts WHERE client=? AND created>?',(client,now-600)).fetchone()[0]
            daily = db.execute('SELECT count(*) FROM attempts WHERE client=? AND created>?',(client,now-86400)).fetchone()[0]
            total = db.execute('SELECT count(*) FROM attempts WHERE created>?',(now-86400,)).fetchone()[0]
            if recent>=3 or daily>=12 or total>=60:
                db.rollback()
                return self.respond(start,'429 Too Many Requests',{'ok':False,'code':'rate','message':'Limit wysyłki został osiągnięty. Spróbuj później lub napisz bezpośrednio na '+MAILBOX+'.'},[('Retry-After','600')])
            db.execute('INSERT INTO attempts VALUES (?,?,?,?,?)',(request_id,fingerprint,client,now,'sending'));db.commit()
        try:
            self.sender(data,request_id,config)
            state='sent'
        except DeliveryUnknown:
            state='unknown'
        except Exception as exc:
            log.warning('contact_delivery_failed id=%s type=%s',request_id,type(exc).__name__)
            state='failed'
        with closing(sqlite3.connect(self.database,timeout=5)) as db:
            db.execute('UPDATE attempts SET status=? WHERE id=?',(state,request_id));db.commit()
        if state == 'sent':
            return self.respond(start,'200 OK',{'ok':True,'status':'sent','request_id':request_id})
        if state == 'unknown':
            return self.respond(start,'503 Service Unavailable',{'ok':False,'code':'delivery_unknown','message':'Nie udało się potwierdzić wysyłki. Nie ponawiaj jej od razu, aby uniknąć duplikatu. Zachowaj opis i skontaktuj się bezpośrednio.'})
        return self.respond(start,'503 Service Unavailable',{'ok':False,'code':'delivery_failed','message':'Wiadomość nie została wysłana. Zachowaj opis i napisz na '+MAILBOX+'.'})

_app = None

def application(environ, start_response):
    global _app
    if _app is None:
        _app = Contact(os.getenv('CONTACT_DB','/data/contact.sqlite3'),
                       Path(os.getenv('CONTACT_KEY_FILE','/run/contact/signing.key')).read_bytes(),
                       os.getenv('CONTACT_CONFIG','/run/contact/smtp.json'))
    return _app(environ,start_response)
