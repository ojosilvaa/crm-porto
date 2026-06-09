import csv, json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CSV_FILE = "prospeccao_porto_sem_website.csv"
OUTPUT   = "crm_prospeccao.html"

# ── helpers ──────────────────────────────────────────────────────────────────

def wa_number(tel):
    """Devolve número PT formatado para wa.me, ou None se fixo."""
    d = re.sub(r'\D', '', tel)
    if d.startswith('351'): d = d[3:]
    if len(d) == 9 and d[0] == '9':
        return f"351{d}"
    return None

def stars(rating):
    try:
        r = float(rating)
        full  = int(r)
        half  = 1 if (r - full) >= 0.5 else 0
        empty = 5 - full - half
        return '★'*full + ('½' if half else '') + '☆'*empty
    except:
        return '☆☆☆☆☆'

def pitch(row):
    nome  = row['nome']
    cat   = row['categoria']
    cidade= row['cidade'].split(',')[0].strip()
    try:    aval = int(row['avaliacoes'])
    except: aval = 0
    try:    rat  = float(row['rating'])
    except: rat  = 0.0

    # ângulo personalizado
    if aval == 0 or aval < 5:
        gancho = f"A {nome} ainda não aparece com muitas avaliações no Google — e sem website, fica praticamente invisível para quem pesquisa online."
    elif aval < 20:
        gancho = f"A {nome} já tem {aval} avaliações no Google, o que é ótimo. O problema é que quem pesquisa online e não encontra website, passa logo para a concorrência."
    elif aval < 60:
        gancho = f"Com {aval} avaliações no Google, a {nome} já tem uma boa reputação. Um website profissional vai multiplicar a visibilidade e atrair clientes que ainda não sabem que existem."
    else:
        gancho = f"A {nome} tem {aval} avaliações — uma das mais avaliadas da zona. Sem website, está a deixar dinheiro na mesa: clientes que pesquisam online e não encontram nada de confiança."

    if rat > 0 and rat < 4.0:
        extra = f"Além disso, com rating de {rat}, um website com depoimentos e apresentação profissional pode melhorar a perceção da marca."
    elif rat >= 4.8:
        extra = f"Com {rat} de rating, têm claramente um serviço excecional — um website vai mostrar isso ao mundo."
    else:
        extra = ""

    if cat == "Clinica Dentaria":
        chamada, area, features = "pacientes", "clínica dentária", "marcações online, apresentação da equipa e localização no mapa"
        abertura = "Boa tarde, estou a falar com o/a responsável pela clínica?"
    elif cat == "Centro de Estetica":
        chamada, area, features = "clientes", "centro de estética", "galeria de tratamentos, preçário e marcações online"
        abertura = "Boa tarde, falo com o/a responsável pelo centro?"
    else:
        chamada, area, features = "clientes", "salão de cabeleireiro", "galeria de trabalhos, preçário e marcações online"
        abertura = "Boa tarde, falo com o/a dono/a do salão?"

    wa_msg = f"Olá! Trabalho com {area}s no Porto a criar websites profissionais. Vi a {nome} no Google e gostaria de mostrar alguns exemplos de trabalhos similares. Posso enviar?"

    return {
        "abertura": abertura,
        "gancho": gancho,
        "extra": extra,
        "proposta": f"Criaria um website profissional para a {nome} com {features} — tudo pronto em menos de 2 semanas, com garantia de satisfação.",
        "cta": "Posso enviar-lhe agora mesmo 3 exemplos de websites que fiz para negócios semelhantes aqui no Porto?",
        "obj1": f"'Já tenho Instagram/Facebook' → 'As redes são ótimas, mas o Google só mostra websites nas pesquisas. Um cliente que pesquisa \"{area} em {cidade}\" só encontra quem tem website.'",
        "obj2": "\"É caro\" → 'O investimento é único, sem mensalidades. A maioria dos meus clientes recupera em 1 a 2 meses com os novos clientes que chegam pelo website.'",
        "obj3": "\"Não tenho tempo\" → 'Eu trato de tudo. Preciso só de 30 minutos da sua parte para recolher as informações. O resto é comigo.'",
        "wa_msg": wa_msg,
        "cidade": cidade,
        "area": area,
    }

