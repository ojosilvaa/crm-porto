"""CRM v3 — Login, log de atividade, follow-up, pitch templates BR-PT em JS."""
import csv, json, re, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CSV_OUT = "porto_leads.csv"
CRM_HTML = "crm/index.html"

def wa_num(tel):
    d = re.sub(r"\D", "", tel)
    if d.startswith("351"): d = d[3:]
    return "351" + d if len(d) == 9 and d[0] == "9" else None

# ─────────────────────────────────────────────────────────────────────────────
# Pitch templates — BR-PT, sem traços longos, sem "vosso/vossa/está a verb"
# Placeholders: {nome} {cidade} {cat}
# ─────────────────────────────────────────────────────────────────────────────
PITCH_TMPL = {
  "Cabeleireiro": {
    "ab": [
      "Oi! Vi o {nome} no Google e percebi uma coisa que pode estar te fazendo perder clientes todo mês. Posso te mostrar o que encontrei?",
      "Oi! Pesquisei 'cabeleireiro {cidade}' agora e o {nome} não aparece nas primeiras posições. Os clientes em potencial estão encontrando a concorrência primeiro. Vale conversar?",
      "Oi! Quando alguém novo chega em {cidade} e procura um cabeleireiro no Google, não encontra o {nome}. São clientes novos indo para outro lugar. Tenho uma solução simples."
    ],
    "ps": [
      "Ajudo salões a aparecer no topo do Google e a receber agendamentos online. Sem depender só do boca a boca. Quer saber como?",
      "A maioria dos salões depende do boca a boca para conseguir clientes novos. O problema é que isso é imprevisível. Com um site e SEO local, o {nome} aparece quando alguém pesquisa 'cabeleireiro {cidade}' e traz clientes novos todo mês de forma consistente. Posso te mostrar como funciona em 10 minutos?",
      "Oi,\n\nAnalisei a presença digital do {nome} e encontrei o principal problema: quando alguém novo em {cidade} pesquisa 'cabeleireiro' no Google, o salão não aparece.\n\nIsso significa:\n- Clientes novos que nunca encontram o {nome}\n- Dependência total do boca a boca\n- A concorrência aparecendo primeiro\n\nO que proponho: site profissional com sistema de agendamentos + SEO local para aparecer no topo do Google Maps.\n\nResultado: clientes novos te encontrando sozinhos, sem gastar em anúncios.\n\nPosso te mostrar com um exemplo real?"
    ],
    "obs": [
      {"ob": "Nossos clientes já nos conhecem", "q": "Ótimo! Isso significa que o serviço é excelente. Mas os clientes atuais um dia mudam de cidade, de rotina. Um site com SEO garante que sempre tem clientes novos entrando, independente do que acontecer com os atuais."},
      {"ob": "Usamos Instagram para divulgação", "q": "O Instagram é ótimo para manter clientes. Mas quem nunca ouviu falar de você não vai no Instagram procurar, vai no Google. O site garante que aparece quando alguém pesquisa ativamente um cabeleireiro na área. São canais diferentes para públicos diferentes."},
      {"ob": "É muito caro", "q": "O investimento se paga com 2 a 3 clientes novos por mês. Quanto vale um cliente fiel em um ano? Se vier uma vez por mês com ticket médio de 30€, são 360€ por ano. O retorno é bem rápido."},
      {"ob": "Não entendo nada de tecnologia", "q": "Não precisa entender nada. Eu cuido de tudo, crio, gerencio e otimizo. Você só precisa continuar fazendo o que faz bem."},
      {"ob": "Vou pensar", "q": "Claro! Para ajudar a decidir: posso fazer uma análise gratuita do {nome} no Google e te mostrar quantas pesquisas por 'cabeleireiro {cidade}' tem por mês e onde aparece hoje. Assim decide com dados reais. Quer que eu faça?"}
    ],
    "wa": "Pesquisei agora 'cabeleireiro {cidade}' e o {nome} não aparece nas primeiras opções. Criei uma demo gratuita pra ver como ficaria. Posso enviar?",
    "fu4": "Oi! Sei que o dia a dia de um salão é muito agitado. Só queria deixar a porta aberta. Se quiser saber como o {nome} está aparecendo no Google, faço uma análise gratuita sem compromisso.",
    "fu10": "Oi! Última mensagem da minha parte. O {nome} ainda não aparece pra 'cabeleireiro {cidade}'. São clientes indo pra concorrência todo dia. Se um dia quiser resolver, é só falar.",
    "ni": "Sem problema! Se um dia quiser crescer além do boca a boca, estou por aqui. Bom trabalho com o salão!"
  },
  "Estetica": {
    "ab": [
      "Oi! Vi o {nome} no Google e percebi que não tem site. No nicho de estética isso faz perder muitas clientes, especialmente as que pesquisam antes de agendar. Posso ajudar?",
      "Oi! Pesquisei 'estética {cidade}' e o {nome} não aparece nas primeiras posições. Tem muitas clientes em potencial pesquisando esses serviços todo dia. Vale conversar?",
      "Oi! Serviços como depilação a laser, tratamentos faciais e massagens têm muita procura no Google. O problema é que o {nome} não aparece quando pesquisam em {cidade}. Posso te mostrar como mudar isso?"
    ],
    "ps": [
      "Ajudo centros de estética a aparecer no topo do Google e a receber agendamentos online. Mais clientes sem depender de anúncios. Quer saber como?",
      "As clientes de estética pesquisam muito no Google antes de escolher onde vão. 'Depilação laser {cidade}', 'tratamento facial {cidade}'. Se o {nome} não aparece, essas clientes vão para outro lugar. Com um site e SEO local resolvo isso de forma definitiva. Posso te mostrar os números reais da sua área?",
      "Oi,\n\nAnalisei a presença digital do {nome} e identifiquei uma oportunidade clara.\n\nPalavras como 'depilação laser {cidade}', 'estética facial {cidade}' e 'massagem relaxante {cidade}' têm centenas de pesquisas por mês. O {nome} não aparece para nenhuma delas.\n\nO que faço:\n- Site com página para cada serviço\n- SEO local para aparecer no topo do Google Maps\n- Google Business otimizado\n- Sistema de agendamentos online\n\nResultado: clientes novas te encontrando todo dia de forma orgânica.\n\nPosso te mostrar como funciona?"
    ],
    "obs": [
      {"ob": "Já temos muitas clientes", "q": "Ótimo! Isso significa que o serviço é excelente. Com SEO, para de depender só do boca a boca e tem sempre clientes novas entrando. É crescimento previsível sem esforço extra."},
      {"ob": "Usamos Instagram e funciona bem", "q": "O Instagram é perfeito para fidelizar. Mas quem nunca ouviu falar vai no Google, não no Instagram. O SEO captura quem está ativamente procurando, e essas pessoas já estão prontas para agendar."},
      {"ob": "Não temos tempo para gerenciar site", "q": "Não precisa gerenciar nada. Eu crio, atualizo e otimizo. Vocês recebem os agendamentos e se concentram no atendimento."},
      {"ob": "Já temos um site", "q": "Ótimo! Posso fazer uma análise gratuita? Na maioria dos casos o site existe mas não está aparecendo no Google para as palavras certas. Se estiver tudo bem, te digo e ponto final."},
      {"ob": "Quanto custa?", "q": "O setup inicial começa em 350€ com opção de pagar em 2x. Isso se paga com 1-2 clientes novas por mês. Posso fazer uma proposta personalizada?"}
    ],
    "wa": "Fiz uma pesquisa de centros de estética em {cidade}. O {nome} tem boas avaliações mas não aparece quando pesquisam online. Isso está fazendo perder clientes novas todo dia. Tenho 2 minutos para te mostrar a solução?",
    "fu4": "Oi! Só queria confirmar se recebeu minha mensagem. Se não for o momento certo, sem problema. Posso entrar em contato outra hora.",
    "fu10": "Oi! Última mensagem. O {nome} ainda não aparece nas pesquisas de estética em {cidade}. Se um dia quiser explorar isso, estou disponível.",
    "ni": "Sem problema! Se um dia quiser crescer além das redes sociais, estou disponível. Bom trabalho com o centro!"
  },
  "Dentaria": {
    "ab": [
      "Oi! Vi a {nome} no Google e percebi uma coisa que pode estar fazendo perder pacientes todo mês. Posso compartilhar o que encontrei?",
      "Oi! Fiz uma pesquisa rápida de 'dentista {cidade}' e a {nome} não aparece nas primeiras posições. Os pacientes em potencial estão indo para a concorrência. Vale conversar?",
      "Oi! A {nome} ainda não tem site, o que significa que quando alguém pesquisa dentista em {cidade} no Google, simplesmente não encontra vocês. Posso mostrar como resolver isso?"
    ],
    "ps": [
      "Ajudo clínicas dentárias a aparecer no topo do Google e a receber mais agendamentos sem gastar em publicidade paga. Crio o site e cuido do SEO local. Posso mostrar como funciona?",
      "A maioria das clínicas perde pacientes todo dia porque não aparece no Google quando alguém pesquisa 'dentista + cidade'. Crio sites profissionais e faço SEO local para a {nome} aparecer nas primeiras posições de forma orgânica. Sem anúncios, sem custos mensais de publicidade. Faz sentido conversar 15 minutos?",
      "Oi,\n\nAnalisei a presença digital da {nome} e encontrei 3 situações que estão fazendo perder pacientes todo mês:\n\n1. A clínica não aparece quando alguém pesquisa 'dentista {cidade}'\n2. O Google Business está incompleto, menos visibilidade no Maps\n3. Não há páginas dedicadas a implantes, ortodontia ou clareamento\n\nCada ponto representa pessoas que procuraram dentista na sua área e foram para a concorrência.\n\nO que faço: site profissional + SEO local + Google Business otimizado.\n\nPosso mostrar resultados de outras clínicas numa conversa rápida de 15 minutos?"
    ],
    "obs": [
      {"ob": "Já temos pacientes suficientes", "q": "Ótimo sinal! Isso significa que o serviço é bom. Mas quantos pacientes estão indo para a concorrência só porque não aparecem no Google? Com SEO, os pacientes te encontram sozinhos sem esforço extra."},
      {"ob": "Já temos um site", "q": "Ótimo! Posso fazer uma análise rápida e gratuita? Na maioria dos casos o site existe mas não está otimizado para aparecer no Google. São coisas técnicas invisíveis que fazem toda a diferença. Se estiver tudo bem, te falo."},
      {"ob": "Não temos orçamento agora", "q": "Entendo. O modelo que proponho tem investimento inicial acessível e mensalidade que se paga com 1 ou 2 pacientes novos por mês. Quanto vale um paciente novo? Um implante pode valer 2000€. O retorno é imediato."},
      {"ob": "Usamos publicidade no Instagram", "q": "Faz sentido. A diferença é que quando param os anúncios, param os pacientes. Com SEO, a {nome} continua aparecendo no Google mesmo sem gastar em publicidade. Os dois funcionam juntos, mas o SEO trabalha 24h sem custo adicional."},
      {"ob": "Já tentamos SEO e não funcionou", "q": "Isso acontece muito. SEO genérico raramente funciona para clínicas. O que faço é diferente: foco em SEO local para dentistas em Portugal. Conheço as palavras-chave certas e o que o Google valoriza nesse nicho. Posso te mostrar um exemplo?"}
    ],
    "wa": "Testei agora: pesquisei 'dentista {cidade} urgência' e a {nome} não aparece no top 5. Nesse momento alguém com dor está ligando para a concorrência. Posso mostrar como mudar isso em 2 semanas?",
    "fu4": "Oi! Sei que o dia a dia de uma clínica é muito ocupado. Só queria confirmar se recebeu minha mensagem. Me fala quando prefere que eu entre em contato.",
    "fu10": "Oi! Última mensagem. A {nome} ainda não aparece para 'dentista {cidade}'. Se um dia quiser explorar isso, faço uma análise gratuita sem compromisso. Bom trabalho!",
    "ni": "Sem problema, obrigado pela resposta! Se um dia quiser saber como a clínica está aparecendo no Google, faço uma análise gratuita sem compromisso. Bom trabalho!"
  },
  "Oficina": {
    "ab": [
      "Oi! Vi a {nome} no Google e percebi que não tem site. Isso pode estar fazendo perder clientes que pesquisam mecânico antes de ir. Posso ajudar?",
      "Oi! Pesquisei 'mecânico {cidade}' e a {nome} não aparece nas primeiras posições. Tem muita gente procurando mecânico na área e estão indo para outro lugar. Vale conversar?",
      "Oi! Quando um carro quebra, a primeira coisa que fazem é pesquisar 'mecânico perto de mim' ou 'mecânico {cidade}'. Se a {nome} não aparece, esse cliente vai para a concorrência. Posso resolver isso."
    ],
    "ps": [
      "Ajudo oficinas a aparecer no topo do Google quando alguém pesquisa mecânico na área. Mais clientes sem gastar em publicidade. Quer saber como?",
      "A maioria das pessoas pesquisa mecânico no Google antes de ir a algum lugar, especialmente em urgência. Se a {nome} não aparece nas primeiras posições, estão perdendo esses clientes. Com site e SEO local resolvo isso. O retorno é rápido porque as pesquisas de mecânico têm intenção de compra imediata.",
      "Oi,\n\nAnalisei a presença digital da {nome} e encontrei uma oportunidade:\n\nPesquisas como 'mecânico {cidade}', 'revisão automóvel {cidade}' têm muita procura na área, e a oficina não aparece para nenhuma delas.\n\nO que faço:\n- Site com serviços e especialidades\n- SEO local para aparecer no topo do Google Maps\n- Google Business otimizado\n- Página de urgências para pesquisas de última hora\n\nResultado: clientes te encontrando quando mais precisam.\n\nPosso mostrar como funciona?"
    ],
    "obs": [
      {"ob": "Tenho trabalho demais, não preciso de mais clientes", "q": "Ótimo problema! O SEO serve para filtrar então. Com um site bem feito você mostra os serviços que quer fazer e afasta o que não quer. Atrai os clientes certos, não todos."},
      {"ob": "Meus clientes já me conhecem há anos", "q": "Isso é ouro! Mas esses clientes vão recomendar você para alguém que vai pesquisar no Google antes de ir. Se não aparecer, a recomendação pode se perder. Um site profissional garante que a indicação converte."},
      {"ob": "Não entendo nada disso", "q": "Não precisa entender nada. Eu cuido de tudo, crio, mantenho e otimizo. Você continua fazendo o que sabe: consertar carros."},
      {"ob": "Quanto custa?", "q": "O setup começa em 400€ com opção de pagar em 2x. Uma revisão ou reparo médio já paga o mês inteiro. Com 2-3 clientes novos por mês, o retorno é imediato."},
      {"ob": "Já tenho página no Facebook", "q": "O Facebook é bom para quem já te conhece. O Google é para quem ainda não te conhece e está procurando agora. São públicos completamente diferentes."}
    ],
    "wa": "Fiz o teste: pesquisei 'oficina {cidade}' agora e a {nome} não aparece nos primeiros resultados. Os concorrentes com site estão recebendo esses clientes. Tenho uma solução rápida. Posso explicar?",
    "fu4": "Oi! Sei que o dia a dia de uma oficina é corrido. Só deixando a porta aberta. Se quiser saber como a {nome} está aparecendo no Google, faço uma análise gratuita.",
    "fu10": "Oi! Última mensagem. A {nome} ainda não aparece pra 'mecânico {cidade}'. Se um dia quiser resolver, é só falar. Bom trabalho!",
    "ni": "Sem problema! Se um dia quiser mais clientes pelo Google, estou por aqui. Bom trabalho com a oficina!"
  },
  "Fisioterapia": {
    "ab": [
      "Oi! Vi a {nome} no Google e percebi que não tem site. Pacientes com dores crônicas pesquisam fisioterapeuta antes de agendar e estão perdendo essas oportunidades. Posso ajudar?",
      "Oi! Pessoas com dores nas costas, lesões esportivas ou pós-operatório pesquisam 'fisioterapeuta {cidade}' com urgência. Se a {nome} não aparece, esse paciente agenda em outro lugar. Tenho uma solução.",
      "Oi! Quando alguém em {cidade} pesquisa fisioterapeuta no Google, vocês não aparecem. São pacientes em potencial indo direto para a concorrência. Posso te mostrar como mudar isso?"
    ],
    "ps": [
      "Ajudo clínicas de fisioterapia a aparecer no topo do Google e a receber mais agendamentos de pacientes que pesquisam ativamente. Sem anúncios. Quer saber como?",
      "Fisioterapia tem um perfil de procura muito específico: as pessoas pesquisam quando têm dor ou necessidade imediata. Essa intenção de agendar é altíssima. Se a {nome} não aparece, está perdendo os pacientes mais qualificados. Com SEO local, aparecem exatamente no momento certo.",
      "Oi,\n\nAnalisei a presença digital da {nome} e encontrei uma oportunidade:\n\nPesquisas como 'fisioterapeuta {cidade}' têm muita procura de pessoas com dor que querem agendar.\n\nA {nome} não aparece nas primeiras posições.\n\nO que faço:\n- Site com especialidades e perfil da equipe\n- Sistema de agendamentos online\n- SEO local para aparecer nas primeiras posições\n- Google Business otimizado\n\nResultado: pacientes te encontrando quando mais precisam.\n\nPosso te mostrar como funciona?"
    ],
    "obs": [
      {"ob": "Trabalhamos com seguros e ADSE", "q": "Ótimo, isso é um argumento de venda enorme. Com um site podemos destacar exatamente quais seguros e subsistemas são aceitos. É um diferencial que a concorrência muitas vezes não comunica bem."},
      {"ob": "Temos lista de espera", "q": "Perfeito! O SEO serve para manter essa lista cheia mesmo nas épocas mais calmas. E quando expandirem, não precisam começar do zero para atrair pacientes."},
      {"ob": "Já temos pacientes suficientes", "q": "Ótimo! Com SEO, param de depender só do boca a boca e têm sempre pacientes novos entrando. É crescimento previsível sem esforço extra."},
      {"ob": "Não temos tempo", "q": "Não precisa de tempo nenhum. Eu cuido de tudo. Vocês só recebem os agendamentos."},
      {"ob": "É muito caro", "q": "Um paciente com 20 sessões a 45€ são 900€. O site se paga com 1 paciente novo, e depois continua trazendo mais."}
    ],
    "wa": "Pesquisei 'fisioterapeuta {cidade}' e a {nome} não aparece nas primeiras opções. Alguém com dores crônicas está agendando numa clínica concorrente agora. Criei uma demo do que seria o site de vocês. Posso enviar?",
    "fu4": "Oi! Só verificando se recebeu minha mensagem. Se não for o momento certo, sem problema. Me fale quando prefere.",
    "fu10": "Oi! Última mensagem. A {nome} ainda não aparece para 'fisioterapeuta {cidade}'. Se um dia quiserem explorar isso, faço uma análise gratuita. Bom trabalho!",
    "ni": "Sem problema! Se um dia quiserem crescer além das indicações, estou disponível. Bom trabalho com a clínica!"
  },
  "Restaurante": {
    "ab": [
      "Oi! Vi o {nome} no Google e percebi que não tem site. Muita gente pesquisa onde comer antes de sair de casa e estão perdendo essas visitas. Posso ajudar?",
      "Oi! Pesquisei 'restaurante {cidade}' e o {nome} não aparece nas primeiras posições. Tem pessoas na área pesquisando onde comer todo dia. Vale conversar?",
      "Oi! O turismo em {cidade} está crescendo e os turistas pesquisam tudo no Google antes de sair. Se o {nome} não aparece, estão perdendo um público enorme que estava ali do lado."
    ],
    "ps": [
      "Ajudo restaurantes a aparecer no topo do Google Maps e a atrair mais clientes locais e turistas. Sem anúncios. Quer saber como?",
      "Antes de entrar num lugar novo, a maioria das pessoas pesquisa no Google, vê as fotos, as avaliações, o horário. Se o {nome} não aparece bem posicionado, estão perdendo essas visitas. Com SEO local e Google Business otimizado, aparecem em primeiro quando alguém pesquisa na área.",
      "Oi,\n\nAnalisei a presença digital do {nome} e encontrei o seguinte:\n\n- O Google Business tem poucas fotos e informação incompleta\n- Não há site com menu, horários e localização\n- O {nome} não aparece nas primeiras posições para 'restaurante {cidade}'\n\nPessoas que estão pertinho, e turistas na área, não encontram vocês.\n\nO que faço:\n- Site simples com menu, fotos e horários\n- Google Business totalmente otimizado\n- SEO local para aparecer no topo do Maps\n\nResultado: mais visitas de pessoas que já estão na área e querem o que vocês oferecem."
    ],
    "obs": [
      {"ob": "Já estamos cheios", "q": "Ótimo! Mas um site bem feito serve também para gerenciar expectativas: horários, menu, preços. Reduz chamadas desnecessárias. E quando tiver época mais calma, o SEO já está trabalhando."},
      {"ob": "Temos muitas avaliações no Google, já aparecemos", "q": "As avaliações ajudam muito, mas o SEO vai além. Com site e otimização técnica, aparecem não só no Maps mas também nas pesquisas normais do Google. São duas fontes de visibilidade."},
      {"ob": "Somos conhecidos na zona", "q": "Ser conhecido na área é ótimo. Mas os turistas e as pessoas que se mudaram recentemente não conhecem vocês e pesquisam no Google. Um site simples captura esse público sem qualquer esforço."},
      {"ob": "Já temos Instagram", "q": "O Instagram é para quem já segue vocês. O Google é para quem está com fome agora e não sabe onde ir. O Google captura intenção imediata, o Instagram não consegue fazer isso."},
      {"ob": "É complicado de gerenciar", "q": "Não gerenciam nada. Eu cuido de tudo, crio, atualizo e otimizo. Vocês continuam fazendo o que fazem bem."}
    ],
    "wa": "Pesquisei restaurantes em {cidade} para jantar essa semana. Vi o {nome} com boas avaliações, mas sem menu online fui ver outro. Isso acontece todo dia. Criei uma demo gratuita. Quer ver?",
    "fu4": "Oi! Só verificando se recebeu minha mensagem. Se não for o momento certo, me fale quando prefere.",
    "fu10": "Oi! Última mensagem. O {nome} ainda não aparece bem posicionado em {cidade}. Se um dia quiser explorar, estou disponível. Bom trabalho!",
    "ni": "Sem problema! Se um dia quiser crescer além dos clientes regulares, estou por aqui. Bom trabalho!"
  },
  "Pastelaria": {
    "ab": [
      "Oi! Vi a {nome} no Google e percebi que não tem site. Quem quer encomendar bolo pesquisa online primeiro e acaba indo para quem aparece. Posso ajudar?",
      "Oi! Pesquisei 'pastelaria {cidade}' e a {nome} não aparece nas primeiras posições. Tem pessoas na área pesquisando onde tomar café e comer todo dia. Vale conversar?",
      "Oi! Quem quer encomendar bolo de aniversário ou casamento pesquisa no Google. Sem site com catálogo e preços, a encomenda vai para quem aparece. Posso te mostrar como resolver isso?"
    ],
    "ps": [
      "Ajudo pastelarias a aparecer no topo do Google Maps e a atrair mais clientes locais e turistas. Sem anúncios. Quer saber como?",
      "Antes de encomendar um bolo especial, a maioria das pessoas pesquisa no Google. Se a {nome} não aparece bem posicionada, estão perdendo essas encomendas. Com um site com catálogo e SEO local resolvo isso.",
      "Oi,\n\nAnalisei a presença digital da {nome} e encontrei uma oportunidade:\n\nPesquisas como 'pastelaria {cidade}' e 'bolo de casamento {cidade}' têm muita procura na área.\n\nA {nome} não aparece para nenhuma delas.\n\nO que faço:\n- Site com catálogo de produtos, encomendas online e horários\n- Google Business totalmente otimizado\n- SEO local para aparecer no topo do Maps\n\nResultado: encomendas chegando enquanto dorme, sem telefones de última hora."
    ],
    "obs": [
      {"ob": "Já estamos cheios", "q": "Ótimo! Um site bem feito serve para gerenciar expectativas: horários, produtos, preços. E quando tiver época mais calma, o SEO já está trabalhando."},
      {"ob": "Temos muitas avaliações no Google", "q": "As avaliações ajudam muito, mas o SEO vai além. Com site e otimização técnica, aparecem não só no Maps mas também nas pesquisas normais do Google."},
      {"ob": "Já temos Instagram", "q": "Instagram e Facebook mostram o que já fizeram. Um site tem catálogo, preços e formulário de encomenda. Transforma visitas em pedidos reais."},
      {"ob": "É complicado de gerenciar", "q": "Não gerenciam nada. Eu cuido de tudo, crio, atualizo e otimizo."},
      {"ob": "É muito caro", "q": "Uma encomenda de evento são 200-500€. São 1-2 encomendas novas para recuperar o investimento total."}
    ],
    "wa": "Alguém em {cidade} está procurando onde encomendar um bolo especial agora, e sem site a {nome} não aparece. Já ajudei outras pastelarias na zona a aumentar as encomendas online. Posso mostrar como?",
    "fu4": "Oi! Só verificando se recebeu minha mensagem. Se não for o momento certo, me fale quando prefere.",
    "fu10": "Oi! Última mensagem. A {nome} ainda não aparece nas pesquisas de pastelaria em {cidade}. Se um dia quiser explorar, estou disponível.",
    "ni": "Sem problema! Se um dia quiser mais encomendas pelo Google, estou por aqui. Bom trabalho!"
  },
  "Advocacia": {
    "ab": [
      "Oi! Vi o escritório {nome} no Google e percebi que não tem site. No setor jurídico isso pode fazer perder clientes que pesquisam advogado antes de ligar. Posso ajudar?",
      "Oi! Pesquisei 'advogado {cidade}' e o escritório {nome} não aparece nas primeiras posições. Tem pessoas precisando de serviços jurídicos na área todo dia e não estão encontrando vocês. Vale conversar?",
      "Oi! Quando alguém em {cidade} precisa urgentemente de um advogado, a primeira coisa que faz é pesquisar no Google. Se o {nome} não aparece, essa pessoa vai para outro escritório. Posso resolver isso."
    ],
    "ps": [
      "Ajudo escritórios de advocacia a aparecer no topo do Google e a receber contatos de clientes em potencial de forma orgânica. Sem anúncios. Quer saber como?",
      "A maioria dos clientes começa a pesquisa no Google hoje. 'Advogado divórcio {cidade}', 'advogado trabalhista {cidade}' são pesquisas reais todo dia. Se o {nome} não aparece, esses clientes vão para outro lugar. Com SEO local, o escritório aparece quando os clientes certos pesquisam.",
      "Oi Dr./Dra.,\n\nFiz uma análise da presença digital do {nome} e gostaria de compartilhar o que encontrei.\n\nPesquisas mensais estimadas na área:\n- 'advogado {cidade}': alta procura\n- 'advogado divórcio {cidade}': procura significativa\n- 'advogado trabalhista {cidade}': procura crescente\n\nO escritório não aparece para nenhuma dessas pesquisas.\n\nO que proponho: site profissional com páginas dedicadas a cada área de atuação + SEO local.\n\nResultado: contatos qualificados de pessoas que já precisam de um advogado.\n\nPoderia agendar 15 minutos para eu mostrar como funciona?"
    ],
    "obs": [
      {"ob": "Nossos clientes vêm por indicação", "q": "As indicações são o melhor canal, mas têm um limite. Quando um cliente recomenda vocês a alguém, essa pessoa vai ao Google verificar o escritório antes de ligar. Se não aparecer, a indicação pode se perder."},
      {"ob": "Não é ético fazer marketing na advocacia", "q": "Entendo a preocupação. O que faço não é publicidade. É visibilidade orgânica. Aparecer no Google quando alguém pesquisa 'advogado {cidade}' é equivalente a estar nas páginas amarelas antigamente. É informação, não promoção."},
      {"ob": "Já temos clientes suficientes", "q": "Ótimo! O SEO serve para consolidar a posição e garantir que quando um sócio se aposenta ou a carteira muda, sempre tem novos contatos entrando. É segurança a longo prazo."},
      {"ob": "Não temos tempo", "q": "Não precisam de tempo nenhum. Eu cuido de tudo, crio o conteúdo, otimizo, mantenho. Vocês só recebem os contatos."},
      {"ob": "Já tentamos e não funcionou", "q": "SEO genérico raramente funciona para advocacia. O que faço é diferente: foco em palavras-chave locais e de nicho específico onde a concorrência é menor e a intenção de contratar é alta. Posso te mostrar a diferença?"}
    ],
    "wa": "Pesquisei 'advogado {cidade}' e o {nome} não aparece nas primeiras posições. Clientes que precisam de ajuda urgente estão ligando para a concorrência. Posso mostrar em 2 minutos o que está faltando?",
    "fu4": "Oi! Sei que o dia a dia de um escritório é muito ocupado. Só queria confirmar se recebeu minha mensagem. Me fale quando prefere que eu entre em contato.",
    "fu10": "Oi! Última mensagem. O {nome} ainda não aparece para 'advogado {cidade}'. Se um dia quiserem explorar isso, faço uma análise gratuita. Bom trabalho!",
    "ni": "Sem problema, obrigado pela resposta! Se o contexto mudar, estou por aqui. Bom trabalho!"
  },
  "Limpeza": {
    "ab": [
      "Oi! Vi a {nome} no Google e percebi que não tem site. No setor de limpeza isso faz perder contratos, empresas e particulares pesquisam online antes de contratar. Posso ajudar?",
      "Oi! Empresas que precisam de serviços de limpeza pesquisam fornecedores no Google. Se a {nome} não aparece, estão perdendo contratos para a concorrência. Tenho uma solução simples.",
      "Oi! 'Empresa de limpeza {cidade}' tem muitas pesquisas por mês na sua área. A {nome} não aparece para essa pesquisa. São contratos indo para a concorrência todo mês."
    ],
    "ps": [
      "Ajudo empresas de limpeza a aparecer no topo do Google e a receber pedidos de orçamento de empresas e particulares. Sem anúncios. Quer saber como?",
      "Empresas e condomínios pesquisam serviços de limpeza no Google antes de pedir orçamentos. Se a {nome} não aparece bem posicionada, esses contratos vão para a concorrência. Com site profissional e SEO local, aparecem quando as pessoas certas pesquisam.",
      "Oi,\n\nAnalisei a presença digital da {nome} e encontrei uma oportunidade:\n\nPesquisas como 'empresa de limpeza {cidade}' e 'limpeza comercial {cidade}' têm muita procura na área.\n\nA {nome} não aparece para nenhuma delas.\n\nO que faço:\n- Site profissional com serviços, preços e zona de cobertura\n- Formulário de orçamento online\n- SEO local para aparecer no topo\n\nResultado: contratos chegando sem precisar prospectar todo dia."
    ],
    "obs": [
      {"ob": "Trabalhamos por indicação", "q": "As indicações são o melhor canal, mas têm um teto. SEO é o único canal que escala sem limite. E quando uma indicação pesquisa o nome de vocês no Google, um site profissional aumenta a confiança e a probabilidade de fechar."},
      {"ob": "Já temos clientes suficientes", "q": "Ótimo! O SEO serve para conseguir contratos maiores e mais rentáveis. Com um site bem posicionado vocês atraem empresas e condomínios em vez de só particulares."},
      {"ob": "Não temos orçamento", "q": "Um contrato de limpeza comercial pode valer centenas de euros por mês. O investimento se paga com um único contrato novo. Depois é só lucro."},
      {"ob": "Já temos redes sociais", "q": "Gestores e proprietários não pedem orçamentos pelo Facebook. Pesquisam no Google e pedem orçamento online. São canais diferentes."},
      {"ob": "Não temos tempo", "q": "Lista de serviços e zona de cobertura. Eu mando um formulário por WhatsApp. 20 minutos seus e eu cuido do resto."}
    ],
    "wa": "Pesquisei 'empresa limpeza {cidade}' e a {nome} não aparece nas primeiras opções. Proprietários e empresas estão contratando a concorrência todo dia. Tenho uma solução. Posso explicar em 2 min?",
    "fu4": "Oi! Só verificando se recebeu minha mensagem. Se não for o momento certo, me fale quando prefere.",
    "fu10": "Oi! Última mensagem. A {nome} ainda não aparece para 'empresa limpeza {cidade}'. Se um dia quiser explorar, estou disponível.",
    "ni": "Sem problema! Se um dia quiser mais contratos pelo Google, estou por aqui. Bom trabalho!"
  },
  "Explicacoes": {
    "ab": [
      "Oi! Vi o {nome} no Google e percebi que não tem site. Muitos pais pesquisam explicações online antes de matricular os filhos. Estão perdendo esses alunos. Posso ajudar?",
      "Oi! Com o início do ano letivo, os pais vão pesquisar 'explicações {cidade}' em massa. Se o {nome} não aparecer no Google nessa época, estão perdendo a melhor janela do ano. Tenho uma solução.",
      "Oi! Pais que procuram reforço escolar para os filhos pesquisam no Google primeiro. Se o {nome} não aparece nas primeiras posições, esses alunos vão para outro centro. Posso resolver isso."
    ],
    "ps": [
      "Ajudo centros de explicações a aparecer no topo do Google e a receber inscrições de novos alunos de forma orgânica. Quer saber como?",
      "Os pais pesquisam tudo no Google antes de decidir onde matricular os filhos. 'Explicações matemática {cidade}', 'centro de estudos {cidade}' são pesquisas com alta intenção. Se o {nome} não aparece, esses alunos vão para outro lugar. Especialmente importante antes do início do ano letivo.",
      "Oi,\n\nAnalisei a presença digital do {nome} e encontrei uma oportunidade:\n\nPesquisas como 'explicações {cidade}' e 'reforço escolar {cidade}' têm muita procura, especialmente em setembro e janeiro.\n\nO {nome} não aparece nas primeiras posições.\n\nO que faço:\n- Site com matérias, horários, preços e metodologia\n- Sistema de inscrição online\n- SEO local para aparecer quando os pais pesquisam\n\nResultado: inscrições chegando nos picos de demanda sem esforço extra."
    ],
    "obs": [
      {"ob": "Já estamos cheios", "q": "Ótimo! Então o SEO serve para criar lista de espera e selecionar melhor. Atrai os alunos certos e pode até aumentar o preço por estar em maior demanda."},
      {"ob": "O boca a boca funciona bem", "q": "Funciona, mas tem sazonalidade. Com SEO, vocês garantem visibilidade nos picos de procura (setembro, janeiro) quando os pais pesquisam ativamente. É complementar ao boca a boca."},
      {"ob": "Não temos tempo", "q": "Lista de matérias e horários, 20 minutos seus. Eu cuido do resto."},
      {"ob": "É muito caro", "q": "Um aluno a 80€/mês durante o ano letivo representa 720€. São menos de 5 meses para recuperar o investimento."},
      {"ob": "Já temos redes sociais", "q": "Pais preocupados com notas não procuram no Instagram. Pesquisam no Google e querem ver matérias, preços e localização antes de ligar."}
    ],
    "wa": "Época de testes chegando e os pais em {cidade} estão pesquisando explicações agora. Pesquisei e o {nome} não aparece nas primeiras opções. Essas inscrições estão indo para a concorrência. Posso mostrar como mudar isso?",
    "fu4": "Oi! Sei que o dia a dia de um centro de estudos é agitado. Só deixando a porta aberta. Se quiser saber como o {nome} está aparecendo no Google, faço uma análise gratuita.",
    "fu10": "Oi! Última mensagem. O {nome} ainda não aparece pra 'explicações {cidade}'. Se um dia quiser resolver, é só falar.",
    "ni": "Sem problema! Se um dia quiser mais alunos pelo Google, estou por aqui. Bom trabalho!"
  },
  "ArtesMarc": {
    "ab": [
      "Oi! Vi a {nome} no Google e percebi que não tem site. Pais pesquisam {cat} em {cidade} para os filhos e estão perdendo esses alunos. Posso ajudar?",
      "Oi! Pesquisei '{cat} {cidade}' e a {nome} não aparece nas primeiras posições. Tem pais procurando academias na área que acabam indo para outro lugar. Vale conversar?",
      "Oi! Pais pesquisam atividades para os filhos no Google antes de decidir. Sem site com horários e preços visíveis, não ligam. Vão para a academia que aparece. Posso resolver isso."
    ],
    "ps": [
      "Ajudo academias de artes marciais a aparecer no topo do Google e a receber inscrições de novos alunos. Sem anúncios. Quer saber como?",
      "Pais pesquisam atividades para os filhos no Google antes de decidir. Se a {nome} não aparece nas primeiras posições para '{cat} {cidade}', esses alunos vão para outra academia. Com site e SEO local, aparecem quando os pais certos pesquisam.",
      "Oi,\n\nAnalisei a presença digital da {nome}. Pesquisas como '{cat} {cidade}' têm muita procura de pais buscando atividades para os filhos, e a {nome} não aparece nas primeiras posições.\n\nO que faço:\n- Site com modalidades, horários, preços e aula experimental\n- SEO local para aparecer no topo\n- Formulário de inscrição online\n\nResultado: alunos novos chegando sem precisar prospectar."
    ],
    "obs": [
      {"ob": "Já temos muitos alunos", "q": "Ótimo! Com SEO, você cria lista de espera e pode selecionar melhor. Ou abre uma turma nova com demanda garantida antes de começar."},
      {"ob": "Usamos Instagram", "q": "O Instagram fideliza os alunos que já têm. Um site traz alunos novos que pesquisam no Google. São canais diferentes."},
      {"ob": "É muito caro", "q": "5 alunos novos a 50€/mês recuperam em 1 mês. O resto é crescimento sem mais custos."},
      {"ob": "Não temos tempo", "q": "Horários e modalidades por WhatsApp. Eu construo o site com formulário de aula experimental. 2 semanas."},
      {"ob": "Não entendo de tecnologia", "q": "Não precisa entender nada. Eu cuido de tudo."}
    ],
    "wa": "Pesquisei '{cat} {cidade}' e há academias abaixo da {nome} em avaliações mas à frente no Google só porque têm site. Esses alunos podiam ser de vocês. Criei uma demo. Posso enviar?",
    "fu4": "Oi! Sei que o dia a dia de uma academia é corrido. Só deixando a porta aberta para uma análise gratuita.",
    "fu10": "Oi! Última mensagem. A {nome} ainda não aparece bem pra '{cat} {cidade}'. Se um dia quiser resolver, é só falar.",
    "ni": "Sem problema! Se um dia quiser mais alunos pelo Google, estou por aqui. Bom trabalho!"
  },
  "Veterinario": {
    "ab": [
      "Oi! Vi a {nome} no Google e percebi que não tem site. Quando um animal adoece, os donos pesquisam veterinário urgência antes de ligar. Estão perdendo esses pacientes. Posso ajudar?",
      "Oi! Pesquisei 'veterinário {cidade}' e a {nome} não aparece nas primeiras posições. Donos de pets estão levando seus animais para outra clínica. Vale conversar?",
      "Oi! Quando um animal adoece de madrugada, o dono pesquisa 'veterinário {cidade}' e liga para o primeiro resultado com site. Esse número devia ser o de vocês."
    ],
    "ps": [
      "Ajudo clínicas veterinárias a aparecer no topo do Google e a receber mais agendamentos e urgências. Sem anúncios. Quer saber como?",
      "Em urgência veterinária, as pessoas pesquisam e ligam para o primeiro resultado. Se a {nome} não aparece nas primeiras posições, estão perdendo os pacientes mais urgentes. Com site e SEO local, aparecem quando os donos mais precisam.",
      "Oi,\n\nAnalisei a presença digital da {nome}. Pesquisas como 'veterinário {cidade}' e 'veterinário urgência {cidade}' têm muita procura, e a {nome} não aparece.\n\nO que faço:\n- Site com serviços, urgências e localização\n- SEO local para aparecer no topo\n- Google Business otimizado\n\nResultado: donos de pets te encontrando quando mais precisam."
    ],
    "obs": [
      {"ob": "Já temos muitos pacientes", "q": "Ótimo! Com SEO, vocês ficam com a lista cheia e podem escolher melhor os casos."},
      {"ob": "Somos indicados pelos clientes", "q": "Ótimo! Mas quando alguém recebe uma indicação, a primeira coisa que faz é pesquisar no Google. Sem site profissional, a indicação pode se perder."},
      {"ob": "Não temos tempo", "q": "Lista de serviços e horários, 20 minutos. Eu cuido do resto."},
      {"ob": "É muito caro", "q": "Uma cirurgia ou tratamento intensivo vale 300-1500€. O site se paga numa única urgência."},
      {"ob": "Já temos redes sociais", "q": "Em urgência ninguém abre o Instagram. Abre o Google e liga para o primeiro resultado que aparecer."}
    ],
    "wa": "Pesquisei 'veterinário urgência {cidade}' agora e a {nome} não aparece nas primeiras opções. Essa noite alguém vai ligar para outra clínica. Posso mostrar como mudar isso em 2 semanas?",
    "fu4": "Oi! Só verificando se recebeu minha mensagem. Se não for o momento certo, me fale quando prefere.",
    "fu10": "Oi! Última mensagem. A {nome} ainda não aparece pra 'veterinário {cidade}'. Se um dia quiser resolver, é só falar.",
    "ni": "Sem problema! Se um dia quiser mais pacientes pelo Google, estou por aqui. Bom trabalho!"
  },
  "Psicologo": {
    "ab": [
      "Oi! Vi o consultório {nome} no Google e percebi que não tem site. Quem procura psicólogo quer discreção e confiança antes de ligar. Um site profissional transmite isso. Posso ajudar?",
      "Oi! Pesquisei 'psicólogo {cidade}' e o {nome} não aparece nas primeiras posições. Pessoas precisando de apoio estão contactando outro consultório. Vale conversar?",
      "Oi! Quem procura psicólogo pesquisa com cuidado no Google antes de ligar. Se o {nome} não aparece, estão perdendo esses pacientes para a concorrência."
    ],
    "ps": [
      "Ajudo psicólogos a aparecer no topo do Google e a receber mais contatos de pacientes que pesquisam ativamente. Sem anúncios. Quer saber como?",
      "Quem procura psicólogo quer discreção e profissionalismo antes de dar o primeiro passo. Um site bem posicionado transmite isso e aparece quando a pessoa está pronta para buscar ajuda. Se o {nome} não aparece, esses pacientes vão para outro consultório.",
      "Oi,\n\nAnalisei a presença digital do {nome}. Pesquisas como 'psicólogo {cidade}' têm muita procura de pessoas buscando apoio, e o {nome} não aparece nas primeiras posições.\n\nO que faço:\n- Site profissional e discreto com abordagens terapêuticas\n- Sistema de agendamento confidencial online\n- SEO local para aparecer no topo\n\nResultado: pacientes te encontrando quando estão prontos para buscar ajuda."
    ],
    "obs": [
      {"ob": "Já tenho agenda cheia", "q": "Ótimo! Com SEO, você mantém a lista de espera cheia e pode cobrar mais pelos horários escassos."},
      {"ob": "Trabalho por indicação", "q": "As indicações são ótimas. Mas quando alguém recebe uma indicação, pesquisa no Google antes de ligar. Um site profissional garante que a indicação converte."},
      {"ob": "Não quero aparecer muito", "q": "Entendo a discrição. O site pode ser minimalista e neutro. Aparece só quando pesquisam diretamente 'psicólogo {cidade}'."},
      {"ob": "Não temos tempo", "q": "Tudo por email, sem reunião presencial."},
      {"ob": "É muito caro", "q": "Um paciente semanal a 60€ são 240€/mês. São menos de 2 meses para recuperar o investimento."}
    ],
    "wa": "Pesquisei 'psicólogo {cidade}' e o {nome} não aparece nas primeiras posições. Quem precisa de apoio urgente está contactando outro consultório. Tenho uma demo discreta e profissional preparada. Posso enviar?",
    "fu4": "Oi! Só verificando se recebeu minha mensagem. Se não for o momento certo, sem problema.",
    "fu10": "Oi! Última mensagem. O {nome} ainda não aparece pra 'psicólogo {cidade}'. Se um dia quiser explorar, estou disponível.",
    "ni": "Sem problema! Se um dia quiser mais pacientes pelo Google, estou por aqui. Bom trabalho!"
  },
  "_default": {
    "ab": [
      "Oi! Vi o {nome} no Google e percebi que não tem site. Isso pode estar te fazendo perder clientes todo mês. Posso te mostrar como resolver?",
      "Oi! Pesquisei '{cat} {cidade}' e o {nome} não aparece nas primeiras posições. Os clientes em potencial estão encontrando a concorrência primeiro. Vale conversar?",
      "Oi! Quando alguém em {cidade} pesquisa {cat} no Google, não encontra o {nome}. São clientes indo para outro lugar. Tenho uma solução simples para isso."
    ],
    "ps": [
      "Ajudo negócios locais a aparecer no topo do Google e a receber mais clientes sem gastar em anúncios. Quer saber como funciona?",
      "A maioria dos negócios em {cidade} perde clientes todo dia porque não aparece no Google. Com um site e SEO local, o {nome} passa a aparecer quando alguém pesquisa {cat} na área. São clientes novos chegando sem pagar por publicidade. Posso mostrar como funciona em 10 minutos?",
      "Oi,\n\nAnalisei a presença digital do {nome} e encontrei o principal problema: quando alguém pesquisa {cat} em {cidade} no Google, o negócio não aparece.\n\nIsso significa clientes em potencial indo para a concorrência todo dia.\n\nO que faço:\n- Site profissional com serviços, localização e contatos\n- SEO local para aparecer nas primeiras posições\n- Google Business otimizado\n\nResultado: clientes novos te encontrando sozinhos, sem gastar em anúncios.\n\nPosso mostrar como funciona?"
    ],
    "obs": [
      {"ob": "Tenho redes sociais", "q": "Redes sociais são para quem já te segue. O Google é para quem ainda não te conhece e está procurando agora. São canais completamente diferentes."},
      {"ob": "É muito caro", "q": "O investimento se recupera com 2-3 clientes novos por mês. E pode pagar em 2x. Quanto vale um cliente novo para o seu negócio?"},
      {"ob": "Não tenho tempo", "q": "Não precisa de tempo nenhum. Eu cuido de tudo. 30 minutos seus no total para me passar as informações."},
      {"ob": "Já tenho clientes suficientes", "q": "Ótimo sinal! Um site garante que quando os clientes atuais saem ou recomendam, sempre tem novos chegando."},
      {"ob": "Vou pensar", "q": "Claro! Posso fazer uma análise gratuita e te mostrar quantas pesquisas por '{cat} {cidade}' tem por mês. Assim decide com dados reais."}
    ],
    "wa": "Vi o {nome} no Google Maps em {cidade}. Não tem site ainda e os concorrentes estão aparecendo na frente. Criei uma demo gratuita pra ver como ficaria. Posso enviar?",
    "fu4": "Oi! Sei que o dia a dia é muito corrido. Só queria deixar a porta aberta. Se quiser saber como o {nome} está aparecendo no Google, faço uma análise gratuita.",
    "fu10": "Oi! Última mensagem da minha parte. O {nome} ainda não aparece bem para '{cat} {cidade}'. Se um dia quiser explorar isso, estou disponível.",
    "ni": "Sem problema, obrigado pela resposta! Se o contexto mudar, estou por aqui. Bom trabalho!"
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Load CSV + build minimal lead JSON
# ─────────────────────────────────────────────────────────────────────────────
with open(CSV_OUT, encoding="utf-8-sig") as f:
    todos = list(csv.DictReader(f))

cidade_counts = Counter(r.get("cidade", "").split(",")[0].strip() for r in todos)
cat_counts = Counter(r.get("categoria", "") for r in todos if r.get("categoria"))
cidades = sorted(cidade_counts.keys())
cats = sorted(cat_counts.keys())
print(f"Leads: {len(todos)} | Cidades: {len(cidades)} | Categorias: {len(cats)}")

data = []
for row in todos:
    t = row.get("telefone", ""); w = wa_num(t)
    cat = row.get("categoria", "")
    cidade = row.get("cidade", "").split(",")[0].strip()
    try: av = int(row.get("avaliacoes", 0) or 0)
    except: av = 0
    try: r = float(row.get("rating", 0) or 0)
    except: r = 0.0
    data.append({"id": len(data), "nome": row["nome"], "cat": cat, "cidade": cidade,
                 "morada": row.get("morada",""), "tel": t, "wa": w, "r": r, "av": av})

js_leads = json.dumps(data, ensure_ascii=False, separators=(',',':'))
js_pitch = json.dumps(PITCH_TMPL, ensure_ascii=False, separators=(',',':'))

def dd_cidade():
    opts = f'<div class="ddi on" onclick="sF(\'ci\',\'\',this)"><span>Todas as cidades</span><span class="ddc">{len(todos)}</span></div>'
    for c in cidades:
        opts += f'<div class="ddi" onclick="sF(\'ci\',\'{c}\',this)"><span>{c}</span><span class="ddc">{cidade_counts[c]}</span></div>'
    return opts

def dd_cat():
    opts = f'<div class="ddi on" onclick="sF(\'c\',\'\',this)"><span>Todos os nichos</span><span class="ddc">{len(todos)}</span></div>'
    for c in cats:
        opts += f'<div class="ddi" onclick="sF(\'c\',\'{c}\',this)"><span>{c}</span><span class="ddc">{cat_counts[c]}</span></div>'
    return opts

# ─────────────────────────────────────────────────────────────────────────────
# HTML template
# ─────────────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRM Porto</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d0d0d;--bg2:#111;--bg3:#181818;--bg4:#202020;--bo:#262626;
  --go:#C8A96E;--go2:rgba(200,169,110,.12);--gr:#5DCA9A;--re:#e05555;--bl:#4A9EFF;
  --tx:#f0f0f0;--mu:#555;--mu2:#777;
}
body{background:var(--bg);color:var(--tx);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}

/* ── LOGIN ── */
#lp{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:2000}
.lb{background:var(--bg2);border:1px solid var(--bo);border-radius:14px;padding:40px 36px;width:320px;max-width:92vw;text-align:center}
.lb-logo{font-size:1.5rem;font-weight:700;color:var(--go);letter-spacing:.03em}
.lb-sub{font-size:.75rem;color:var(--mu2);margin-top:4px;margin-bottom:28px}
.lb input{
  display:block;width:100%;background:var(--bg3);border:1px solid var(--bo);
  color:var(--tx);padding:10px 12px;border-radius:8px;font-size:.88rem;
  outline:none;margin-bottom:10px;transition:border-color .2s;
}
.lb input:focus{border-color:var(--go)}
#li-err{color:var(--re);font-size:.73rem;height:18px;margin-bottom:6px}
.lb-btn{
  width:100%;background:var(--go);color:#000;border:none;padding:11px;
  border-radius:8px;font-size:.88rem;font-weight:700;cursor:pointer;transition:opacity .15s;
}
.lb-btn:hover{opacity:.88}

/* ── HEADER ── */
.hd{
  background:var(--bg2);border-bottom:1px solid var(--bo);
  padding:0 18px;height:52px;display:flex;align-items:center;gap:10px;
  position:sticky;top:0;z-index:200;
}
.hd-logo{font-size:.95rem;font-weight:700;color:var(--go);white-space:nowrap;letter-spacing:.03em}
.hd-logo span{color:var(--mu2);font-weight:400;font-size:.75rem;margin-left:6px}
.hd-search{
  flex:1;background:var(--bg3);border:1px solid var(--bo);border-radius:7px;
  padding:7px 12px;color:var(--tx);font-size:.84rem;outline:none;transition:border-color .2s;min-width:0;
}
.hd-search:focus{border-color:var(--go)}
.hd-search::placeholder{color:var(--mu)}
.hd-btn{
  background:transparent;border:1px solid var(--bo);color:var(--mu2);
  padding:5px 10px;border-radius:6px;cursor:pointer;font-size:.71rem;white-space:nowrap;transition:all .15s;
}
.hd-btn:hover{border-color:var(--go);color:var(--go)}

/* ── STATS ── */
.sb{display:flex;border-bottom:1px solid var(--bo);background:var(--bg2);overflow-x:auto;scrollbar-width:none}
.sb::-webkit-scrollbar{display:none}
.sbi{display:flex;flex-direction:column;align-items:center;padding:9px 16px;flex:1;min-width:66px;border-right:1px solid var(--bo);cursor:default;transition:background .2s}
.sbi:last-child{border-right:none}
.sbi:hover{background:var(--bg3)}
.sbi-n{font-size:1.2rem;font-weight:700;font-variant-numeric:tabular-nums;line-height:1}
.sbi-l{font-size:.58rem;color:var(--mu2);margin-top:3px;text-transform:uppercase;letter-spacing:.06em}

/* ── FILTER ── */
.fb{
  display:flex;align-items:center;gap:8px;padding:10px 18px;
  border-bottom:1px solid var(--bo);background:var(--bg2);position:sticky;top:52px;z-index:190;flex-wrap:wrap;
}
.dd{position:relative;display:inline-block}
.dd-btn{
  display:flex;align-items:center;gap:5px;background:var(--bg3);border:1px solid var(--bo);color:var(--tx);
  padding:6px 11px;border-radius:7px;cursor:pointer;font-size:.79rem;transition:all .2s;user-select:none;white-space:nowrap;
}
.dd-btn:hover{border-color:var(--go);color:var(--go)}
.dd-btn.act{border-color:var(--go);background:var(--go2);color:var(--go);font-weight:600}
.dd-badge{background:var(--go);color:#000;border-radius:10px;padding:1px 6px;font-size:.63rem;font-weight:700}
.dd-arr{font-size:.58rem;opacity:.5;transition:transform .2s}
.dd.open .dd-arr{transform:rotate(180deg)}
.dd-panel{
  position:absolute;top:calc(100% + 5px);left:0;min-width:190px;
  background:var(--bg2);border:1px solid var(--bo);border-radius:9px;
  box-shadow:0 8px 32px rgba(0,0,0,.6);z-index:300;
  opacity:0;transform:translateY(-8px) scale(.97);pointer-events:none;
  transition:opacity .18s,transform .18s;max-height:300px;overflow-y:auto;
  scrollbar-width:thin;scrollbar-color:var(--bo) transparent;
}
.dd.open .dd-panel{opacity:1;transform:none;pointer-events:all}
.ddi{
  display:flex;align-items:center;justify-content:space-between;
  padding:8px 13px;cursor:pointer;font-size:.8rem;color:var(--mu2);
  transition:background .12s;border-bottom:1px solid var(--bo);
}
.ddi:last-child{border-bottom:none}
.ddi:hover{background:var(--bg3);color:var(--tx)}
.ddi.on{color:var(--go);font-weight:600;background:var(--go2)}
.ddc{background:var(--bg4);border-radius:10px;padding:1px 7px;font-size:.65rem;color:var(--mu2);font-weight:600;flex-shrink:0;margin-left:8px}
.ddi.on .ddc{background:var(--go2);color:var(--go)}

/* ── RESULT BAR ── */
.rc{font-size:.73rem;color:var(--mu2);padding:9px 18px 5px;display:flex;align-items:center;gap:6px}
.rc strong{color:var(--tx)}
.rc-bar{flex:1;height:2px;background:var(--bg3);border-radius:1px;overflow:hidden}
.rc-fill{height:100%;background:var(--go);border-radius:1px;transition:width .4s}

/* ── CARD ── */
.ll{padding:8px 18px 60px;display:flex;flex-direction:column;gap:6px}
.cd{background:var(--bg2);border:1px solid var(--bo);border-radius:10px;overflow:hidden;transition:border-color .2s,box-shadow .2s;animation:fadeUp .2s ease both}
@keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.cd:hover{border-color:#333;box-shadow:0 2px 12px rgba(0,0,0,.3)}
.ct{display:flex;align-items:center;gap:9px;padding:10px 13px}
.cn{background:var(--bg4);border-radius:6px;width:27px;height:27px;display:flex;align-items:center;justify-content:center;font-size:.6rem;color:var(--mu);flex-shrink:0;font-weight:700}
.ci{flex:1;min-width:0}
.cm{font-weight:600;font-size:.87rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cx{display:flex;align-items:center;gap:4px;margin-top:3px;flex-wrap:wrap}
.ba{font-size:.58rem;padding:2px 6px;border-radius:5px;font-weight:600;white-space:nowrap}
.bsw{background:#1f0a0a;color:#e05555}
.bci{background:#0d1a0d;color:#5DCA9A}
.rat{font-size:.66rem;color:var(--go);margin-left:2px}
.adr{font-size:.65rem;color:var(--mu);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cac{display:flex;gap:5px;align-items:center;flex-shrink:0}
.wa-link{background:#25D366;border:none;color:#fff;border-radius:6px;padding:5px 9px;font-size:.7rem;font-weight:700;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:3px;white-space:nowrap;transition:opacity .15s}
.wa-link:hover{opacity:.85}
.tel{background:var(--bg4);border:1px solid var(--bo);color:var(--tx);border-radius:6px;padding:5px 9px;font-size:.7rem;cursor:pointer;text-decoration:none;white-space:nowrap;transition:border-color .15s}
.tel:hover{border-color:var(--go)}
.ss2{padding:4px 6px;border-radius:6px;border:1px solid var(--bo);background:var(--bg4);color:var(--tx);font-size:.67rem;cursor:pointer;outline:none;transition:all .15s}
.s-novo{border-color:#333;color:var(--mu2)}
.s-contactado{border-color:var(--bl);color:var(--bl);background:#0d1a2a}
.s-interessado{border-color:var(--go);color:var(--go);background:#1a140a}
.s-fechado{border-color:var(--gr);color:var(--gr);background:#0d1a10}
.s-recusado{border-color:var(--re);color:var(--re);background:#1a0d0d}
.bp{background:transparent;border:1px solid var(--bo);color:var(--mu2);border-radius:6px;padding:5px 9px;font-size:.7rem;cursor:pointer;transition:all .15s;white-space:nowrap}
.bp:hover,.bp.open{border-color:var(--go);color:var(--go);background:var(--go2)}
.fu-chip{font-size:.6rem;padding:2px 6px;border-radius:10px;font-weight:600;white-space:nowrap;cursor:default}
.fu-ov{background:#2a0d0d;color:var(--re)}
.fu-td{background:#2a1a0d;color:var(--go)}
.fu-ft{background:#0d1a2a;color:var(--bl)}

/* ── PITCH PANEL ── */
.pp{display:grid;grid-template-rows:0fr;transition:grid-template-rows .25s ease;border-top:0px solid var(--bo)}
.pp.o{grid-template-rows:1fr;border-top-width:1px}
.pp-in{overflow:hidden}
.pp-body{padding:12px 14px}

/* pitch tabs */
.ptabs{display:flex;gap:3px;margin-bottom:10px;overflow-x:auto;scrollbar-width:none;flex-wrap:nowrap}
.ptabs::-webkit-scrollbar{display:none}
.ptab{background:var(--bg3);border:1px solid var(--bo);color:var(--mu2);border-radius:6px;padding:5px 10px;font-size:.7rem;cursor:pointer;white-space:nowrap;transition:all .15s}
.ptab:hover{color:var(--tx);border-color:#444}
.ptab.on{background:var(--go2);border-color:var(--go);color:var(--go);font-weight:600}
.pt-sec{display:none}
.pt-sec.on{display:block}

/* pitch size sub-tabs */
.psz-bar{display:flex;gap:4px;margin-bottom:8px}
.psz{background:var(--bg4);border:1px solid var(--bo);color:var(--mu2);border-radius:5px;padding:4px 10px;font-size:.68rem;cursor:pointer;transition:all .15s}
.psz:hover{color:var(--tx)}
.psz.on{background:var(--go2);border-color:var(--go);color:var(--go);font-weight:600}
.psz-c{display:none}
.psz-c.on{display:block}

/* pitch section */
.ps{margin-bottom:9px}
.ps h4{font-size:.58rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px}
.pb{
  background:var(--bg3);border:1px solid var(--bo);border-radius:6px;
  padding:9px 11px;font-size:.77rem;line-height:1.6;white-space:pre-wrap;position:relative;
}
.pb.ab{border-left:3px solid var(--bl)}
.pb.pit{border-left:3px solid var(--gr)}
.pb.wa-box{border-left:3px solid #25D366;color:#7ed4a0;background:#071a0f}
.cb{
  position:absolute;top:7px;right:7px;background:var(--bg2);
  border:1px solid var(--bo);color:var(--mu);border-radius:4px;
  padding:2px 8px;font-size:.61rem;cursor:pointer;transition:all .15s;
}
.cb:hover{border-color:var(--go);color:var(--go)}

/* objections */
.ob-item{border:1px solid var(--bo);border-radius:7px;margin-bottom:5px;overflow:hidden}
.ob-q{display:flex;align-items:center;gap:7px;padding:8px 11px;cursor:pointer;font-size:.78rem;color:var(--mu2);transition:background .12s}
.ob-q:hover{background:var(--bg3);color:var(--tx)}
.ob-icon{color:var(--go);font-size:.8rem;flex-shrink:0}
.ob-arr{margin-left:auto;font-size:.6rem;opacity:.5;transition:transform .2s;flex-shrink:0}
.ob-item.open .ob-arr{transform:rotate(180deg)}
.ob-ans{display:none;padding:8px 11px 10px 28px;font-size:.76rem;line-height:1.6;border-top:1px solid var(--bo);color:var(--tx);background:var(--bg3)}
.ob-item.open .ob-ans{display:block}

/* follow-up */
.fu-row{display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.fu-row label{font-size:.73rem;color:var(--mu2)}
.fu-row input[type=date]{
  background:var(--bg3);border:1px solid var(--bo);color:var(--tx);
  padding:5px 9px;border-radius:6px;font-size:.78rem;outline:none;cursor:pointer;
}
.fu-row input[type=date]:focus{border-color:var(--go)}
.fu-ind{font-size:.68rem;font-weight:600;padding:2px 7px;border-radius:10px}
.fu-ov-ind{color:var(--re);background:#2a0d0d}
.fu-td-ind{color:var(--go);background:#2a1a0d}
.fu-ft-ind{color:var(--bl);background:#0d1a2a}

/* activity log */
.log-list{margin-bottom:10px}
.log-entry{border:1px solid var(--bo);border-radius:7px;padding:8px 11px;margin-bottom:5px;background:var(--bg3)}
.log-ts{font-size:.62rem;color:var(--mu);margin-bottom:3px}
.log-txt{font-size:.77rem;line-height:1.5}
.log-empty{color:var(--mu);font-size:.76rem;text-align:center;padding:16px}
.log-new textarea{
  width:100%;background:var(--bg3);border:1px solid var(--bo);border-radius:6px;
  color:var(--tx);padding:8px;font-size:.76rem;resize:vertical;min-height:52px;
  outline:none;font-family:inherit;transition:border-color .2s;margin-bottom:6px;
}
.log-new textarea:focus{border-color:var(--go)}
.log-add{background:var(--go2);border:1px solid var(--go);color:var(--go);border-radius:6px;padding:6px 14px;font-size:.74rem;cursor:pointer;font-weight:600;transition:all .15s}
.log-add:hover{background:var(--go);color:#000}

/* wa open button */
.wa-open{background:#071a0f;border:1px solid #1a4a28;color:#7ed4a0;border-radius:6px;padding:6px 12px;font-size:.73rem;cursor:pointer;margin-top:7px;text-decoration:none;display:inline-flex;align-items:center;gap:5px;transition:all .15s}
.wa-open:hover{background:#0d2a18;border-color:#25D366}

/* load more */
.lm{display:block;margin:12px 0;background:var(--bg3);border:1px solid var(--bo);color:var(--go);padding:10px;border-radius:8px;cursor:pointer;font-size:.8rem;width:100%;text-align:center;transition:all .2s}
.lm:hover{background:var(--go);color:#000;border-color:var(--go)}
.em{text-align:center;padding:50px;color:var(--mu);font-size:.9rem}

@media(max-width:600px){
  .hd{padding:0 12px;gap:7px}.fb{padding:8px 12px}.ll{padding:6px 12px 60px}
  .sbi{padding:7px 10px;min-width:58px}.sbi-n{font-size:1rem}
  .cac{flex-wrap:wrap}.ptabs{gap:2px}
}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="lp">
  <div class="lb">
    <div class="lb-logo">CRM Porto</div>
    <div class="lb-sub">Acesso Restrito</div>
    <input id="li-u" type="text" placeholder="Usuário" autocomplete="username">
    <input id="li-p" type="password" placeholder="Senha" autocomplete="current-password">
    <div id="li-err"></div>
    <button class="lb-btn" onclick="doLogin()">Entrar</button>
  </div>
</div>

<!-- APP -->
<div id="app" style="display:none">

<header class="hd">
  <div class="hd-logo">CRM Porto <span>Grande Porto</span></div>
  <input class="hd-search" id="sr" placeholder="🔍  Pesquisar nome, categoria ou cidade..." oninput="rnd()">
  <button class="hd-btn" onclick="expN()">Exportar</button>
  <button class="hd-btn" onclick="doLogout()">Sair</button>
</header>

<div class="sb">
  <div class="sbi"><div class="sbi-n" style="color:var(--go)" id="st-t">0</div><div class="sbi-l">Total</div></div>
  <div class="sbi"><div class="sbi-n" style="color:var(--mu2)" id="st-n">0</div><div class="sbi-l">Novos</div></div>
  <div class="sbi"><div class="sbi-n" style="color:var(--bl)" id="st-c">0</div><div class="sbi-l">Contactados</div></div>
  <div class="sbi"><div class="sbi-n" style="color:var(--go)" id="st-i">0</div><div class="sbi-l">Interessados</div></div>
  <div class="sbi"><div class="sbi-n" style="color:var(--gr)" id="st-f">0</div><div class="sbi-l">Fechados</div></div>
  <div class="sbi"><div class="sbi-n" style="color:var(--re)" id="st-fu">0</div><div class="sbi-l">Follow-up</div></div>
</div>

<div class="fb">
  <div class="dd" id="dd-ci">
    <div class="dd-btn" id="btn-ci" onclick="tgDd('dd-ci')">
      <span id="lbl-ci">Cidade</span>
      <span class="dd-badge" id="bdg-ci" style="display:none"></span>
      <span class="dd-arr">▾</span>
    </div>
    <div class="dd-panel">CIDADE_OPTS</div>
  </div>
  <div class="dd" id="dd-c">
    <div class="dd-btn" id="btn-c" onclick="tgDd('dd-c')">
      <span id="lbl-c">Nicho</span>
      <span class="dd-badge" id="bdg-c" style="display:none"></span>
      <span class="dd-arr">▾</span>
    </div>
    <div class="dd-panel">CAT_OPTS</div>
  </div>
  <div class="dd" id="dd-s">
    <div class="dd-btn" id="btn-s" onclick="tgDd('dd-s')">
      <span id="lbl-s">Estado</span>
      <span class="dd-arr">▾</span>
    </div>
    <div class="dd-panel" style="min-width:170px">
      <div class="ddi on" onclick="sF('s','',this)"><span>Todos</span><span class="ddc" id="cn-all">0</span></div>
      <div class="ddi" onclick="sF('s','novo',this)"><span>🔵 Novos</span><span class="ddc" id="cn-novo">0</span></div>
      <div class="ddi" onclick="sF('s','contactado',this)"><span>📞 Contactados</span><span class="ddc" id="cn-cont">0</span></div>
      <div class="ddi" onclick="sF('s','interessado',this)"><span>⭐ Interessados</span><span class="ddc" id="cn-int">0</span></div>
      <div class="ddi" onclick="sF('s','fechado',this)"><span>✅ Fechados</span><span class="ddc" id="cn-fech">0</span></div>
      <div class="ddi" onclick="sF('s','recusado',this)"><span>❌ Recusados</span><span class="ddc" id="cn-rec">0</span></div>
      <div class="ddi" onclick="sF('s','followup',this)"><span>📅 Com follow-up</span><span class="ddc" id="cn-fu">0</span></div>
    </div>
  </div>
  <div style="margin-left:auto"><span id="hs" style="font-size:.72rem;color:var(--mu2)"></span></div>
</div>

<div class="rc">
  <strong id="rc-n">0</strong> <span id="rc-txt">leads</span>
  <div class="rc-bar"><div class="rc-fill" id="rc-fill" style="width:0%"></div></div>
</div>

<div class="ll" id="ll"></div>

</div><!-- /app -->

<script>
const L = /*LEAD_DATA*/;
const PT = /*PITCH_DATA*/;

const BADGE = {
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
  "Pintura Arte":"background:#2a0a2a;color:#FF69B4"
};

function getBadge(cat){ return BADGE[cat]||"background:#222;color:#aaa"; }

function stars(r){
  if(!r) return '';
  r=parseFloat(r); if(isNaN(r)||r<=0) return '';
  const f=Math.floor(r),h=(r-f)>=0.5?1:0;
  return '★'.repeat(f)+(h?'½':'')+'☆'.repeat(5-f-h);
}

function esc(s){ return s?(s+'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'):''; }

function today(){
  const d=new Date();
  return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
}
function todayFmt(){
  const d=new Date();
  return String(d.getDate()).padStart(2,'0')+'/'+String(d.getMonth()+1).padStart(2,'0')+'/'+d.getFullYear()
    +' '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
}

// ── localStorage ──────────────────────────────────────────────────────────
const ld=()=>{try{return JSON.parse(localStorage.getItem('crmPorto')||'{}')}catch(e){return{}}};
const sv=s=>localStorage.setItem('crmPorto',JSON.stringify(s));

// ── Login ──────────────────────────────────────────────────────────────────
function checkLogin(){
  if(sessionStorage.getItem('crmAuth')==='1'){
    document.getElementById('lp').style.display='none';
    document.getElementById('app').style.display='block';
    rnd();
  }
}
function doLogin(){
  const u=document.getElementById('li-u').value.trim();
  const p=document.getElementById('li-p').value;
  if(u==='josilva'&&p==='2026'){
    sessionStorage.setItem('crmAuth','1');
    document.getElementById('lp').style.display='none';
    document.getElementById('app').style.display='block';
    rnd();
  } else {
    document.getElementById('li-err').textContent='Usuário ou senha incorretos.';
  }
}
function doLogout(){
  sessionStorage.removeItem('crmAuth');
  document.getElementById('app').style.display='none';
  document.getElementById('lp').style.display='flex';
  document.getElementById('li-p').value='';
  document.getElementById('li-err').textContent='';
}
document.getElementById('li-p').addEventListener('keydown',e=>{ if(e.key==='Enter') doLogin(); });
document.getElementById('li-u').addEventListener('keydown',e=>{ if(e.key==='Enter') document.getElementById('li-p').focus(); });

// ── Dropdown ──────────────────────────────────────────────────────────────
function tgDd(id){
  const el=document.getElementById(id),was=el.classList.contains('open');
  document.querySelectorAll('.dd.open').forEach(d=>d.classList.remove('open'));
  if(!was) el.classList.add('open');
}
document.addEventListener('click',e=>{ if(!e.target.closest('.dd')) document.querySelectorAll('.dd.open').forEach(d=>d.classList.remove('open')); });

let F={c:'',s:'',ci:''}, PG=30, pg=0, FL=[];

function sF(k,v,el){
  F[k]=v;
  if(el){ el.closest('.dd-panel').querySelectorAll('.ddi').forEach(d=>d.classList.remove('on')); el.classList.add('on'); }
  const dd={'ci':'dd-ci','c':'dd-c','s':'dd-s'};
  if(dd[k]) document.getElementById(dd[k]).classList.remove('open');
  if(k==='ci'){
    const lbl=document.getElementById('lbl-ci'),bdg=document.getElementById('bdg-ci'),btn=document.getElementById('btn-ci');
    if(v){lbl.textContent=v;bdg.textContent=FL.filter(l=>l.cidade===v).length||'';bdg.style.display='inline';btn.classList.add('act');}
    else{lbl.textContent='Cidade';bdg.style.display='none';btn.classList.remove('act');}
  }
  if(k==='c'){
    const lbl=document.getElementById('lbl-c'),bdg=document.getElementById('bdg-c'),btn=document.getElementById('btn-c');
    if(v){lbl.textContent=v;bdg.textContent=FL.filter(l=>l.cat===v).length||'';bdg.style.display='inline';btn.classList.add('act');}
    else{lbl.textContent='Nicho';bdg.style.display='none';btn.classList.remove('act');}
  }
  if(k==='s'){
    const lm={'':'Estado','novo':'🔵 Novos','contactado':'📞 Contact.','interessado':'⭐ Interest.','fechado':'✅ Fechados','recusado':'❌ Recusados','followup':'📅 Follow-up'};
    document.getElementById('lbl-s').textContent=lm[v]||'Estado';
    document.getElementById('btn-s').classList.toggle('act',v!=='');
  }
  rnd();
}

// ── Filter & render ────────────────────────────────────────────────────────
function rnd(){
  const s=ld(), q=(document.getElementById('sr').value||'').toLowerCase(), td=today();
  FL=L.filter(l=>{
    const st=(s[l.id]?.st)||'novo';
    const fu=(s[l.id]?.fu)||'';
    if(F.c&&l.cat!==F.c) return false;
    if(F.ci&&l.cidade!==F.ci) return false;
    if(F.s==='followup'){
      if(!fu||fu>td) return false;
    } else if(F.s&&st!==F.s) return false;
    if(q&&!l.nome.toLowerCase().includes(q)&&!l.cidade.toLowerCase().includes(q)&&!l.cat.toLowerCase().includes(q)) return false;
    return true;
  });
  // stats (global, not filtered)
  const c={novo:0,contactado:0,interessado:0,fechado:0,recusado:0};
  let fuDue=0;
  L.forEach(l=>{
    const st=(s[l.id]?.st)||'novo'; if(c[st]!==undefined) c[st]++;
    const fu=(s[l.id]?.fu)||''; if(fu&&fu<=td) fuDue++;
  });
  document.getElementById('st-t').textContent=L.length;
  document.getElementById('st-n').textContent=c.novo;
  document.getElementById('st-c').textContent=c.contactado;
  document.getElementById('st-i').textContent=c.interessado;
  document.getElementById('st-f').textContent=c.fechado;
  document.getElementById('st-fu').textContent=fuDue;
  // estado dropdown counts
  document.getElementById('cn-all').textContent=FL.length;
  document.getElementById('cn-novo').textContent=FL.filter(l=>(s[l.id]?.st||'novo')==='novo').length;
  document.getElementById('cn-cont').textContent=FL.filter(l=>(s[l.id]?.st)==='contactado').length;
  document.getElementById('cn-int').textContent=FL.filter(l=>(s[l.id]?.st)==='interessado').length;
  document.getElementById('cn-fech').textContent=FL.filter(l=>(s[l.id]?.st)==='fechado').length;
  document.getElementById('cn-rec').textContent=FL.filter(l=>(s[l.id]?.st)==='recusado').length;
  document.getElementById('cn-fu').textContent=L.filter(l=>{const fu=(s[l.id]?.fu)||'';return fu&&fu<=td;}).length;
  // result bar
  const pct=L.length?(FL.length/L.length*100):0;
  document.getElementById('rc-n').textContent=FL.length;
  document.getElementById('rc-txt').textContent=FL.length===1?'lead':'leads';
  document.getElementById('rc-fill').style.width=pct+'%';
  if(F.ci) document.getElementById('bdg-ci').textContent=FL.length;
  if(F.c) document.getElementById('bdg-c').textContent=FL.length;
  pg=0; document.getElementById('ll').innerHTML=''; rp();
}

function rp(){
  const s=ld(), sl=FL.slice(pg*PG,(pg+1)*PG), ll=document.getElementById('ll'), td=today();
  const ob=document.getElementById('lmbtn'); if(ob) ob.remove();
  if(!FL.length&&pg===0){ll.innerHTML='<div class="em">Sem leads para os filtros selecionados.</div>';return;}
  sl.forEach((l,i)=>{
    const st=(s[l.id]?.st)||'novo';
    const fu=(s[l.id]?.fu)||'';
    const wab=l.wa?`<a class="wa-link" href="https://wa.me/${l.wa}" target="_blank">WA</a>`:'';
    const telb=l.tel?`<a class="tel" href="tel:${l.tel.replace(/\s/g,'')}">${l.tel}</a>`:`<span style="color:var(--mu);font-size:.7rem">Sem tel.</span>`;
    const stl=stars(l.r);
    let fuChip='';
    if(fu){
      if(fu<td) fuChip=`<span class="fu-chip fu-ov">⚠️ ${fu}</span>`;
      else if(fu===td) fuChip=`<span class="fu-chip fu-td">📅 Hoje</span>`;
      else fuChip=`<span class="fu-chip fu-ft">🔵 ${fu}</span>`;
    }
    const d=document.createElement('div'); d.className='cd'; d.id='cd'+l.id;
    d.style.animationDelay=(i*0.025)+'s';
    d.innerHTML=`<div class="ct">
      <div class="cn">${pg*PG+i+1}</div>
      <div class="ci">
        <div class="cm">${esc(l.nome)}</div>
        <div class="cx">
          <span class="ba" style="${getBadge(l.cat)}">${esc(l.cat)}</span>
          <span class="ba bci">${esc(l.cidade)}</span>
          <span class="ba bsw">Sem site</span>
          ${stl?`<span class="rat">${stl} <span style="color:var(--mu);font-size:.62rem">(${l.av})</span></span>`:''}
          ${fuChip}
        </div>
        <div class="adr">📍 ${esc(l.morada||l.cidade)}</div>
      </div>
      <div class="cac" onclick="event.stopPropagation()">
        ${telb}${wab}
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
    <div class="pp" id="pp${l.id}"><div class="pp-in"><div class="pp-body"></div></div></div>`;
    ll.appendChild(d);
  });
  if((pg+1)*PG<FL.length){
    const b=document.createElement('button'); b.className='lm'; b.id='lmbtn';
    const rem=FL.length-(pg+1)*PG;
    b.textContent=`Carregar mais ${rem} lead${rem!==1?'s':''}`;
    b.onclick=()=>{pg++;rp();}; ll.appendChild(b);
  }
}

// ── Pitch panel ────────────────────────────────────────────────────────────
function getPT(cat){
  if(!cat) return PT['_default'];
  if(PT[cat]) return PT[cat];
  const cl=cat.toLowerCase();
  for(const k of Object.keys(PT)){
    if(k==='_default') continue;
    if(k.toLowerCase().includes(cl)||cl.includes(k.toLowerCase())) return PT[k];
  }
  return PT['_default'];
}

function rp2(s,l){
  return s.replace(/{nome}/g,esc(l.nome)).replace(/{cidade}/g,esc(l.cidade)).replace(/{cat}/g,esc(l.cat));
}
// version without html-escaping for copy/clipboard
function rp2raw(s,l){
  return s.replace(/{nome}/g,l.nome).replace(/{cidade}/g,l.cidade).replace(/{cat}/g,l.cat);
}

function tog(id){
  const pp=document.getElementById('pp'+id);
  const btn=document.getElementById('bpb'+id);
  if(!pp.dataset.built){ buildPanel(id); pp.dataset.built='1'; }
  pp.classList.toggle('o');
  btn.classList.toggle('open');
  btn.textContent=pp.classList.contains('o')?'Pitch ▴':'Pitch ▾';
}

function buildPanel(id){
  const l=L.find(x=>x.id===id); if(!l) return;
  const pt=getPT(l.cat);
  const s=ld(), fu=(s[id]?.fu)||'', log=(s[id]?.log)||[], td=today();

  // abertura
  const abNames=['Fria','Curiosidade','Direta'];
  const abH=pt.ab.map((a,i)=>`
    <div class="ps"><h4>Variação ${i+1} — ${abNames[i]||''}</h4>
      <div class="pb ab" id="ab-${id}-${i}">${rp2(a,l)}
        <button class="cb" onclick="cptxt(${id},'ab',${i})">Copiar</button>
      </div>
    </div>`).join('');

  // pitch sizes
  const psH=`<div class="psz-bar">
    <button class="psz on" id="psz-${id}-0" onclick="pszSwitch(${id},0)">Curto</button>
    <button class="psz" id="psz-${id}-1" onclick="pszSwitch(${id},1)">Médio</button>
    <button class="psz" id="psz-${id}-2" onclick="pszSwitch(${id},2)">Completo</button>
  </div>
  ${pt.ps.map((p,i)=>`<div class="psz-c ${i===0?'on':''}" id="psc-${id}-${i}">
    <div class="pb pit" id="ps-${id}-${i}">${rp2(p,l)}
      <button class="cb" onclick="cptxt(${id},'ps',${i})">Copiar</button>
    </div>
  </div>`).join('')}`;

  // objections
  const obH=pt.obs.map((o,i)=>`
    <div class="ob-item" id="obi-${id}-${i}">
      <div class="ob-q" onclick="togOb(${id},${i})">
        <span class="ob-icon">❝</span>
        <span>${esc(o.ob)}</span>
        <span class="ob-arr">▾</span>
      </div>
      <div class="ob-ans">${rp2(o.q,l)}</div>
    </div>`).join('');

  // whatsapp
  const waRaw=rp2raw(pt.wa,l);
  const waH=l.wa?`
    <div class="ps"><h4>Mensagem de abertura</h4>
      <div class="pb wa-box" id="wa-${id}">${rp2(pt.wa,l)}
        <button class="cb" onclick="cptxt(${id},'wa',0)">Copiar</button>
      </div>
    </div>
    <button class="wa-open" onclick="window.open('https://wa.me/${l.wa}?text='+encodeURIComponent(document.getElementById('wa-${id}').innerText.replace(/Copiar$/,'')))">📱 Abrir no WhatsApp</button>`
    :`<div style="color:var(--mu);font-size:.8rem;padding:8px">Sem número WhatsApp disponível.</div>`;

  // follow-up
  let fuInd='';
  if(fu){ if(fu<td) fuInd='<span class="fu-ind fu-ov-ind">⚠️ Atrasado</span>'; else if(fu===td) fuInd='<span class="fu-ind fu-td-ind">📅 Hoje</span>'; else fuInd=`<span class="fu-ind fu-ft-ind">🔵 Agendado</span>`; }
  const fuH=`
    <div class="fu-row">
      <label>Data do follow-up:</label>
      <input type="date" id="fui-${id}" value="${fu}" onchange="svFu(${id},this.value)">
      <span id="fu-ind-${id}">${fuInd}</span>
    </div>
    <div class="ps"><h4>Mensagem Dia 4 (sem resposta)</h4>
      <div class="pb" id="fu4-${id}">${rp2(pt.fu4,l)}
        <button class="cb" onclick="cptxt(${id},'fu4',0)">Copiar</button>
      </div>
    </div>
    <div class="ps"><h4>Mensagem Dia 10 (sem resposta)</h4>
      <div class="pb" id="fu10-${id}">${rp2(pt.fu10,l)}
        <button class="cb" onclick="cptxt(${id},'fu10',0)">Copiar</button>
      </div>
    </div>
    <div class="ps"><h4>Resposta "Não tenho interesse"</h4>
      <div class="pb" id="ni-${id}">${rp2(pt.ni,l)}
        <button class="cb" onclick="cptxt(${id},'ni',0)">Copiar</button>
      </div>
    </div>`;

  // activity log
  const lgH=`
    <div id="log-list-${id}" class="log-list">${renderLogHtml(log)}</div>
    <div class="log-new">
      <textarea id="log-ta-${id}" placeholder="O que aconteceu na ligação? O que o cliente disse..."></textarea>
      <button class="log-add" onclick="addLog(${id})">+ Adicionar nota</button>
    </div>`;

  const body=document.querySelector('#pp'+id+' .pp-body');
  body.innerHTML=`
    <div class="ptabs">
      <button class="ptab on" id="ptab-${id}-ab" onclick="ptabSwitch(${id},'ab')">Abertura</button>
      <button class="ptab" id="ptab-${id}-pi" onclick="ptabSwitch(${id},'pi')">Pitch</button>
      <button class="ptab" id="ptab-${id}-ob" onclick="ptabSwitch(${id},'ob')">Objeções</button>
      <button class="ptab" id="ptab-${id}-wa" onclick="ptabSwitch(${id},'wa')">WhatsApp</button>
      <button class="ptab" id="ptab-${id}-fu" onclick="ptabSwitch(${id},'fu')">Follow-up</button>
      <button class="ptab" id="ptab-${id}-lg" onclick="ptabSwitch(${id},'lg')">Atividade</button>
    </div>
    <div class="pt-sec on" id="pts-${id}-ab">${abH}</div>
    <div class="pt-sec" id="pts-${id}-pi">${psH}</div>
    <div class="pt-sec" id="pts-${id}-ob">${obH}</div>
    <div class="pt-sec" id="pts-${id}-wa">${waH}</div>
    <div class="pt-sec" id="pts-${id}-fu">${fuH}</div>
    <div class="pt-sec" id="pts-${id}-lg">${lgH}</div>`;
}

function ptabSwitch(id,key){
  ['ab','pi','ob','wa','fu','lg'].forEach(k=>{
    document.getElementById('pts-'+id+'-'+k)?.classList.toggle('on',k===key);
    document.getElementById('ptab-'+id+'-'+k)?.classList.toggle('on',k===key);
  });
}

function pszSwitch(id,idx){
  [0,1,2].forEach(i=>{
    document.getElementById('psz-'+id+'-'+i)?.classList.toggle('on',i===idx);
    document.getElementById('psc-'+id+'-'+i)?.classList.toggle('on',i===idx);
  });
}

function togOb(id,idx){
  const item=document.getElementById('obi-'+id+'-'+idx);
  if(item) item.classList.toggle('open');
}

// ── Copy ──────────────────────────────────────────────────────────────────
function cptxt(id,type,idx){
  const l=L.find(x=>x.id===id); if(!l) return;
  const pt=getPT(l.cat);
  let text='';
  if(type==='ab') text=rp2raw(pt.ab[idx]||'',l);
  else if(type==='ps') text=rp2raw(pt.ps[idx]||'',l);
  else if(type==='wa') text=rp2raw(pt.wa,l);
  else if(type==='fu4') text=rp2raw(pt.fu4,l);
  else if(type==='fu10') text=rp2raw(pt.fu10,l);
  else if(type==='ni') text=rp2raw(pt.ni,l);
  if(!text) return;
  navigator.clipboard.writeText(text).then(()=>{
    // find button near type
    let btnId;
    if(type==='ab') btnId=`ab-${id}-${idx}`;
    else if(type==='ps') btnId=`ps-${id}-${idx}`;
    else if(type==='wa') btnId=`wa-${id}`;
    else if(type==='fu4') btnId=`fu4-${id}`;
    else if(type==='fu10') btnId=`fu10-${id}`;
    else if(type==='ni') btnId=`ni-${id}`;
    const el=document.getElementById(btnId);
    if(el){ const b=el.querySelector('.cb'); if(b){b.textContent='✓';setTimeout(()=>b.textContent='Copiar',2000);} }
  }).catch(()=>{});
}

// ── Status ────────────────────────────────────────────────────────────────
function sst(id,v){
  const s=ld(); if(!s[id]) s[id]={}; s[id].st=v; sv(s);
  const el=document.querySelector('#cd'+id+' .ss2'); if(el) el.className='ss2 s-'+v;
  rnd();
}

// ── Follow-up ─────────────────────────────────────────────────────────────
function svFu(id,v){
  const s=ld(); if(!s[id]) s[id]={}; s[id].fu=v; sv(s);
  const td=today();
  let html='', cls='';
  if(v){ if(v<td){html='⚠️ Atrasado';cls='fu-ov-ind';} else if(v===td){html='📅 Hoje';cls='fu-td-ind';} else{html='🔵 Agendado';cls='fu-ft-ind';} }
  const ind=document.getElementById('fu-ind-'+id);
  if(ind){ ind.className='fu-ind '+(cls||''); ind.textContent=html; }
  // update chip on card
  rnd();
}

// ── Activity log ──────────────────────────────────────────────────────────
function renderLogHtml(log){
  if(!log||!log.length) return '<div class="log-empty">Nenhuma atividade registrada ainda.</div>';
  return log.map(e=>`<div class="log-entry"><div class="log-ts">${esc(e.ts)}</div><div class="log-txt">${esc(e.txt)}</div></div>`).join('');
}
function renderLog(id){
  const s=ld(), log=(s[id]?.log)||[];
  const el=document.getElementById('log-list-'+id);
  if(el) el.innerHTML=renderLogHtml(log);
}
function addLog(id){
  const ta=document.getElementById('log-ta-'+id);
  if(!ta||!ta.value.trim()) return;
  const s=ld(); if(!s[id]) s[id]={}; if(!s[id].log) s[id].log=[];
  s[id].log.unshift({ts:todayFmt(),txt:ta.value.trim()});
  sv(s); ta.value=''; renderLog(id);
}

// ── Export ────────────────────────────────────────────────────────────────
function expN(){
  const s=ld(); let t='CRM Porto — '+new Date().toLocaleDateString('pt-BR')+'\n\n';
  FL.forEach(l=>{
    const d=s[l.id]; if(!d||(!d.log?.length&&(!d.st||d.st==='novo')&&!d.fu)) return;
    t+=`[${(d.st||'novo').toUpperCase()}] ${l.nome} (${l.cidade}) — ${l.tel||'—'}\n`;
    if(d.fu) t+=`Follow-up: ${d.fu}\n`;
    if(d.log?.length){ t+='Atividade:\n'; d.log.forEach(e=>t+=`  [${e.ts}] ${e.txt}\n`); }
    t+='\n';
  });
  const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([t],{type:'text/plain;charset=utf-8'}));
  a.download='crm_porto_'+new Date().toISOString().slice(0,10)+'.txt'; a.click();
}

checkLogin();
</script>
</body>
</html>"""

html = HTML.replace("CIDADE_OPTS", dd_cidade())
html = html.replace("CAT_OPTS", dd_cat())
html = html.replace("/*LEAD_DATA*/", js_leads)
html = html.replace("/*PITCH_DATA*/", js_pitch)

import os
os.makedirs("crm", exist_ok=True)
with open(CRM_HTML, "w", encoding="utf-8") as f:
    f.write(html)
print(f"CRM v3 gerado: {CRM_HTML} ({len(html)//1024}KB)")
