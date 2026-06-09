import json
import urllib.request
import urllib.error
import base64
import os
from datetime import datetime, timezone

# Zugangsdaten aus Umgebungsvariablen
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
        print(f"HTTP Fehler {e.code} bei {url}")
        print(f"Response: {body[:500]}")
        return None
    except Exception as e:
        print(f"Fehler bei {url}: {e}")
        return None

def save_empty(error_msg=''):
    output = {
        'updated': datetime.now(timezone.utc).isoformat(),
        'count': 0,
        'vehicles': [],
        'error': error_msg
    }
    with open('bestand.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

# Schritt 1: Seller-Liste abrufen
print("=" * 50)
print("Schritt 1: Seller-Liste abrufen")
sellers_data = api_get('https://services.mobile.de/seller-api/sellers')

if not sellers_data:
    print("FEHLER: Keine Antwort von Seller-Endpoint.")
    print("Mögliche Ursachen: Falsche Zugangsdaten oder API nicht aktiviert.")
    save_empty('Keine Antwort von der API')
    exit(0)

print(f"Vollständige Seller-Antwort:")
print(json.dumps(sellers_data, ensure_ascii=False, indent=2))

sellers = sellers_data.get('sellers', [])
if not sellers:
    print("FEHLER: Seller-Liste ist leer.")
    save_empty('Keine Seller gefunden')
    exit(0)

# Alle Seller anzeigen
print(f"\nGefundene Seller: {len(sellers)}")
for s in sellers:
    print(f"  mobileSellerId: {s.get('mobileSellerId')} | customerNumber: {s.get('customerNumber')} | Name: {s.get('companyName', '')}")

# Seller mit customerNumber 39194176 suchen, sonst ersten nehmen
seller_id = None
for s in sellers:
    if str(s.get('customerNumber', '')) == '39194176':
        seller_id = s['mobileSellerId']
        print(f"\nTreffer: customerNumber 39194176 -> mobileSellerId {seller_id}")
        break

if not seller_id:
    seller_id = sellers[0]['mobileSellerId']
    print(f"\nKeine Übereinstimmung mit 39194176, nehme ersten Seller: {seller_id}")

# Schritt 2: Inserate abrufen
print("=" * 50)
print(f"Schritt 2: Inserate für Seller {seller_id} abrufen")
ads_data = api_get(f'https://services.mobile.de/seller-api/sellers/{seller_id}/ads')

if not ads_data:
    print("FEHLER: Keine Inserate-Daten erhalten.")
    save_empty('Keine Inserate-Daten')
    exit(0)

print(f"Ads-Antwort (erste 800 Zeichen):")
print(json.dumps(ads_data)[:800])

ads_raw = ads_data.get('ads', [])
print(f"\nAnzahl Inserate: {len(ads_raw)}")

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

print(f"\nFertig: {len(result)} Fahrzeuge in bestand.json gespeichert.")
print("=" * 50)
