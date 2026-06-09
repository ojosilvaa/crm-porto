"""Expansão para 1000+ leads — mínimo de código, máximo de resultados."""
import requests,csv,json,re,time,os,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')

API_KEY="AIzaSyDXbxVoQNe8AzT8aSbbmTyCQ6nzob5O-30"
SEARCH_URL="https://places.googleapis.com/v1/places:searchText"
CSV1="prospeccao_porto_sem_website.csv"   # originais (104)
CSV2="nichos_sem_website.csv"              # nichos porto (166)
CSV3="expansao_leads.csv"                  # novo ficheiro incremental
CRM_HTML="crm_prospeccao.html"
CAMPOS=["nome","categoria","cidade","morada","telefone","rating","avaliacoes","tem_website","website_url"]
OBJETIVO=20
FM="places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount"

# ── Cidades novas ─────────────────────────────────────────────────────────────
CIDADES={
    "Braga":     {"lat":41.5454,"lon":-8.4265,"r":10000},
    "Lisboa":    {"lat":38.7223,"lon":-9.1393,"r":12000},
    "Coimbra":   {"lat":40.2033,"lon":-8.4103,"r":9000},
    "Aveiro":    {"lat":40.6443,"lon":-8.6455,"r":8000},
    "Guimaraes": {"lat":41.4435,"lon":-8.2976,"r":8000},
    "Setubal":   {"lat":38.5244,"lon":-8.8882,"r":8000},
    "Viseu":     {"lat":40.6566,"lon":-7.9122,"r":7000},
    "Faro":      {"lat":37.0194,"lon":-7.9323,"r":9000},
    "Leiria":    {"lat":39.7436,"lon":-8.8071,"r":7000},
    "Viana":     {"lat":41.6936,"lon":-8.8338,"r":7000},
}

# ── Nichos existentes × novas cidades ────────────────────────────────────────
NICHOS_BASE={
    "Cabeleireiro":    ["salao cabeleireiro","cabeleireiro hairstylist"],
    "Estetica":        ["centro estetica beleza","estetica avancada"],
    "Dentaria":        ["clinica dentaria","medico dentista"],
    "Oficina":         ["oficina mecanica","mecanico automovel"],
    "Fisioterapia":    ["fisioterapeuta","clinica fisioterapia"],
    "Restaurante":     ["tasca restaurante tipico","restaurante tradicional"],
    "Explicacoes":     ["centro explicacoes","explicador"],
    "Pastelaria":      ["padaria pastelaria artesanal","pastelaria cafe"],
    "Advocacia":       ["advogado escritorio","solicitador advogado"],
    "Limpeza":         ["empresa limpeza","limpeza domicilios"],
    "ArtesMarc":       ["academia artes marciais","box judo crossfit"],
    "Veterinario":     ["clinica veterinaria","veterinario"],
    "Psicologo":       ["psicologo terapeuta","psicologa clinica"],
}

# ── Novos nichos (Porto + todas as cidades) ───────────────────────────────────
NOVOS_NICHOS=[
    {"label":"Escola Conducao",     "q":["escola de conducao autoescola","autoescola"]},
    {"label":"Creche ATL",          "q":["creche infantil","ATL jardim infancia"]},
    {"label":"Personal Trainer",    "q":["personal trainer ginasio","ginasio fitness studio"]},
    {"label":"Escola Musica Danca", "q":["escola musica danca","academia danca ballet"]},
    {"label":"Fotografo Studio",    "q":["fotografo estudio fotografia","estudio fotografico"]},
    {"label":"Mudancas Transportes",    "q":["empresa mudancas transportes","mudancas residenciais"]},
    {"label":"Eletricista",         "q":["eletricista servicos eletricos","instalacoes eletricas"]},
    {"label":"Loja Roupa Moda",     "q":["loja roupa moda boutique","loja moda vestuario"]},
    {"label":"Relojoeiro Ourivesaria","q":["relojoeiro ourivesaria","joalharia ourivesaria"]},
    {"label":"Catering Eventos",    "q":["catering eventos empresas","servico catering festas"]},
    {"label":"Reparacao Eletrodom", "q":["reparacao eletrodomesticos","tecnico electrodomesticos"]},
    {"label":"Pintor Construcao",   "q":["pintor obras construcao","servicos pinturas paredes"]},
    {"label":"Farmacia",            "q":["farmacia independente","farmacia comunitaria"]},
    {"label":"Agencia Viagens",     "q":["agencia viagens turismo","agencia turistica"]},
    {"label":"Hotel Pensao",        "q":["hotel pensao residencial","pensao alojamento"]},
]

