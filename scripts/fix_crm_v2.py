"""CRM v2 — design minimalista com dropdowns, contagens por cidade e transições."""
import csv, json, re, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CSV_OUT = "porto_leads.csv"
CRM_HTML = "crm/index.html"

BADGE = {
    "Cabeleireiro":"background:#1a2a1a;color:#5DCA9A","Estetica":"background:#2a1a3a;color:#A78BFA",
    "Dentaria":"background:#1a2a3a;color:#4A9EFF","Oficina":"background:#2a1a0d;color:#FF9A3C",
    "Fisioterapia":"background:#0d2a2a;color:#4ECDC4","Restaurante":"background:#2a0d0d;color:#FF6B6B",
    "Explicacoes":"background:#0d1a2a;color:#4A9EFF","Pastelaria":"background:#2a200d;color:#FFD166",
    "Advocacia":"background:#1a1a1a;color:#aaa","Limpeza":"background:#0d2a0d;color:#5DCA9A",
    "ArtesMarc":"background:#2a0a0a;color:#FF4444","Veterinario":"background:#0d200d;color:#7BC67E",
    "Psicologo":"background:#1a0d2a;color:#C77DFF","Escola Conducao":"background:#2a1a0d;color:#FFB347",
    "Creche ATL":"background:#0d1a2a;color:#87CEEB","Personal Trainer":"background:#0d2a10;color:#00FF7F",
    "Escola Musica Danca":"background:#1a0a2a;color:#DDA0DD","Fotografo Studio":"background:#1a1a2a;color:#B0C4DE",
    "Mudancas":"background:#2a1a0a;color:#DEB887","Eletricista":"background:#1a1a0a;color:#FFD700",
    "Loja Roupa":"background:#2a0a1a;color:#FFB6C1","Relojoeiro":"background:#1a1a0d;color:#DAA520",
    "Catering":"background:#0d2a1a;color:#90EE90","Reparacao Eletro":"background:#1a2a2a;color:#20B2AA",
    "Pintor":"background:#2a2a0d;color:#ADFF2F","Farmacia":"background:#0a2a0a;color:#32CD32",
    "Agencia Viagens":"background:#0a1a2a;color:#00BFFF","Hotel Pensao":"background:#2a1a1a;color:#F4A460",
    "Contabilidade":"background:#1a1a2a;color:#9FB3FF","Informatica":"background:#0a1a1a;color:#7FFFD4",
    "Canalizador":"background:#0d0d2a;color:#6495ED","Seguranca":"background:#2a0a0a;color:#DC143C",
    "Yoga Pilates":"background:#1a2a1a;color:#98FF98","Optica":"background:#2a2a1a;color:#F0E68C",
    "Pintura Arte":"background:#2a0a2a;color:#FF69B4",
}

def wa(tel):
    d = re.sub(r"\D", "", tel)
    if d.startswith("351"): d = d[3:]
    return "351" + d if len(d) == 9 and d[0] == "9" else None

def stars(r):
    try:
        r = float(r); f = int(r); h = 1 if r - f >= 0.5 else 0
        return "★" * f + ("½" if h else "") + "☆" * (5 - f - h)
    except: return ""

