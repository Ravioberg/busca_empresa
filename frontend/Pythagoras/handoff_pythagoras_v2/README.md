# Handoff — Pythagoras v2 (Redesign Adaptativo)

> **Para o Claude Code:** este pacote é uma **referência de design**, não código de produção pra copiar diretamente. Sua tarefa é **adaptar o frontend React/Vite atual** (em `frontend/src/`) na direção visual e estrutural do protótipo, **preservando o que o usuário já gosta** da implementação atual.

---

## Visão geral

O Pythagoras é uma plataforma de consulta de CNPJ baseada na base pública da Receita Federal, com diferencial em **rastreamento temporal** (histórico de presença de empresas, entrada/saída de sócios mês a mês, mudanças de qualificação). O repositório atual está em fase de protótipo funcional — esta entrega é o redesign da próxima versão.

**Repositório:** `Ravioberg/busca_empresa`  
**Frontend atual:** `frontend/src/components/` — React + Vite + Tailwind  
**Backend:** FastAPI + SQLAlchemy + SQLite/PostgreSQL (ver README do repo)

---

## Como usar este handoff

Esta é uma **integração adaptativa**, não uma reescrita. O usuário gostou da direção do v2 mas quer **manter informações e visualizações específicas do código atual** que ele prefere.

### Fluxo recomendado com o usuário:

1. **Abrir o protótipo** `prototype/Pythagoras v2.html` em um navegador para ver o estado-alvo
2. **Abrir as telas atuais** uma a uma (`frontend/src/components/Login.jsx`, `BuscaEmpresa.jsx`, `ResultadoEmpresa.jsx`, `ResultadoSocio.jsx`, `HomeSelecao.jsx`, `Sidebar.jsx`)
3. **Para cada tela**, perguntar ao usuário: "O que você quer manter da versão atual? O que quer adotar do v2?"
4. **Aplicar** mudanças incrementais — token de design primeiro (cores/tipografia), depois estrutura (header temporal, QSA Ativos/Ex-Sócios), depois detalhes
5. **Validar** com o usuário a cada tela antes de seguir

> **Importante:** O usuário diz "tem informações e visualizações que eu tenho agora que eu prefiro" — significa que **NÃO** é só copiar o v2 por cima. Ele quer um híbrido. Pergunte preferências antes de cortar funcionalidades existentes.

---

## Fidelidade

**Alta fidelidade.** Cores hex exatos, tipografia definida, espaçamentos calibrados. O CSS está em `prototype/v2/styles.css` com todos os tokens em `:root`. Pode usar como referência exata.

---

## Direção visual (resumo)

| Aspecto | Antes (atual) | Depois (v2) |
|---|---|---|
| **Paleta** | Warm/teal + accent indigo | Navy corporativo + azul institucional |
| **Tom** | SaaS de produtividade | Ferramenta enterprise de inteligência |
| **Sidebar** | Branca/cinza | Navy 900 sólido, item ativo com border-left azure |
| **Tipografia** | Inter + JetBrains Mono (genérico) | Inter Tight (display) + Inter (body) + JetBrains Mono **disciplinado para todo dado** |
| **QSA** | Lista única plana | **Ativos × Ex-Sócios separados** + histórico de qualificações expandível |
| **Header da empresa** | Chips de meta | Barra temporal: 1ª vez vista, última atualização, contagem ativos/ex, abertura |
| **Estado especial** | Não tratado | Banner vermelho (RJ/Falência) + amarelo (matriz baixada/filial ativa) |

### Tokens de design

```css
/* Navy (estrutura) */
--navy-950: #061227;
--navy-900: #0a1f3d;  /* sidebar, hero */
--navy-800: #01244a;  /* primary */
--navy-700: #173366;

/* Blue (ação) */
--blue-700: #0a5494;
--blue-600: #0a6cb8;  /* botão primário, links */
--blue-500: #0085ca;  /* accent, focus ring */
--blue-100: #dee7f0;
--blue-50:  #eef4f9;  /* hover de linhas */

/* Neutros (slate, frios) */
--ink:       #0f172a;
--ink-2:     #334155;
--ink-3:     #64748b;
--ink-4:     #94a3b8;
--ink-5:     #cbd5e1;
--line:      #e2e8f0;
--line-soft: #edf1f6;
--paper:     #ffffff;
--surface:   #f7f9fc;

/* Semânticas */
--ok:   #15803d;  --ok-50:   #ecfdf5;
--warn: #b45309;  --warn-50: #fef3c7;
--bad:  #b91c1c;  --bad-50:  #fef2f2;
--info: #1d4ed8;  --info-50: #eff6ff;
```

### Tipografia

```css
--font-display: "Inter Tight", "Inter", system-ui, sans-serif;
--font-ui:      "Inter", system-ui, sans-serif;
--font-mono:    "JetBrains Mono", ui-monospace, "SF Mono", monospace;
```

