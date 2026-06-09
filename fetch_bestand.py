import json
from datetime import datetime, timezone

# raw.json einlesen (vom curl-Schritt gespeichert)
with open('raw.json', 'r', encoding='utf-8') as f:
    raw_text = f.read()

try:
    raw = json.loads(raw_text)
except Exception as e:
    output = {
        'error': str(e),
        'raw_preview': raw_text[:200],
        'updated': datetime.now(timezone.utc).isoformat(),
        'count': 0,
        'vehicles': []
    }
    with open('bestand.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"JSON-Fehler: {e}")
    exit(0)

ads_raw = raw.get('ads', [])
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

print(f"Gespeichert: {len(result)} Fahrzeuge")
