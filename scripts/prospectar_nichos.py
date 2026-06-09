"""
Prospecção de 10 novos nichos — 20 leads sem website cada.
Guarda progresso após cada nicho. Regenera CRM no final.
"""
import requests, csv, json, re, time, sys, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_KEY    = "AIzaSyDXbxVoQNe8AzT8aSbbmTyCQ6nzob5O-30"
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
CSV_NICHOS = "nichos_sem_website.csv"
CSV_TODOS  = "prospeccao_porto_sem_website.csv"  # CSV original (3 categorias)
CRM_HTML   = "crm_prospeccao.html"
OBJETIVO   = 20

NICHOS = [
    {"label":"Oficina Mecanica",       "queries":["oficina mecanica Porto","mecanico automovel Porto","oficina automovel Gaia","mecanico Matosinhos"]},
    {"label":"Fisioterapeuta",          "queries":["fisioterapeuta Porto","clinica fisioterapia Porto","osteopata Porto","fisioterapeuta Gaia"]},
    {"label":"Restaurante Tasca",       "queries":["tasca restaurante tipico Porto","restaurante tradicional Porto","tasca Porto","restaurante tipico Gaia"]},
    {"label":"Psicologo Terapeuta",     "queries":["psicologo Porto","psicologa Porto","terapeuta psicologico Porto","psicologo Gaia"]},
    {"label":"Centro de Explicacoes",   "queries":["centro de explicacoes Porto","explicador Porto","explicacoes Porto","centro explicacoes Matosinhos"]},
    {"label":"Padaria Pastelaria",      "queries":["padaria artesanal Porto","pastelaria Porto","padaria Porto","pastelaria artesanal Gaia"]},
    {"label":"Advogado Solicitador",    "queries":["advogado Porto","escritorio advocacia Porto","solicitador Porto","advogado Gaia"]},
    {"label":"Empresa de Limpeza",      "queries":["empresa limpeza Porto","limpezas domesticas Porto","servico limpeza Porto","limpeza Matosinhos"]},
    {"label":"Academia Artes Marciais", "queries":["academia artes marciais Porto","box crossfit Porto","judo karate Porto","artes marciais Gaia"]},
    {"label":"Veterinario",             "queries":["veterinario Porto","clinica veterinaria Porto","veterinario Gaia","clinica veterinaria Matosinhos"]},
]

LOCATIONS = [
    {"latitude":41.1579,"longitude":-8.6291,"radius":8000},
    {"latitude":41.1333,"longitude":-8.6167,"radius":8000},
    {"latitude":41.1833,"longitude":-8.6900,"radius":7000},
    {"latitude":41.2333,"longitude":-8.6167,"radius":7000},
]

FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount"

# ── API ───────────────────────────────────────────────────────────────────────
def search(query, loc, page_token=None):
    headers = {"Content-Type":"application/json","X-Goog-Api-Key":API_KEY,"X-Goog-FieldMask":FIELD_MASK}
    body = {"textQuery":query,"languageCode":"pt","maxResultCount":20,
            "locationBias":{"circle":{"center":{"latitude":loc["latitude"],"longitude":loc["longitude"]},"radius":float(loc["radius"])}}}
    if page_token: body["pageToken"] = page_token
    try:
        r = requests.post(SEARCH_URL, json=body, headers=headers, timeout=15)
        if r.status_code != 200: return [], None
        d = r.json()
        return d.get("places",[]), d.get("nextPageToken")
    except: return [], None

def extrair_cidade(end):
    if not end: return "Porto"
    for p in [x.strip() for x in end.split(",")]:
        if any(k in p.lower() for k in ["porto","gaia","matosinhos","maia","gondomar","valongo","espinho"]):
            return p
    return "Porto"

