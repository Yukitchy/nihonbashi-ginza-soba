#!/usr/bin/env python3
"""Builds index.html (page, Dec-10 design) and the A4-landscape one-page PDF/PNG.
Run with /usr/local/bin/python3 (has playwright). Needs Pillow, qrcode."""
import io, os, re, json, base64, html, tempfile
import qrcode
from maplib import render, foot, CACHE

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
URL = 'https://yukitchy.github.io/nihonbashi-ginza-soba/'
TITLE = 'Nihonbashi to Ginza: Soba, Sweets and Strolls'
CR = json.load(open('credits.json'))

# ---- stops: n -> (name, jp, lat, lon). Coordinates: OSM Nominatim; Megumiya & LOBOS placed from street address (approx, +-60 m)
P = {1: ('Mitsukoshimae Stn', '三越前駅', 35.68499, 139.77154), 2: ('Nihonbashi Bridge', '日本橋', 35.68413, 139.77440),
     3: ('Sobayoshi', 'そばよし', 35.68535, 139.77656), 4: ('Sembikiya', '千疋屋', 35.68685, 139.77333),
     5: ('Megumiya', '恵み屋', 35.6757, 139.7697), 6: ('Art Aquarium', 'アートアクアリウム', 35.67138, 139.76570),
     7: ('GINZA SIX', '銀座 蔦屋書店', 35.66953, 139.76404), 8: ('Wako', '和光', 35.67173, 139.76500),
     9: ('LOBOS', 'ロボス', 35.6700, 139.7668), 'H': ('Hakuhinkan', '博品館', 35.66792, 139.76095)}
ll = lambda k: (P[k][2], P[k][3])