# Limpa entradas malformadas (o dict duplo acima)
NOVOS_NICHOS=[n for n in NOVOS_NICHOS if isinstance(n.get("q"),list)]

# ── Helpers ───────────────────────────────────────────────────────────────────
def search(q,lat,lon,r,tok=None):
    h={"Content-Type":"application/json","X-Goog-Api-Key":API_KEY,"X-Goog-FieldMask":FM}
    b={"textQuery":q,"languageCode":"pt","maxResultCount":20,
       "locationBias":{"circle":{"center":{"latitude":lat,"longitude":lon},"radius":float(r)}}}
    if tok: b["pageToken"]=tok
    try:
        r2=requests.post(SEARCH_URL,json=b,headers=h,timeout=12)
        if r2.status_code!=200: return [],None
        d=r2.json(); return d.get("places",[]),d.get("nextPageToken")
    except: return [],None

def cidade_str(end):
    if not end: return ""
    for p in [x.strip() for x in end.split(",")]:
        if any(k in p.lower() for k in ["braga","lisboa","coimbra","aveiro","guimar","porto","gaia","matosinhos","maia","setubal","viseu","faro","leiria","viana","gondomar","valongo","matosinhos"]):
            return p
    return end.split(",")[0].strip()

def load(f):
    if not os.path.exists(f): return []
    with open(f,encoding="utf-8-sig") as h: return list(csv.DictReader(h))