# ── Dados de nicho para pitch personalizado ──────────────────────────────────
NICHO_DATA = {
    "Cabeleireiro": {
        "abertura": ["a responsável pelo salão","o responsável pelo salão"],
        "produto": "portfólio de cortes e colorações, marcações online 24h e galeria de antes/depois",
        "dor": "Quando alguém pesquisa 'cabeleireiro {c}', os salões com website aparecem primeiro — e ficam com o cliente antes de vos encontrar.",
        "valor": "Marcações automáticas 24h: recupera o investimento com 2-3 novos clientes que antes iam para a concorrência.",
        "wa_hook": "Pesquisei agora 'cabeleireiro {c}' — há {n} salões à vossa frente só porque têm website. Criei uma demo gratuita para o {n}. Posso enviar?",
        "objec": {
            "redes": "Instagram mostra o trabalho a quem já vos segue. Google mostra a clientes novos que nunca ouviram falar de vocês — e só aparece quem tem website.",
            "caro": "Um cliente regular vale ~€200/ano. Basta 2 clientes novos por mês para recuperar em 3 semanas.",
            "tempo": "30 minutos seus — eu trato do resto. Fotos, texto, publicação. 2 semanas e está no ar.",
            "ja_tem_clientes": "Ótimo sinal. Um website vai fazer os clientes atuais recomendar com um link em vez de tentar explicar onde ficam.",
        }
    },
    "Estetica": {
        "abertura": ["a responsável pelo centro","o responsável pelo centro"],
        "produto": "lista de tratamentos com preços, marcações online e galeria de resultados",
        "dor": "Mulheres pesquisam 'estética {c}' antes de ligar. Sem website com preços visíveis, escolhem o primeiro que encontram.",
        "valor": "Agenda preenchida automaticamente 24h — sem telefonemas perdidos, sem horas de silêncio.",
        "wa_hook": "Fiz uma pesquisa de centros de estética em {c} — o {n} tem boas avaliações mas não aparece quando pesquisam online. Isso está a custar clientes novos todos os dias. Tenho 2 min para mostrar a solução?",
        "objec": {
            "redes": "Redes sociais constroem audiência. Um website converte visitas em marcações — são ferramentas diferentes com objetivos diferentes.",
            "caro": "Um tratamento facial é €60-80. São 5-6 clientes novos para recuperar o investimento total — e depois é lucro.",
            "tempo": "Lista dos tratamentos + algumas fotos. Eu construo, publico e optimizo. Dois semanas.",
        }
    },
    "Dentaria": {
        "abertura": ["a recetora ou responsável","o responsável pela clínica"],
        "produto": "serviços detalhados, marcação online de consultas, perfil da equipa e localização",
        "dor": "Dor de dentes às 22h — o paciente pesquisa no Google e liga para a 1ª clínica com website. Sem website, esse paciente não é vosso.",
        "valor": "Uma consulta de implante vale €800-1500. O website paga-se na primeira marcação urgente que viesse de pesquisa.",
        "wa_hook": "Testei agora: pesquisei 'dentista {c} urgência' — a {n} não aparece no top 5. Neste momento alguém com dor está a ligar para a concorrência. Posso mostrar como mudar isso em 2 semanas?",
        "objec": {
            "redes": "Pacientes com dor não abrem o Instagram — abrem o Google. Website é o que aparece nas pesquisas de urgência.",
            "caro": "Uma consulta de implante ou ortodontia paga o website inteiro. São literalmente 1-2 marcações.",
            "tempo": "Todo o processo por email ou WhatsApp. Sem reunião presencial se não quiser.",
        }
    },
    "Oficina": {
        "abertura": ["o responsável pela oficina","a responsável pela oficina"],
        "produto": "serviços com preços, pedido de orçamento online e localização com mapa",
        "dor": "Avaria na estrada — o condutor pesquisa 'oficina {c}' e liga para o primeiro que aparecer com website. Sem website, não existe para ele.",
        "valor": "Uma revisão ou reparação média são €200+. São 2 clientes novos de pesquisa para ter retorno total.",
        "wa_hook": "Fiz o teste: pesquisei 'oficina {c}' agora — o {n} não aparece nos primeiros resultados. Os vossos concorrentes com website estão a receber esses clientes. Tenho uma solução rápida. Posso explicar?",
        "objec": {
            "redes": "Quando o carro avaria, ninguém abre o Instagram. Abrem o Google e ligam para o primeiro resultado.",
            "caro": "Uma revisão completa são €150-300. São 2 clientes para ter retorno total — depois é crescimento.",
            "tempo": "Mando formulário por WhatsApp. Preenche em 20 minutos. Faço o resto.",
        }
    },
    "Fisioterapia": {
        "abertura": ["a recetora ou responsável","o fisioterapeuta responsável"],
        "produto": "especialidades, marcação online de consultas e perfil da equipa clínica",
        "dor": "Quem tem dores crónicas pesquisa 'fisioterapeuta {c}' repetidamente — e escolhe a clínica que aparece com website e informação clara.",
        "valor": "Um doente crónico faz sessões semanais por meses — é receita recorrente que começa com uma pesquisa no Google.",
        "wa_hook": "Pesquisei 'fisioterapeuta {c}' — a {n} não aparece nas primeiras opções. Alguém com dores crónicas está agora a marcar numa clínica concorrente. Criei uma demo do que o vosso website podia ser. Posso enviar?",
        "objec": {
            "redes": "Doentes não marcam fisioterapia pelo Instagram. Pesquisam no Google quando a dor aparece — e ligam para o que encontram.",
            "caro": "Um doente com 20 sessões a €45 são €900. O website paga-se com 1 doente novo — e depois continua a trazer mais.",
            "tempo": "WhatsApp ou email, ao vosso ritmo. Não há reunião obrigatória.",
        }
    },
    "Restaurante": {
        "abertura": ["o responsável pelo restaurante","a responsável pelo restaurante"],
        "produto": "ementa com preços, reservas online, galeria de pratos e localização",
        "dor": "Famílias e turistas pesquisam 'restaurante {c}' antes de sair de casa. Sem ementa online, escolhem outro que mostre os pratos e preços.",
        "valor": "Uma mesa de 4 ao jantar são €80-120. Reservas online enchem mesas que ficavam vazias — especialmente fim de semana.",
        "wa_hook": "Pesquisei restaurantes em {c} para jantar esta semana — vi o {n} com boas avaliações, mas sem ementa online fui ver outro. Isso acontece todos os dias. Criei uma demo gratuita. Quer ver?",
        "objec": {
            "redes": "Instagram mostra fotos. Website mostra ementa, preços e aceita reservas — e aparece no Google quando pesquisam para jantar.",
            "caro": "Um fim de semana com mesas cheias graças a reservas online são €500-1000 a mais. O website recupera-se numa noite.",
            "tempo": "Manda a ementa em foto ou PDF. Eu trato de tudo — texto, fotos, publicação.",
        }
    },
    "Explicacoes": {
        "abertura": ["o responsável pelo centro","a responsável pelo centro"],
        "produto": "matérias, horários, preços, metodologia e inscrição online",
        "dor": "Pais pesquisam 'explicações {c}' quando os filhos têm maus resultados — é urgente para eles. Sem website, não confiam sem referências claras.",
        "valor": "Um aluno a €80/mês por 9 meses são €720. O website paga-se com 1 inscrição — depois é só crescimento.",
        "wa_hook": "Época de testes a chegar — os pais em {c} estão a pesquisar explicações agora. Pesquisei e o {n} não aparece nas primeiras opções. Essas inscrições estão a ir para a concorrência. Posso mostrar como mudar isso?",
        "objec": {
            "redes": "Pais preocupados com notas não procuram no Instagram. Pesquisam no Google e querem ver matérias, preços e localização antes de ligar.",
            "caro": "Um aluno a €80/mês durante o ano letivo representa €720. São menos de 5 meses para recuperar o investimento.",
            "tempo": "Lista de matérias e horários — 20 minutos seus. Construo o resto.",
        }
    },
    "Pastelaria": {
        "abertura": ["o responsável pela pastelaria","a responsável pela pastelaria"],
        "produto": "catálogo de produtos, encomendas online, horários e localização",
        "dor": "Quem quer encomendar bolo de aniversário ou casamento pesquisa no Google. Sem website com catálogo e preços, a encomenda vai para quem aparece.",
        "valor": "Um bolo de casamento são €300-800. Encomendas online chegam enquanto dorme — sem telefonemas nem WhatsApps de última hora.",
        "wa_hook": "Alguém em {c} está agora a pesquisar onde encomendar um bolo especial — e sem website o {n} não aparece. Já ajudei 3 pastelarias na zona a duplicar as encomendas online. Posso mostrar como?",
        "objec": {
            "redes": "Facebook mostra o que já fizeram. Um website tem catálogo, preços e formulário de encomenda — transforma visitas em pedidos reais.",
            "caro": "Uma encomenda de evento são €200-500. São 1-2 encomendas novas para recuperar o investimento total.",
            "tempo": "Fotos dos vossos produtos — eu cuido de texto, layout e publicação. 2 semanas.",
        }
    },
    "Advocacia": {
        "abertura": ["o advogado responsável","a advogada responsável"],
        "produto": "áreas de prática, perfil profissional, formulário de contacto e marcação de consulta",
        "dor": "Quem precisa de advogado com urgência pesquisa no Google e contacta o primeiro resultado com website profissional. Credibilidade começa online.",
        "valor": "Um processo vale €500-5000 em honorários. O website paga-se com um único cliente convertido de pesquisa orgânica.",
        "wa_hook": "Pesquisei 'advogado {c}' — o {n} não aparece nas primeiras posições. Clientes que precisam de ajuda urgente estão a ligar para a concorrência. Posso mostrar em 2 minutos o que está a falhar e como corrigir?",
        "objec": {
            "redes": "Clientes que precisam de advogado não procuram no Instagram. Pesquisam 'advogado {c}' no Google — e ligam para o primeiro que aparecer.",
            "caro": "Um processo de direito laboral ou família vale €1000-5000. O website paga-se com 1 consulta convertida.",
            "tempo": "Tudo por email — sem reunião presencial. Proteção da privacidade dos dois.",
        }
    },
    "Limpeza": {
        "abertura": ["o responsável pela empresa","a responsável pela empresa"],
        "produto": "serviços com preços, orçamento online e zona de cobertura",
        "dor": "Empresas e senhorios pesquisam 'empresa limpeza {c}' antes de ligar. Sem website, parece menos profissional — e a encomenda vai para quem aparece.",
        "valor": "Um contrato mensal de escritório são €200-500/mês. O website paga-se no 1º mês de um único contrato.",
        "wa_hook": "Pesquisei 'empresa limpeza {c}' — o {n} não aparece nas primeiras opções. Senhorios e empresas estão a contratar a concorrência todos os dias. Tenho uma solução. Posso explicar em 2 min?",
        "objec": {
            "redes": "Senhorios e gestores de empresas não pedem orçamentos pelo Facebook. Pesquisam no Google e pedem orçamento online.",
            "caro": "Um contrato mensal de €300 recupera o investimento em 2 meses. Depois é margem pura todos os meses.",
            "tempo": "Lista de serviços e zona de cobertura — mando formulário por WhatsApp. 20 minutos seus.",
        }
    },
    "ArtesMarc": {
        "abertura": ["o responsável pela academia","a responsável pela academia"],
        "produto": "modalidades, horários, preços, aula experimental e inscrições online",
        "dor": "Pais pesquisam 'judo {c}' ou 'boxe {c}' para os filhos. Sem website com horários e preços visíveis, não ligam — vão para a academia que aparece.",
        "valor": "Um aluno a €50/mês por 12 meses são €600. Uma turma nova de 10 alunos são €6.000/ano — e começa com uma pesquisa no Google.",
        "wa_hook": "Pesquisei '{cat} {c}' — há academias abaixo da vossa em avaliações mas à vossa frente no Google só porque têm website. Esses alunos novos podiam ser vossos. Criei uma demo para o {n}. Posso enviar?",
        "objec": {
            "redes": "Instagram fideliza os alunos que já têm. Um website traz alunos novos que pesquisam no Google — são canais diferentes.",
            "caro": "5 alunos novos a €50/mês recuperam em 1 mês. O resto é crescimento sem mais custos.",
            "tempo": "Horários e modalidades por WhatsApp. Construo o website com formulário de aula experimental. 2 semanas.",
        }
    },
    "Veterinario": {
        "abertura": ["a recetora ou responsável","o veterinário responsável"],
        "produto": "serviços, urgências 24h, marcação online e localização",
        "dor": "Quando o animal adoece de madrugada, o dono pesquisa 'veterinário {c}' e liga para o primeiro resultado com website. Esse devia ser o vosso número.",
        "valor": "Uma cirurgia ou tratamento intensivo vale €300-1500. Um website com urgências visíveis no Google paga-se numa única noite.",
        "wa_hook": "Pesquisei 'veterinário urgência {c}' agora — a {n} não aparece nas primeiras opções. Esta noite alguém vai ligar para outra clínica com essa pesquisa. Posso mostrar como mudar isso em 2 semanas?",
        "objec": {
            "redes": "Em urgência ninguém abre o Instagram — abrem o Google e ligam para o primeiro resultado que aparecer.",
            "caro": "Uma consulta de urgência são €80-150. São 3-4 urgências para recuperar o investimento — depois continua a trazer mais.",
            "tempo": "Lista de serviços e horários — por WhatsApp. Sem reunião presencial.",
        }
    },
    "Psicologo": {
        "abertura": ["o/a psicólogo/a responsável","a responsável"],
        "produto": "abordagens terapêuticas, marcação confidencial online e informações de acesso",
        "dor": "Quem procura psicólogo quer discreção e confiança antes de ligar. Um website profissional transmite isso — ausência de website transmite incerteza.",
        "valor": "Um paciente semanal a €60/sessão representa €720+/ano. O website paga-se com 1 paciente novo.",
        "wa_hook": "Pesquisei 'psicólogo {c}' — o {n} não aparece nas primeiras posições. Quem precisa de apoio urgente está a contactar outro consultório. Tenho uma demo discreta e profissional preparada. Posso enviar?",
        "objec": {
            "redes": "Quem procura psicólogo não quer que o Instagram lhe apareça em sugestões. Website é neutro, discreto e profissional.",
            "caro": "Um paciente semanal a €60 são €240/mês. São menos de 2 meses para recuperar o investimento.",
            "tempo": "Tudo por email — sem reunião, proteção da privacidade dos dois.",
        }
    },
}

