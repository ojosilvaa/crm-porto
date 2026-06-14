-- ═══════════════════════════════════════════════════════════
--  Migração: crm-porto → Supabase
--  Para usar no projeto "primeira-pagina-seo" ou novo projeto dedicado
-- ═══════════════════════════════════════════════════════════

-- 1. CRIAR TABELA DE LEADS
CREATE TABLE IF NOT EXISTS leads (
  id          BIGINT PRIMARY KEY,
  nome        TEXT NOT NULL,
  cat         TEXT,                     -- nicho (Cabeleireiro, Restaurante, etc.)
  cidade      TEXT,
  morada      TEXT,
  tel         TEXT,
  wa          TEXT,                     -- número WhatsApp (351XXXXXXXXX)
  rating      NUMERIC(2,1),             -- ex: 4.7
  avaliacoes  INTEGER,                  -- número de avaliações Google
  -- campos de CRM (estado da prospeção)
  status      TEXT DEFAULT 'novo'
              CHECK (status IN ('novo','contactado','proposta','reuniao','fechado','perdido')),
  followup    DATE,
  notas       TEXT,
  estrelas    SMALLINT CHECK (estrelas BETWEEN 1 AND 5),
  criado_em   TIMESTAMPTZ DEFAULT now(),
  atualizado_em TIMESTAMPTZ DEFAULT now()
);

-- 2. TRIGGER para atualizar atualizado_em automaticamente
CREATE OR REPLACE FUNCTION atualizar_timestamp()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.atualizado_em = now(); RETURN NEW; END; $$;

CREATE TRIGGER leads_atualizado_em
  BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();

-- 3. ÍNDICES úteis para filtros do CRM
CREATE INDEX IF NOT EXISTS leads_status_idx ON leads(status);
CREATE INDEX IF NOT EXISTS leads_cat_idx    ON leads(cat);
CREATE INDEX IF NOT EXISTS leads_cidade_idx ON leads(cidade);
CREATE INDEX IF NOT EXISTS leads_followup_idx ON leads(followup) WHERE followup IS NOT NULL;

-- 4. RLS — só o dono vê os seus leads
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "utilizador_ve_os_seus_leads" ON leads
  FOR ALL TO authenticated
  USING (true)   -- simplificado: ajustar quando houver multi-user
  WITH CHECK (true);

-- 5. TABELA DE LOG DE ATIVIDADE
CREATE TABLE IF NOT EXISTS leads_log (
  id          BIGSERIAL PRIMARY KEY,
  lead_id     BIGINT REFERENCES leads(id) ON DELETE CASCADE,
  ts          TIMESTAMPTZ DEFAULT now(),
  texto       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS leads_log_lead_idx ON leads_log(lead_id);

-- ═══════════════════════════════════════════════════════════
--  COMO IMPORTAR OS DADOS
--  1. Correr: python exportar_leads.py
--  2. No Supabase Dashboard → Table Editor → leads → Import CSV
--     Mapear: id→id, nome→nome, cat→cat, cidade→cidade,
--             morada→morada, tel→tel, wa→wa, r→rating, av→avaliacoes
-- ═══════════════════════════════════════════════════════════