# ---- content (E = English text, J = Japanese small add-on). scout = GUIDE SCOUT spot
STOPS = [
 dict(n=2, t='15:05', end='15:10', scout=True, title='NIHONBASHI BRIDGE & ROAD ORIGIN', jp='日本橋・日本国道路元標', genre='Photo stop',
      img='hero', alt='Nihonbashi Bridge with the expressway above it', co='hero',
      tx='The stone bridge that started it all: in the Edo period every highway in Japan was measured from here, and the Japan Road Origin marker still sits at the centre of the bridge. Look up and you see the expressway built right over it. A five-minute photo stop; the second photo shows the Japan Road Origin plaque.',
      hrs='Always open · outdoors', note='GUIDE SCOUT: check the best photo angle, how busy the pavement is, and how easy the marker is to find.', q='Nihonbashi+Bridge+Tokyo', img2='origin', alt2='The Japan Road Origin plaque', co2='origin'),
 dict(n=3, t='15:15', end='15:45', title='SOBAYOSHI', jp='そばよし 日本橋本店', genre='Soba · late lunch',
      img='soba2', alt='Example photo: a bowl of soba in broth', co='soba2', example=True,
      tx='A quick counter soba shop run by an Edo-period bonito-flake wholesaler. Order soba and a bowl of rice, then shake as much freshly shaved bonito powder over the rice as you like: okaka gohan, the shop\'s signature. Bring an appetite; this is the proper lunch of the day.',
      hrs='Weekdays 7:30-20:00 · closed Saturday, Sunday and holidays (Yahoo! News Japan review, checked 12 Nov 2026)', q='Sobayoshi+Nihonbashi+Honcho'),
 dict(n=4, t='15:50', end='16:15', title='SEMBIKIYA SOHONTEN FRUIT PARLOR', jp='千疋屋総本店 日本橋本店', genre='Fruit parfait break',
      img='parfait', alt='A melon parfait at Sembikiya', co='parfait', img2='sembikiya', alt2='The Sembikiya shop front in Nihonbashi', co2='sembikiya',
      tx='The old fruit house of Nihonbashi, and its parlor on the 2nd floor of Nihonbashi Mitsui Tower. Order the fruit parfait of the season and sit down for 25 minutes: soft seats, good fruit, a break before the second soba.',
      hrs='11:00-21:00 (last order 20:30) · Nihonbashi Mitsui Tower 2F (ikyu and Gurunavi listings, checked 12 Nov 2026)', q='Sembikiya+Sohonten+Nihonbashi'),
 dict(n=5, t='16:35', end='16:55', warn=True, title='KYOBASHI MEGUMIYA', jp='京橋 恵み屋', genre='Soba · second bowl, light',
      img='soba5', alt='Example photo: cold soba on a bamboo tray', co='soba5', example=True,
      tx='A standing soba counter in Kyobashi known for 100%-buckwheat (juwari) noodles at a low price, with no fried food on the menu. A small bowl is enough: this is the light second round.',
      hrs='CHECK BEFORE GOING: Megumiya is reported to be lunch only, 11:00-15:00, closed Saturday, Sunday and holidays (shop Instagram and sobadb, checked 12 Nov 2026). The 16:35 slot may not work: call 03-3272-8616.', q='Kyobashi+Megumiya+soba'),
 dict(n=6, t='17:10', end='17:25', scout=True, title='ART AQUARIUM MUSEUM GINZA', jp='アートアクアリウム美術館 GINZA', genre='Goldfish art · research only',
      img='aqua', alt='Photo of an earlier Art Aquarium exhibition (goldfish in lit tanks)', co='aqua', example=True, exlabel='Photo: an earlier Art Aquarium exhibition, not this venue.',
      img2='mitsukoshi', alt2='Ginza Mitsukoshi, the building that houses the museum', co2='mitsukoshi',
      tx='A museum of goldfish in lit, sculpted tanks, inside Ginza Mitsukoshi. We do not go in: a 15-minute look only, to check the entrance, the ticket counter and how crowded it feels at this hour. The current show, the Ginza Goldfish Hyakka exhibition, runs until 6 January 2027.',
      hrs='10:00-19:00 · last entry 18:00 (Fashionsnap, 1 Oct 2026; may close irregularly for maintenance)', note='GUIDE SCOUT: entrance, ticket price and queue, crowd level at 17:10, English signs.', q='Art+Aquarium+Museum+GINZA'),
 dict(n=7, t='17:35', end='18:00', scout=True, title='TSUTAYA BOOKS & ROOFTOP GARDEN', jp='銀座 蔦屋書店 / GINZA SIX 屋上庭園', genre='Bookstore · rooftop garden',
      img='tsutaya', alt='Inside Ginza Tsutaya Books', co='tsutaya', img2='roof', alt2='The rooftop garden of GINZA SIX', co2='roof',
      tx='Tsutaya Books on the 6th floor of GINZA SIX: art and design books, magazines, a long hall made for browsing. Then up to the rooftop garden, about 4,000 m2 of open green space on top of the mall, with the city around it. Spend 20 minutes inside and the last few on the roof.',
      hrs='Tsutaya 10:30-21:00 (rurubu listing, checked 12 Nov 2026) · Rooftop garden hours: check on the day, it is outdoors', note='GUIDE SCOUT: rooftop access, view, quiet level, how it feels for a tour group at dusk.', q='Ginza+Tsutaya+Books'),
 dict(n=8, t='18:10', end='18:15', scout=True, title='WAKO CLOCK TOWER', jp='和光 時計塔', genre='Photo stop · Ginza crossing',
      img='wako', alt='The Wako building and clock tower at the Ginza crossing', co='wako',
      tx='The clock tower of the Wako building is the postcard view of Ginza. We pass it on the way to dinner: stand on the corner of the Ginza 4-chome crossing, take the photo, keep walking.',
      hrs='Always visible · outdoors', note='GUIDE SCOUT: best corner for a group photo and how crowded the crossing is.', q='Wako+Ginza+Clock+Tower'),
 dict(n=9, t='18:25', end='', title='LOBOS GINZA, DINNER 18:30', jp='LOBOS 銀座 スペイン料理&ワイン', genre='Dinner · booked',
      img=None, tx='Spanish food and wine, a few minutes\' walk from the Ginza crossing towards Higashi-Ginza. Table booked for 18:30; we arrive at 18:25. Address: Ginza 4-9-6, Mihara-bashi Building 1F.',
      hrs='Dinner from 17:00; closing days listed differently by Retty and ikyu, so the booking is the thing that matters. Tel 03-5148-2688 (ikyu).', q='LOBOS+Ginza'),
]
BONUS = dict(n='+', title='HAKUHINKAN TOY PARK', jp='博品館 TOY PARK', genre='Only if we are ahead of time',
             img='toy', alt='The Hakuhinkan building in Ginza', co='toy',
             tx='A big toy store in Ginza 8-chome, about five minutes west of GINZA SIX: the opposite way from dinner. We go only if we leave the rooftop early; otherwise it is a wave from the pavement.',
             hrs='Opening hours: not checked, see the shop site', q='Hakuhinkan+Toy+Park')


