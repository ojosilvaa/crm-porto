"""mais_leads.py — Adiciona ~200 leads novos ao porto_leads.csv."""
import requests, csv, json, re, time, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_KEY = "AIzaSyDXbxVoQNe8AzT8aSbbmTyCQ6nzob5O-30"
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
CSV_OUT = "porto_leads.csv"
FM = "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount"

ZONAS = [
    {"nome": "Porto Centro",  "lat": 41.1579, "lon": -8.6291, "r": 5000},
    {"nome": "Gaia",          "lat": 41.1300, "lon": -8.6167, "r": 7000},
    {"nome": "Matosinhos",    "lat": 41.1833, "lon": -8.6900, "r": 6000},
    {"nome": "Maia",          "lat": 41.2333, "lon": -8.6167, "r": 7000},
    {"nome": "Gondomar",      "lat": 41.1500, "lon": -8.5333, "r": 6000},
    {"nome": "Valongo",       "lat": 41.1833, "lon": -8.4967, "r": 6000},
    {"nome": "Porto Este",    "lat": 41.1700, "lon": -8.5700, "r": 5000},
    {"nome": "Espinho",       "lat": 41.0100, "lon": -8.6400, "r": 5000},
]

# Nichos novos + queries alternativas para nichos existentes com baixo número
NOVOS_NICHOS = [
    {"label": "Veterinario",         "q": ["clinica veterinaria gatos caes", "veterinario animais domesticos", "hospital veterinario porto"]},
    {"label": "Psicologo",           "q": ["psicologo consultas", "psicologa clinica terapia", "psicologia clinica consultorio"]},
    {"label": "Escola Conducao",     "q": ["escola conducao autoescola", "autoescola carta conducao", "escola de conducao porto"]},
    {"label": "Contabilidade",       "q": ["gabinete contabilidade toc", "contabilista empresa", "servicos contabilidade fiscal"]},
    {"label": "Informatica",         "q": ["reparacao computadores portateis", "assistencia informatica pc", "tecnico informatica porto"]},
    {"label": "Canalizador",         "q": ["canalizador reparacoes urgentes", "servico canalizacao porto", "canalizador instalacoes"]},
    {"label": "Yoga Pilates",        "q": ["estudio yoga pilates porto", "aulas yoga meditacao", "pilates studio porto"]},
    {"label": "Creche ATL",          "q": ["creche infantil porto", "jardim infancia ATL", "infantario creche criancas"]},
    {"label": "Personal Trainer",    "q": ["personal trainer ginasio porto", "ginasio fitness crossfit", "personal trainer musculacao"]},
    {"label": "Escola Musica Danca", "q": ["escola musica porto", "academia danca ballet porto", "conservatorio musica danca"]},
    {"label": "Catering",            "q": ["catering eventos casamentos porto", "empresa catering festas", "catering empresas porto"]},
    {"label": "Optica",              "q": ["optica oculista porto", "loja optica oculos", "oculista exame vista"]},
    {"label": "Fotografo Studio",    "q": ["fotografo estudio porto", "fotografia profissional retratos", "estudio fotografico porto"]},
    {"label": "Eletricista",         "q": ["eletricista instalacoes eletricas", "tecnico eletricista porto", "eletricista obras"]},
]

CIDADE_MAPA = {
    "Porto": "Porto", "Vila Nova de Gaia": "Vila Nova de Gaia", "Gaia": "Vila Nova de Gaia",
    "Matosinhos": "Matosinhos", "Maia": "Maia", "Gondomar": "Gondomar",
    "Valongo": "Valongo", "Espinho": "Espinho", "Ermesinde": "Valongo",
    "Pedrouços": "Maia", "Águas Santas": "Maia", "Moreira": "Maia",
    "Figueiredo": "Gondomar", "Fânzeres": "Gondomar", "Rio Tinto": "Gondomar",
    "Leça da Palmeira": "Matosinhos", "Leça do Balio": "Matosinhos",
    "Senhora da Hora": "Matosinhos", "Perafita": "Matosinhos",
    "São Mamede de Infesta": "Matosinhos", "Santa Cruz do Bispo": "Matosinhos",
    "Paranhos": "Porto", "Campanhã": "Porto", "Bonfim": "Porto",
    "Cedofeita": "Porto", "Massarelos": "Porto", "Lordelo do Ouro": "Porto",
    "Ramalde": "Porto", "Aldoar": "Porto", "Nevogilde": "Porto",
    "Foz do Douro": "Porto", "Antas": "Porto", "Areosa": "Porto",
    "Oliveira do Douro": "Vila Nova de Gaia", "Avintes": "Vila Nova de Gaia",
    "Canidelo": "Vila Nova de Gaia", "Mafamude": "Vila Nova de Gaia",
    "Santa Marinha": "Vila Nova de Gaia", "Pedroso": "Vila Nova de Gaia",
    "Vilar de Andorinho": "Vila Nova de Gaia", "Crestuma": "Vila Nova de Gaia",
}