def save(f,rows):
    with open(f,"w",newline="",encoding="utf-8-sig") as h:
        w=csv.DictWriter(h,fieldnames=CAMPOS,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def fetch_sem_website(queries,lat,lon,r,objetivo=OBJETIVO):
    todos={}
    for q in queries:
        places,tok=search(q,lat,lon,r)
        for p in places:
            pid=p.get("id")
            if pid and pid not in todos: todos[pid]=p
        if tok:
            time.sleep(1.2)
            places2,_=search(q,lat,lon,r,tok)
            for p in places2:
                pid=p.get("id")
                if pid and pid not in todos: todos[pid]=p
        sem=sum(1 for p in todos.values() if not p.get("websiteUri"))
        if sem>=objetivo*2: break
    rows=[]
    for p in todos.values():
        if p.get("websiteUri"): continue
        rows.append({
            "nome":p.get("displayName",{}).get("text",""),
            "morada":p.get("formattedAddress",""),
            "cidade":cidade_str(p.get("formattedAddress","")),
            "telefone":p.get("nationalPhoneNumber",""),
            "rating":round(p["rating"],1) if p.get("rating") else "",
            "avaliacoes":p.get("userRatingCount",0),
            "tem_website":"nao","website_url":"",
        })
    rows.sort(key=lambda x:int(x["avaliacoes"]) if str(x["avaliacoes"]).isdigit() else 0)
    return rows[:objetivo]

# ── CRM (compacto, lazy) ──────────────────────────────────────────────────────
BADGE={
    "Cabeleireiro":"background:#1a2a1a;color:#5DCA9A","Estetica":"background:#2a1a3a;color:#A78BFA",
    "Dentaria":"background:#1a2a3a;color:#4A9EFF","Oficina":"background:#2a1a0d;color:#FF9A3C",
    "Fisioterapia":"background:#0d2a2a;color:#4ECDC4","Restaurante":"background:#2a0d0d;color:#FF6B6B",
    "Explicacoes":"background:#0d1a2a;color:#4A9EFF","Pastelaria":"background:#2a200d;color:#FFD166",
    "Advocacia":"background:#1a1a1a;color:#aaa","Limpeza":"background:#0d2a0d;color:#5DCA9A",
    "ArtesMarc":"background:#2a0a0a;color:#FF4444","Veterinario":"background:#0d200d;color:#7BC67E",
    "Psicologo":"background:#1a0d2a;color:#C77DFF","Escola Conducao":"background:#2a1a0d;color:#FFB347",
    "Creche ATL":"background:#0d1a2a;color:#87CEEB","Personal Trainer":"background:#0d2a10;color:#00FF7F",
    "Escola Musica Danca":"background:#1a0a2a;color:#DDA0DD","Fotografo Studio":"background:#1a1a2a;color:#B0C4DE",
    "Mudancas Transportes":"background:#2a1a0a;color:#DEB887","Eletricista":"background:#1a1a0a;color:#FFD700",
    "Loja Roupa Moda":"background:#2a0a1a;color:#FFB6C1","Relojoeiro Ourivesaria":"background:#1a1a0d;color:#DAA520",
    "Catering Eventos":"background:#0d2a1a;color:#90EE90","Reparacao Eletrodom":"background:#1a2a2a;color:#20B2AA",
    "Pintor Construcao":"background:#2a2a0d;color:#ADFF2F","Farmacia":"background:#0a2a0a;color:#32CD32",
    "Agencia Viagens":"background:#0a1a2a;color:#00BFFF","Hotel Pensao":"background:#2a1a1a;color:#F4A460",
    "Clinica Dentaria":"background:#1a2a3a;color:#4A9EFF","Centro de Estetica":"background:#2a1a3a;color:#A78BFA",
    "Salao de Cabeleireiro":"background:#1a2a1a;color:#5DCA9A","Oficina Mecanica":"background:#2a1a0d;color:#FF9A3C",
    "Fisioterapeuta":"background:#0d2a2a;color:#4ECDC4","Restaurante Tasca":"background:#2a0d0d;color:#FF6B6B",
    "Centro de Explicacoes":"background:#0d1a2a;color:#4A9EFF","Padaria Pastelaria":"background:#2a200d;color:#FFD166",
    "Advogado Solicitador":"background:#1a1a1a;color:#aaa","Empresa de Limpeza":"background:#0d2a0d;color:#5DCA9A",
    "Academia Artes Marciais":"background:#2a0a0a;color:#FF4444","Psicologo Terapeuta":"background:#1a0d2a;color:#C77DFF",
}

def wa(tel):
    d=re.sub(r"\D","",tel)
    if d.startswith("351"): d=d[3:]
    return f"351{d}" if len(d)==9 and d[0]=="9" else None

def st(r):
    try:
        r=float(r); f=int(r); h=1 if r-f>=0.5 else 0
        return "★"*f+("½"if h else "")+"☆"*(5-f-h)
    except: return ""

def gpitch(row):
    n=row["nome"]; cat=row.get("categoria",""); c=row.get("cidade","Porto").split(",")[0].strip()
    try: av=int(row["avaliacoes"])
    except: av=0
    try: rt=float(row["rating"])
    except: rt=0.0
    if av<5: g=f"A {n} ainda não tem avaliações no Google — sem website é invisível online."
    elif av<20: g=f"A {n} tem {av} avaliações. Sem website, quem pesquisa passa para a concorrência."
    elif av<60: g=f"Com {av} avaliações, a {n} tem reputação. Um website vai multiplicar a visibilidade."
    else: g=f"A {n} tem {av} avaliações. Sem website perde clientes que pesquisam online."
    ex=""
    if rt>0 and rt<4.0: ex=f" Com {rt} de rating, um website com depoimentos vai melhorar a perceção."
    elif rt>=4.8: ex=f" Com {rt}★ — um website mostra esse excelente serviço ao mundo."
    return {"ab":f"Boa tarde, falo com o/a responsável pela {n}?",
            "ga":g+ex,
            "pr":f"Criaria um website profissional para a {n} com marcações, serviços e localização — pronto em 2 semanas.",
            "ct":f"Posso enviar-lhe agora 3 exemplos de websites que fiz para negócios em {c}?",
            "ob":f"'Tenho redes' → 'Google só mostra websites nas pesquisas locais.'\\n'É caro' → 'Recupera em 1-2 meses de novos clientes.'\\n'Sem tempo' → 'Eu trato de tudo — só preciso 30 min da sua parte.'",
            "wa":f"Olá! Crio websites profissionais para negócios em {c}. Vi a {n} no Google — gostaria de mostrar exemplos. Posso enviar?"}

def gerar_crm(todos):
    cats=sorted(set(r.get("categoria","") for r in todos))
    copts="".join(f'<button class="bf" onclick="sF(\'c\',\'{c}\')">{c}</button>' for c in cats)
    data=[]
    for row in todos:
        t=row.get("telefone",""); w=wa(t); p=gpitch(row)
        data.append({"id":len(data),"nome":row["nome"],"cat":row.get("categoria",""),
                     "cidade":row.get("cidade","").split(",")[0].strip(),
                     "morada":row.get("morada",row.get("cidade","")),"tel":t,"wa":w,
                     "r":row.get("rating",""),"av":row.get("avaliacoes",0),
                     "st":st(row.get("rating","")),"p":p,
                     "bg":BADGE.get(row.get("categoria",""),"background:#222;color:#aaa")})
    js=json.dumps(data,ensure_ascii=False)
    html="""<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRM Prospeção Portugal</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d0d0d;--bg2:#141414;--bg3:#1c1c1c;--bg4:#252525;--bo:#2a2a2a;--go:#C8A96E;--gr:#5DCA9A;--re:#e05555;--bl:#4A9EFF;--tx:#f0f0f0;--mu:#666}
body{background:var(--bg);color:var(--tx);font-family:'Segoe UI',sans-serif}
.h{background:var(--bg2);border-bottom:1px solid var(--bo);padding:12px 18px;display:flex;align-items:center;position:sticky;top:0;z-index:100}
.h h1{font-size:1rem;font-weight:700;color:var(--go)}
.h span{color:var(--mu);font-size:.8rem;margin-left:8px}
.ss{display:flex;gap:8px;padding:14px 18px;flex-wrap:wrap}
.s{background:var(--bg3);border:1px solid var(--bo);border-radius:9px;padding:10px 14px;text-align:center;min-width:90px}
.sn{font-size:1.5rem;font-weight:700;color:var(--go)}.sl{font-size:.7rem;color:var(--mu);margin-top:2px}
.fs{padding:0 18px 10px;display:flex;gap:5px;flex-wrap:wrap;align-items:center}
.fs label{color:var(--mu);font-size:.75rem}
.bf{background:var(--bg3);border:1px solid var(--bo);color:var(--mu);padding:4px 10px;border-radius:18px;cursor:pointer;font-size:.72rem;transition:.15s}
.bf:hover,.bf.on{background:var(--go);border-color:var(--go);color:#000;font-weight:600}
.sp{width:1px;height:18px;background:var(--bo);margin:0 2px}
.sw{padding:0 18px 10px}
#sr{width:100%;background:var(--bg3);border:1px solid var(--bo);border-radius:7px;padding:8px 12px;color:var(--tx);font-size:.85rem;outline:none}
#sr:focus{border-color:var(--go)}
.l{padding:0 18px 40px;display:flex;flex-direction:column;gap:8px}
.cd{background:var(--bg2);border:1px solid var(--bo);border-radius:9px;overflow:hidden}
.ct{display:flex;align-items:flex-start;gap:10px;padding:12px}
.cn{background:var(--bg4);border-radius:6px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:.68rem;color:var(--mu);flex-shrink:0;font-weight:700}
.ci{flex:1;min-width:0}
.cm{font-weight:700;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cx{display:flex;align-items:center;gap:5px;margin-top:3px;flex-wrap:wrap}
.ba{font-size:.62rem;padding:2px 6px;border-radius:8px;font-weight:600;white-space:nowrap}
.bsw{background:#2a0d0d;color:#e05555}
.cad{font-size:.7rem;color:var(--mu)}
.cac{display:flex;gap:5px;align-items:center;flex-shrink:0}
.wa{background:#25D366;border:none;color:#fff;border-radius:6px;padding:5px 9px;font-size:.72rem;font-weight:600;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:3px;white-space:nowrap}
.tel{background:var(--bg4);border:1px solid var(--bo);color:var(--tx);border-radius:6px;padding:5px 9px;font-size:.72rem;cursor:pointer;text-decoration:none;white-space:nowrap}
.ss2{padding:4px 5px;border-radius:5px;border:1px solid var(--bo);background:var(--bg4);color:var(--tx);font-size:.7rem;cursor:pointer;outline:none}
.s-novo{border-color:#444;color:#aaa}.s-contactado{border-color:var(--bl);color:var(--bl);background:#0d1a2a}
.s-interessado{border-color:var(--go);color:var(--go);background:#1a140a}
.s-fechado{border-color:var(--gr);color:var(--gr);background:#0d1a10}
.s-recusado{border-color:var(--re);color:var(--re);background:#1a0d0d}
.bp{background:var(--bg4);border:1px solid var(--bo);color:var(--go);border-radius:6px;padding:5px 9px;font-size:.72rem;cursor:pointer}
.bp:hover{background:var(--go);color:#000}
.pp{display:none;border-top:1px solid var(--bo);padding:14px}
.pp.o{display:block}
.ps{margin-bottom:12px}
.ps h4{font-size:.63rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.07em;margin-bottom:5px}
.pb{background:var(--bg3);border:1px solid var(--bo);border-radius:6px;padding:10px;font-size:.8rem;line-height:1.55;white-space:pre-wrap}
.pb.a{border-left:3px solid var(--bl);color:var(--bl)}.pb.g{border-left:3px solid var(--go)}
.pb.p{border-left:3px solid var(--gr)}.pb.c{border-left:3px solid #A78BFA;color:#A78BFA}
.pb.o{border-left:3px solid #444;color:#aaa;font-size:.75rem}
.wb{background:#0a1a0f;border:1px solid #25D366;border-radius:6px;padding:10px;font-size:.78rem;color:#a0f0b0;position:relative;margin-top:6px}
.cb{position:absolute;top:6px;right:6px;background:var(--bg3);border:1px solid var(--bo);color:var(--mu);border-radius:4px;padding:2px 7px;font-size:.65rem;cursor:pointer}
.nw{margin-top:8px}
.nw textarea{width:100%;background:var(--bg3);border:1px solid var(--bo);border-radius:6px;color:var(--tx);padding:8px;font-size:.78rem;resize:vertical;min-height:55px;outline:none;font-family:inherit}
.nw textarea:focus{border-color:var(--go)}
.em{text-align:center;padding:40px;color:var(--mu)}
.lm{display:block;margin:14px auto;background:var(--bg3);border:1px solid var(--bo);color:var(--go);padding:9px 20px;border-radius:7px;cursor:pointer;font-size:.82rem;width:100%;text-align:center}
.lm:hover{background:var(--go);color:#000}
</style></head><body>
<div class="h"><div><h1>CRM Prospeção<span>Websites · Portugal</span></h1></div>
  <div style="margin-left:auto;display:flex;gap:7px;align-items:center">
    <span id="hs" style="font-size:.75rem;color:var(--mu)"></span>
    <button onclick="expN()" style="background:var(--bg3);border:1px solid var(--bo);color:var(--mu);padding:4px 9px;border-radius:6px;cursor:pointer;font-size:.7rem">Exportar</button>
  </div>
</div>
<div class="ss">
  <div class="s"><div class="sn" id="st2">0</div><div class="sl">Total</div></div>
  <div class="s"><div class="sn" id="sn2" style="color:var(--mu)">0</div><div class="sl">Novos</div></div>
  <div class="s"><div class="sn" id="sc2" style="color:var(--bl)">0</div><div class="sl">Contactados</div></div>
  <div class="s"><div class="sn" id="si2" style="color:var(--go)">0</div><div class="sl">Interessados</div></div>
  <div class="s"><div class="sn" id="sf2" style="color:var(--gr)">0</div><div class="sl">Fechados</div></div>
</div>
<div class="fs">
  <label>Cat:</label>
  <button class="bf on" onclick="sF('c','')">Todos</button>"""+copts+"""
  <div class="sp"></div>
  <label>Estado:</label>
  <button class="bf on" onclick="sF('s','')">Todos</button>
  <button class="bf" onclick="sF('s','novo')">Novos</button>
  <button class="bf" onclick="sF('s','contactado')">Contactados</button>
  <button class="bf" onclick="sF('s','interessado')">Interessados</button>
  <button class="bf" onclick="sF('s','fechado')">Fechados</button>
  <button class="bf" onclick="sF('s','recusado')">Recusados</button>
</div>
<div class="sw"><input id="sr" placeholder="Pesquisar nome ou cidade..." oninput="rnd()"></div>
<div class="l" id="ll"></div>
<script>
const L="""+js+""";
let F={c:'',s:''},PG=25,pg=0,FL=[];
const ld=()=>{try{return JSON.parse(localStorage.getItem('crm4')||'{}')}catch(e){return {}}};
const sv=s=>localStorage.setItem('crm4',JSON.stringify(s));
function sF(k,v){F[k]=v;document.querySelectorAll('.bf').forEach(b=>{const o=b.getAttribute('onclick')||'';b.classList.toggle('on',o.includes("'"+k+"'")&&o.includes("'"+v+"'"))});rnd()}
function rnd(){
  const s=ld(),q=(document.getElementById('sr').value||'').toLowerCase();
  FL=L.filter(l=>{const st=(s[l.id]?.st)||'novo';
    if(F.c&&l.cat!==F.c)return false;
    if(F.s&&st!==F.s)return false;
    if(q&&!l.nome.toLowerCase().includes(q)&&!l.cidade.toLowerCase().includes(q))return false;
    return true});
  const c={novo:0,contactado:0,interessado:0,fechado:0};
  L.forEach(l=>{const st=(s[l.id]?.st)||'novo';if(c[st]!==undefined)c[st]++});
  document.getElementById('st2').textContent=L.length;
  document.getElementById('sn2').textContent=c.novo;
  document.getElementById('sc2').textContent=c.contactado;
  document.getElementById('si2').textContent=c.interessado;
  document.getElementById('sf2').textContent=c.fechado;
  document.getElementById('hs').textContent=FL.length+' leads';
  pg=0;document.getElementById('ll').innerHTML='';rp();
}
function rp(){
  const s=ld(),sl=FL.slice(pg*PG,(pg+1)*PG),ll=document.getElementById('ll');
  const ob=document.getElementById('lmbtn');if(ob)ob.remove();
  if(!FL.length&&pg===0){ll.innerHTML='<div class="em">Sem resultados.</div>';return}
  sl.forEach((l,i)=>{
    const st=(s[l.id]?.st)||'novo';
    const wb=l.wa?`<a class="wa" href="https://wa.me/${l.wa}" target="_blank">WA</a>`:'';
    const tb=l.tel?`<a class="tel" href="tel:${l.tel.replace(/\\s/g,'')}">${l.tel}</a>`:`<span style="color:var(--mu);font-size:.7rem">Sem tel.</span>`;
    const d=document.createElement('div');d.className='cd';d.id='cd'+l.id;
    d.innerHTML=`<div class="ct">
      <div class="cn">${pg*PG+i+1}</div>
      <div class="ci"><div class="cm">${l.nome}</div>
        <div class="cx">
          <span class="ba" style="${l.bg}">${l.cat}</span>
          <span class="ba bsw">Sem website</span>
          <span class="cad">📍 ${l.morada||l.cidade}</span>
          ${l.r?`<span style="color:var(--go);font-size:.7rem">${l.st}</span><span style="color:var(--mu);font-size:.67rem">(${l.av} aval.)</span>`:''}
        </div>
      </div>
      <div class="cac" onclick="event.stopPropagation()">
        ${tb}${wb}
        <select class="ss2 s-${st}" onchange="sst(${l.id},this.value)">
          <option value="novo" ${st==='novo'?'selected':''}>🔵 Novo</option>
          <option value="contactado" ${st==='contactado'?'selected':''}>📞 Contactado</option>
          <option value="interessado" ${st==='interessado'?'selected':''}>⭐ Interessado</option>
          <option value="fechado" ${st==='fechado'?'selected':''}>✅ Fechado</option>
          <option value="recusado" ${st==='recusado'?'selected':''}>❌ Recusado</option>
        </select>
        <button class="bp" onclick="tog(${l.id})">Pitch ▾</button>
      </div>
    </div>
    <div class="pp" id="pp${l.id}">
      <div class="ps"><h4>Abertura</h4><div class="pb a">${l.p.ab}</div></div>
      <div class="ps"><h4>Gancho</h4><div class="pb g">${l.p.ga}</div></div>
      <div class="ps"><h4>Proposta</h4><div class="pb p">${l.p.pr}</div></div>
      <div class="ps"><h4>Call to Action</h4><div class="pb c">${l.p.ct}</div></div>
      <div class="ps"><h4>Objeções</h4><div class="pb o">${l.p.ob}</div></div>
      ${l.wa?`<div class="ps"><h4>WhatsApp</h4>
        <div class="wb" id="wm${l.id}">${l.p.wa}<button class="cb" onclick="cpw(${l.id})">Copiar</button></div>
        <a class="wa" style="margin-top:6px;display:inline-flex" href="https://wa.me/${l.wa}?text=${encodeURIComponent(l.p.wa)}" target="_blank">Abrir WA</a></div>`:''}
      <div class="nw"><h4 style="font-size:.63rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px">Notas</h4>
        <textarea id="nt${l.id}" placeholder="Notas..." oninput="svn(${l.id})"></textarea></div>
    </div>`;
    const ta=d.querySelector('textarea');if(ta)ta.value=(s[l.id]?.nota)||'';
    ll.appendChild(d);
  });
  if((pg+1)*PG<FL.length){
    const b=document.createElement('button');b.className='lm';b.id='lmbtn';
    b.textContent='Carregar mais '+(FL.length-(pg+1)*PG)+' leads';
    b.onclick=()=>{pg++;rp()};ll.appendChild(b);
  }
}
function tog(id){document.getElementById('pp'+id).classList.toggle('o')}
function sst(id,v){const s=ld();if(!s[id])s[id]={};s[id].st=v;sv(s);
  const el=document.querySelector('#cd'+id+' .ss2');if(el)el.className='ss2 s-'+v;
  const c={novo:0,contactado:0,interessado:0,fechado:0};
  L.forEach(l=>{const st=(s[l.id]?.st)||'novo';if(c[st]!==undefined)c[st]++});
  document.getElementById('sn2').textContent=c.novo;document.getElementById('sc2').textContent=c.contactado;
  document.getElementById('si2').textContent=c.interessado;document.getElementById('sf2').textContent=c.fechado}
function svn(id){const s=ld();if(!s[id])s[id]={};const t=document.getElementById('nt'+id);if(t)s[id].nota=t.value;sv(s)}
function cpw(id){const el=document.getElementById('wm'+id);const b=el.querySelector('.cb');
  navigator.clipboard.writeText(el.childNodes[0].textContent.trim()).then(()=>{b.textContent='✓';setTimeout(()=>b.textContent='Copiar',2000)})}
function expN(){const s=ld();let t='CRM '+new Date().toLocaleDateString('pt-PT')+'\\n\\n';
  L.forEach(l=>{const d=s[l.id];if(!d||(!d.nota&&(!d.st||d.st==='novo')))return;
    t+=`[${(d.st||'novo').toUpperCase()}] ${l.nome} (${l.cidade}) — ${l.tel||'—'}\\n`;
    if(d.nota)t+='Nota: '+d.nota+'\\n';t+='\\n'});
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([t],{type:'text/plain'}));
  a.download='crm_notas_'+new Date().toISOString().slice(0,10)+'.txt';a.click()}
rnd();
</script></body></html>"""
    with open(CRM_HTML,"w",encoding="utf-8") as f: f.write(html)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    base1=load(CSV1); base2=load(CSV2); expansao=load(CSV3)
    feitos=set(r["categoria"] for r in expansao)
    print(f"Base: {len(base1)+len(base2)} | Expansão já feita: {len(expansao)} ({len(feitos)} nichos)")

    tarefas=[]
    # Nichos base × novas cidades
    for label,queries in NICHOS_BASE.items():
        for cname,cloc in CIDADES.items():
            key=f"{label}-{cname}"
            if key not in feitos:
                tarefas.append({"key":key,"queries":[f"{q} {cname}" for q in queries],"loc":cloc})
    # Novos nichos × Porto + todas as cidades
    porto={"lat":41.1579,"lon":-8.6291,"r":12000}
    todas={"Porto":porto,**CIDADES}
    for nicho in NOVOS_NICHOS:
        for cname,cloc in todas.items():
            key=f"{nicho['label']}-{cname}"
            if key not in feitos:
                tarefas.append({"key":key,"queries":[f"{q} {cname}" for q in nicho["q"]],"loc":cloc})

    print(f"Tarefas pendentes: {len(tarefas)}")
    todos=base1+base2+expansao

    for i,t in enumerate(tarefas):
        sys.stdout.write(f"\r[{i+1}/{len(tarefas)}] {t['key']:<40}")
        sys.stdout.flush()
        novos=fetch_sem_website(t["queries"],t["loc"]["lat"],t["loc"]["lon"],t["loc"]["r"])
        # etiqueta categoria
        for r in novos: r["categoria"]=t["key"]
        expansao.extend(novos)
        feitos.add(t["key"])
        save(CSV3,expansao)  # guarda incrementalmente
        todos=base1+base2+expansao
        # actualiza CRM a cada 20 tarefas
        if (i+1)%20==0 or (i+1)==len(tarefas):
            gerar_crm(todos)
            print(f"\n  CRM actualizado: {len(todos)} leads totais")
        if len(todos)>=1000:
            print(f"\n1000 leads atingido! Total: {len(todos)}")
            gerar_crm(todos)
            break

    print(f"\nFim. Total: {len(todos)} leads")
    gerar_crm(todos)

if __name__=="__main__":
    main()