# ---- EXTRA STOPS: optional detours, not on the main timeline. g = area group. ph=None -> no free photo exists
EXTRA = [
 dict(k='A', g='Near the start', title='HAMANOYA PARLOR', jp='はまの屋パーラー 日本橋本店', ph=None, short='Egg sandwich',
      tx='A classic-style kissaten in the basement of the Yagicho Building, one minute from Mitsukoshimae. The egg sandwich follows the first owner\'s recipe; a half-and-half of egg and fruit sandwich is on the menu. A quiet, old-fashioned coffee break before the walk.',
      hrs='9:00-18:00, last order 17:30 · Nihonbashi Muromachi 1-7-2, B1F · Closed days not confirmed: check on the day', src='Time Out Tokyo, 20 Nov 2023 article, read 12 Nov 2026', q='Hamanoya+Parlor+Nihonbashi', hshort='9:00-18:00'),
 dict(k='A', g='Near the start', title='NINBEN NIHONBASHI', jp='にんべん 日本橋本店', ph=None, short='Bonito flakes',
      tx='A bonito-flake house from the Edo period, on the ground floor of COREDO Muromachi 1. Buy a pack of freshly shaved flakes or dashi packs: light, cheap, easy to carry home, and very Japanese. The Dashi-ba counter next door serves bonito broth.',
      hrs='Shop 11:00-19:00 weekdays, 10:30 on weekends · Dashi-ba counter reported 11:00-18:00: check on the day', src='Mitsui Shopping Park COREDO Muromachi store page; san-tatsu.jp', q='Ninben+Nihonbashi+Main+Store', hshort='11:00-19:00'),
 dict(k='A', g='Near the start', title='FUKUTOKU SHRINE & FUKUTOKU NO MORI', jp='福徳神社・福徳の森', ph='fukutoku', short='Shrine + garden',
      tx='A small shrine said to be here since the 9th century, now tucked behind COREDO Muromachi with a little garden beside it. A calm five minutes between the glass towers; the amulet office sells lottery-luck charms and goshuin stamps.',
      hrs='Grounds are outdoors: hours not published, check on the day · Amulet office 10:00-17:00', src='Shrine official site mebuki.jp, read 12 Nov 2026', q='Fukutoku+Shrine+Nihonbashi', hshort='Amulets 10:00-17:00'),
 dict(k='A', g='In Ginza', title='TRICOLORE HONTEN', jp='銀座トリコロール 本店', ph='tricolore', short='Kissaten since 1936',
      tx='A Ginza coffee house open since 1936, with a revolving door at the entrance and a Showa-era room. Order the small, light eclair or the milk coffee: a proper old kissaten stop for a visitor who wants the real thing.',
      hrs='8:00-19:00, last order 18:30; closed Tuesday (Gurunavi). Another listing says no closed day: CHECK ON THE DAY, tel 03-3571-1811 · Ginza 5-9-17', src='Gurunavi r.gnavi.co.jp; san-tatsu.jp (updated Feb 2023)', q='Ginza+Tricolore+Honten', hshort='to 19:00 · Tue? check'),
 dict(k='A', g='In Ginza', title='G. ITOYA', jp='銀座 伊東屋 本店', ph='itoya', short='Stationery flagship',
      tx='Japan\'s best-known stationery store, a 12-floor flagship on Chuo-dori. Pens, notebooks, washi and postcards make easy, light souvenirs, and the staff are used to visitors. There is a cafe on the 12th floor.',
      hrs='Mon-Sat 10:00-20:00, Sun and holidays 10:00-19:00 · No regular closed day · Ginza 2-7-15', src='Itoya official site ito-ya.co.jp (store page and FAQ)', q='G.Itoya+Ginza', hshort='to 20:00 (Sun 19:00)'),
 dict(k='B', g='In Ginza', title='CAFE DE L\'AMBRE', jp='カフェ・ド・ランブル', ph='lambre', short='Coffee only, since 1948',
      tx='A coffee-only shop with the year 1948 on its sign: hand-drip, own roast, aged beans. It is small and serious about coffee, so go for one cup, not a long stay. Ginza 8-chome, on the Hakuhinkan side.',
      hrs='Listings disagree on hours and closed day (Tuesday on HotPepper, Monday on Tabelog): CHECK ON THE DAY, tel 03-3571-1551 · Ginza 8-10-15', src='HotPepper (updated Feb 2020); Tabelog English page', q='Cafe+de+L%27Ambre+Ginza', hshort='check on the day'),
 dict(k='B', g='In Ginza', title='MATSUZAKI SENBEI', jp='銀座 松﨑煎餅 本店', ph=None, short='Rice-cracker gifts',
      tx='A rice-cracker house with a long Ginza history, known for crackers printed with pictures. Light, flat and cheap: a good souvenir. The main store moved in May 2026 to a new place in Ginza 3-chome on the same street.',
      hrs='New store hours and exact address not confirmed: CHECK ON THE DAY (shop tel 03-6264-6703)', src='PR TIMES release on the 7 May 2026 opening', q='Matsuzaki+Senbei+Ginza', hshort='check on the day'),
]
# ---------------------------------------------------------------- credits
def credit(k):
    c = CR[k]; return f'{html.escape(c["artist"] or "unknown")}, {c["license"]}, via <a href="{c["page"]}">Wikimedia Commons</a>'