**Regra de uso:**
- `Inter Tight` — títulos (`.company-name` 24px/600, `.idle h1` 32px/600)
- `Inter` — corpo (13.5px/400 padrão)
- `JetBrains Mono` — **todo dado** (CNPJ, datas, valores monetários, códigos, labels). Se é número/identificador, é mono.

**Labels em mono CAPS:** `text-transform: uppercase; letter-spacing: 0.14em; font-size: 10.5px; font-weight: 600;`

---

## Telas (com adaptação por tela)

### 1. Login (`Login.jsx`)

**Layout proposto:** Split-screen
- Esquerda (50%): Gradient navy-900 → navy-700 com logo Pythagoras grande + tagline em PT-BR
- Direita (50%): Formulário em paper branco, inputs com borda `--line`, CTA primário em `--blue-600`

**Perguntar ao usuário antes:**
- Tem foto/imagem stock atualmente? Substituir por gradient?
- A tagline atual fica? Sugestão: "Inteligência cadastral sobre empresas brasileiras"
- SSO ou só email/senha?

### 2. Home / Seleção (`HomeSelecao.jsx`)

**Layout proposto:**
- 2 cards lado a lado: "Buscar Empresa" e "Buscar Sócio"
- Cards com borda navy hover, ícone interno
- Embaixo: linha mono com métricas da base (`Última base processada: abril/2026 · 67M empresas · 30M sócios`)

**Manter do atual:** estrutura de 2 cards (já está certa).

### 3. Sidebar (`Sidebar.jsx`)

**Layout proposto:**
- Fundo `--navy-900` sólido, largura 264px, sticky
- Brand no topo: monogram "π" em quadrado `--blue-500` + nome + sub-label "CNPJ Intelligence"
- Grupo "Buscas recentes" (mock localStorage no frontend)
- Footer: métricas da base (`Base RFB · abr/26 · 67M empresas`)

**Perguntar ao usuário:**
- Os atalhos / áreas que existem na sidebar atual valem a pena manter?
- "Listas salvas" — manter ou tirar? (Direção v2 sugere tirar até ter persistência real)

### 4. Busca (`BuscaEmpresa.jsx`, `BuscaSocio.jsx`)

**Adições:**
- Validação de CNPJ mod-11 em tempo real (já implementada em `prototype/v2/components.jsx` — função `validCNPJ`)
- Autocomplete unificado (CNPJ + razão social + nome fantasia)
- **Aviso fixo na busca de CPF:** "A Receita Federal omite 5 dígitos do CPF — resultados podem incluir múltiplas pessoas com mesmos dígitos visíveis."

**Manter do atual:** detecção automática de tipo de busca (CNPJ vs CPF vs nome) se já existir.

### 5. Resultado Empresa (`ResultadoEmpresa.jsx`) — **CENTRAL**

#### 5a. Header
- Logo quadrado navy com iniciais
- Eyebrow: `CNPJ · Situação (pill) · Matriz/Filial · Motivo (se baixada)`
- Nome em Inter Tight 24px/600 cor `--navy-900`
- Botões à direita: "Ver rede" (disabled, teaser do v3) + "Exportar PDF" (primary `--blue-600`)

#### 5b. Banner crítico (condicional)
Quando `situacao_especial` preenchido (Recuperação Judicial, Falência, etc.):
```html
<div class="special-banner">
  [ícone] [label "Situação Especial"] Em Recuperação Judicial [desde data]
</div>
```

#### 5c. Banner informativo (condicional)
Quando `situacao = Baixada` E `has_filial_ativa = true`:
```html
<div class="info-banner">
  [ícone] Atenção: matriz baixada, mas há filial(is) ativa(s). Verifique transferência de sede.
</div>
```

#### 5d. **Barra temporal** (4 células)
- 1ª vez vista (`dt_primeira_carga`, com "X+ anos")
- Última atualização (`dt_ultima_atualizacao`, com "na base atual"/"fora da base")
- Quadro societário (`N sócios + M ex-sócios`)
- Abertura (`dt_datainicioatividade`, com idade)

#### 5e. QSA — **coração do produto**
- Bloco "Sócios Ativos" + bloco "Ex-Sócios" separados visualmente
- Click em uma linha expande → histórico de qualificações (timeline com dot ativo + anteriores)
- Badge "mudou" em sócios cuja qualificação mudou nos últimos 12 meses
- Ícones por tipo: PF (iniciais), PJ (building quadrado), Estrangeiro (globo amarelo)

#### 5f. Outras seções
- Identificação cadastral (KV grid)
- Atividades econômicas (CNAE principal destacado azure, secundários em lista)
- Endereço (KV grid + botão "Abrir no Maps")
- Contato (KV grid)
- Filiais (lista compacta)

