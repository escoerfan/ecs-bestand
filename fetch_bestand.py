import json
import urllib.request
import urllib.error
import base64
import os
from datetime import datetime, timezone

# Zugangsdaten aus Umgebungsvariablen
user = os.environ.get('MOBILE_USER', '')
password = os.environ.get('MOBILE_PASS', '')

# Basic Auth Header
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
        print(f"HTTP Fehler {e.code} bei {url}: {body[:300]}")
        return None
    except Exception as e:
        print(f"Fehler bei {url}: {e}")
        return None

# Schritt 1: Alle Seller abrufen
print("Rufe Seller-Liste ab...")
sellers_data = api_get('https://services.mobile.de/seller-api/sellers')

if not sellers_data:
    print("Fehler: Keine Seller-Daten erhalten.")
    output = {'updated': datetime.now(timezone.utc).isoformat(), 'count': 0, 'vehicles': []}
    with open('bestand.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    exit(0)

print(f"Seller Response: {json.dumps(sellers_data)[:500]}")

sellers = sellers_data.get('sellers', [])
if not sellers:
    print("Keine Seller gefunden.")
    output = {'updated': datetime.now(timezone.utc).isoformat(), 'count': 0, 'vehicles': []}
    with open('bestand.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    exit(0)

# Erste Seller-ID verwenden
seller_id = sellers[0]['mobileSellerId']
print(f"Verwende mobileSellerId: {seller_id}")

# Schritt 2: Inserate abrufen
print(f"Rufe Inserate für Seller {seller_id} ab...")
ads_data = api_get(f'https://services.mobile.de/seller-api/sellers/{seller_id}/ads')

if not ads_data:
    print("Fehler: Keine Inserate-Daten erhalten.")
    output = {'updated': datetime.now(timezone.utc).isoformat(), 'count': 0, 'vehicles': []}
    with open('bestand.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    exit(0)

print(f"Ads Response (erste 500 Zeichen): {json.dumps(ads_data)[:500]}")

ads_raw = ads_data.get('ads', [])
print(f"Anzahl Inserate: {len(ads_raw)}")

result = []
for ad in ads_raw:
    vehicle = ad.get('ad', ad)

    # Preis
    price_obj = vehicle.get('price', {})
    if isinstance(price_obj, dict):
        price = price_obj.get('consumerPriceGross', price_obj.get('dealerPriceGross', ''))
    else:
        price = ''

    # Kilometerstand
    mileage = vehicle.get('mileage', {})
    km = mileage.get('value', '') if isinstance(mileage, dict) else mileage

    # Erstzulassung
    reg = vehicle.get('firstRegistration', '')

    # Titel
    make = vehicle.get('make', {})
    make_name = make.get('displayName', '') if isinstance(make, dict) else str(make)
    model = vehicle.get('model', {})
    model_name = model.get('displayName', '') if isinstance(model, dict) else str(model)
    title = f'{make_name} {model_name}'.strip() or vehicle.get('title', 'Fahrzeug')

    # Beschreibung
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
    cat_name = cat.get('displayName', '') if isinstance(cat, dict) else str(cat)

    # Ad-ID
    ad_id = vehicle.get('id', '')

    result.append({
        'id': str(ad_id),
        'title': title,
        'make': make_name,
        'model': model_name,
        'price': str(price),
        'km': str(km),
        'firstRegistration': str(reg),
        'description': str(description)[:300],
        'images': images,
        'category': cat_name,
        'mobileUrl': f'https://www.mobile.de/fahrzeuge/details.html?id={ad_id}' if ad_id else ''
    })

output = {
    'updated': datetime.now(timezone.utc).isoformat(),
    'count': len(result),
    'vehicles': result
}

with open('bestand.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Fertig: {len(result)} Fahrzeuge gespeichert.")