# Fallback genérico para nichos sem data específica
NICHO_DEFAULT = {
    "abertura": ["o responsável","a responsável"],
    "produto": "página de serviços com contactos, localização e formulário de marcação",
    "dor": "Quando alguém pesquisa o vosso serviço em {c} no Google, os negócios com website aparecem — os sem website ficam invisíveis.",
    "valor": "Com SEO local ativo, novos clientes encontram-nos no Google sem pagar publicidade.",
    "wa_hook": "Vi o {n} no Google Maps em {c}. Tenho uma proposta para aumentar a visibilidade online.",
    "objec": {
        "redes": "Redes sociais são para seguidores. Google Maps e pesquisa orgânica — onde os clientes novos aparecem — precisam de website.",
        "caro": "Novos clientes recorrentes recuperam o investimento em semanas. Depois é crescimento sem custos.",
        "tempo": "Todo o processo por WhatsApp. Preciso de 30 minutos seus no total.",
    }
}

def _nd(cat):
    """Devolve dados de nicho pelo nome da categoria (fuzzy match)."""
    cl = cat.lower()
    for k, v in NICHO_DATA.items():
        if k.lower() in cl or cl in k.lower():
            return v
    return NICHO_DEFAULT

def gpitch(row):
    n    = row["nome"]
    cat  = row.get("categoria", "")
    c    = row.get("cidade", "Porto").split(",")[0].strip()
    try: av = int(row["avaliacoes"])
    except: av = 0
    try: rt = float(row["rating"])
    except: rt = 0.0

    nd = _nd(cat)

    # ── ABERTURA ─────────────────────────────────────────────────────────────
    ab = f"Boa tarde, estou a falar com {nd['abertura'][0]} d{'a ' + n if n[0].lower() in 'aeiou' else 'o ' + n}?"

    # ── GANCHO — cruzamento avaliações × rating ───────────────────────────
    if av == 0:
        ga_base = f"Pesquisei a {n} no Google agora mesmo — ainda não tem avaliações nem website. Neste momento é praticamente invisível para quem pesquisa {cat.lower()} em {c}."
    elif av < 10:
        ga_base = f"Vi a {n} no Google com {av} avaliação{'ões' if av>1 else ''}. Está a começar a ganhar reputação — mas sem website perde clientes para concorrentes que já aparecem bem nos resultados."
    elif av < 30:
        ga_base = f"A {n} já tem {av} avaliações no Google — já tem uma base sólida. O problema é que sem website, quem pesquisa '{cat.lower()} {c}' clica nos concorrentes que aparecem com website antes de encontrar os vossos contactos."
    elif av < 80:
        ga_base = f"A {n} tem {av} avaliações — isso é excelente para {c}. Mas sem website estão a deixar dinheiro em cima da mesa: quem pesquisa online não consegue ver os vossos serviços nem marcar diretamente."
    else:
        ga_base = f"Com {av} avaliações, a {n} é claramente uma referência em {c}. Mas sem website próprio, toda essa reputação não aparece numa pesquisa do Google — e os concorrentes com website ficam com os clientes novos."

    # Rating overlay
    if rt >= 4.8:
        ga_rt = f" Com {rt}★ de média — uma das melhores classificações do mercado — um website ia mostrar esse excelente serviço a quem pesquisa online."
    elif rt >= 4.3:
        ga_rt = f" Com {rt}★, têm a reputação que os clientes precisam de ver antes de marcar — falta só o website para isso ser visível no Google."
    elif rt > 0 and rt < 3.8:
        ga_rt = f" Além disso, com {rt}★ no Google Maps, um website com depoimentos selecionados ajudaria a recuperar a perceção dos novos clientes."
    else:
        ga_rt = ""

    # Nicho-specific pain
    dor = nd["dor"].replace("{c}", c).replace("{n}", n)
    ga = f"{ga_base}{ga_rt}\n\n{dor}"

    # ── PROPOSTA ─────────────────────────────────────────────────────────────
    pr = (f"O que faço especificamente para {cat.lower()}s em {c}:\n"
          f"→ Crio uma página com {nd['produto']}.\n"
          f"→ Optimizo para aparecer no Google quando pesquisam '{cat.lower()} {c}'.\n"
          f"→ {nd['valor'].replace('{c}', c)}\n"
          f"Prazo: 2 semanas. Preço: a partir de €350 (pagamento em 2x).")

    # ── CALL TO ACTION ────────────────────────────────────────────────────────
    ct = (f"Posso enviar-lhe agora mesmo uma demonstração gratuita — "
          f"um website já construído para a {n} em {c} para ver como ficaria.\n"
          f"Se gostar, avançamos. Se não gostar, não há compromisso nenhum.\n"
          f"Posso enviar por WhatsApp agora?")

    # ── OBJEÇÕES ─────────────────────────────────────────────────────────────
    obs = nd["objec"]
    ob_lines = []
    ob_lines.append(f"❝Tenho redes sociais❞\n→ {obs.get('redes', 'Redes não aparecem nas pesquisas do Google para novos clientes.')}")
    ob_lines.append(f"❝É muito caro❞\n→ {obs.get('caro', 'Recupera com 2-3 clientes novos. Pagamento disponível em 2x.')}")
    ob_lines.append(f"❝Não tenho tempo❞\n→ {obs.get('tempo', 'Só preciso de 30 minutos seus. Eu trato de todo o resto.')}")
    if "ja_tem_clientes" in obs:
        ob_lines.append(f"❝Já tenho clientes suficientes❞\n→ {obs['ja_tem_clientes']}")
    ob = "\n\n".join(ob_lines)

    # ── WHATSAPP ──────────────────────────────────────────────────────────────
    # O hook já é a mensagem principal — adapta só o detalhe final
    hook = nd["wa_hook"].replace("{c}", c).replace("{n}", n).replace("{cat}", cat.lower())
    if av >= 50 and rt >= 4.5:
        wa_msg = f"{hook}\n\nP.S. {av} avaliações a {rt}★ — têm tudo para dominar o Google em {c}. Só falta o website."
    elif av >= 20:
        wa_msg = hook
    elif av > 0:
        wa_msg = hook
    else:
        wa_msg = f"{hook}\n\nNão têm website — criei uma demo gratuita para ver como ficaria. Sem compromisso."

    return {"ab": ab, "ga": ga, "pr": pr, "ct": ct, "ob": ob, "wa": wa_msg}

