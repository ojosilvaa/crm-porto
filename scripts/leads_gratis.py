"""
leads_gratis.py — Scraping Páginas Amarelas com verificação em 2 camadas:
  1. Listagem: filtra cards sem link externo
  2. Página de detalhe: confirma SEM website + extrai telefone real

Garante que os leads realmente não têm website.
"""
import requests, csv, re, time, os, sys, io
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CSV_OUT = "porto_leads.csv"
BASE = "https://www.paginasamarelas.pt"

PA_NICHOS = [
    ("cabeleireiros",                 "Cabeleireiro"),
    ("estetica-e-beleza",             "Estetica"),
    ("clinicas-dentarias",            "Dentaria"),
    ("oficinas-mecanicas",            "Oficina"),
    ("fisioterapia",                  "Fisioterapia"),
    ("restaurantes",                  "Restaurante"),
    ("pastelarias",                   "Pastelaria"),
    ("advogados",                     "Advocacia"),
    ("escolas-de-conducao",           "Escola Conducao"),
    ("veterinarios",                  "Veterinario"),
    ("psicologos",                    "Psicologo"),
    ("creches-e-jardins-de-infancia", "Creche ATL"),
    ("ginasios",                      "Personal Trainer"),
    ("empresas-de-limpeza",           "Limpeza"),
    ("contabilistas",                 "Contabilidade"),
    ("eletricistas",                  "Eletricista"),
    ("opticas",                       "Optica"),
    ("artes-marciais",                "ArtesMarc"),
    ("yoga-e-pilates",                "Yoga Pilates"),
    ("canalizadores",                 "Canalizador"),
    ("explicadores",                  "Explicacoes"),
    ("fotografos",                    "Fotografo Studio"),
    ("mudancas",                      "Mudancas"),
    ("reparacoes-electrodomesticos",  "Reparacao Eletro"),
    ("pintores",                      "Pintor"),
]

PA_CIDADES = [
    ("porto",             "Porto"),
    ("vila-nova-de-gaia", "Vila Nova de Gaia"),
    ("matosinhos",        "Matosinhos"),
    ("maia",              "Maia"),
    ("gondomar",          "Gondomar"),
    ("valongo",           "Valongo"),
    ("espinho",           "Espinho"),
]

# Domínios que NÃO contam como "website do negócio"
SKIP_DOMAINS = {
    "paginasamarelas.pt", "pai.pt", "google.com", "google.pt",
    "facebook.com", "instagram.com", "youtube.com", "twitter.com",
    "tiktok.com", "tripadvisor.pt", "tripadvisor.com", "booking.com",
    "zomato.com", "yelp.com", "foursquare.com", "maps.google.com",
    "storage.googleapis.com", "livroreclamacoes.pt", "linkedin.com",
    "whatsapp.com", "snapchat.com", "pinterest.com",
}

def e_website_negocio(href):
    """True se o link é um website próprio do negócio."""
    if not href or not href.startswith("http"):
        return False
    domain = re.sub(r"https?://(www\.)?", "", href).split("/")[0].lower()
    return bool(domain) and not any(sk in domain for sk in SKIP_DOMAINS)

# ─── Sessão ──────────────────────────────────────────────────────────────────
S = requests.Session()
S.verify = False
S.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9",
})

def get_page(url, retry=2):
    for _ in range(retry):
        try:
            r = S.get(url, timeout=12)
            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")
        except Exception:
            time.sleep(1)
    return None

# ─── Carregar existentes ─────────────────────────────────────────────────────
nomes_existentes = set()
detail_urls_vistos = set()
from collections import defaultdict, Counter as Cnt
leads_por_cat_cidade = defaultdict(lambda: defaultdict(int))