# ── Recolher nicho ────────────────────────────────────────────────────────────
def recolher_nicho(nicho):
    label = nicho["label"]
    print(f"\n[{label}]", end=" ", flush=True)
    todos = {}
    for q in nicho["queries"]:
        for loc in LOCATIONS:
            places, tok = search(q, loc)
            for p in places:
                pid = p.get("id")
                if pid and pid not in todos: todos[pid] = p
            if tok:
                time.sleep(1.5)
                places2, _ = search(q, loc, tok)
                for p in places2:
                    pid = p.get("id")
                    if pid and pid not in todos: todos[pid] = p
            sem = sum(1 for p in todos.values() if not p.get("websiteUri"))
            sys.stdout.write(f"\r[{label}] {len(todos)} únicos | {sem} sem website")
            sys.stdout.flush()
            if sem >= OBJETIVO * 2: break
        if sum(1 for p in todos.values() if not p.get("websiteUri")) >= OBJETIVO * 2: break
        time.sleep(0.3)

    resultados = []
    for p in todos.values():
        if p.get("websiteUri"): continue
        nome     = p.get("displayName",{}).get("text","")
        telefone = p.get("nationalPhoneNumber","")
        rating   = p.get("rating")
        aval     = p.get("userRatingCount",0)
        end      = p.get("formattedAddress","")
        resultados.append({
            "nome": nome, "categoria": label,
            "cidade": extrair_cidade(end), "morada": end,
            "telefone": telefone,
            "rating": round(rating,1) if rating else "",
            "avaliacoes": aval, "tem_website":"nao", "website_url":"",
        })

    resultados.sort(key=lambda x: int(x["avaliacoes"]) if str(x["avaliacoes"]).isdigit() else 0)
    resultado_final = resultados[:OBJETIVO]
    print(f" → {len(resultado_final)} leads guardados")
    return resultado_final

# ── CSV helpers ───────────────────────────────────────────────────────────────
CAMPOS = ["nome","categoria","cidade","morada","telefone","rating","avaliacoes","tem_website","website_url"]

def carregar_csv(path):
    if not os.path.exists(path): return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def guardar_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

# ── CRM generator (inline, compacto) ─────────────────────────────────────────
def wa_num(tel):
    d = re.sub(r"\D","",tel)
    if d.startswith("351"): d=d[3:]
    return f"351{d}" if len(d)==9 and d[0]=="9" else None

def gerar_pitch(row):
    nome=row["nome"]; cat=row["categoria"]
    try: aval=int(row["avaliacoes"])
    except: aval=0
    try: rat=float(row["rating"])
    except: rat=0.0
    if aval<5:     g=f"A {nome} ainda não tem avaliações suficientes no Google — sem website, é praticamente invisível online."
    elif aval<20:  g=f"A {nome} tem {aval} avaliações no Google. Sem website, quem pesquisa online passa para a concorrência."
    elif aval<60:  g=f"Com {aval} avaliações no Google, a {nome} tem boa reputação. Um website vai multiplicar a visibilidade."
    else:           g=f"A {nome} tem {aval} avaliações — já é referência. Sem website está a perder clientes que pesquisam online."
    extra=""
    if rat>0 and rat<4.0: extra=f" Com rating de {rat}, um website com depoimentos vai melhorar a perceção da marca."
    elif rat>=4.8: extra=f" Com {rat} de rating, têm um serviço excecional — um website vai mostrá-lo ao mundo."
    cats={
        "Oficina Mecanica":        ("clientes","oficina mecânica","localização, serviços e marcação de revisões"),
        "Fisioterapeuta":           ("pacientes","clínica de fisioterapia","serviços, equipa e marcações online"),
        "Restaurante Tasca":        ("clientes","restaurante","menu, horários e reservas online"),
        "Psicologo Terapeuta":      ("pacientes","psicólogo","apresentação, especialidades e contacto seguro"),
        "Centro de Explicacoes":    ("alunos","centro de explicações","disciplinas, horários e inscrições online"),
        "Padaria Pastelaria":       ("clientes","padaria/pastelaria","catálogo de produtos, horários e encomendas"),
        "Advogado Solicitador":     ("clientes","escritório de advocacia","áreas de prática, equipa e contacto"),
        "Empresa de Limpeza":       ("clientes","empresa de limpeza","serviços, preçário e pedido de orçamento"),
        "Academia Artes Marciais":  ("alunos","academia","modalidades, horários e inscrições online"),
        "Veterinario":              ("clientes","clínica veterinária","serviços, equipa e marcações online"),
    }
    chamada,area,feat = cats.get(cat,("clientes","negócio","informações e contacto"))
    cidade = row.get("cidade","Porto").split(",")[0].strip()
    return {
        "abertura": f"Boa tarde, estou a falar com o/a responsável pela {nome}?",
        "gancho":   g+extra,
        "proposta": f"Criaria um website profissional para a {nome} com {feat} — pronto em 2 semanas, com garantia.",
        "cta":      "Posso enviar-lhe agora 3 exemplos de websites que fiz para negócios similares no Porto?",
        "obj1":     f"'Tenho redes sociais' → 'O Google só mostra websites nas pesquisas de \"{area} em {cidade}\". São complementares.'",
        "obj2":     "'É caro' → 'Investimento único, sem mensalidades. Recupera em 1-2 meses de novos clientes.'",
        "obj3":     "'Não tenho tempo' → 'Eu trato de tudo. Preciso só de 30 min da sua parte.'",
        "wa_msg":   f"Olá! Trabalho com {area}s no Porto a criar websites profissionais. Vi a {nome} no Google e gostaria de mostrar exemplos. Posso enviar?",
    }

