"""Leads super qualificados — Google Places API.
Critérios: rating >= 4.2, reviews >= 20, sem website.
Nichos de alto valor: dentistas, veterinários, fisio, advocacia, estética, ópticas, psicólogos.
"""
import csv, json, time, re, sys, io, os
import urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_KEY = "AIzaSyDXbxVoQNe8AzT8aSbbmTyCQ6nzob5O-30"
CSV_FILE = "porto_leads.csv"
ALVO = 200

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"

# Nichos de alto valor — maior ticket médio e menor resistência ao investimento
NICHOS = [
    ("Clínica dentária",      "Dentaria"),
    ("Clínica veterinária",   "Veterinario"),
    ("Fisioterapia",          "Fisioterapia"),
    ("Advogado",              "Advocacia"),
    ("Centro de estética",    "Estetica"),
    ("Óptica",                "Optica"),
    ("Psicólogo",             "Psicologo"),
    ("Contabilista",          "Contabilidade"),
    ("Escola de condução",    "Escola Conducao"),
    ("Clínica de nutrição",   "Fisioterapia"),
    ("Ginásio",               "ArtesMarc"),
    ("Cabeleireiro",          "Cabeleireiro"),
    ("Restaurante",           "Restaurante"),
    ("Padaria pastelaria",    "Pastelaria"),
]

CIDADES = [
    "Porto, Portugal",
    "Vila Nova de Gaia, Portugal",
    "Matosinhos, Portugal",
    "Maia, Portugal",
    "Gondomar, Portugal",
    "Valongo, Portugal",
    "Espinho, Portugal",
    "Braga, Portugal",
    "Guimarães, Portugal",
    "Barcelos, Portugal",
]

# Carregar nomes já existentes para evitar duplicados
nomes_existentes = set()
cat_cidade_counts = {}
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            nomes_existentes.add(r["nome"].strip().lower())
            cat = r.get("categoria","")
            cid = r.get("cidade","").split(",")[0].strip()
            cat_cidade_counts.setdefault(cat, {}).setdefault(cid, 0)
            cat_cidade_counts[cat][cid] = cat_cidade_counts[cat][cid] + 1

print(f"Leads existentes: {len(nomes_existentes)}")
print(f"Alvo: {ALVO} leads super qualificados (rating ≥ 4.2, avaliações ≥ 20, sem website)\n")

def places_search(query, city, page_token=None):
    payload = {
        "textQuery": f"{query} em {city}",
        "languageCode": "pt",
        "regionCode": "PT",
        "maxResultCount": 20,
    }
    if page_token:
        payload["pageToken"] = page_token
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        PLACES_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.rating,places.userRatingCount,places.websiteUri,places.id,nextPageToken",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  Erro API: {e}")
        return {}

novos = []
total = 0

for nicho_q, nicho_cat in NICHOS:
    if total >= ALVO:
        break
    for cidade in CIDADES:
        if total >= ALVO:
            break
        cidade_nome = cidade.replace(", Portugal", "")
        # Skip se já temos muitos deste par
        existentes_pair = cat_cidade_counts.get(nicho_cat, {}).get(cidade_nome, 0)
        if existentes_pair >= 60:
            continue

        page_token = None
        found_city = 0
        max_pages = 2

        for page in range(max_pages):
            res = places_search(nicho_q, cidade_nome, page_token)
            places = res.get("places", [])
            if not places:
                break

            for p in places:
                nome = p.get("displayName", {}).get("text", "").strip()
                if not nome or nome.lower() in nomes_existentes:
                    continue

                rating = p.get("rating", 0) or 0
                reviews = p.get("userRatingCount", 0) or 0
                website = p.get("websiteUri", "")

                # Filtros de qualificação
                if rating < 4.2:
                    continue
                if reviews < 20:
                    continue
                if website:
                    continue  # só sem website

                tel = p.get("nationalPhoneNumber", "")
                morada = p.get("formattedAddress", "")

                novos.append({
                    "nome": nome,
                    "categoria": nicho_cat,
                    "cidade": cidade_nome,
                    "morada": morada,
                    "telefone": tel,
                    "rating": round(rating, 1),
                    "avaliacoes": reviews,
                    "tem_website": "Não",
                    "website_url": "",
                })
                nomes_existentes.add(nome.lower())
                found_city += 1
                total += 1
                if total >= ALVO:
                    break

            page_token = res.get("nextPageToken")
            if not page_token:
                break
            time.sleep(0.5)

        if found_city > 0:
            print(f"  [{nicho_cat}] {cidade_nome}: +{found_city} (total: {total})")

        time.sleep(0.3)

print(f"\nTotal novos qualificados: {total}")

if novos:
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        existentes = list(csv.DictReader(f))

    campos = ["nome","categoria","cidade","morada","telefone","rating","avaliacoes","tem_website","website_url"]
    with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in existentes:
            w.writerow({k: r.get(k,"") for k in campos})
        for r in novos:
            w.writerow(r)

    print(f"CSV actualizado: {len(existentes) + len(novos)} leads total")
    print("A regenerar CRM...")
    os.system("python scripts/fix_crm_v3.py")
else:
    print("Nenhum lead novo encontrado.")