# ── ler CSV e montar leads ───────────────────────────────────────────────────

leads = []
with open(CSV_FILE, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        tel   = row['telefone'].strip()
        wa    = wa_number(tel)
        p     = pitch(row)
        leads.append({
            "id":       len(leads),
            "nome":     row['nome'],
            "cat":      row['categoria'],
            "cidade":   row['cidade'].split(',')[0].strip(),
            "morada":   row.get('morada', row.get('cidade', '')),
            "tel":      tel,
            "wa":       wa,
            "rating":   row['rating'],
            "aval":     row['avaliacoes'],
            "tem_website": row.get('tem_website','nao'),
            "website":  row.get('website_url',''),
            "stars":    stars(row['rating']),
            "pitch":    p,
        })

leads_json = json.dumps(leads, ensure_ascii=False)

# ── HTML ─────────────────────────────────────────────────────────────────────

html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRM Prospeção — Websites Porto</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0d0d0d;--bg2:#141414;--bg3:#1c1c1c;--bg4:#252525;
  --border:#2a2a2a;--gold:#C8A96E;--green:#5DCA9A;--red:#e05555;
  --blue:#4A9EFF;--purple:#A78BFA;--text:#f0f0f0;--muted:#666;
}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',sans-serif;min-height:100vh}}

/* ── HEADER ── */
.header{{background:var(--bg2);border-bottom:1px solid var(--border);padding:18px 24px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:100}}
.header h1{{font-size:1.2rem;font-weight:700;color:var(--gold)}}
.header h1 span{{color:var(--muted);font-weight:400;font-size:.9rem;margin-left:8px}}

/* ── STATS ── */
.stats{{display:flex;gap:12px;padding:20px 24px;flex-wrap:wrap}}
.stat{{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:14px 20px;min-width:120px;text-align:center}}
.stat-n{{font-size:1.8rem;font-weight:700;color:var(--gold)}}
.stat-l{{font-size:.75rem;color:var(--muted);margin-top:2px}}