#### 5g. Coluna lateral (~360px)
- Card navy "Pythagoras · Histórico" com 5 linhas de presença na base
- Card placeholder "Em desenvolvimento · v3 — Rede de sócios"

**REMOVER do atual (já documentado em `direction/Direção v2.html`):**
- Timeline de eventos com diffs (backend não fornece)
- Mapa com lat/lng
- Painel de sinais genéricos
- Listas salvas / favoritos

**Mas perguntar ao usuário antes de cortar.**

### 6. Resultado Sócio (`ResultadoSocio.jsx`)

Aplicar **a mesma lógica temporal**:
- Bloco "Empresas Atuais" (onde a pessoa ainda é sócia)
- Bloco "Empresas Passadas" (saiu — com data de saída)
- Aviso de CPF parcial fixo

---

## Estado / Lógica

### Validação de CNPJ
Função `validCNPJ()` em `prototype/v2/components.jsx` — algoritmo mod-11 dos dígitos verificadores. Pode copiar.

### Separação Ativos × Ex-Sócios
Esta é lógica de **backend**, não frontend. Backend retorna `socios_ativos[]` e `socios_inativos[]` já separados — frontend só renderiza em blocos diferentes.

Ver documento `direction/Integração Backend.html` para o shape exato do JSON e a query Python.

### Banners contextuais
- `special-banner` se `company.situacao_especial != null`
- `info-banner` (warn) se `company.situacao == 'Baixada' && company.has_filial_ativa == true`

---

## Backend (resumo)

A integração com o backend FastAPI tem **doc separado** em `direction/Integração Backend.html` — abra ele em paralelo ao implementar. Inclui:

- 4 endpoints necessários (`/empresa/{cnpj}`, `/empresa/busca`, `/socio/busca`, `/health`)
- Shape JSON completo da resposta de empresa (incluindo `SocioWithHistory`)
- Mapeamento campo-a-campo (schema do banco → resposta da API)
- Mapas de tradução de códigos da RFB (porte, situação, faixa etária, etc.)
- Algoritmo Python para separar Ativos/Ex-Sócios e montar histórico de qualificações
- 6 passos práticos de implementação

---

## Arquivos neste pacote

```
handoff_pythagoras_v2/
├── README.md                           ← este arquivo
├── prototype/
│   ├── Pythagoras v2.html              ← entry HTML, abra no navegador
│   └── v2/
│       ├── app.jsx                     ← App, Sidebar, Result, QSA com expand
│       ├── components.jsx              ← Icon, StatusPill, KV, Copyable, maskCNPJ, validCNPJ
│       ├── styles.css                  ← TODOS os tokens + styles (1 arquivo)
│       └── mockdata.js                 ← shape esperado da API (use como contrato)
└── direction/
    ├── Direção v2.html                 ← justificativa da direção (palette, tipografia, remoções, adições)
    ├── direcao-v2.css
    ├── Integração Backend.html         ← handoff técnico do backend (endpoints, schema, algoritmos)
    └── integracao-v2.css
```

**Como abrir os HTMLs:** basta dois cliques — eles são auto-contidos com CDN do React/Babel.

---

## Conversa com o usuário — sugestão de fluxo

1. "Antes de mexer em nada, me confirma qual stack o frontend usa hoje?" *(esperado: React + Vite + Tailwind)*
2. "Você quer que a paleta navy seja aplicada via tokens do Tailwind ou via CSS vars?" 
3. "Vamos tela por tela. Começando pela Sidebar — você quer manter algo do design atual ou adotar o navy completo?"
4. *Implementar a mudança, mostrar, validar.*
5. *Repetir pra Login → Home → Busca → ResultadoEmpresa → ResultadoSocio.*

**Pontos onde o usuário provavelmente vai querer manter o atual:**
- Lógica de detecção do tipo de busca (CNPJ/CPF/nome)
- Estrutura do roteamento entre telas
- Componentes utilitários (api.js, formatadores)
- Possivelmente algumas seções que ele já refinou no `ResultadoEmpresa.jsx`

**Pontos onde o v2 é claramente upgrade:**
- Paleta (warm → navy)
- QSA Ativos × Ex-Sócios
- Barra temporal no header
- Banners contextuais
- Card lateral navy "Histórico"

---

## Notas finais

- **Não inclui screenshots por padrão** — abra os HTMLs no navegador para ver o resultado renderizado.
- O protótipo HTML usa React via CDN (Babel) — em produção, transpilar via Vite normalmente.
- O backend doc (`Integração Backend.html`) referencia campos reais do schema (`backend/models.py`) do repo `Ravioberg/busca_empresa` — use como ground truth, não como sugestão.
- Próximo grande passo após v2 = **rede de sócios** (v3). O placeholder no card lateral já antecipa isso.
