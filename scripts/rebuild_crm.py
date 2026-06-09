import csv, json, re, os, sys, io

OUT = "crm_prospeccao.html"
CSV1 = "prospeccao_porto_sem_website.csv"
CSV2 = "nichos_sem_website.csv"

def load(f):
    if not os.path.exists(f): return []
    with open(f, encoding="utf-8-sig") as h: return list(csv.DictReader(h))

def wa(tel):
    d = re.sub(r"\D","",tel)
    if d.startswith("351"): d=d[3:]
    return f"351{d}" if len(d)==9 and d[0]=="9" else None

def stars(r):
    try:
        r=float(r); f=int(r); h=1 if r-f>=0.5 else 0
        return "★"*f+("½"if h else "")+"☆"*(5-f-h)
    except: return ""

BADGE={
    "Oficina Mecanica":"background:#2a1a0d;color:#FF9A3C",
    "Fisioterapeuta":"background:#0d2a2a;color:#4ECDC4",
    "Restaurante Tasca":"background:#2a0d0d;color:#FF6B6B",
    "Psicologo Terapeuta":"background:#1a0d2a;color:#C77DFF",
    "Centro de Explicacoes":"background:#0d1a2a;color:#4A9EFF",
    "Padaria Pastelaria":"background:#2a200d;color:#FFD166",
    "Advogado Solicitador":"background:#1a1a1a;color:#aaa",
    "Empresa de Limpeza":"background:#0d2a0d;color:#5DCA9A",
    "Academia Artes Marciais":"background:#2a0a0a;color:#FF4444",
    "Veterinario":"background:#0d200d;color:#7BC67E",
    "Clinica Dentaria":"background:#1a2a3a;color:#4A9EFF",
    "Centro de Estetica":"background:#2a1a3a;color:#A78BFA",
    "Salao de Cabeleireiro":"background:#1a2a1a;color:#5DCA9A",
}

CATS_INFO = {
    "Oficina Mecanica":("clientes","oficina mecânica","localização, serviços e marcação de revisões"),
    "Fisioterapeuta":("pacientes","clínica de fisioterapia","serviços, equipa e marcações online"),
    "Restaurante Tasca":("clientes","restaurante","menu, horários e reservas online"),
    "Psicologo Terapeuta":("pacientes","psicólogo","apresentação, especialidades e contacto"),
    "Centro de Explicacoes":("alunos","centro de explicações","disciplinas, horários e inscrições"),
    "Padaria Pastelaria":("clientes","padaria/pastelaria","catálogo, horários e encomendas"),
    "Advogado Solicitador":("clientes","escritório de advocacia","áreas de prática, equipa e contacto"),
    "Empresa de Limpeza":("clientes","empresa de limpeza","serviços, preçário e orçamento"),
    "Academia Artes Marciais":("alunos","academia","modalidades, horários e inscrições"),
    "Veterinario":("clientes","clínica veterinária","serviços, equipa e marcações"),
    "Clinica Dentaria":("pacientes","clínica dentária","marcações, equipa e localização"),
    "Centro de Estetica":("clientes","centro de estética","tratamentos, preçário e marcações"),
    "Salao de Cabeleireiro":("clientes","salão de cabeleireiro","galeria, preçário e marcações"),
}

def pitch(row):
    nome=row["nome"]; cat=row["categoria"]
    try: aval=int(row["avaliacoes"])
    except: aval=0
    try: rat=float(row["rating"])
    except: rat=0.0
    if aval<5:    g=f"A {nome} ainda não tem avaliações no Google — sem website, é invisível online."
    elif aval<20: g=f"A {nome} tem {aval} avaliações. Sem website, quem pesquisa passa para a concorrência."
    elif aval<60: g=f"Com {aval} avaliações, a {nome} já tem reputação. Um website vai multiplicar a visibilidade."
    else:          g=f"A {nome} tem {aval} avaliações. Sem website está a perder clientes que pesquisam online."
    extra=""
    if rat>0 and rat<4.0: extra=f" Com {rat} de rating, um website com depoimentos vai melhorar a perceção."
    elif rat>=4.8: extra=f" Com {rat} estrelas, têm serviço excecional — um website mostra isso ao mundo."
    chamada,area,feat=CATS_INFO.get(cat,("clientes","negócio","informações e contacto"))
    cidade=row.get("cidade","Porto").split(",")[0].strip()
    return {
        "ab":f"Boa tarde, falo com o/a responsável pela {nome}?",
        "ga":g+extra,
        "pr":f"Criaria um website profissional para a {nome} com {feat} — pronto em 2 semanas, com garantia.",
        "ct":"Posso enviar-lhe agora 3 exemplos de websites que fiz para negócios similares no Porto?",
        "ob":f"'Tenho redes' → 'Google só mostra websites nas pesquisas de \"{area} em {cidade}\".'\\n'É caro' → 'Investimento único. Recupera em 1-2 meses de novos clientes.'\\n'Sem tempo' → 'Eu trato de tudo. Preciso só de 30 min da sua parte.'",
        "wa":f"Olá! Trabalho com {area}s no Porto a criar websites. Vi a {nome} no Google e gostaria de mostrar exemplos. Posso enviar?",
    }