def norm_cidade(morada):
    segs = [s.strip() for s in morada.split(",")]
    for seg in segs:
        m = re.search(r'\d{4}[-\s]\d{3}\s+(.+)', seg)
        if m:
            raw = m.group(1).strip()
            for k, v in CIDADE_MAPA.items():
                if k.lower() in raw.lower():
                    return v
            # fallback: use raw
            raw2 = raw.split("/")[0].strip()
            return raw2 if len(raw2) < 30 else "Porto"
    # try direct match
    for seg in segs[1:]:
        for k, v in CIDADE_MAPA.items():
            if k.lower() in seg.lower():
                return v
    return segs[-2].strip() if len(segs) >= 2 else "Porto"

# Carregar place_ids existentes para deduplicação
ids_existentes = set()
nomes_existentes = set()
if os.path.exists(CSV_OUT):
    with open(CSV_OUT, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            nomes_existentes.add(row["nome"].strip().lower())

print(f"Leads existentes: {len(nomes_existentes)}")

CAMPOS = ["place_id","nome","categoria","cidade","morada","telefone","rating","avaliacoes","tem_website","website_url"]

# Abrir CSV existente, adicionar place_id se necessário, ou criar novo buffer
novos = []
ALVO_TOTAL = 200

def fetch(queries, lat, lon, r, label, max_pp=20):
    results = []
    for q in queries:
        if len(results) >= max_pp:
            break
        body = {
            "textQuery": q,
            "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": r}},
            "maxResultCount": 20,
            "languageCode": "pt"
        }
        headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY, "X-Goog-FieldMask": FM}
        try:
            resp = requests.post(SEARCH_URL, json=body, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"  API erro {resp.status_code}")
                continue
            places = resp.json().get("places", [])
            for p in places:
                if len(results) >= max_pp:
                    break
                nome = p.get("displayName", {}).get("text", "").strip()
                if not nome:
                    continue
                website = p.get("websiteUri", "")
                # Só sem website
                if website:
                    continue
                pid = p.get("id", "")
                if pid in ids_existentes:
                    continue
                if nome.lower() in nomes_existentes:
                    continue
                morada = p.get("formattedAddress", "")
                tel = p.get("nationalPhoneNumber", "")
                rat = p.get("rating", "")
                av = p.get("userRatingCount", 0)
                cidade = norm_cidade(morada)
                ids_existentes.add(pid)
                nomes_existentes.add(nome.lower())
                results.append({
                    "place_id": pid, "nome": nome, "categoria": label,
                    "cidade": cidade, "morada": morada, "telefone": tel,
                    "rating": str(rat) if rat else "", "avaliacoes": str(av),
                    "tem_website": "Nao", "website_url": ""
                })
        except Exception as e:
            print(f"  Erro: {e}")
        time.sleep(0.3)
    return results

# Abrir CSV para append (sem place_id para manter compatibilidade)
f_out = open(CSV_OUT, "a", encoding="utf-8-sig", newline="")
writer = csv.DictWriter(f_out, fieldnames=["nome","categoria","cidade","morada","telefone","rating","avaliacoes","tem_website","website_url"])

total_novos = 0
for nicho in NOVOS_NICHOS:
    if total_novos >= ALVO_TOTAL:
        break
    por_nicho = 0
    print(f"\n[{nicho['label']}]")
    for zona in ZONAS:
        if total_novos >= ALVO_TOTAL:
            break
        rows = fetch(nicho["q"], zona["lat"], zona["lon"], zona["r"], nicho["label"], max_pp=5)
        for row in rows:
            writer.writerow({k: row[k] for k in ["nome","categoria","cidade","morada","telefone","rating","avaliacoes","tem_website","website_url"]})
            f_out.flush()
            por_nicho += 1
            total_novos += 1
        if rows:
            print(f"  {zona['nome']}: +{len(rows)} ({total_novos} total)")

f_out.close()
print(f"\nConcluido: +{total_novos} leads novos")
print(f"A regenerar CRM...")
os.system("python fix_crm_v3.py")