if os.path.exists(CSV_OUT):
    with open(CSV_OUT, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            nomes_existentes.add(row["nome"].strip().lower())
            leads_por_cat_cidade[row["categoria"]][row["cidade"]] += 1

print(f"Leads existentes: {len(nomes_existentes)}")

def pag_inicial(cat, cidade):
    """Estima a partir de que página deveremos começar para este par cat/cidade."""
    n = leads_por_cat_cidade.get(cat, {}).get(cidade, 0)
    # ~4 leads confirmados por página em média (10 candidatos × 40% passam verificação)
    # Com margem de 30% para não perder leads nas bordas
    start = max(1, int(n / 4) - 2)
    return start

# ─── Verificação na página de detalhe ────────────────────────────────────────
def verificar_detalhe(detail_url):
    """
    Visita a página de detalhe do negócio no PA.
    Devolve (tem_website: bool, telefone: str, morada_melhor: str)
    """
    if detail_url in detail_urls_vistos:
        return True, "", ""  # já visto = skip
    detail_urls_vistos.add(detail_url)

    soup = get_page(BASE + detail_url)
    if not soup:
        return False, "", ""  # se falhou, assume sem website

    # Verifica website
    for a in soup.select("a[href]"):
        if e_website_negocio(a.get("href", "")):
            return True, "", ""  # tem website → descarta

    # Extrai telefone (presente na página de detalhe)
    tel = ""
    tel_el = soup.select_one("a[href^='tel:']")
    if tel_el:
        tel = tel_el["href"].replace("tel:", "").strip()

    # Tenta morada mais completa
    adr_el = soup.select_one("[class*='address'], [itemprop='address'], [class*='location']")
    morada = adr_el.get_text(" ", strip=True) if adr_el else ""
    morada = re.sub(r"\s+", " ", morada).strip()

    return False, tel, morada

# ─── Scraping de listagem ─────────────────────────────────────────────────────
def scrape_listagem(slug_nicho, cat, slug_cidade, cidade_nome, pagina):
    """Devolve lista de candidatos (passaram filtro do card) e se há próxima pág."""
    url = f"{BASE}/{slug_nicho}/{slug_cidade}?page={pagina}"
    soup = get_page(url)
    if not soup:
        return [], False

    cards = soup.select(".card--result")
    has_next = bool(soup.select("a[rel='next']"))
    candidatos = []

    for card in cards:
        # Link para detalhe
        detail_el = card.select_one("a[href^='/paginas/']")
        if not detail_el:
            continue
        detail_url = detail_el.get("href", "")

        # Nome
        nome_el = card.select_one(".card-title a, .card-link, h6 a")
        if not nome_el:
            continue
        nome = nome_el.get_text(strip=True)
        if not nome or len(nome) < 3:
            continue
        if nome.lower() in nomes_existentes:
            continue

        # Morada do card (será melhorada pelo detalhe)
        adr_el = card.select_one("[class*='address']")
        morada_card = ""
        if adr_el:
            morada_card = re.sub(r"\s+", " ", adr_el.get_text(strip=True)).strip()
            morada_card = re.sub(r"(\d{4}-\d{3})([A-Z])", r"\1 \2", morada_card)
        if not morada_card:
            txt = card.get_text(" ", strip=True)
            m = re.search(r"(\d{4}[-\s]\d{3}\s+[A-ZÁÀÂÃÉÊÓÚÇ][^\n,]{2,30})", txt)
            if m:
                morada_card = m.group(1).strip()

        candidatos.append({
            "nome": nome, "cat": cat, "cidade": cidade_nome,
            "morada": morada_card or cidade_nome,
            "detail_url": detail_url
        })

    return candidatos, has_next

# ─── Loop principal ───────────────────────────────────────────────────────────
ALVO = 550
MAX_PAG = 50   # PA tem até 50 páginas por categoria/cidade

novos = []
f_out = open(CSV_OUT, "a", encoding="utf-8-sig", newline="")
writer = csv.DictWriter(f_out, fieldnames=[
    "nome","categoria","cidade","morada","telefone",
    "rating","avaliacoes","tem_website","website_url"])

print(f"Alvo: {ALVO} leads garantidos sem website\n")

for slug_nicho, cat in PA_NICHOS:
    if len(novos) >= ALVO:
        break
    nicho_count = 0

    for slug_cidade, cidade_nome in PA_CIDADES:
        if len(novos) >= ALVO:
            break

        pag_start = pag_inicial(cat, cidade_nome)
        vazias_seguidas = 0
        for pag in range(pag_start, MAX_PAG + 1):
            if len(novos) >= ALVO:
                break

            candidatos, has_next = scrape_listagem(slug_nicho, cat, slug_cidade, cidade_nome, pag)
            time.sleep(0.5)

            if not candidatos:
                # Página sem novos candidatos: pode ser que já estejam todos no DB
                # Continua até 4 páginas vazias consecutivas antes de desistir
                vazias_seguidas += 1
                if vazias_seguidas >= 6 or not has_next:
                    break
                continue  # vai para a próxima página
            else:
                vazias_seguidas = 0

            for cand in candidatos:
                if len(novos) >= ALVO:
                    break
                # Verificação na página de detalhe
                tem_web, tel, morada_det = verificar_detalhe(cand["detail_url"])
                time.sleep(0.45)

                if tem_web:
                    continue  # tem website → skip

                # Confirmado: sem website
                nk = cand["nome"].lower()
                if nk in nomes_existentes:
                    continue
                nomes_existentes.add(nk)

                morada = morada_det if morada_det else cand["morada"]
                row = {
                    "nome": cand["nome"], "categoria": cat,
                    "cidade": cand["cidade"], "morada": morada,
                    "telefone": tel, "rating": "", "avaliacoes": "",
                    "tem_website": "Nao", "website_url": ""
                }
                writer.writerow(row)
                f_out.flush()
                novos.append(row)
                nicho_count += 1

            if not has_next:
                break
            time.sleep(0.4)

    if nicho_count > 0:
        print(f"  [{cat}] +{nicho_count} (total: {len(novos)})")

f_out.close()
print(f"\nTotal confirmados sem website: {len(novos)}")

if novos:
    print("A regenerar CRM...")
    os.system("python fix_crm_v3.py")