todos = load(CSV1) + load(CSV2)
cats = sorted(set(r["categoria"] for r in todos))
cat_opts = "".join(f'<button class="btn-f" onclick="setF(\'cat\',\'{c}\')">{c.replace(chr(39),chr(39))}</button>' for c in cats)

data = []
for row in todos:
    tel=row.get("telefone",""); w=wa(tel); p=pitch(row)
    data.append({"id":len(data),"nome":row["nome"],"cat":row["categoria"],
                 "cidade":row.get("cidade","").split(",")[0].strip(),
                 "morada":row.get("morada",row.get("cidade","")),"tel":tel,"wa":w,
                 "rating":row.get("rating",""),"aval":row.get("avaliacoes",0),
                 "stars":stars(row.get("rating","")),"pitch":p,
                 "badge":BADGE.get(row["categoria"],"background:#222;color:#aaa")})

js = json.dumps(data, ensure_ascii=False)

html = """<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRM Prospeção — Websites Porto</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d0d0d;--bg2:#141414;--bg3:#1c1c1c;--bg4:#252525;--border:#2a2a2a;
  --gold:#C8A96E;--green:#5DCA9A;--red:#e05555;--blue:#4A9EFF;--text:#f0f0f0;--muted:#666}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',sans-serif}
.hdr{background:var(--bg2);border-bottom:1px solid var(--border);padding:14px 20px;
  display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:100}
.hdr h1{font-size:1.1rem;font-weight:700;color:var(--gold)}
.hdr span{color:var(--muted);font-size:.85rem}
.stats{display:flex;gap:10px;padding:16px 20px;flex-wrap:wrap}
.stat{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:12px 16px;text-align:center;min-width:100px}
.stat-n{font-size:1.6rem;font-weight:700;color:var(--gold)}
.stat-l{font-size:.72rem;color:var(--muted);margin-top:2px}
.filtros{padding:0 20px 12px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.filtros label{color:var(--muted);font-size:.78rem;margin-right:2px}
.btn-f{background:var(--bg3);border:1px solid var(--border);color:var(--muted);padding:5px 12px;border-radius:20px;cursor:pointer;font-size:.75rem;transition:.15s}
.btn-f:hover,.btn-f.on{background:var(--gold);border-color:var(--gold);color:#000;font-weight:600}
.sep{width:1px;height:20px;background:var(--border);margin:0 3px}
.sw{padding:0 20px 12px}
#srch{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:9px 13px;color:var(--text);font-size:.88rem;outline:none}
#srch:focus{border-color:var(--gold)}
.lista{padding:0 20px 40px;display:flex;flex-direction:column;gap:10px}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.ct{display:flex;align-items:flex-start;gap:12px;padding:14px}
.cn{background:var(--bg4);border-radius:7px;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:.72rem;color:var(--muted);flex-shrink:0;font-weight:700}
.ci{flex:1;min-width:0}
.cnm{font-weight:700;font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cs{display:flex;align-items:center;gap:6px;margin-top:3px;flex-wrap:wrap}
.badge{font-size:.65rem;padding:2px 7px;border-radius:9px;font-weight:600;white-space:nowrap}
.bsw{background:#2a0d0d;color:#e05555}
.ca{font-size:.72rem;color:var(--muted)}
.cst{font-size:.72rem;color:var(--gold)}
.cav{font-size:.68rem;color:var(--muted)}
.cac{display:flex;gap:6px;align-items:center;flex-shrink:0}
.bwa{background:#25D366;border:none;color:#fff;border-radius:7px;padding:6px 10px;font-size:.75rem;font-weight:600;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:4px;white-space:nowrap}
.btel{background:var(--bg4);border:1px solid var(--border);color:var(--text);border-radius:7px;padding:6px 10px;font-size:.75rem;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:4px;white-space:nowrap}
.ssel{padding:4px 6px;border-radius:6px;border:1px solid var(--border);background:var(--bg4);color:var(--text);font-size:.73rem;cursor:pointer;outline:none}
.s-novo{border-color:#444;color:#aaa}.s-contactado{border-color:var(--blue);color:var(--blue);background:#0d1a2a}
.s-interessado{border-color:var(--gold);color:var(--gold);background:#1a140a}
.s-fechado{border-color:var(--green);color:var(--green);background:#0d1a10}
.s-recusado{border-color:var(--red);color:var(--red);background:#1a0d0d}
.bp{background:var(--bg4);border:1px solid var(--border);color:var(--gold);border-radius:7px;padding:6px 10px;font-size:.75rem;cursor:pointer;white-space:nowrap}
.bp:hover{background:var(--gold);color:#000}
.pp{display:none;border-top:1px solid var(--border);padding:16px}
.pp.open{display:block}
.ps{margin-bottom:14px}
.ps h4{font-size:.67rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}
.pb{background:var(--bg3);border:1px solid var(--border);border-radius:7px;padding:12px;font-size:.82rem;line-height:1.6;white-space:pre-wrap}
.pb.ab{border-left:3px solid var(--blue);color:var(--blue)}.pb.ga{border-left:3px solid var(--gold)}
.pb.pr{border-left:3px solid var(--green)}.pb.ct{border-left:3px solid #A78BFA;color:#A78BFA}
.pb.ob{font-size:.78rem;color:#aaa;border-left:3px solid #444}
.wbox{background:#0a1a0f;border:1px solid #25D366;border-radius:7px;padding:12px;font-size:.8rem;line-height:1.5;color:#a0f0b0;position:relative;margin-top:8px}
.cbtn{position:absolute;top:7px;right:7px;background:var(--bg3);border:1px solid var(--border);color:var(--muted);border-radius:5px;padding:2px 8px;font-size:.68rem;cursor:pointer}
.nw{margin-top:10px}
.nw textarea{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:7px;color:var(--text);padding:9px;font-size:.8rem;resize:vertical;min-height:60px;outline:none;font-family:inherit}
.nw textarea:focus{border-color:var(--gold)}
.empty{text-align:center;padding:50px 20px;color:var(--muted)}
.lmbtn{display:block;margin:16px auto;background:var(--bg3);border:1px solid var(--border);color:var(--gold);padding:10px 24px;border-radius:8px;cursor:pointer;font-size:.85rem;width:100%;text-align:center}
.lmbtn:hover{background:var(--gold);color:#000}
@media(max-width:600px){.ct{flex-wrap:wrap}.cac{width:100%;justify-content:flex-end}}
</style></head><body>
<div class="hdr">
  <div><h1>CRM Prospeção <span>Websites · Grande Porto</span></h1></div>
  <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <span id="hs" style="font-size:.78rem;color:var(--muted)"></span>
    <button onclick="expN()" style="background:var(--bg3);border:1px solid var(--border);color:var(--muted);padding:5px 10px;border-radius:7px;cursor:pointer;font-size:.72rem">Exportar Notas</button>
  </div>
</div>
<div class="stats">
  <div class="stat"><div class="stat-n" id="st">0</div><div class="stat-l">Total Leads</div></div>
  <div class="stat"><div class="stat-n" id="sn" style="color:var(--muted)">0</div><div class="stat-l">Novos</div></div>
  <div class="stat"><div class="stat-n" id="sc" style="color:var(--blue)">0</div><div class="stat-l">Contactados</div></div>
  <div class="stat"><div class="stat-n" id="si" style="color:var(--gold)">0</div><div class="stat-l">Interessados</div></div>
  <div class="stat"><div class="stat-n" id="sf" style="color:var(--green)">0</div><div class="stat-l">Fechados</div></div>
</div>
<div class="filtros">
  <label>Cat:</label>
  <button class="btn-f on" onclick="setF('cat','')">Todos</button>
""" + cat_opts + """
  <div class="sep"></div>
  <label>Estado:</label>
  <button class="btn-f on" onclick="setF('st','')">Todos</button>
  <button class="btn-f" onclick="setF('st','novo')">Novos</button>
  <button class="btn-f" onclick="setF('st','contactado')">Contactados</button>
  <button class="btn-f" onclick="setF('st','interessado')">Interessados</button>
  <button class="btn-f" onclick="setF('st','fechado')">Fechados</button>
  <button class="btn-f" onclick="setF('st','recusado')">Recusados</button>
</div>
<div class="sw"><input id="srch" placeholder="Pesquisar nome ou cidade..." oninput="render()"></div>
<div class="lista" id="lista"></div>
<script>
const L=""" + js + """;
let F={cat:'',st:''},PAGE=25,page=0,FL=[];
const ld=()=>{try{return JSON.parse(localStorage.getItem('crm3')||'{}')}catch(e){return {}}};
const sv=s=>localStorage.setItem('crm3',JSON.stringify(s));
function setF(k,v){F[k]=v;document.querySelectorAll('.btn-f').forEach(b=>{const o=b.getAttribute('onclick')||'';b.classList.toggle('on',o.includes("'"+k+"'")&&o.includes("'"+v+"'"))});render()}
function render(){
  const s=ld(),q=(document.getElementById('srch').value||'').toLowerCase();
  FL=L.filter(l=>{
    const st=(s[l.id]?.st)||'novo';
    if(F.cat&&l.cat!==F.cat)return false;
    if(F.st&&st!==F.st)return false;
    if(q&&!l.nome.toLowerCase().includes(q)&&!l.cidade.toLowerCase().includes(q))return false;
    return true;
  });
  const c={novo:0,contactado:0,interessado:0,fechado:0};
  L.forEach(l=>{const st=(s[l.id]?.st)||'novo';if(c[st]!==undefined)c[st]++});
  document.getElementById('st').textContent=L.length;
  document.getElementById('sn').textContent=c.novo;
  document.getElementById('sc').textContent=c.contactado;
  document.getElementById('si').textContent=c.interessado;
  document.getElementById('sf').textContent=c.fechado;
  document.getElementById('hs').textContent=FL.length+' leads';
  page=0;
  document.getElementById('lista').innerHTML='';
  renderPage();
}
function renderPage(){
  const s=ld(),slice=FL.slice(page*PAGE,(page+1)*PAGE);
  const lista=document.getElementById('lista');
  const old=document.getElementById('lmbtn');if(old)old.remove();
  if(!FL.length&&page===0){lista.innerHTML='<div class="empty">Sem resultados.</div>';return}
  slice.forEach((l,i)=>{
    const st=(s[l.id]?.st)||'novo';
    const waBtn=l.wa?`<a class="bwa" href="https://wa.me/${l.wa}" target="_blank">WA</a>`:'';
    const telBtn=l.tel?`<a class="btel" href="tel:${l.tel.replace(/\\s/g,'')}">${l.tel}</a>`:`<span style="color:var(--muted);font-size:.75rem">Sem tel.</span>`;
    const div=document.createElement('div');
    div.className='card';div.id='c'+l.id;
    div.innerHTML=`<div class="ct">
      <div class="cn">${page*PAGE+i+1}</div>
      <div class="ci">
        <div class="cnm">${l.nome}</div>
        <div class="cs">
          <span class="badge" style="${l.badge}">${l.cat}</span>
          <span class="badge bsw">Sem website</span>
          <span class="ca">📍 ${l.morada||l.cidade}</span>
          ${l.rating?`<span class="cst">${l.stars}</span><span class="cav">(${l.aval} aval.)`:''}
        </div>
      </div>
      <div class="cac" onclick="event.stopPropagation()">
        ${telBtn}${waBtn}
        <select class="ssel s-${st}" onchange="setSt(${l.id},this.value)">
          <option value="novo" ${st==='novo'?'selected':''}>🔵 Novo</option>
          <option value="contactado" ${st==='contactado'?'selected':''}>📞 Contactado</option>
          <option value="interessado" ${st==='interessado'?'selected':''}>⭐ Interessado</option>
          <option value="fechado" ${st==='fechado'?'selected':''}>✅ Fechado</option>
          <option value="recusado" ${st==='recusado'?'selected':''}>❌ Recusado</option>
        </select>
        <button class="bp" onclick="tog(${l.id})">Pitch ▾</button>
      </div>
    </div>
    <div class="pp" id="p${l.id}">
      <div class="ps"><h4>1. Abertura</h4><div class="pb ab">${l.pitch.ab}</div></div>
      <div class="ps"><h4>2. Gancho</h4><div class="pb ga">${l.pitch.ga}</div></div>
      <div class="ps"><h4>3. Proposta</h4><div class="pb pr">${l.pitch.pr}</div></div>
      <div class="ps"><h4>4. Call to Action</h4><div class="pb ct">${l.pitch.ct}</div></div>
      <div class="ps"><h4>5. Objeções</h4><div class="pb ob">${l.pitch.ob}</div></div>
      ${l.wa?`<div class="ps"><h4>Mensagem WhatsApp</h4>
        <div class="wbox" id="wm${l.id}">${l.pitch.wa}<button class="cbtn" onclick="cpWA(${l.id})">Copiar</button></div>
        <a class="bwa" style="margin-top:8px;display:inline-flex" href="https://wa.me/${l.wa}?text=${encodeURIComponent(l.pitch.wa)}" target="_blank">Abrir WA com mensagem</a></div>`:''}
      <div class="nw"><h4 style="font-size:.67rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px">Notas</h4>
        <textarea id="nt${l.id}" placeholder="Notas..." oninput="svN(${l.id})"></textarea></div>
    </div>`;
    const ta=div.querySelector('textarea');if(ta)ta.value=(s[l.id]?.nota)||'';
    lista.appendChild(div);
  });
  if((page+1)*PAGE<FL.length){
    const btn=document.createElement('button');
    btn.className='lmbtn';btn.id='lmbtn';
    btn.textContent='Carregar mais '+(FL.length-(page+1)*PAGE)+' leads';
    btn.onclick=()=>{page++;renderPage()};
    lista.appendChild(btn);
  }
}
function tog(id){document.getElementById('p'+id).classList.toggle('open')}
function setSt(id,v){const s=ld();if(!s[id])s[id]={};s[id].st=v;sv(s);const el=document.querySelector('#c'+id+' .ssel');if(el)el.className='ssel s-'+v;
  const c={novo:0,contactado:0,interessado:0,fechado:0};L.forEach(l=>{const st=(s[l.id]?.st)||'novo';if(c[st]!==undefined)c[st]++});
  document.getElementById('sn').textContent=c.novo;document.getElementById('sc').textContent=c.contactado;
  document.getElementById('si').textContent=c.interessado;document.getElementById('sf').textContent=c.fechado}
function svN(id){const s=ld();if(!s[id])s[id]={};const t=document.getElementById('nt'+id);if(t)s[id].nota=t.value;sv(s)}
function cpWA(id){const el=document.getElementById('wm'+id);const b=el.querySelector('.cbtn');navigator.clipboard.writeText(el.childNodes[0].textContent.trim()).then(()=>{b.textContent='✓';setTimeout(()=>b.textContent='Copiar',2000)})}
function expN(){const s=ld();let t='CRM '+new Date().toLocaleDateString('pt-PT')+'\\n\\n';L.forEach(l=>{const d=s[l.id];if(!d||(!d.nota&&(!d.st||d.st==='novo')))return;t+=`[${(d.st||'novo').toUpperCase()}] ${l.nome} — ${l.tel||'—'}\\n`;if(d.nota)t+='Nota: '+d.nota+'\\n';t+='\\n'});const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([t],{type:'text/plain'}));a.download='crm_notas_'+new Date().toISOString().slice(0,10)+'.txt';a.click()}
render();
</script></body></html>"""

with open(OUT,"w",encoding="utf-8") as f: f.write(html)
print(f"CRM: {OUT} ({len(data)} leads, lazy loading de 25 em 25)")
