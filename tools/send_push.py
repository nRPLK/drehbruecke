"""Schickt einmal am Tag Erinnerungen an Spieler, die Push erlaubt haben.
Läuft als GitHub Action. Braucht das Secret FIREBASE_SA (Service-Account-JSON aus der Firebase-Konsole)."""
import json, os, time, urllib.request
from google.oauth2 import service_account
from google.auth.transport.requests import Request

DB = os.environ.get('FIREBASE_DB', 'https://drehbruecke-default-rtdb.europe-west1.firebasedatabase.app')
GAME = 'https://nrplk.github.io/drehbruecke/'
sa = json.loads(os.environ['FIREBASE_SA'])
cred = service_account.Credentials.from_service_account_info(sa, scopes=[
    'https://www.googleapis.com/auth/firebase.database', 'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/firebase.messaging'])
cred.refresh(Request()); TOK = cred.token

def req(url, data=None, method=None):
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, method=method,
                               headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(r) as f: return json.loads(f.read() or 'null')

TXT = {'de': {'daily': ('🎁 Deine Tagesbelohnung wartet!', 'Hol dir deine Münzen und halte deine Serie am Leben 🔥'),
              'away': ('🌉 Die Brücke vermisst dich!', 'Komm zurück – ein Willkommens-Geschenk wartet auf dich 🎁'),
              'league': ('🏅 Die Liga-Woche endet heute!', 'Noch eine Runde für den Aufstieg?'),
              'duel': ('⚔️ Du wurdest herausgefordert!', '{n} wartet auf dein Duell.')},
       'en': {'daily': ('🎁 Your daily reward is waiting!', 'Grab your coins and keep your streak alive 🔥'),
              'away': ('🌉 The bridge misses you!', 'Come back – a welcome gift is waiting 🎁'),
              'league': ('🏅 The league week ends today!', 'One more run for promotion?'),
              'duel': ('⚔️ You have been challenged!', '{n} is waiting for your duel.')}}

now = time.time() * 1000; H = 3600e3
subs = req(DB + '/push.json') or {}
duels = req(DB + '/duels.json') or {}
open_duel = {}
for d in duels.values():
    if isinstance(d, dict) and d.get('bl') and 'sb' not in d and now - d.get('t', 0) < 48 * H:
        open_duel[d['bl']] = d.get('a', '?')
sunday = time.gmtime().tm_wday == 6
sent = 0
for dev, s in subs.items():
    if not isinstance(s, dict) or not s.get('tk'): continue
    ls, last = s.get('ls', 0), s.get('sent', 0)
    if now - last < 20 * H: continue          # höchstens 1× am Tag
    lang = 'en' if s.get('l') == 'en' else 'de'; kind = None; me = (s.get('n') or '').strip().lower()
    if me and me in open_duel: kind = 'duel'
    elif now - ls > 30 * 24 * H: continue      # nach 30 Tagen nicht mehr nerven
    elif now - ls > 72 * H: kind = 'away'
    elif sunday and now - ls > 12 * H: kind = 'league'
    elif now - ls > 20 * H: kind = 'daily'
    if not kind: continue
    t, b = TXT[lang][kind]; b = b.format(n=open_duel.get(me, ''))
    try:
        req(f"https://fcm.googleapis.com/v1/projects/{sa['project_id']}/messages:send", {'message': {
            'token': s['tk'], 'notification': {'title': t, 'body': b},
            'webpush': {'fcm_options': {'link': GAME}}, 'data': {'url': GAME}}})
        req(f'{DB}/push/{dev}/sent.json', now, 'PUT'); sent += 1
    except urllib.error.HTTPError as e:
        if e.code in (400, 404): req(f'{DB}/push/{dev}.json', method='DELETE')   # Token ungültig → entfernen
print('gesendet:', sent)
