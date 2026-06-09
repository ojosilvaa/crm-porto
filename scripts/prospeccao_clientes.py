import requests
import csv
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_KEY = "AIzaSyDXbxVoQNe8AzT8aSbbmTyCQ6nzob5O-30"
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
OUTPUT_FILE = "prospeccao_porto_sem_website.csv"

# Múltiplas queries por categoria para maximizar resultados
CATEGORIAS = [
    {
        "label": "Clinica Dentaria",
        "queries": [
            "clinica dentaria Porto",
            "medico dentista Porto",
            "clinica dentaria Vila Nova de Gaia",
            "clinica dentaria Matosinhos",
            "clinica dentaria Maia Portugal",
            "clinica dentaria Gondomar Portugal",
        ]
    },
    {
        "label": "Centro de Estetica",
        "queries": [
            "centro estetica Porto",
            "gabinete estetica Porto",
            "estetica avancada Porto",
            "centro de beleza Porto",
            "centro estetica Vila Nova de Gaia",
            "centro estetica Matosinhos",
        ]
    },
    {
        "label": "Salao de Cabeleireiro",
        "queries": [
            "salao cabeleireiro Porto",
            "cabeleireiro hairstylist Porto",
            "salao beleza cabeleireiro Porto",
            "cabeleireiro Vila Nova de Gaia",
            "cabeleireiro Matosinhos",
            "cabeleireiro Maia Portugal",
        ]
    },
]

# Centros de busca: Porto, Gaia, Matosinhos, Maia
LOCATIONS = [
    {"latitude": 41.1579, "longitude": -8.6291, "radius": 8000},   # Porto centro
    {"latitude": 41.1333, "longitude": -8.6167, "radius": 8000},   # Vila Nova de Gaia
    {"latitude": 41.1833, "longitude": -8.6900, "radius": 7000},   # Matosinhos
    {"latitude": 41.2333, "longitude": -8.6167, "radius": 7000},   # Maia
]

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
])


def search(query, location, page_token=None):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {
        "textQuery": query,
        "languageCode": "pt",
        "maxResultCount": 20,
        "locationBias": {
            "circle": {
                "center": {"latitude": location["latitude"], "longitude": location["longitude"]},
                "radius": float(location["radius"])
            }
        }
    }
    if page_token:
        body["pageToken"] = page_token
    r = requests.post(SEARCH_URL, json=body, headers=headers, timeout=15)
    if r.status_code != 200:
        return [], None
    data = r.json()
    return data.get("places", []), data.get("nextPageToken")


def extrair_cidade(endereco):
    if not endereco:
        return "Porto"
    keywords = ["porto", "gaia", "matosinhos", "maia", "gondomar", "valongo", "espinho", "vila nova"]
    for parte in [p.strip() for p in endereco.split(",")]:
        if any(k in parte.lower() for k in keywords):
            return parte
    return "Porto"


def prioridade(avaliacoes, rating):
    score = 0
    if avaliacoes and avaliacoes < 30:
        score += 20
    if rating and rating < 4.2:
        score += 10
    return score


def recolher_sem_website(categoria, objetivo=40):
    label = categoria["label"]
    print(f"\n[{label}] A recolher (objetivo: {objetivo} sem website)...")

    todos_lugares = {}  # place_id -> dados

    total_pesquisas = 0
    for query in categoria["queries"]:
        for loc in LOCATIONS:
            next_token = None
            for _ in range(2):  # até 2 páginas por query+localização
                places, next_token = search(query, loc, next_token)
                for p in places:
                    pid = p.get("id")
                    if pid and pid not in todos_lugares:
                        todos_lugares[pid] = p
                total_pesquisas += 1
                sys.stdout.write(f"\r  Pesquisas: {total_pesquisas} | Locais únicos: {len(todos_lugares)}")
                sys.stdout.flush()
                if not next_token:
                    break
                time.sleep(1.5)

            if len([p for p in todos_lugares.values() if not p.get("websiteUri")]) >= objetivo * 2:
                break  # já temos mais do que suficiente sem website

    print(f"\n  Total único recolhido: {len(todos_lugares)} locais")

    # Filtrar apenas sem website
    sem_website = []
    for p in todos_lugares.values():
        website = p.get("websiteUri", "")
        if website:
            continue  # ignorar os que TEM website

        nome = p.get("displayName", {}).get("text", "")
        telefone = p.get("nationalPhoneNumber", "")
        rating = p.get("rating")
        avaliacoes = p.get("userRatingCount", 0)
        endereco = p.get("formattedAddress", "")
        cidade = extrair_cidade(endereco)

        sem_website.append({
            "nome": nome,
            "categoria": label,
            "cidade": cidade,
            "morada": endereco,
            "telefone": telefone,
            "rating": round(rating, 1) if rating else "",
            "avaliacoes": avaliacoes,
            "tem_website": "nao",
            "website_url": "",
            "_prioridade": prioridade(avaliacoes, rating),
        })

    # Ordenar por prioridade (menos avaliações e rating mais baixo = mais fácil de fechar)
    sem_website.sort(key=lambda x: -x["_prioridade"])
    resultado = sem_website[:objetivo]
    print(f"  Sem website encontrados: {len(sem_website)} | A usar: {len(resultado)}")
    return resultado


def exportar_csv(todos):
    campos = ["nome", "categoria", "cidade", "morada", "telefone", "rating", "avaliacoes", "tem_website", "website_url"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(todos)
    print(f"\nCSV exportado: {OUTPUT_FILE} ({len(todos)} registos)")


def main():
    todos = []
    for cat in CATEGORIAS:
        resultados = recolher_sem_website(cat, objetivo=40)
        todos.extend(resultados)
        print(f"  -> {len(resultados)} {cat['label']} sem website adicionados")

    print(f"\n[STATS] Total leads sem website: {len(todos)}")
    for cat in CATEGORIAS:
        n = sum(1 for r in todos if r["categoria"] == cat["label"])
        print(f"  {cat['label']}: {n}")

    exportar_csv(todos)


if __name__ == "__main__":
    main()
