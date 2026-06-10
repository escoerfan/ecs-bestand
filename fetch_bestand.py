import json
import urllib.request
import urllib.error
import base64
import os
from datetime import datetime, timezone

user = os.environ.get('MOBILE_USER', '')
password = os.environ.get('MOBILE_PASS', '')

credentials = base64.b64encode(f'{user}:{password}'.encode()).decode()
headers = {
    'Accept': 'application/vnd.de.mobile.api+json',
    'Authorization': f'Basic {credentials}'
}

def api_get(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"HTTP Fehler {e.code}: {body[:300]}")
        return None
    except Exception as e:
        print(f"Fehler: {e}")
        return None

def save_empty(msg=''):
    with open('bestand.json', 'w', encoding='utf-8') as f:
        json.dump({'updated': datetime.now(timezone.utc).isoformat(), 'count': 0, 'vehicles': [], 'error': msg}, f, ensure_ascii=False, indent=2)

# Seller abrufen
sellers_data = api_get('https://services.mobile.de/seller-api/sellers')
if not sellers_data:
    save_empty('Keine Seller-Antwort'); exit(0)

sellers = sellers_data.get('sellers', [])
if not sellers:
    save_empty('Keine Seller'); exit(0)

seller_id = sellers[0]['mobileSellerId']
print(f"Seller ID: {seller_id}")

# Alle Ads abrufen
ads_data = api_get(f'https://services.mobile.de/seller-api/sellers/{seller_id}/ads')
if not ads_data:
    save_empty('Keine Ads'); exit(0)

ads_raw = ads_data.get('ads', [])
print(f"Anzahl Ads: {len(ads_raw)}")

result = []
for ad in ads_raw:
    vehicle = ad.get('ad', ad)

    # ── Titel: direkt aus dem API-Feld 'title' ──
    # Mobile.de liefert den echten Inseratstitel hier.
    # Kein Parsen der Description nötig.
    title_raw = vehicle.get('title', '')
    if isinstance(title_raw, dict):
        title = title_raw.get('value', title_raw.get('displayName', ''))
    else:
        title = str(title_raw or '').strip()

    # Marke
    make_raw = vehicle.get('make', {})
    if isinstance(make_raw, dict):
        make_name = make_raw.get('displayName', make_raw.get('key', ''))
    else:
        make_name = str(make_raw) if make_raw else ''

    # Modell
    model_raw = vehicle.get('model', {})
    if isinstance(model_raw, dict):
        model_name = (model_raw.get('displayName') or model_raw.get('description') or
                      model_raw.get('name') or model_raw.get('key') or '')
    else:
        model_name = str(model_raw) if model_raw else ''

    # Fallback-Titel: Marke + Modell wenn title leer
    if not title or len(title) < 3:
        parts = [p for p in [make_name, model_name] if p]
        title = ' '.join(parts) if parts else 'Fahrzeug'

    # Preis
    price_obj = vehicle.get('price', {})
    if isinstance(price_obj, dict):
        price = price_obj.get('consumerPriceGross', price_obj.get('dealerPriceGross', price_obj.get('value', '')))
    else:
        price = str(price_obj) if price_obj else ''

    # KM
    mileage = vehicle.get('mileage', {})
    km = mileage.get('value', '') if isinstance(mileage, dict) else mileage

    # Erstzulassung
    reg = vehicle.get('firstRegistration', '')

    # Description (vollständig, kein Kürzen mehr)
    description = vehicle.get('description', '')
    if isinstance(description, dict):
        description = description.get('value', '')

    # Bilder
    images = []
    imgs = vehicle.get('images', {})
    if isinstance(imgs, dict):
        img_list = imgs.get('images', [])
    elif isinstance(imgs, list):
        img_list = imgs
    else:
        img_list = []
    for img in img_list[:6]:
        ref = img.get('ref', '') if isinstance(img, dict) else str(img)
        if ref:
            images.append(ref)

    # Kategorie
    cat = vehicle.get('category', {})
    cat_name = cat.get('displayName', cat.get('key', '')) if isinstance(cat, dict) else str(cat)

    # Ad-ID
    ad_id = (vehicle.get('id') or vehicle.get('mobileAdId') or
             ad.get('id') or ad.get('mobileAdId') or '')

    mobile_url = f'https://www.mobile.de/fahrzeuge/details.html?id={ad_id}' if ad_id else ''

    result.append({
        'id': str(ad_id),
        'title': title,
        'make': make_name,
        'model': model_name,
        'price': str(price),
        'km': str(km),
        'firstRegistration': str(reg),
        'description': str(description),
        'images': images,
        'category': cat_name,
        'mobileUrl': mobile_url
    })

output = {
    'updated': datetime.now(timezone.utc).isoformat(),
    'count': len(result),
    'vehicles': result
}

with open('bestand.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Fertig: {len(result)} Fahrzeuge gespeichert.")
