"""
Exporta os leads do crm-porto (index.html) para CSV limpo.

Uso:
  python exportar_leads.py
  python exportar_leads.py --com-status  (inclui status do localStorage se fornecido)

Output:
  leads_export.csv   — todos os 1857 leads
  leads_com_tel.csv  — só leads com telefone (1419)
"""

import re
import json
import csv
import sys
from pathlib import Path

HTML_FILE = Path(__file__).parent / "index.html"
OUT_ALL   = Path(__file__).parent / "leads_export.csv"
OUT_TEL   = Path(__file__).parent / "leads_com_tel.csv"

def extrair_leads(html: str) -> list[dict]:
    idx = html.find("const L = [")
    if idx == -1:
        raise ValueError("Array de leads não encontrado no HTML")
    start = idx + len("const L = ")
    depth, i = 0, start
    while i < len(html):
        if html[i] == "[":   depth += 1
        elif html[i] == "]": depth -= 1
        if depth == 0:
            end = i + 1
            break
        i += 1
    return json.loads(html[start:end])

def exportar(leads: list[dict], caminho: Path) -> int:
    if not leads:
        return 0
    campos = ["id", "nome", "cat", "cidade", "morada", "tel", "wa", "r", "av"]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(leads)
    return len(leads)

def main():
    if not HTML_FILE.exists():
        print(f"Ficheiro não encontrado: {HTML_FILE}")
        sys.exit(1)

    html = HTML_FILE.read_text(encoding="utf-8", errors="replace")
    leads = extrair_leads(html)
    print(f"Leads encontrados: {len(leads)}")

    # Exportar todos
    n = exportar(leads, OUT_ALL)
    print(f"Exportados {n} leads -> {OUT_ALL.name}")

    # Exportar só com telefone
    com_tel = [l for l in leads if l.get("tel")]
    n2 = exportar(com_tel, OUT_TEL)
    print(f"Exportados {n2} leads com telefone -> {OUT_TEL.name}")

    # Estatísticas rápidas
    from collections import Counter
    print(f"\nTop 10 nichos:")
    for cat, n in Counter(l.get("cat","") for l in leads).most_common(10):
        print(f"  {cat}: {n}")

    print(f"\nCidades:")
    for cidade, n in Counter(l.get("cidade","") for l in leads).most_common(8):
        print(f"  {cidade}: {n}")

    ratings = [l.get("r",0) for l in leads if l.get("r")]
    if ratings:
        print(f"\nRatings: avg={sum(ratings)/len(ratings):.2f} | min={min(ratings)} | max={max(ratings)}")

if __name__ == "__main__":
    main()
