import concurrent.futures
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid
from app import Contact, DeliveryUnknown, MAILBOX, ORIGIN, deliver


class FormTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.cfg=self.root/'smtp.json'
        self.cfg.write_text(json.dumps({'verified':True,'user':MAILBOX,'password':'unit-test-placeholder'}))
        self.now=100000.0
        self.sent=[]
        self.app=Contact(self.root/'data.sqlite',b'x'*32,self.cfg,sender=lambda *args:self.sent.append(args),clock=lambda:self.now)
        self.client=self.app.digest('ip:192.0.2.1')

    def tearDown(self):
        self.tmp.cleanup()

    def body(self):
        token=self.app.token(self.client)
        self.now+=3
        return {'imie':'Osoba testowa','email':'visitor@example.org','typ':'Aplikacja',
                'dzis':'Opis pracy','problem':'Ręczne czynności','request_id':str(uuid.uuid4()),'token':token,'website':''}

    def call(self,body=None,method='POST',path='/api/contact',**headers):
        raw=json.dumps(body,ensure_ascii=False).encode() if body is not None else b''
        env={'REQUEST_METHOD':method,'PATH_INFO':path,'CONTENT_TYPE':'application/json',
             'CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw),'REMOTE_ADDR':'192.0.2.1',
             'HTTP_ORIGIN':ORIGIN,'HTTP_X_CONTACT_FORM':'1','HTTP_SEC_FETCH_SITE':'same-origin'}
        env.update(headers)
        status=[]
        result=b''.join(self.app(env,lambda s,h:status.append((s,dict(h)))))
        return status[0][0],json.loads(result),status[0][1]

    def test_send_and_no_duplicate(self):
        b=self.body()
        for _ in range(2):
            s,r,h=self.call(b);self.assertTrue(s.startswith('200'));self.assertEqual(r['status'],'sent');self.assertEqual(h['Cache-Control'],'no-store')
        self.assertEqual(len(self.sent),1)

    def test_reused_key_changed_data(self):
        b=self.body();self.call(b);b['dzis']='Zmieniona treść'
        self.assertTrue(self.call(b)[0].startswith('409'));self.assertEqual(len(self.sent),1)

    def test_validation(self):
        for field,value in [('email','a@example.org\r\nBcc: other@example.org'),('email','x@@example.org'),
                            ('email','a..b@example.org'),('email','bad@-example.org'),('imie',''),
                            ('dzis','x'*2501),('problem',[]),('website','https://spam.example'),('request_id','not-a-uuid')]:
            with self.subTest(field=field,value=str(value)[:30]):
                b=self.body();b[field]=value
                self.assertTrue(self.call(b)[0].startswith('400'))
        self.assertEqual(self.sent,[])

    def test_cross_origin_and_simple_requests(self):
        b=self.body()
        for headers in ({'HTTP_ORIGIN':'https://untrusted.example'},{'HTTP_ORIGIN':''},
                        {'HTTP_X_CONTACT_FORM':''},{'HTTP_SEC_FETCH_SITE':'cross-site'}):
            with self.subTest(headers=headers):self.assertTrue(self.call(b,**headers)[0].startswith('403'))
        self.assertTrue(self.call(b,CONTENT_TYPE='text/plain')[0].startswith('415'))
        self.assertTrue(self.call(b,method='GET')[0].startswith('405'))
        self.assertEqual(self.sent,[])

    def test_unknown_fields(self):
        for k in ['to','from','smtp_host','attachment','bcc']:
            b=self.body();b[k]='attacker@example.org';self.assertTrue(self.call(b)[0].startswith('400'))
        self.assertEqual(self.sent,[])

    def test_body_limits(self):
        self.assertTrue(self.call(self.body(),CONTENT_LENGTH='32769')[0].startswith('413'))
        self.assertTrue(self.call(self.body(),CONTENT_LENGTH='0')[0].startswith('413'))
        self.assertTrue(self.call(self.body(),CONTENT_LENGTH='oops')[0].startswith('413'))

    def test_token_time_tampering_and_address(self):
        b=self.body();b['token']='invalid';self.assertTrue(self.call(b)[0].startswith('400'))
        b=self.body();self.now+=3601;self.assertTrue(self.call(b)[0].startswith('400'))
        b=self.body();self.assertTrue(self.call(b,REMOTE_ADDR='192.0.2.8')[0].startswith('400'))
        b=self.body();b['token']=self.app.token(self.client);self.assertTrue(self.call(b)[0].startswith('400'))
        self.assertEqual(self.sent,[])

    def test_unconfigured_never_success(self):
        self.cfg.unlink()
        self.assertTrue(self.call(self.body())[0].startswith('503'))
        s,r,_=self.call(method='GET',path='/api/contact/session');self.assertFalse(r['ready'])
        self.assertEqual(self.sent,[])

    def test_session_and_rate_limits(self):
        s,r,_=self.call(method='GET',path='/api/contact/session');self.assertTrue(r['ready']);self.assertIn('token',r)
        for _ in range(3):self.assertTrue(self.call(self.body())[0].startswith('200'))
        self.assertTrue(self.call(self.body())[0].startswith('429'))
        self.assertEqual(len(self.sent),3)

    def test_no_message_content_or_raw_ip_stored(self):
        b=self.body();self.call(b)
        db=sqlite3.connect(self.app.database)
        dump='\n'.join(db.iterdump());db.close()
        for forbidden in ['192.0.2.1',b['email'],b['imie'],b['dzis'],b['problem'],'unit-test-placeholder']:
            self.assertNotIn(forbidden,dump)

    def test_known_and_ambiguous_failure_not_reported_sent(self):
        for exc,code in [(OSError('test'),'delivery_failed'),(DeliveryUnknown(),'delivery_unknown')]:
            def fail(*_):raise exc
            self.app.sender=fail
            s,r,_=self.call(self.body());self.assertTrue(s.startswith('503'));self.assertEqual(r['code'],code);self.assertFalse(r['ok'])

    def test_parallel_duplicate_sends_only_once(self):
        def sender(*args):time.sleep(.05);self.sent.append(args)
        self.app.sender=sender;b=self.body()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(lambda _:self.call(b),range(4)))
        self.assertEqual(len(self.sent),1)
        self.assertTrue(any(r[0].startswith('200') for r in result))
        self.assertTrue(all(r[0].startswith(('200','409')) for r in result))

    def test_fixed_recipients_reply_to_and_plaintext(self):
        data={k:'' for k in ['imie','email','firma','telefon','typ','dzis','problem','narzedzia','uzytkownicy','budzet','efekt']}
        data.update(email='visitor@example.org',imie='Test',dzis='<script>alert(1)</script>')
        with patch('app.smtplib.SMTP_SSL') as smtp:
            smtp.return_value.send_message.return_value={}
            deliver(data,str(uuid.uuid4()),{'password':'unit-test-placeholder'})
            args=smtp.return_value.send_message.call_args
            msg=args.args[0]
            self.assertEqual(args.kwargs['to_addrs'],[MAILBOX]);self.assertEqual(args.kwargs['from_addr'],MAILBOX)
            self.assertEqual(msg['Reply-To'],'visitor@example.org');self.assertEqual(msg.get_content_type(),'text/plain')
            self.assertNotIn('Bcc',msg)

if __name__=='__main__':unittest.main(verbosity=2)