def credit_txt(k):
    c = CR[k]; return f'{c["artist"] or "unknown"} ({c["license"]})'

# ---------------------------------------------------------------- page
def card(s, bonus=False):
    n = s['n']; tag = '<span class="scout">★ GUIDE SCOUT</span>' if s.get('scout') else ''
    warn = '<p class="warnbox">⚠ Hours to check: this stop may be closed at 16:35, see below.</p>' if s.get('warn') else ''
    imgs = ''
    for im, alt, co in ((s.get('img'), s.get('alt'), s.get('co')), (s.get('img2'), s.get('alt2'), s.get('co2'))):
        if im: imgs += f'<img class="ph" src="img/{im}.jpg" alt="{html.escape(alt)}">'
    cs = [c for c in (s.get('co'), s.get('co2')) if c]; pcs = ' '.join((f'Photo {i+1}: ' if len(cs) > 1 else 'Photo: ') + credit(c) + '.' for i, c in enumerate(cs))
    ex = ' ' + (s.get('exlabel') or 'Photo: example of the dish, not the shop.') if s.get('example') else ''
    note = f'<p class="scoutnote">{s["note"]}</p>' if s.get('note') else ''
    clock = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 4.5V8l2.5 1.8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
    when = f'{s["t"]}' + (f' to {s["end"]}' if s.get('end') else ' arrive') if not bonus else 'If time allows, about 10 minutes'
    return f'''<article class="card{' r' if s.get('warn') else ''}" id="p{n if not bonus else 'b'}">
<div class="hd"><span class="big">{'0'+str(n) if not bonus else '+'}</span><div><span class="genre">{s['genre']}</span><h3>{s['title']}</h3><p class="jp" lang="ja">{s['jp']}</p></div></div>
{tag}{imgs}
<p class="tx">{s['tx']}</p>{note}{warn}
<p class="strip"><span>{clock}<b class="today">{when}</b></span></p>
<p class="hrs">{html.escape(s['hrs'])}</p>
<div class="bt"><a class="btn" href="https://www.google.com/maps/search/?api=1&amp;query={s['q']}">Google Maps <i>&rarr;</i></a></div>
<p class="pcr">{pcs}{ex}</p>
</article>'''


def extra_card(e):
    ph = f'<img class="ph" src="img/{e["ph"]}.jpg" alt="{html.escape(e["title"].title())}">' if e['ph'] else ''
    pc = f'Photo: {credit(e["ph"])}.' if e['ph'] else 'No freely licensed photo exists, so none is shown.'
    return f'''<article class="card x"><div class="hd"><span class="big">{e['k']}</span><div><span class="genre">{e['g']} · {e['short']}</span><h3>{e['title']}</h3><p class="jp" lang="ja">{e['jp']}</p></div></div>
{ph}<p class="tx">{e['tx']}</p><p class="hrs">{html.escape(e['hrs'])}</p><p class="hrs">Source: {html.escape(e['src'])}</p>
<div class="bt"><a class="btn" href="https://www.google.com/maps/search/?api=1&amp;query={e['q']}">Google Maps <i>&rarr;</i></a></div><p class="pcr">{pc}</p></article>'''

def extra_section():
    return '<section><div class="bar"><h2>EXTRA STOPS</h2><span>OPTIONAL</span></div></section><p class="gp">Optional detours, not on the timeline. The 18:25 arrival at LOBOS does not change: pick one or two only if we are ahead of time. A = first choice, B = second choice. Hours marked CHECK ON THE DAY could not be confirmed.</p>' + ''.join(extra_card(e) for e in EXTRA)

TL = [('15:00', 'Start at Mitsukoshimae Station', 'Meet at the station; five minutes on foot to the bridge.', None),
      ('15:05', 'Nihonbashi Bridge &amp; Japan Road Origin', 'Photo stop at the zero point of Japan.', 'p2', True),
      ('15:15', 'Sobayoshi: soba and okaka gohan', 'A late, proper lunch.', 'p3'),
      ('15:50', 'Sembikiya fruit parlor', 'Parfait break, 25 minutes.', 'p4'),
      ('16:35', 'Megumiya, Kyobashi: second soba', 'Light bowl. <b class="wr">Check hours first: may be lunch only.</b>', 'p5'),
      ('17:10', 'Art Aquarium Museum GINZA', 'Look only: entrance, tickets, crowds.', 'p6', True),
      ('17:35', 'Tsutaya Books &amp; GINZA SIX rooftop', 'Books first, then the garden.', 'p7', True),
      ('18:10', 'Wako Clock Tower', 'Photo at the Ginza crossing, on the way.', 'p8', True),
      ('18:25', 'Arrive at LOBOS Ginza', 'Dinner is booked for 18:30; five minutes to spare.', 'p9')]