with open(CSV_OUT, encoding="utf-8-sig") as f:
    todos = list(csv.DictReader(f))

# Contagens para os dropdowns
cidade_counts = Counter(r.get("cidade", "").split(",")[0].strip() for r in todos)
cat_counts = Counter(r.get("categoria", "") for r in todos if r.get("categoria"))
cidades = sorted(cidade_counts.keys())
cats = sorted(cat_counts.keys())

print(f"Leads: {len(todos)} | Cidades: {len(cidades)} | Categorias: {len(cats)}")

# Build JS data
data = []
for row in todos:
    t = row.get("telefone", ""); w = wa(t); p = gpitch(row)
    cat = row.get("categoria", "")
    cidade = row.get("cidade", "").split(",")[0].strip()
    data.append({"id": len(data), "nome": row["nome"], "cat": cat, "cidade": cidade,
                 "morada": row.get("morada", ""), "tel": t, "wa": w,
                 "r": row.get("rating", ""), "av": row.get("avaliacoes", 0),
                 "st": stars(row.get("rating", "")), "p": p,
                 "bg": BADGE.get(cat, "background:#222;color:#aaa")})

js = json.dumps(data, ensure_ascii=False)

# Dropdown options HTML
def dd_cidade():
    opts = f'<div class="ddi on" onclick="sF(\'ci\',\'\',this)"><span>Todas as cidades</span><span class="ddc">{len(todos)}</span></div>'
    for c in cidades:
        n = cidade_counts[c]
        opts += f'<div class="ddi" onclick="sF(\'ci\',\'{c}\',this)"><span>{c}</span><span class="ddc">{n}</span></div>'
    return opts

def dd_cat():
    opts = f'<div class="ddi on" onclick="sF(\'c\',\'\',this)"><span>Todos os nichos</span><span class="ddc">{len(todos)}</span></div>'
    for c in cats:
        n = cat_counts[c]
        opts += f'<div class="ddi" onclick="sF(\'c\',\'{c}\',this)"><span>{c}</span><span class="ddc">{n}</span></div>'
    return opts

html = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRM Porto — 1002 Leads</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d0d0d;--bg2:#111;--bg3:#181818;--bg4:#202020;--bo:#262626;
  --go:#C8A96E;--go2:rgba(200,169,110,.12);--gr:#5DCA9A;--re:#e05555;--bl:#4A9EFF;
  --tx:#f0f0f0;--mu:#555;--mu2:#777;
}
body{background:var(--bg);color:var(--tx);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}

/* ── HEADER ── */
.hd{
  background:var(--bg2);border-bottom:1px solid var(--bo);
  padding:0 18px;height:52px;display:flex;align-items:center;gap:12px;
  position:sticky;top:0;z-index:200;backdrop-filter:blur(8px);
}
.hd-logo{font-size:.95rem;font-weight:700;color:var(--go);white-space:nowrap;letter-spacing:.03em}
.hd-logo span{color:var(--mu2);font-weight:400;font-size:.78rem;margin-left:6px}
.hd-search{
  flex:1;background:var(--bg3);border:1px solid var(--bo);border-radius:7px;
  padding:7px 12px;color:var(--tx);font-size:.85rem;outline:none;
  transition:border-color .2s;min-width:0;
}
.hd-search:focus{border-color:var(--go)}
.hd-search::placeholder{color:var(--mu)}
.hd-exp{
  background:transparent;border:1px solid var(--bo);color:var(--mu2);
  padding:5px 10px;border-radius:6px;cursor:pointer;font-size:.72rem;white-space:nowrap;
  transition:all .15s;
}
.hd-exp:hover{border-color:var(--go);color:var(--go)}

/* ── STATS BAR ── */
.sb{
  display:flex;gap:0;border-bottom:1px solid var(--bo);overflow-x:auto;
  scrollbar-width:none;background:var(--bg2);
}
.sb::-webkit-scrollbar{display:none}
.sbi{
  display:flex;flex-direction:column;align-items:center;padding:10px 20px;
  flex:1;min-width:70px;border-right:1px solid var(--bo);cursor:default;
  transition:background .2s;
}
.sbi:last-child{border-right:none}
.sbi:hover{background:var(--bg3)}
.sbi-n{font-size:1.3rem;font-weight:700;font-variant-numeric:tabular-nums;line-height:1}
.sbi-l{font-size:.62rem;color:var(--mu2);margin-top:3px;text-transform:uppercase;letter-spacing:.06em}

/* ── FILTER BAR ── */
.fb{
  display:flex;align-items:center;gap:8px;padding:10px 18px;
  border-bottom:1px solid var(--bo);background:var(--bg2);position:sticky;top:52px;z-index:190;
}
.fb-r{margin-left:auto;display:flex;align-items:center;gap:6px}

/* ── DROPDOWN ── */
.dd{position:relative;display:inline-block}
.dd-btn{
  display:flex;align-items:center;gap:6px;
  background:var(--bg3);border:1px solid var(--bo);color:var(--tx);
  padding:6px 12px;border-radius:7px;cursor:pointer;font-size:.8rem;
  transition:all .2s;user-select:none;white-space:nowrap;
}
.dd-btn:hover{border-color:var(--go);color:var(--go)}
.dd-btn.act{border-color:var(--go);background:var(--go2);color:var(--go);font-weight:600}
.dd-badge{
  background:var(--go);color:#000;border-radius:10px;
  padding:1px 6px;font-size:.65rem;font-weight:700;
}
.dd-arr{font-size:.6rem;opacity:.5;transition:transform .2s}
.dd.open .dd-arr{transform:rotate(180deg)}
.dd-panel{
  position:absolute;top:calc(100% + 6px);left:0;min-width:200px;
  background:var(--bg2);border:1px solid var(--bo);border-radius:9px;
  box-shadow:0 8px 32px rgba(0,0,0,.6);z-index:300;
  overflow:hidden;
  opacity:0;transform:translateY(-8px) scale(.97);pointer-events:none;
  transition:opacity .18s ease,transform .18s ease;
  max-height:320px;overflow-y:auto;scrollbar-width:thin;
  scrollbar-color:var(--bo) transparent;
}
.dd.open .dd-panel{opacity:1;transform:translateY(0) scale(1);pointer-events:all}
.ddi{
  display:flex;align-items:center;justify-content:space-between;
  padding:9px 14px;cursor:pointer;font-size:.82rem;color:var(--mu2);
  transition:background .12s;border-bottom:1px solid var(--bo);
}
.ddi:last-child{border-bottom:none}
.ddi:hover{background:var(--bg3);color:var(--tx)}
.ddi.on{color:var(--go);font-weight:600;background:var(--go2)}
.ddc{
  background:var(--bg4);border-radius:10px;padding:1px 7px;
  font-size:.68rem;color:var(--mu2);font-weight:600;flex-shrink:0;margin-left:10px;
}
.ddi.on .ddc{background:var(--go2);color:var(--go)}

/* Estado dropdown (mais pequeno) */
.dd-estado .dd-panel{min-width:160px}

/* ── RESULT COUNT ── */
.rc{
  font-size:.75rem;color:var(--mu2);padding:10px 18px 6px;
  display:flex;align-items:center;gap:6px;
}
.rc strong{color:var(--tx)}
.rc-bar{flex:1;height:2px;background:var(--bg3);border-radius:1px;overflow:hidden}
.rc-fill{height:100%;background:var(--go);border-radius:1px;transition:width .4s ease}