def stars(r):
    try:
        r=float(r); f=int(r); h=1 if r-f>=0.5 else 0
        return "★"*f+("½"if h else "")+"☆"*(5-f-h)
    except: return "☆☆☆☆☆"

def badge_class(cat):
    m={"Oficina Mecanica":"#2a1a0d,#FF9A3C","Fisioterapeuta":"#0d2a2a,#4ECDC4",
       "Restaurante Tasca":"#2a0d0d,#FF6B6B","Psicologo Terapeuta":"#1a0d2a,#C77DFF",
       "Centro de Explicacoes":"#0d1a2a,#4A9EFF","Padaria Pastelaria":"#2a200d,#FFD166",
       "Advogado Solicitador":"#1a1a1a,#aaa","Empresa de Limpeza":"#0d2a0d,#5DCA9A",
       "Academia Artes Marciais":"#2a0a0a,#FF4444","Veterinario":"#0d200d,#7BC67E",
       "Clinica Dentaria":"#1a2a3a,#4A9EFF","Centro de Estetica":"#2a1a3a,#A78BFA",
       "Salao de Cabeleireiro":"#1a2a1a,#5DCA9A"}
    bg,fg=m.get(cat,"#222,#aaa").split(",")
    return f"background:{bg};color:{fg}"

def gerar_crm(leads):
    data = []
    for row in leads:
        tel=row.get("telefone",""); wa=wa_num(tel)
        p=gerar_pitch(row)
        data.append({"id":len(data),"nome":row["nome"],"cat":row["categoria"],
                     "cidade":row.get("cidade","Porto").split(",")[0].strip(),
                     "morada":row.get("morada",row.get("cidade","")),"tel":tel,"wa":wa,
                     "rating":row.get("rating",""),"aval":row.get("avaliacoes",0),
                     "stars":stars(row.get("rating","")),"pitch":p,
                     "badge":badge_class(row["categoria"])})
    cats = sorted(set(d["cat"] for d in data))
    cat_opts = "".join(f'<button class="btn-f" onclick="setF(\'cat\',\'{c}\')">{c}</button>' for c in cats)
    leads_js = json.dumps(data, ensure_ascii=False)

    html = f"""<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRM Prospeção — Websites Porto</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0d0d0d;--bg2:#141414;--bg3:#1c1c1c;--bg4:#252525;--border:#2a2a2a;
  --gold:#C8A96E;--green:#5DCA9A;--red:#e05555;--blue:#4A9EFF;--text:#f0f0f0;--muted:#666}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',sans-serif}}
.hdr{{background:var(--bg2);border-bottom:1px solid var(--border);padding:14px 20px;
  display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:100}}
.hdr h1{{font-size:1.1rem;font-weight:700;color:var(--gold)}}
.hdr span{{color:var(--muted);font-size:.85rem}}
.stats{{display:flex;gap:10px;padding:16px 20px;flex-wrap:wrap}}
.stat{{background:var(--bg3);border:1px solid var(--border);border-radius:10px;
  padding:12px 16px;text-align:center;min-width:100px}}
.stat-n{{font-size:1.6rem;font-weight:700;color:var(--gold)}}
.stat-l{{font-size:.72rem;color:var(--muted);margin-top:2px}}
.filtros{{padding:0 20px 12px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}}
.filtros label{{color:var(--muted);font-size:.78rem;margin-right:2px}}
.btn-f{{background:var(--bg3);border:1px solid var(--border);color:var(--muted);
  padding:5px 12px;border-radius:20px;cursor:pointer;font-size:.75rem;transition:.15s}}
.btn-f:hover,.btn-f.on{{background:var(--gold);border-color:var(--gold);color:#000;font-weight:600}}
.sep{{width:1px;height:20px;background:var(--border);margin:0 3px}}
.search-w{{padding:0 20px 12px}}
#srch{{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:8px;
  padding:9px 13px;color:var(--text);font-size:.88rem;outline:none}}
#srch:focus{{border-color:var(--gold)}}
.lista{{padding:0 20px 40px;display:flex;flex-direction:column;gap:10px}}
.card{{background:var(--bg2);border:1px solid var(--border);border-radius:10px;overflow:hidden}}
.card-top{{display:flex;align-items:flex-start;gap:12px;padding:14px;cursor:pointer}}
.cnum{{background:var(--bg4);border-radius:7px;width:32px;height:32px;display:flex;
  align-items:center;justify-content:center;font-size:.72rem;color:var(--muted);flex-shrink:0;font-weight:700}}
.cinfo{{flex:1;min-width:0}}
.cnome{{font-weight:700;font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.csub{{display:flex;align-items:center;gap:7px;margin-top:3px;flex-wrap:wrap}}
.badge{{font-size:.65rem;padding:2px 7px;border-radius:9px;font-weight:600;white-space:nowrap}}
.bsw{{background:#2a0d0d;color:#e05555}}
.caddr{{font-size:.72rem;color:var(--muted)}}
.cstars{{font-size:.72rem;color:var(--gold)}}
.caval{{font-size:.68rem;color:var(--muted)}}
.cacoes{{display:flex;gap:6px;align-items:center;flex-shrink:0}}
.btn-wa{{background:#25D366;border:none;color:#fff;border-radius:7px;padding:6px 10px;
  font-size:.75rem;font-weight:600;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:4px;white-space:nowrap}}
.btn-tel{{background:var(--bg4);border:1px solid var(--border);color:var(--text);border-radius:7px;
  padding:6px 10px;font-size:.75rem;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:4px;white-space:nowrap}}
.ssel{{padding:4px 6px;border-radius:6px;border:1px solid var(--border);background:var(--bg4);
  color:var(--text);font-size:.73rem;cursor:pointer;outline:none}}
.s-novo{{border-color:#444;color:#aaa}} .s-contactado{{border-color:var(--blue);color:var(--blue);background:#0d1a2a}}
.s-interessado{{border-color:var(--gold);color:var(--gold);background:#1a140a}}
.s-fechado{{border-color:var(--green);color:var(--green);background:#0d1a10}}
.s-recusado{{border-color:var(--red);color:var(--red);background:#1a0d0d}}
.btn-p{{background:var(--bg4);border:1px solid var(--border);color:var(--gold);
  border-radius:7px;padding:6px 10px;font-size:.75rem;cursor:pointer;white-space:nowrap}}
.btn-p:hover{{background:var(--gold);color:#000}}
.ppanel{{display:none;border-top:1px solid var(--border);padding:16px}}
.ppanel.open{{display:block}}
.ps{{margin-bottom:14px}}
.ps h4{{font-size:.67rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}}
.pb{{background:var(--bg3);border:1px solid var(--border);border-radius:7px;
  padding:12px;font-size:.82rem;line-height:1.6;white-space:pre-wrap}}
.pb.ab{{border-left:3px solid var(--blue);color:var(--blue)}}
.pb.ga{{border-left:3px solid var(--gold)}}
.pb.pr{{border-left:3px solid var(--green)}}
.pb.ct{{border-left:3px solid #A78BFA;color:#A78BFA}}
.pb.ob{{font-size:.78rem;color:#aaa;border-left:3px solid #444}}
.wa-box{{background:#0a1a0f;border:1px solid #25D366;border-radius:7px;padding:12px;
  font-size:.8rem;line-height:1.5;color:#a0f0b0;position:relative;margin-top:8px}}
.cbtn{{position:absolute;top:7px;right:7px;background:var(--bg3);border:1px solid var(--border);
  color:var(--muted);border-radius:5px;padding:2px 8px;font-size:.68rem;cursor:pointer}}
.nota-w{{margin-top:10px}}
.nota-w textarea{{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:7px;
  color:var(--text);padding:9px;font-size:.8rem;resize:vertical;min-height:60px;outline:none;font-family:inherit}}
.nota-w textarea:focus{{border-color:var(--gold)}}
.empty{{text-align:center;padding:50px 20px;color:var(--muted)}}
@media(max-width:600px){{.card-top{{flex-wrap:wrap}}.cacoes{{width:100%;justify-content:flex-end}}}}
</style></head><body>
<div class="hdr">
  <div><h1>CRM Prospeção <span>Websites · Grande Porto</span></h1></div>
  <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <span id="hstat" style="font-size:.78rem;color:var(--muted)"></span>
    <button onclick="expNotas()" style="background:var(--bg3);border:1px solid var(--border);color:var(--muted);padding:5px 10px;border-radius:7px;cursor:pointer;font-size:.72rem">Exportar Notas</button>
  </div>
</div>
<div class="stats">
  <div class="stat"><div class="stat-n" id="s-t">0</div><div class="stat-l">Total Leads</div></div>
  <div class="stat"><div class="stat-n" id="s-n" style="color:var(--muted)">0</div><div class="stat-l">Novos</div></div>
  <div class="stat"><div class="stat-n" id="s-c" style="color:var(--blue)">0</div><div class="stat-l">Contactados</div></div>
  <div class="stat"><div class="stat-n" id="s-i" style="color:var(--gold)">0</div><div class="stat-l">Interessados</div></div>
  <div class="stat"><div class="stat-n" id="s-f" style="color:var(--green)">0</div><div class="stat-l">Fechados</div></div>
</div>
<div class="filtros">
  <label>Cat:</label>
  <button class="btn-f on" onclick="setF('cat','')">Todos</button>
  {cat_opts}
  <div class="sep"></div>
  <label>Estado:</label>
  <button class="btn-f on" onclick="setF('st','')">Todos</button>
  <button class="btn-f" onclick="setF('st','novo')">Novos</button>
  <button class="btn-f" onclick="setF('st','contactado')">Contactados</button>
  <button class="btn-f" onclick="setF('st','interessado')">Interessados</button>
  <button class="btn-f" onclick="setF('st','fechado')">Fechados</button>
  <button class="btn-f" onclick="setF('st','recusado')">Recusados</button>
</div>
<div class="search-w"><input id="srch" placeholder="Pesquisar nome ou cidade..." oninput="render()"></div>
<div class="lista" id="lista"></div>
<script>
const L={leads_js};
let F={{cat:'',st:''}};
const ld=()=>{{try{{return JSON.parse(localStorage.getItem('crm2')||'{{}}')}}catch(e){{return {{}}}}}}
const sv=s=>localStorage.setItem('crm2',JSON.stringify(s));
function setF(k,v){{F[k]=v;document.querySelectorAll('.btn-f').forEach(b=>{{const o=b.getAttribute('onclick')||'';b.classList.toggle('on',o.includes(`'${{k}}'`)&&o.includes(`'${{v}}'`))}});render()}}
function render(){{
  const s=ld(),q=(document.getElementById('srch').value||'').toLowerCase();
  const fl=L.filter(l=>{{
    const st=(s[l.id]?.st)||'novo';
    if(F.cat&&l.cat!==F.cat)return false;
    if(F.st&&st!==F.st)return false;
    if(q&&!l.nome.toLowerCase().includes(q)&&!l.cidade.toLowerCase().includes(q))return false;
    return true;
  }});
  const c={{novo:0,contactado:0,interessado:0,fechado:0}};
  L.forEach(l=>{{const st=(s[l.id]?.st)||'novo';if(c[st]!==undefined)c[st]++}});
  document.getElementById('s-t').textContent=L.length;
  document.getElementById('s-n').textContent=c.novo;
  document.getElementById('s-c').textContent=c.contactado;
  document.getElementById('s-i').textContent=c.interessado;
  document.getElementById('s-f').textContent=c.fechado;
  document.getElementById('hstat').textContent=fl.length+' a mostrar';
  const lista=document.getElementById('lista');
  page=0; renderPage(fl,s,true);
}}
function tog(id){{document.getElementById('p'+id).classList.toggle('open')}}
function setSt(id,v){{const s=ld();if(!s[id])s[id]={{}};s[id].st=v;sv(s);const el=document.querySelector('#c'+id+' .ssel');if(el)el.className='ssel s-'+v;render()}}
function svNota(id){{const s=ld();if(!s[id])s[id]={{}};const t=document.getElementById('nt'+id);if(t)s[id].nota=t.value;sv(s)}}
function cpWA(id){{const el=document.getElementById('wm'+id);const b=el.querySelector('.cbtn');navigator.clipboard.writeText(el.childNodes[0].textContent.trim()).then(()=>{{b.textContent='✓';setTimeout(()=>b.textContent='Copiar',2000)}})}}
function expNotas(){{const s=ld();let t='CRM EXPORT '+new Date().toLocaleDateString('pt-PT')+'\\n\\n';L.forEach(l=>{{const d=s[l.id];if(!d||(!d.nota&&(!d.st||d.st==='novo')))return;t+=`[${{(d.st||'novo').toUpperCase()}}] ${{l.nome}} — ${{l.tel||'—'}}\\n`;if(d.nota)t+='Nota: '+d.nota+'\\n';t+='\\n'}});const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([t],{{type:'text/plain'}}));a.download='crm_notas_'+new Date().toISOString().slice(0,10)+'.txt';a.click()}}
// Lazy render — só 30 de cada vez
let PAGE=30, page=0;
function render(){{
  const s=ld(),q=(document.getElementById('srch').value||'').toLowerCase();
  const fl=L.filter(l=>{{
    const st=(s[l.id]?.st)||'novo';
    if(F.cat&&l.cat!==F.cat)return false;
    if(F.st&&st!==F.st)return false;
    if(q&&!l.nome.toLowerCase().includes(q)&&!l.cidade.toLowerCase().includes(q))return false;
    return true;
  }});
  const c={{novo:0,contactado:0,interessado:0,fechado:0}};
  L.forEach(l=>{{const st=(s[l.id]?.st)||'novo';if(c[st]!==undefined)c[st]++}});
  document.getElementById('s-t').textContent=L.length;
  document.getElementById('s-n').textContent=c.novo;
  document.getElementById('s-c').textContent=c.contactado;
  document.getElementById('s-i').textContent=c.interessado;
  document.getElementById('s-f').textContent=c.fechado;
  document.getElementById('hstat').textContent=fl.length+' leads';
  page=0; renderPage(fl,s,true);
}}
function renderPage(fl,s,reset){{
  const lista=document.getElementById('lista');
  if(reset) lista.innerHTML='';
  if(!fl.length&&reset){{lista.innerHTML='<div class="empty">Sem resultados.</div>';return}}
  const slice=fl.slice(page*PAGE,(page+1)*PAGE);
  const frag=document.createDocumentFragment();
  slice.forEach((l,i)=>{{
    const st=(s[l.id]?.st)||'novo';
    const wa=l.wa?`<a class="btn-wa" href="https://wa.me/${{l.wa}}" target="_blank"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>WA</a>`:'';
    const tel=l.tel?`<a class="btn-tel" href="tel:${{l.tel.replace(/\\s/g,'')}}">${{l.tel}}</a>`:`<span style="color:var(--muted);font-size:.75rem">Sem tel.</span>`;
    const div=document.createElement('div');
    div.className='card'; div.id='c'+l.id;
    div.innerHTML=`<div class="card-top" onclick="tog(${{l.id}})">
        <div class="cnum">${{page*PAGE+i+1}}</div>
        <div class="cinfo">
          <div class="cnome">${{l.nome}}</div>
          <div class="csub">
            <span class="badge" style="${{l.badge}}">${{l.cat}}</span>
            <span class="badge bsw">Sem website</span>
            <span class="caddr">📍 ${{l.morada||l.cidade}}</span>
            ${{l.rating?`<span class="cstars">${{l.stars}}</span><span class="caval">(${{l.aval}} aval.)</span>`:''}}
          </div>
        </div>
        <div class="cacoes" onclick="event.stopPropagation()">
          ${{tel}}${{wa}}
          <select class="ssel s-${{st}}" onchange="setSt(${{l.id}},this.value)">
            <option value="novo" ${{st==='novo'?'selected':''}}>🔵 Novo</option>
            <option value="contactado" ${{st==='contactado'?'selected':''}}>📞 Contactado</option>
            <option value="interessado" ${{st==='interessado'?'selected':''}}>⭐ Interessado</option>
            <option value="fechado" ${{st==='fechado'?'selected':''}}>✅ Fechado</option>
            <option value="recusado" ${{st==='recusado'?'selected':''}}>❌ Recusado</option>
          </select>
          <button class="btn-p" onclick="tog(${{l.id}})">Pitch ▾</button>
        </div>
      </div>
      <div class="ppanel" id="p${{l.id}}">
        <div class="ps"><h4>1. Abertura</h4><div class="pb ab">${{l.pitch.abertura}}</div></div>
        <div class="ps"><h4>2. Gancho</h4><div class="pb ga">${{l.pitch.gancho}}</div></div>
        <div class="ps"><h4>3. Proposta</h4><div class="pb pr">${{l.pitch.proposta}}</div></div>
        <div class="ps"><h4>4. Call to Action</h4><div class="pb ct">${{l.pitch.cta}}</div></div>
        <div class="ps"><h4>5. Objeções</h4><div class="pb ob">${{l.pitch.obj1}}\\n${{l.pitch.obj2}}\\n${{l.pitch.obj3}}</div></div>
        ${{l.wa?`<div class="ps"><h4>Mensagem WhatsApp</h4>
          <div class="wa-box" id="wm${{l.id}}">${{l.pitch.wa_msg}}<button class="cbtn" onclick="cpWA(${{l.id}})">Copiar</button></div>
          <a class="btn-wa" style="margin-top:8px;display:inline-flex" href="https://wa.me/${{l.wa}}?text=${{encodeURIComponent(l.pitch.wa_msg)}}" target="_blank">Abrir WhatsApp com mensagem</a>
        </div>`:''}}
        <div class="nota-w"><h4 style="font-size:.67rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px">Notas</h4>
          <textarea id="nt${{l.id}}" placeholder="Notas..." oninput="svNota(${{l.id}})"></textarea>
        </div>
      </div>`;
    const ta=div.querySelector('textarea');
    if(ta) ta.value=(s[l.id]?.nota)||'';
    frag.appendChild(div);
  }});
  lista.appendChild(frag);
  // botão "carregar mais"
  const old=document.getElementById('load-more');
  if(old) old.remove();
  if((page+1)*PAGE < fl.length){{
    const btn=document.createElement('button');
    btn.id='load-more';
    btn.textContent=`Carregar mais (${{fl.length-(page+1)*PAGE}} restantes)`;
    btn.style.cssText='display:block;margin:16px auto;background:var(--bg3);border:1px solid var(--border);color:var(--gold);padding:10px 24px;border-radius:8px;cursor:pointer;font-size:.85rem;width:100%';
    btn.onclick=()=>{{page++;renderPage(fl,s,false)}};
    lista.appendChild(btn);
  }}
}}
// init
(function(){{
  const s=ld(),fl=L;
  const c={{novo:0,contactado:0,interessado:0,fechado:0}};
  fl.forEach(l=>{{const st=(s[l.id]?.st)||'novo';if(c[st]!==undefined)c[st]++}});
  document.getElementById('s-t').textContent=fl.length;
  document.getElementById('s-n').textContent=c.novo;
  document.getElementById('s-c').textContent=c.contactado;
  document.getElementById('s-i').textContent=c.interessado;
  document.getElementById('s-f').textContent=c.fechado;
  document.getElementById('hstat').textContent=fl.length+' leads';
  renderPage(fl,s,true);
}})();
</script></body></html>"""
    with open(CRM_HTML,"w",encoding="utf-8") as f: f.write(html)
    print(f"  CRM guardado: {CRM_HTML} ({len(data)} leads)")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    # Carrega leads existentes (3 categorias originais)
    leads_existentes = carregar_csv(CSV_TODOS)
    print(f"Leads existentes: {len(leads_existentes)}")

    # Carrega progresso anterior dos nichos
    nichos_feitos = carregar_csv(CSV_NICHOS)
    cats_feitas   = set(r["categoria"] for r in nichos_feitos)
    print(f"Nichos já processados: {cats_feitas if cats_feitas else 'nenhum'}")

    todos_leads = leads_existentes + nichos_feitos

    for nicho in NICHOS:
        if nicho["label"] in cats_feitas:
            print(f"[{nicho['label']}] já feito — skip")
            continue

        novos = recolher_nicho(nicho)
        nichos_feitos.extend(novos)
        guardar_csv(CSV_NICHOS, nichos_feitos)  # guarda progresso

        todos_leads = leads_existentes + nichos_feitos
        gerar_crm(todos_leads)  # actualiza CRM após cada nicho
        print(f"  Total acumulado: {len(todos_leads)} leads")

    print(f"\nConcluído! {len(todos_leads)} leads totais no CRM.")

if __name__ == "__main__":
    main()