def tl_li(x):
    t, a, b, href = x[:4]; sc = len(x) > 4 or t in ('17:10', '17:35', '18:10')
    tag = ' <span class="scout s">★ SCOUT</span>' if sc else ''
    a = f'<a href="#{href}">{a}</a>' if href else a
    return f'<li><b>{t}</b><span>{a}{tag}<em>{b}</em></span></li>'

def build_page():
    cards = ''.join(card(s) for s in STOPS) + card(BONUS, True)
    css = open('style-dec10.css').read() if os.path.exists('style-dec10.css') else open('style.css').read()
    extra = '''.scout{display:inline-block;margin:10px 0 0;padding:3px 9px;border:2px solid var(--red);color:var(--red);font:900 12px/1.3 Archivo,sans-serif;letter-spacing:.14em}.scout.s{margin:0 0 0 6px;padding:0 6px;font-size:10px;vertical-align:2px}
.scoutnote{margin:8px 0 0;padding:8px 10px;background:#fff;border-left:5px solid var(--red);font-size:14px}.warnbox{margin:8px 0 0;padding:8px 10px;background:var(--red);color:#fff;font-weight:800;font-size:14px}
.wr{color:var(--red)}.pcr{margin:10px 0 0;font-size:11px;color:#8a867e;line-height:1.5}.pcr a{color:inherit}.mapimg{display:block;width:100%;height:auto;border:4px solid var(--ink);margin-top:10px}
.cred{margin:34px 0 10px;font-size:12px;color:var(--mu);line-height:1.6}.cred h2{font-size:22px;margin:0 0 6px}.cred a{color:inherit}
.card .ph{margin-top:10px}.tl a{color:inherit;text-decoration:none;border-bottom:2px solid #0001}'''
    creds = ''.join(f'<li>{k}: {html.escape(CR[k]["title"][5:])}, {credit(k)}</li>' for k in CR if k not in ('hero',) or True)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{TITLE}</title><meta name="robots" content="noindex,nofollow">