/* ── LEAD LIST ── */
.ll{padding:8px 18px 60px;display:flex;flex-direction:column;gap:6px}
.cd{
  background:var(--bg2);border:1px solid var(--bo);border-radius:10px;
  overflow:hidden;transition:border-color .2s,box-shadow .2s;
  animation:fadeUp .2s ease both;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.cd:hover{border-color:#333;box-shadow:0 2px 12px rgba(0,0,0,.3)}
.ct{display:flex;align-items:center;gap:10px;padding:11px 14px;cursor:default}
.cn{
  background:var(--bg4);border-radius:6px;width:28px;height:28px;
  display:flex;align-items:center;justify-content:center;
  font-size:.62rem;color:var(--mu);flex-shrink:0;font-weight:700;
}
.ci{flex:1;min-width:0}
.cm{font-weight:600;font-size:.88rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cx{display:flex;align-items:center;gap:4px;margin-top:4px;flex-wrap:wrap}
.ba{font-size:.6rem;padding:2px 6px;border-radius:6px;font-weight:600;white-space:nowrap}
.bsw{background:#1f0a0a;color:#e05555}
.bci{background:#0d1a0d;color:#5DCA9A}
.rat{font-size:.68rem;color:var(--go);margin-left:2px}
.adr{font-size:.67rem;color:var(--mu);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cac{display:flex;gap:5px;align-items:center;flex-shrink:0}
.wa{
  background:#25D366;border:none;color:#fff;border-radius:6px;
  padding:5px 9px;font-size:.7rem;font-weight:700;cursor:pointer;
  text-decoration:none;display:inline-flex;align-items:center;gap:3px;white-space:nowrap;
  transition:opacity .15s;
}
.wa:hover{opacity:.85}
.tel{
  background:var(--bg4);border:1px solid var(--bo);color:var(--tx);
  border-radius:6px;padding:5px 9px;font-size:.7rem;cursor:pointer;
  text-decoration:none;white-space:nowrap;transition:border-color .15s;
}
.tel:hover{border-color:var(--go)}
.ss2{
  padding:4px 6px;border-radius:6px;border:1px solid var(--bo);
  background:var(--bg4);color:var(--tx);font-size:.68rem;cursor:pointer;outline:none;
  transition:all .15s;
}
.s-novo{border-color:#333;color:var(--mu2)}
.s-contactado{border-color:var(--bl);color:var(--bl);background:#0d1a2a}
.s-interessado{border-color:var(--go);color:var(--go);background:#1a140a}
.s-fechado{border-color:var(--gr);color:var(--gr);background:#0d1a10}
.s-recusado{border-color:var(--re);color:var(--re);background:#1a0d0d}
.bp{
  background:transparent;border:1px solid var(--bo);color:var(--mu2);
  border-radius:6px;padding:5px 9px;font-size:.7rem;cursor:pointer;
  transition:all .15s;white-space:nowrap;
}
.bp:hover,.bp.open{border-color:var(--go);color:var(--go);background:var(--go2)}

/* ── PITCH PANEL ── */
.pp{
  display:grid;grid-template-rows:0fr;transition:grid-template-rows .25s ease;
  border-top:0px solid var(--bo);
}
.pp.o{grid-template-rows:1fr;border-top-width:1px}
.pp-in{overflow:hidden}
.pp-body{padding:14px}
.ps{margin-bottom:10px}
.ps h4{font-size:.6rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px}
.pb{
  background:var(--bg3);border:1px solid var(--bo);border-radius:6px;
  padding:9px 11px;font-size:.78rem;line-height:1.6;white-space:pre-wrap;
}
.pb.a{border-left:3px solid var(--bl);color:var(--bl)}.pb.g{border-left:3px solid var(--go)}
.pb.p{border-left:3px solid var(--gr)}.pb.c{border-left:3px solid #A78BFA;color:#A78BFA}
.pb.o{border-left:3px solid #333;color:var(--mu2);font-size:.74rem}
.wb{
  background:#071a0f;border:1px solid #1a4a28;border-radius:6px;
  padding:10px 12px;font-size:.77rem;color:#7ed4a0;position:relative;margin-top:6px;
  line-height:1.5;
}
.cb{
  position:absolute;top:7px;right:7px;background:var(--bg3);
  border:1px solid var(--bo);color:var(--mu);border-radius:4px;
  padding:2px 8px;font-size:.62rem;cursor:pointer;transition:all .15s;
}
.cb:hover{border-color:var(--go);color:var(--go)}
.nw{margin-top:8px}
.nw textarea{
  width:100%;background:var(--bg3);border:1px solid var(--bo);border-radius:6px;
  color:var(--tx);padding:8px;font-size:.76rem;resize:vertical;min-height:50px;
  outline:none;font-family:inherit;transition:border-color .2s;
}
.nw textarea:focus{border-color:var(--go)}

/* ── LOAD MORE ── */
.lm{
  display:block;margin:12px 0;background:var(--bg3);border:1px solid var(--bo);
  color:var(--go);padding:10px;border-radius:8px;cursor:pointer;
  font-size:.8rem;width:100%;text-align:center;transition:all .2s;
}
.lm:hover{background:var(--go);color:#000;border-color:var(--go)}
.em{text-align:center;padding:50px;color:var(--mu);font-size:.9rem}

/* ── MOBILE ── */
@media(max-width:600px){
  .hd{padding:0 12px;gap:8px}
  .fb{padding:8px 12px;flex-wrap:wrap}
  .ll{padding:6px 12px 60px}
  .sbi{padding:8px 14px;min-width:60px}
  .sbi-n{font-size:1.1rem}
  .cac{flex-wrap:wrap}
}
</style>
</head>
<body>

<!-- HEADER -->
<header class="hd">
  <div class="hd-logo">CRM Porto <span>Grande Porto</span></div>
  <input class="hd-search" id="sr" placeholder="🔍  Pesquisar nome, categoria ou cidade..." oninput="rnd()">
  <button class="hd-exp" onclick="expN()">Exportar</button>
</header>

<!-- STATS BAR -->
<div class="sb">
  <div class="sbi"><div class="sbi-n" id="st2" style="color:var(--go)">0</div><div class="sbi-l">Total</div></div>
  <div class="sbi"><div class="sbi-n" id="sn2" style="color:var(--mu2)">0</div><div class="sbi-l">Novos</div></div>
  <div class="sbi"><div class="sbi-n" id="sc2" style="color:var(--bl)">0</div><div class="sbi-l">Contactados</div></div>
  <div class="sbi"><div class="sbi-n" id="si2" style="color:var(--go)">0</div><div class="sbi-l">Interessados</div></div>
  <div class="sbi"><div class="sbi-n" id="sf2" style="color:var(--gr)">0</div><div class="sbi-l">Fechados</div></div>
</div>

<!-- FILTER BAR -->
<div class="fb">

  <!-- Cidade dropdown -->
  <div class="dd" id="dd-ci">
    <div class="dd-btn" id="btn-ci" onclick="tgDd('dd-ci')">
      <span id="lbl-ci">Cidade</span>
      <span class="dd-badge" id="bdg-ci" style="display:none"></span>
      <span class="dd-arr">▾</span>
    </div>
    <div class="dd-panel">
      CIDADE_OPTS
    </div>
  </div>

  <!-- Nicho dropdown -->
  <div class="dd" id="dd-c">
    <div class="dd-btn" id="btn-c" onclick="tgDd('dd-c')">
      <span id="lbl-c">Nicho</span>
      <span class="dd-badge" id="bdg-c" style="display:none"></span>
      <span class="dd-arr">▾</span>
    </div>
    <div class="dd-panel">
      CAT_OPTS
    </div>
  </div>

  <!-- Estado dropdown -->
  <div class="dd dd-estado" id="dd-s">
    <div class="dd-btn" id="btn-s" onclick="tgDd('dd-s')">
      <span id="lbl-s">Estado</span>
      <span class="dd-arr">▾</span>
    </div>
    <div class="dd-panel">
      <div class="ddi on" onclick="sF('s','',this,'dd-s')"><span>Todos</span><span class="ddc" id="cnt-s-all">0</span></div>
      <div class="ddi" onclick="sF('s','novo',this,'dd-s')"><span>🔵 Novos</span><span class="ddc" id="cnt-s-novo">0</span></div>
      <div class="ddi" onclick="sF('s','contactado',this,'dd-s')"><span>📞 Contactados</span><span class="ddc" id="cnt-s-cont">0</span></div>
      <div class="ddi" onclick="sF('s','interessado',this,'dd-s')"><span>⭐ Interessados</span><span class="ddc" id="cnt-s-int">0</span></div>
      <div class="ddi" onclick="sF('s','fechado',this,'dd-s')"><span>✅ Fechados</span><span class="ddc" id="cnt-s-fech">0</span></div>
      <div class="ddi" onclick="sF('s','recusado',this,'dd-s')"><span>❌ Recusados</span><span class="ddc" id="cnt-s-rec">0</span></div>
    </div>
  </div>

  <!-- Result info -->
  <div style="margin-left:auto;display:flex;align-items:center;gap:8px">
    <span id="hs" style="font-size:.75rem;color:var(--mu2)"></span>
  </div>
</div>

<!-- RESULT BAR -->
<div class="rc">
  <strong id="rc-n">0</strong> <span id="rc-txt">leads</span>
  <div class="rc-bar"><div class="rc-fill" id="rc-fill" style="width:0%"></div></div>
</div>

<!-- LIST -->
<div class="ll" id="ll"></div>

<script>
const L = JSONDATA;
let F = {c:'', s:'', ci:''}, PG = 30, pg = 0, FL = [];
const ld = () => { try { return JSON.parse(localStorage.getItem('crmPorto') || '{}') } catch(e) { return {} } };
const sv = s => localStorage.setItem('crmPorto', JSON.stringify(s));

/* ── Dropdown logic ── */
function tgDd(id) {
  const el = document.getElementById(id);
  const isOpen = el.classList.contains('open');
  // close all
  document.querySelectorAll('.dd.open').forEach(d => d.classList.remove('open'));
  if (!isOpen) el.classList.add('open');
}
document.addEventListener('click', e => {
  if (!e.target.closest('.dd')) document.querySelectorAll('.dd.open').forEach(d => d.classList.remove('open'));
});

function sF(k, v, el, ddId) {
  F[k] = v;
  // Update active item in panel
  if (el) {
    el.closest('.dd-panel').querySelectorAll('.ddi').forEach(d => d.classList.remove('on'));
    el.classList.add('on');
  }
  // Update button label + badge
  if (k === 'ci') {
    const lbl = document.getElementById('lbl-ci');
    const bdg = document.getElementById('bdg-ci');
    const btn = document.getElementById('btn-ci');
    if (v) { lbl.textContent = v; bdg.textContent = FL.filter(l => l.cidade === v).length || ''; bdg.style.display='inline'; btn.classList.add('act'); }
    else { lbl.textContent = 'Cidade'; bdg.style.display='none'; btn.classList.remove('act'); }
  }
  if (k === 'c') {
    const lbl = document.getElementById('lbl-c');
    const bdg = document.getElementById('bdg-c');
    const btn = document.getElementById('btn-c');
    if (v) { lbl.textContent = v; bdg.textContent = FL.filter(l => l.cat === v).length || ''; bdg.style.display='inline'; btn.classList.add('act'); }
    else { lbl.textContent = 'Nicho'; bdg.style.display='none'; btn.classList.remove('act'); }
  }
  if (k === 's') {
    const lbl = document.getElementById('lbl-s');
    const btn = document.getElementById('btn-s');
    const labels = {'':'Estado','novo':'🔵 Novos','contactado':'📞 Contact.','interessado':'⭐ Interest.','fechado':'✅ Fechados','recusado':'❌ Recusados'};
    lbl.textContent = labels[v] || 'Estado';
    btn.classList.toggle('act', v !== '');
  }
  if (ddId) { const d = document.getElementById(ddId); if (d) d.classList.remove('open'); }
  rnd();
}

/* ── Filter & render ── */
function rnd() {
  const s = ld(), q = (document.getElementById('sr').value || '').toLowerCase();
  FL = L.filter(l => {
    const st = (s[l.id]?.st) || 'novo';
    if (F.c && l.cat !== F.c) return false;
    if (F.ci && l.cidade !== F.ci) return false;
    if (F.s && st !== F.s) return false;
    if (q && !l.nome.toLowerCase().includes(q) && !l.cidade.toLowerCase().includes(q) && !l.cat.toLowerCase().includes(q)) return false;
    return true;
  });
  // Stats
  const c = {novo:0, contactado:0, interessado:0, fechado:0, recusado:0};
  L.forEach(l => { const st = (s[l.id]?.st) || 'novo'; if (c[st] !== undefined) c[st]++; });
  document.getElementById('st2').textContent = L.length;
  document.getElementById('sn2').textContent = c.novo;
  document.getElementById('sc2').textContent = c.contactado;
  document.getElementById('si2').textContent = c.interessado;
  document.getElementById('sf2').textContent = c.fechado;
  // Estado counts in dropdown
  const allN = L.filter(l => { const st=(s[l.id]?.st)||'novo'; return !F.c||l.cat===F.c }).length;
  document.getElementById('cnt-s-all').textContent = FL.length;
  document.getElementById('cnt-s-novo').textContent = FL.filter(l=>(s[l.id]?.st||'novo')==='novo').length;
  document.getElementById('cnt-s-cont').textContent = FL.filter(l=>(s[l.id]?.st)==='contactado').length;
  document.getElementById('cnt-s-int').textContent = FL.filter(l=>(s[l.id]?.st)==='interessado').length;
  document.getElementById('cnt-s-fech').textContent = FL.filter(l=>(s[l.id]?.st)==='fechado').length;
  document.getElementById('cnt-s-rec').textContent = FL.filter(l=>(s[l.id]?.st)==='recusado').length;
  // Result bar
  const pct = L.length ? (FL.length / L.length * 100) : 0;
  document.getElementById('rc-n').textContent = FL.length;
  document.getElementById('rc-txt').textContent = FL.length === 1 ? 'lead' : 'leads';
  document.getElementById('rc-fill').style.width = pct + '%';
  // Update badge counts after filter
  if (F.ci) document.getElementById('bdg-ci').textContent = FL.length;
  if (F.c) document.getElementById('bdg-c').textContent = FL.length;
  pg = 0; document.getElementById('ll').innerHTML = ''; rp();
}

function rp() {
  const s = ld(), sl = FL.slice(pg * PG, (pg + 1) * PG), ll = document.getElementById('ll');
  const ob = document.getElementById('lmbtn'); if (ob) ob.remove();
  if (!FL.length && pg === 0) { ll.innerHTML = '<div class="em">Sem leads para os filtros seleccionados.</div>'; return; }
  sl.forEach((l, i) => {
    const st = (s[l.id]?.st) || 'novo';
    const wb = l.wa ? `<a class="wa" href="https://wa.me/${l.wa}" target="_blank">WA</a>` : '';
    const tb = l.tel ? `<a class="tel" href="tel:${l.tel.replace(/\\s/g,'')}">${l.tel}</a>` : `<span style="color:var(--mu);font-size:.7rem">Sem tel.</span>`;
    const d = document.createElement('div'); d.className = 'cd'; d.id = 'cd' + l.id;
    d.style.animationDelay = (i * 0.03) + 's';
    d.innerHTML = `<div class="ct">
      <div class="cn">${pg * PG + i + 1}</div>
      <div class="ci">
        <div class="cm">${l.nome}</div>
        <div class="cx">
          <span class="ba" style="${l.bg}">${l.cat}</span>
          <span class="ba bci">${l.cidade}</span>
          <span class="ba bsw">Sem website</span>
          ${l.r ? `<span class="rat">${l.st} <span style="color:var(--mu);font-size:.62rem">(${l.av})</span></span>` : ''}
        </div>
        <div class="adr">📍 ${l.morada || l.cidade}</div>
      </div>
      <div class="cac" onclick="event.stopPropagation()">
        ${tb}${wb}
        <select class="ss2 s-${st}" onchange="sst(${l.id},this.value)">
          <option value="novo" ${st==='novo'?'selected':''}>Novo</option>
          <option value="contactado" ${st==='contactado'?'selected':''}>Contactado</option>
          <option value="interessado" ${st==='interessado'?'selected':''}>Interessado</option>
          <option value="fechado" ${st==='fechado'?'selected':''}>Fechado</option>
          <option value="recusado" ${st==='recusado'?'selected':''}>Recusado</option>
        </select>
        <button class="bp" id="bpb${l.id}" onclick="tog(${l.id})">Pitch ▾</button>
      </div>
    </div>
    <div class="pp" id="pp${l.id}"><div class="pp-in"><div class="pp-body">
      <div class="ps"><h4>Abertura</h4><div class="pb a">${l.p.ab}</div></div>
      <div class="ps"><h4>Gancho</h4><div class="pb g">${l.p.ga}</div></div>
      <div class="ps"><h4>Proposta</h4><div class="pb p">${l.p.pr}</div></div>
      <div class="ps"><h4>Call to Action</h4><div class="pb c">${l.p.ct}</div></div>
      <div class="ps"><h4>Objeções</h4><div class="pb o">${l.p.ob}</div></div>
      ${l.wa ? `<div class="ps"><h4>WhatsApp</h4>
        <div class="wb" id="wm${l.id}">${l.p.wa}<button class="cb" onclick="cpw(${l.id})">Copiar</button></div>
        <a class="wa" style="margin-top:6px;display:inline-flex" href="https://wa.me/${l.wa}?text=${encodeURIComponent(l.p.wa)}" target="_blank">Abrir WA</a></div>` : ''}
      <div class="nw"><h4 style="font-size:.6rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px">Notas</h4>
        <textarea id="nt${l.id}" placeholder="Notas sobre este contacto..." oninput="svn(${l.id})"></textarea></div>
    </div></div></div>`;
    const ta = d.querySelector('textarea'); if (ta) ta.value = (s[l.id]?.nota) || '';
    ll.appendChild(d);
  });
  if ((pg + 1) * PG < FL.length) {
    const b = document.createElement('button'); b.className = 'lm'; b.id = 'lmbtn';
    const rem = FL.length - (pg + 1) * PG;
    b.textContent = `Carregar mais ${rem} lead${rem!==1?'s':''}`;
    b.onclick = () => { pg++; rp(); }; ll.appendChild(b);
  }
}

function tog(id) {
  const pp = document.getElementById('pp' + id);
  const btn = document.getElementById('bpb' + id);
  pp.classList.toggle('o');
  btn.classList.toggle('open');
  btn.textContent = pp.classList.contains('o') ? 'Pitch ▴' : 'Pitch ▾';
}
function sst(id, v) {
  const s = ld(); if (!s[id]) s[id] = {}; s[id].st = v; sv(s);
  const el = document.querySelector('#cd' + id + ' .ss2'); if (el) el.className = 'ss2 s-' + v;
  rnd();
}
function svn(id) { const s = ld(); if (!s[id]) s[id] = {}; const t = document.getElementById('nt' + id); if (t) s[id].nota = t.value; sv(s); }
function cpw(id) {
  const el = document.getElementById('wm' + id); const b = el.querySelector('.cb');
  navigator.clipboard.writeText(el.childNodes[0].textContent.trim()).then(() => { b.textContent = '✓'; setTimeout(() => b.textContent = 'Copiar', 2000); });
}
function expN() {
  const s = ld(); let t = 'CRM Porto ' + new Date().toLocaleDateString('pt-PT') + '\\n\\n';
  FL.forEach(l => {
    const d = s[l.id]; if (!d || (!d.nota && (!d.st || d.st === 'novo'))) return;
    t += `[${(d.st||'novo').toUpperCase()}] ${l.nome} (${l.cidade}) — ${l.tel||'—'}\\n`;
    if (d.nota) t += 'Nota: ' + d.nota + '\\n'; t += '\\n';
  });
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([t], {type:'text/plain'}));
  a.download = 'crm_porto_' + new Date().toISOString().slice(0,10) + '.txt'; a.click();
}
rnd();
</script>
</body>
</html>"""

html = html.replace("JSONDATA", js)
html = html.replace("CIDADE_OPTS", dd_cidade())
html = html.replace("CAT_OPTS", dd_cat())

with open(CRM_HTML, "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅ CRM v2 gerado: {CRM_HTML} ({len(html)//1024}KB)")