/* ── FILTROS ── */
.filtros{{padding:0 24px 16px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.filtros label{{color:var(--muted);font-size:.8rem;margin-right:4px}}
.btn-f{{background:var(--bg3);border:1px solid var(--border);color:var(--muted);padding:6px 14px;border-radius:20px;cursor:pointer;font-size:.8rem;transition:.2s}}
.btn-f:hover,.btn-f.active{{background:var(--gold);border-color:var(--gold);color:#000;font-weight:600}}
.sep{{width:1px;height:24px;background:var(--border);margin:0 4px}}

/* ── SEARCH ── */
.search-wrap{{padding:0 24px 16px}}
#search{{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-size:.9rem;outline:none}}
#search:focus{{border-color:var(--gold)}}

/* ── LISTA ── */
.lista{{padding:0 24px 40px;display:flex;flex-direction:column;gap:12px}}

/* ── CARD ── */
.card{{background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden;transition:.2s}}
.card:hover{{border-color:#333}}
.card-top{{display:flex;align-items:flex-start;gap:14px;padding:16px;cursor:pointer}}
.card-num{{background:var(--bg4);border-radius:8px;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-size:.75rem;color:var(--muted);flex-shrink:0;font-weight:700}}
.card-info{{flex:1;min-width:0}}
.card-nome{{font-weight:700;font-size:.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card-sub{{display:flex;align-items:center;gap:10px;margin-top:4px;flex-wrap:wrap}}
.badge{{font-size:.68rem;padding:2px 8px;border-radius:10px;font-weight:600}}
.badge-den{{background:#1a2a3a;color:#4A9EFF}}
.badge-est{{background:#2a1a3a;color:#A78BFA}}
.badge-cab{{background:#1a2a1a;color:#5DCA9A}}
.card-cidade{{font-size:.75rem;color:var(--muted)}}
.card-stars{{font-size:.75rem;color:var(--gold)}}
.card-aval{{font-size:.72rem;color:var(--muted)}}

/* ── STATUS ── */
.status-sel{{padding:4px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg4);color:var(--text);font-size:.75rem;cursor:pointer;outline:none}}
.s-novo{{border-color:#444;color:#aaa}}
.s-contactado{{border-color:var(--blue);color:var(--blue);background:#0d1a2a}}
.s-interessado{{border-color:var(--gold);color:var(--gold);background:#1a140a}}
.s-fechado{{border-color:var(--green);color:var(--green);background:#0d1a10}}
.s-recusado{{border-color:var(--red);color:var(--red);background:#1a0d0d}}

/* ── AÇÕES ── */
.card-acoes{{display:flex;gap:8px;align-items:center;flex-shrink:0}}
.btn-wa{{background:#25D366;border:none;color:#fff;border-radius:8px;padding:7px 12px;font-size:.78rem;font-weight:600;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:5px;white-space:nowrap}}
.btn-tel{{background:var(--bg4);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:7px 12px;font-size:.78rem;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:5px;white-space:nowrap}}
.btn-pitch{{background:var(--bg4);border:1px solid var(--border);color:var(--gold);border-radius:8px;padding:7px 12px;font-size:.78rem;cursor:pointer;white-space:nowrap}}
.btn-pitch:hover{{background:var(--gold);color:#000}}

/* ── PITCH PANEL ── */
.pitch-panel{{display:none;border-top:1px solid var(--border);padding:20px}}
.pitch-panel.open{{display:block}}
.pitch-section{{margin-bottom:16px}}
.pitch-section h4{{font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px}}
.pitch-box{{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:14px;font-size:.85rem;line-height:1.6;white-space:pre-wrap}}
.pitch-box.abertura{{border-left:3px solid var(--blue);color:var(--blue)}}
.pitch-box.gancho{{border-left:3px solid var(--gold)}}
.pitch-box.proposta{{border-left:3px solid var(--green)}}
.pitch-box.obj{{font-size:.8rem;color:#aaa;border-left:3px solid #444}}
.wa-msg-box{{background:#0a1a0f;border:1px solid #25D366;border-radius:8px;padding:14px;font-size:.82rem;line-height:1.5;color:#a0f0b0;position:relative}}
.copy-btn{{position:absolute;top:8px;right:8px;background:var(--bg3);border:1px solid var(--border);color:var(--muted);border-radius:6px;padding:3px 10px;font-size:.7rem;cursor:pointer}}
.copy-btn:hover{{color:var(--text)}}
.notas-wrap{{margin-top:12px}}
.notas-wrap textarea{{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:10px;font-size:.82rem;resize:vertical;min-height:70px;outline:none;font-family:inherit}}
.notas-wrap textarea:focus{{border-color:var(--gold)}}

/* ── EMPTY ── */
.empty{{text-align:center;padding:60px 20px;color:var(--muted)}}

@media(max-width:600px){{
  .card-top{{flex-wrap:wrap}}
  .card-acoes{{width:100%;justify-content:flex-end}}
  .stats{{gap:8px}}
  .stat{{min-width:90px;padding:10px}}
}}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>CRM Prospeção <span>Websites · Grande Porto</span></h1>
  </div>
  <div style="margin-left:auto;display:flex;gap:10px;align-items:center">
    <span id="hdr-stats" style="font-size:.8rem;color:var(--muted)"></span>
    <button onclick="exportNotas()" style="background:var(--bg3);border:1px solid var(--border);color:var(--muted);padding:6px 12px;border-radius:8px;cursor:pointer;font-size:.75rem">Exportar Notas</button>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-n" id="s-total">0</div><div class="stat-l">Total Leads</div></div>
  <div class="stat"><div class="stat-n" id="s-novo" style="color:var(--muted)">0</div><div class="stat-l">Novos</div></div>
  <div class="stat"><div class="stat-n" id="s-contactado" style="color:var(--blue)">0</div><div class="stat-l">Contactados</div></div>
  <div class="stat"><div class="stat-n" id="s-interessado" style="color:var(--gold)">0</div><div class="stat-l">Interessados</div></div>
  <div class="stat"><div class="stat-n" id="s-fechado" style="color:var(--green)">0</div><div class="stat-l">Fechados</div></div>
</div>

<div class="filtros">
  <label>Categoria:</label>
  <button class="btn-f active" onclick="setFiltro('cat','')">Todos</button>
  <button class="btn-f" onclick="setFiltro('cat','Clinica Dentaria')">Dentárias</button>
  <button class="btn-f" onclick="setFiltro('cat','Centro de Estetica')">Estética</button>
  <button class="btn-f" onclick="setFiltro('cat','Salao de Cabeleireiro')">Cabeleireiro</button>
  <div class="sep"></div>
  <label>Estado:</label>
  <button class="btn-f active" onclick="setFiltro('status','')">Todos</button>
  <button class="btn-f" onclick="setFiltro('status','novo')">Novos</button>
  <button class="btn-f" onclick="setFiltro('status','contactado')">Contactados</button>
  <button class="btn-f" onclick="setFiltro('status','interessado')">Interessados</button>
  <button class="btn-f" onclick="setFiltro('status','fechado')">Fechados</button>
  <button class="btn-f" onclick="setFiltro('status','recusado')">Recusados</button>
</div>

<div class="search-wrap">
  <input id="search" placeholder="🔍  Pesquisar por nome ou cidade..." oninput="renderLista()">
</div>

<div class="lista" id="lista"></div>

<script>
const LEADS = {leads_json};

// ── State ──────────────────────────────────────────────────────────────────
let filtros = {{cat:'', status:''}};

function loadState(){{
  try{{ return JSON.parse(localStorage.getItem('crm_state')||'{{}}'); }} catch{{return {{}};}}
}}
function saveState(state){{
  localStorage.setItem('crm_state', JSON.stringify(state));
}}

// ── Filtro ────────────────────────────────────────────────────────────────
function setFiltro(tipo, val){{
  filtros[tipo] = val;
  document.querySelectorAll('.filtros .btn-f').forEach(b=>{{
    const onclick = b.getAttribute('onclick')||'';
    b.classList.toggle('active',
      onclick.includes(`'${{tipo}}'`) && onclick.includes(`'${{val}}'`)
    );
  }});
  renderLista();
}}

// ── Badge ─────────────────────────────────────────────────────────────────
function badgeClass(cat){{
  if(cat.includes('Dentaria')) return 'badge-den';
  if(cat.includes('Estetica')) return 'badge-est';
  return 'badge-cab';
}}
function badgeLabel(cat){{
  if(cat.includes('Dentaria')) return 'Dentária';
  if(cat.includes('Estetica')) return 'Estética';
  return 'Cabeleireiro';
}}

// ── Pitch HTML ────────────────────────────────────────────────────────────
function pitchHTML(l){{
  const p = l.pitch;
  const waLink = l.wa
    ? `<a class="btn-wa" href="https://wa.me/${{l.wa}}?text=${{encodeURIComponent(p.wa_msg)}}" target="_blank">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
        Mensagem WA
      </a>`
    : '';

  return `
  <div class="pitch-section">
    <h4>1. Abertura (primeiros 5 seg)</h4>
    <div class="pitch-box abertura">${{p.abertura}}</div>
  </div>
  <div class="pitch-section">
    <h4>2. Gancho — porque está a ligar</h4>
    <div class="pitch-box gancho">${{p.gancho}}${{p.extra ? '\\n\\n' + p.extra : ''}}</div>
  </div>
  <div class="pitch-section">
    <h4>3. Proposta</h4>
    <div class="pitch-box proposta">${{p.proposta}}</div>
  </div>
  <div class="pitch-section">
    <h4>4. Call to Action</h4>
    <div class="pitch-box" style="border-left:3px solid var(--purple);color:var(--purple)">${{p.cta}}</div>
  </div>
  <div class="pitch-section">
    <h4>5. Objeções</h4>
    <div class="pitch-box obj">${{p.obj1}}\\n${{p.obj2}}\\n${{p.obj3}}</div>
  </div>
  ${{l.wa ? `
  <div class="pitch-section">
    <h4>Mensagem WhatsApp — copiar e enviar</h4>
    <div class="wa-msg-box" id="wa-${{l.id}}">${{p.wa_msg}}<button class="copy-btn" onclick="copyWA(${{l.id}})">Copiar</button></div>
    ${{waLink}}
  </div>` : ''}}
  <div class="notas-wrap">
    <h4 style="font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Notas</h4>
    <textarea id="nota-${{l.id}}" placeholder="Escreve aqui as tuas notas sobre este lead..." oninput="saveNota(${{l.id}})" onchange="saveNota(${{l.id}})"></textarea>
  </div>`;
}}

// ── Render ────────────────────────────────────────────────────────────────
function renderLista(){{
  const state   = loadState();
  const q       = (document.getElementById('search').value||'').toLowerCase();
  const catF    = filtros.cat;
  const statusF = filtros.status;

  const filtered = LEADS.filter(l=>{{
    const st = (state[l.id]?.status)||'novo';
    if(catF    && l.cat    !== catF)    return false;
    if(statusF && st       !== statusF) return false;
    if(q && !l.nome.toLowerCase().includes(q) && !l.cidade.toLowerCase().includes(q)) return false;
    return true;
  }});

  // stats
  const counts = {{novo:0, contactado:0, interessado:0, fechado:0, recusado:0}};
  LEADS.forEach(l=>{{ const s=(state[l.id]?.status)||'novo'; counts[s]=(counts[s]||0)+1; }});
  document.getElementById('s-total').textContent       = LEADS.length;
  document.getElementById('s-novo').textContent        = counts.novo||0;
  document.getElementById('s-contactado').textContent  = counts.contactado||0;
  document.getElementById('s-interessado').textContent = counts.interessado||0;
  document.getElementById('s-fechado').textContent     = counts.fechado||0;
  document.getElementById('hdr-stats').textContent     = `${{filtered.length}} a mostrar`;

  const lista = document.getElementById('lista');
  if(!filtered.length){{
    lista.innerHTML='<div class="empty">Nenhum lead encontrado com esses filtros.</div>';
    return;
  }}

  lista.innerHTML = filtered.map((l,idx)=>{{
    const st   = (state[l.id]?.status)||'novo';
    const nota = state[l.id]?.nota||'';
    const waBtn = l.wa
      ? `<a class="btn-wa" href="https://wa.me/${{l.wa}}" target="_blank">
           <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" style="margin-top:1px"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
           WA
         </a>`
      : '';
    const telBtn = l.tel
      ? `<a class="btn-tel" href="tel:${{l.tel.replace(/\\s/g,'')}}">${{l.tel}}</a>`
      : `<span style="color:var(--muted);font-size:.8rem">Sem tel.</span>`;

    return `
    <div class="card" id="card-${{l.id}}">
      <div class="card-top" onclick="togglePitch(${{l.id}})">
        <div class="card-num">${{idx+1}}</div>
        <div class="card-info">
          <div class="card-nome">${{l.nome}}</div>
          <div class="card-sub">
            <span class="badge ${{badgeClass(l.cat)}}">${{badgeLabel(l.cat)}}</span>
            ${{l.tem_website==='nao'
              ? `<span class="badge" style="background:#2a0d0d;color:#e05555">Sem website</span>`
              : `<span class="badge" style="background:#0d2a0d;color:#5DCA9A">Tem website</span>`}}
            <span class="card-cidade">📍 ${{l.morada || l.cidade}}</span>
            ${{l.rating ? `<span class="card-stars" title="${{l.rating}} estrelas">${{l.stars}}</span><span class="card-aval">(${{l.aval}} aval.)</span>` : ''}}
          </div>
        </div>
        <div class="card-acoes" onclick="event.stopPropagation()">
          ${{telBtn}}
          ${{waBtn}}
          <select class="status-sel s-${{st}}" onchange="setStatus(${{l.id}},this.value)">
            <option value="novo"       ${{st==='novo'?'selected':''}}>🔵 Novo</option>
            <option value="contactado" ${{st==='contactado'?'selected':''}}>📞 Contactado</option>
            <option value="interessado"${{st==='interessado'?'selected':''}}>⭐ Interessado</option>
            <option value="fechado"    ${{st==='fechado'?'selected':''}}>✅ Fechado</option>
            <option value="recusado"   ${{st==='recusado'?'selected':''}}>❌ Recusado</option>
          </select>
          <button class="btn-pitch" onclick="togglePitch(${{l.id}})">Pitch ▾</button>
        </div>
      </div>
      <div class="pitch-panel" id="pitch-${{l.id}}">
        ${{pitchHTML(l)}}
      </div>
    </div>`;
  }}).join('');

  // restaurar notas
  filtered.forEach(l=>{{
    const ta = document.getElementById(`nota-${{l.id}}`);
    if(ta) ta.value = (state[l.id]?.nota)||'';
  }});
}}

// ── Actions ───────────────────────────────────────────────────────────────
function togglePitch(id){{
  const panel = document.getElementById(`pitch-${{id}}`);
  panel.classList.toggle('open');
}}

function setStatus(id, val){{
  const state = loadState();
  if(!state[id]) state[id]={{}};
  state[id].status = val;
  saveState(state);
  const sel = document.querySelector(`#card-${{id}} .status-sel`);
  if(sel){{ sel.className = `status-sel s-${{val}}`; }}
  renderStats();
}}

function renderStats(){{
  const state = loadState();
  const counts = {{novo:0,contactado:0,interessado:0,fechado:0}};
  LEADS.forEach(l=>{{ const s=(state[l.id]?.status)||'novo'; if(counts[s]!==undefined) counts[s]++; }});
  document.getElementById('s-novo').textContent        = counts.novo;
  document.getElementById('s-contactado').textContent  = counts.contactado;
  document.getElementById('s-interessado').textContent = counts.interessado;
  document.getElementById('s-fechado').textContent     = counts.fechado;
}}

function saveNota(id){{
  const state = loadState();
  if(!state[id]) state[id]={{}};
  const ta = document.getElementById(`nota-${{id}}`);
  if(ta) state[id].nota = ta.value;
  saveState(state);
}}

function copyWA(id){{
  const el = document.getElementById(`wa-${{id}}`);
  const btn = el.querySelector('.copy-btn');
  const txt = el.childNodes[0].textContent.trim();
  navigator.clipboard.writeText(txt).then(()=>{{
    btn.textContent='✓ Copiado!';
    setTimeout(()=>btn.textContent='Copiar',2000);
  }});
}}

function exportNotas(){{
  const state = loadState();
  let txt = 'CRM EXPORTAÇÃO — ' + new Date().toLocaleDateString('pt-PT') + '\\n\\n';
  LEADS.forEach(l=>{{
    const s = state[l.id];
    if(!s) return;
    const nota = s.nota||'';
    const status = s.status||'novo';
    if(status === 'novo' && !nota) return;
    txt += `[${{status.toUpperCase()}}] ${{l.nome}} (${{l.cidade}}) — Tel: ${{l.tel||'—'}}\\n`;
    if(nota) txt += `Notas: ${{nota}}\\n`;
    txt += '\\n';
  }});
  const blob = new Blob([txt], {{type:'text/plain'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'crm_notas_' + new Date().toISOString().slice(0,10) + '.txt';
  a.click();
}}

// ── Init ──────────────────────────────────────────────────────────────────
renderLista();
</script>
</body>
</html>"""

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"CRM gerado: {OUTPUT} ({len(leads)} leads)")