<meta name="description" content="A late-afternoon walk from Mitsukoshimae to Ginza: two soba stops, a fruit parfait, goldfish art, a bookstore, a rooftop garden and dinner at 18:30.">
<meta property="og:title" content="{TITLE}"><meta property="og:description" content="Soba, fruit parfait and a stroll from Nihonbashi to Ginza, 15:00 to dinner at 18:30.">
<meta property="og:type" content="website"><meta property="og:url" content="{URL}"><meta property="og:image" content="{URL}img/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22%3E%3Crect width=%2264%22 height=%2264%22 fill=%22%23D9342B%22/%3E%3C/svg%3E">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Noto+Sans+JP:wght@500;700;900&display=swap" rel="stylesheet">
<style>{css}{extra}</style></head><body>
<div class="col"><div class="top"><span>GUEST GUIDE</span><span class="topr"><span>NIHONBASHI &amp; GINZA &middot; 8 STOPS</span>
<button type="button" class="sharebtn hd-share" id="copyLink" aria-label="Copy link to this page" title="Copy link"><svg class="ic-share" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15V4"/><path d="M7.5 8L12 3.5L16.5 8"/><path d="M5 13v7h14v-7"/></svg><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg></button></span></div>
<h1>Nihonbashi to <em>Ginza</em>: Soba, Sweets &amp; <em class="g">Strolls</em></h1></div>
<div class="col" style="padding:0"><div class="hero"><img src="img/hero.jpg" alt="Nihonbashi Bridge with the expressway above it"><div class="vt" style="font-size:30px"><span class="on">日本橋から銀座へ</span></div></div>
<div class="hb"><span>Weekday afternoon &middot; 15:00 to 18:30</span><b>Start at Mitsukoshimae Station</b></div></div>
<div class="col"><section class="intro e"><p class="ie-for">Guide: Yuuki &middot; 3.5 hours on foot &middot; Dinner booked at 18:30</p>
<div class="ie-blk"><h4><i>01</i>The plan</h4><p>We start at <b class="t">Mitsukoshimae Station, 15:00</b>, photograph Nihonbashi Bridge, and eat soba twice with a parfait in between. Then we walk south through Kyobashi into Ginza: goldfish art, a bookstore, a rooftop garden, the Wako clock tower. Dinner is at <b class="t">LOBOS Ginza, 18:30</b>; we arrive at 18:25.</p></div>
<div class="ie-blk"><h4><i>02</i>What GUIDE SCOUT means</h4><p><span class="scout" style="margin:0">★ GUIDE SCOUT</span> marks the places I am researching for my foreign-visitor tours. At those stops we only look and take notes: entrance, tickets, crowds, photo angles.</p></div>
<div class="ie-blk"><h4><i>03</i>Check before the day</h4><p>It has to be a <b class="t">weekday</b>: Sobayoshi is closed on weekends and holidays. And <b class="t">Megumiya</b> (16:35) is reported to serve lunch only, so call 03-3272-8616 first; if it is closed, we skip it and use the time at the fruit parlor or Hakuhinkan.</p></div></section>
<div class="bar"><h2>THE DAY</h2><span>15:00 &ndash; 18:30</span></div><p class="gp">One plan, in order. Times can breathe a little; the only fixed time is 18:25 at the restaurant door.</p>
<ul class="tl">{''.join(tl_li(x) for x in TL)}</ul>
<p class="gp" style="margin-top:10px">Bonus if we are ahead: <a href="#pb">Hakuhinkan Toy Park</a>, ten minutes, instead of the last part of the rooftop.</p>
<div class="maphd"><h2 class="map">The map</h2></div>
<img class="mapimg" src="img/map1.png" alt="Walking map from Mitsukoshimae to Kyobashi"><img class="mapimg" src="img/map2.png" alt="Walking map from Kyobashi to LOBOS Ginza">
<div class="lg"><span><i></i>Numbers match the stops below</span><span><i class="r"></i>Red line: the walking route; the red circled H is the toy store, only if time allows</span></div>
<section><div class="bar"><h2>THE STOPS</h2><span>2-9</span></div></section>
{cards}
{extra_section()}
<div class="cred"><h2>PHOTO CREDITS</h2><p>All photos are real photographs from Wikimedia Commons. Where no photo of the shop itself is free to use, the card says so and shows an example of the dish instead. LOBOS, Hamanoya Parlor, Ninben and Matsuzaki Senbei have no photo: no freely licensed image exists.</p><ul>{creds}</ul><p>Maps &copy; OpenStreetMap contributors.</p></div></div>
<script>document.getElementById("copyLink").addEventListener("click",function(){{var b=this,u="{URL}";function done(){{b.classList.add("done");setTimeout(function(){{b.classList.remove("done")}},1800)}}function fb(){{var t=document.createElement("textarea");t.value=u;document.body.appendChild(t);t.select();try{{document.execCommand("copy");done()}}catch(e){{}}document.body.removeChild(t)}}if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(u).then(done).catch(fb)}}else{{fb()}}}});</script></body></html>'''

# ---------------------------------------------------------------- maps
def make_maps():
    A = [1, 2, 3, 4, 5]; B = [5, 6, 7, 8, 9]
    pins = lambda ks: [(k, P[k][0], *ll(k)) for k in ks]
    render('img/map1.png', 800, 1180, pins(A), [('foot', foot(ll(1), ll(2))), ('foot', foot(ll(2), ll(3))), ('foot', foot(ll(3), ll(4))), ('foot', foot(ll(4), ll(5)))], [], [])
    render('img/map2.png', 800, 1180, pins(B), [('foot', foot(ll(5), ll(6))), ('foot', foot(ll(6), ll(7))), ('foot', foot(ll(7), ll(8))), ('foot', foot(ll(8), ll(9)))],
           [], [('H', *ll('H'))])

# ---------------------------------------------------------------- one-page PDF
BAND = [('15:00', 'Start · Mitsukoshimae'), ('15:05', '★ Nihonbashi Bridge'), ('15:15', 'Sobayoshi soba'), ('15:50', 'Sembikiya parfait'), ('16:35', 'Megumiya soba ⚠'),
        ('17:10', '★ Art Aquarium'), ('17:35', '★ Tsutaya + Rooftop'), ('18:10', '★ Wako Clock Tower'), ('18:25', 'LOBOS · dinner 18:30')]
ROUTE = [(1, 'Mitsukoshimae Stn 三越前駅', 'Start 15:00'), (2, 'Nihonbashi Bridge 日本橋', '15:05 · ★ SCOUT'), (3, 'Sobayoshi そばよし', '15:15 · Mon-Fri 7:30-20:00'),
         (4, 'Sembikiya 千疋屋総本店', '15:50 · 11:00-21:00'), (5, 'Megumiya 恵み屋', '16:35 · ⚠ lunch only?'), (6, 'Art Aquarium アートアクアリウム', '17:10 · ★ last entry 18:00'),
         (7, 'Tsutaya Books + Rooftop 蔦屋書店', '17:35 · ★ SCOUT'), (8, 'Wako Clock Tower 和光', '18:10 · ★ SCOUT'), (9, 'LOBOS Ginza ロボス', 'Arrive 18:25 · dinner 18:30')]
WALK = {1: 'walk 5 min', 2: 'walk 4 min', 3: 'walk 5 min', 4: 'walk 15 min along Chuo-dori', 5: 'walk 13 min', 6: 'walk 6 min', 7: 'walk 9 min', 8: 'walk 5 min'}

def build_pdf_html():
    b64 = lambda p: 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
    jb = lambda p: 'data:image/jpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
    q = qrcode.make(URL, box_size=6, border=1); bb = io.BytesIO(); q.save(bb, 'PNG'); qr = base64.b64encode(bb.getvalue()).decode()
    band = ''.join(f'<div class="s{" first" if i == 0 else " last" if i == len(BAND) - 1 else ""}"><b>{t}</b>{x.replace("★", "<u>★</u>")}</div>' for i, (t, x) in enumerate(BAND))
    photos = ''.join(f'<div><img src="{jb("img/" + k + ".jpg")}" alt=""></div>' for k in ('hero', 'parfait', 'aqua', 'wako'))
    ex = ''.join(f'<div class="x"><b><u>{e["k"]}</u> {e["title"].title().replace(chr(39)+"S",chr(39)+"s")}</b><span>{e["jp"]}</span><em>{e["short"]} · {e["hshort"]}</em></div>' for e in EXTRA)
    rows = ''
    for n, name, hrs in ROUTE:
        warn = ' w' if n == 5 else ''
        rows += f'<li class="{warn}"><i>{n}</i>{name}<small>{hrs}</small></li>' + (f'<li class="leg"><u></u>{WALK[n]}</li>' if n in WALK else '')
    return f'''<!doctype html><meta charset=utf-8><title>{TITLE}</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Noto+Sans+JP:wght@500;700&display=swap" rel="stylesheet">
<style>@page{{size:A4 landscape;margin:0}}*{{box-sizing:border-box}}html,body{{margin:0;padding:0}}body{{font:11px/1.4 Archivo,"Noto Sans JP",-apple-system,"Hiragino Sans",sans-serif;color:#111}}
article{{width:297mm;height:209mm;padding:6mm 11mm;overflow:hidden;display:flex;flex-direction:column}}
header{{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2.5px solid #111;padding-bottom:4px;gap:14px;flex:none}}
h1{{font:900 31px/1 Archivo;font-stretch:75%;margin:0;white-space:nowrap}}.meta{{text-align:right;font-weight:700;font-size:12.5px}}
.chips span{{display:inline-block;border:1px solid #111;border-radius:12px;padding:0 9px;margin:4px 0 0 5px;font-size:11px}}.chips span.g{{border-color:#e60012;color:#e60012;font-weight:800}}
.ph{{display:grid;grid-template-columns:1.3fr 1fr 1fr 1.1fr;gap:6px;margin-top:6px;height:30mm;flex:none}}.ph div{{min-height:0;overflow:hidden}}.ph img{{display:block;width:100%;height:100%;object-fit:cover}}.ph div:nth-child(2) img{{object-position:50% 25%}}
.band{{display:flex;margin-top:7px;flex:none}}.s{{flex:1;background:#e4e0d2;padding:5px 10px 5px 12px;font-size:9.5px;line-height:1.2;font-weight:600;min-height:14.5mm;clip-path:polygon(0 0,calc(100% - 9px) 0,100% 50%,calc(100% - 9px) 100%,0 100%,9px 50%);margin-right:-4px}}
.s b{{display:block;font-size:15px;font-weight:900}}.s u{{text-decoration:none;color:#e60012;font-weight:900}}.s.first{{background:#e60012;color:#fff;clip-path:polygon(0 0,calc(100% - 9px) 0,100% 50%,calc(100% - 9px) 100%,0 100%)}}.s.last{{background:#111;color:#fff}}
.xs{{margin-top:6px;flex:none;border:1.5px dashed #e60012;padding:3px 6px}}.xs h2{{font-size:11px;margin:0 0 2px}}.xs h2 small{{font:600 9px Archivo;color:#555;margin-left:6px}}.xg{{display:grid;grid-template-columns:repeat(7,1fr);gap:5px}}.x{{font-size:8.5px;line-height:1.2;min-width:0}}.x b{{display:block;font-size:9.5px;font-weight:800}}.x u{{text-decoration:none;color:#e60012}}.x span{{display:block;color:#444;font-weight:500}}.x em{{display:block;font-style:normal;color:#777}}
.low{{display:grid;grid-template-columns:80mm 80mm 1fr;gap:8px;margin-top:6px;flex:1;min-height:0}}
.map{{width:100%;height:100%;object-fit:cover;border:2px solid #111;display:block;min-height:0}}
.side{{display:flex;flex-direction:column;min-height:0}}h2{{font:900 15px Archivo;margin:0 0 2px}}
ul{{list-style:none;margin:0 0 2px;padding:0}}li{{display:flex;align-items:center;gap:6px;margin-bottom:1px;font-size:10.5px;font-weight:700;line-height:1.15}}li small{{margin-left:auto;font-size:9px;font-weight:500;color:#777;text-align:right;white-space:nowrap}}
li.w small{{color:#e60012;font-weight:800}}
li.leg{{margin:0 0 1px 5px;font-size:9.5px;font-weight:600;color:#555;line-height:1.1}}li.leg u{{flex:none;border-left:3px solid #e60012;height:9px;margin-left:8px;margin-right:2px}}
li i{{flex:none;width:18px;height:18px;border-radius:50%;background:#111;color:#fff;font:800 11px/18px Archivo;text-align:center;font-style:normal}}
.note{{font-size:9px;line-height:1.3;font-weight:600;color:#444;margin:2px 0 0}}.note b{{color:#e60012}}.tag{{display:inline-block;border:1.5px solid #e60012;color:#e60012;font:900 8.5px/1.4 Archivo;letter-spacing:.1em;padding:0 4px;margin-right:3px}}
.foot{{display:flex;gap:8px;align-items:center;margin-top:auto;font-size:9px;color:#555;border-top:1px solid #111;padding-top:3px}}.foot img{{width:15mm;height:15mm;flex:none}}.foot p{{margin:0 0 2px}}</style>
<article><header><h1>{TITLE}</h1><div class="meta">Guide: Yuuki · start 15:00 Mitsukoshimae · dinner 18:30<div class="chips"><span>Soba ×2</span><span>Parfait</span><span>Goldfish art</span><span class="g">★ = GUIDE SCOUT</span></div></div></header>
<div class="ph">{photos}</div><div class="band">{band}</div>
<div class="xs"><h2>EXTRA STOPS <small>optional · LOBOS 18:25 unchanged</small></h2><div class="xg">{ex}</div></div>
<div class="low"><img class="map" src="{b64('img/map1.png')}" alt=""><img class="map" src="{b64('img/map2.png')}" alt="">
<div class="side"><h2>Route</h2><ul>{rows}</ul>
<ul><li><i style="background:#fff;color:#e60012;border:2px solid #e60012;line-height:14px">H</i>Hakuhinkan 博品館 toy store<small>only if ahead of time</small></li></ul>
<p class="note"><span class="tag">★ GUIDE SCOUT</span>= spot checked for foreign-visitor tours: look and note only.</p>
<p class="note"><b>Check:</b> weekday only (Sobayoshi closed Sat/Sun/holidays). Megumiya reportedly lunch only: call 03-3272-8616. Bonus if early: Hakuhinkan toy store (H).</p>
<div class="foot"><img src="data:image/png;base64,{qr}"><div><p><b>Full plan, hours and maps:</b> yukitchy.github.io/nihonbashi-ginza-soba</p><p>Photos: Wikimedia Commons (credits on the page). Maps © OpenStreetMap contributors.</p></div></div></div></div></article>'''

def main():
    if not os.path.exists('img/map1.png') or os.environ.get('REMAP'): make_maps()
    open('index.html', 'w').write(build_page())
    from PIL import Image
    im = Image.open('img/hero.jpg').convert('RGB'); w, h = im.size; r = 1200 / 630
    nh = int(w / r); y = max(0, (h - nh) // 2); im.crop((0, y, w, y + nh)).resize((1200, 630)).save('img/og.jpg', quality=85)
    tmp = os.path.join(tempfile.gettempdir(), 'nb-sheet.html'); open(tmp, 'w').write(build_pdf_html())
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1123, 'height': 794}); pg.goto('file://' + tmp); pg.wait_for_load_state('networkidle'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(2500)
        over = pg.evaluate("(()=>{const a=document.querySelector('article'),s=document.querySelector('.side');return [a.scrollHeight>a.clientHeight+1, s.scrollHeight>s.clientHeight+1]})()")
        pg.pdf(path='nihonbashi-ginza-soba.pdf', format='A4', landscape=True, print_background=True, prefer_css_page_size=True)
        pg.screenshot(path='nihonbashi-ginza-soba.png', full_page=False); b.close()
    d = open('nihonbashi-ginza-soba.pdf', 'rb').read()
    print('pages', len(re.findall(rb'/Type\s*/Page[^s]', d)), 'overflow(article,side)', over)

if __name__ == '__main__': main()
