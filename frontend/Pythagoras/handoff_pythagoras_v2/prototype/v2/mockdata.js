// ─── Pythagoras v2 — mock data ────────────────────────────────────────────
// Shape mirrors the backend response defined in the README (Decisões do site 1.0).
// Field names match what the API actually returns or is documented to return.

window.MOCK_BASE = {
  // From tb_processamento_mensal (latest CONCLUIDO)
  mes_atual: "2026-04",          // YYYY-MM — the most recent snapshot processed
  total_empresas: 67_413_209,    // for the home page authority line
  total_socios:   29_874_516,
  ultima_carga:   "2026-05-08T03:14:00-03:00", // when the ETL last ran
};

// ─── Empresa principal (CNPJ search result) ──────────────────────────────
window.MOCK_COMPANY = {
  // Identificação cadastral
  cnpj:            "47.819.002/0001-70",
  cnpj_raw:        "47819002000170",
  cnpj_basico:     "47819002",
  razao_social:    "Marambaia Indústria de Alimentos S.A.",
  nome_fantasia:   "Marambaia Foods",
  natureza_juridica: "205-4 — Sociedade Anônima Fechada",
  qualificacao_responsavel: "16 — Presidente",
  capital_social:  28_500_000,
  porte:           "Demais",                  // 00/01/03/05 → traduzido pelo backend

  // Estabelecimento matriz
  matriz:          true,
  cnpj_ordem:      "0001",
  situacao:        "Ativa",                   // 01/02/03/04/08 → texto
  situacao_data:   "2014-03-12",              // dt_datasituacaocadastral
  motivo_situacao: null,                      // null quando ATIVA; texto quando ≠
  situacao_especial:        null,             // ex: "EM RECUPERACAO JUDICIAL"
  situacao_especial_data:   null,
  data_abertura:   "2014-03-12",              // dt_datainicioatividade
  cnae_principal:  { codigo: "10.61-9-01", descricao: "Beneficiamento de arroz" },
  cnae_secundarios: [
    { codigo: "10.62-7-00", descricao: "Moagem de trigo e fabricação de derivados" },
    { codigo: "10.66-0-00", descricao: "Fabricação de alimentos para animais" },
    { codigo: "46.32-0-01", descricao: "Comércio atacadista de cereais e leguminosas beneficiados" },
    { codigo: "49.30-2-02", descricao: "Transporte rodoviário de carga, exceto produtos perigosos" },
  ],

  endereco: {
    logradouro: "RODOVIA BR 116, KM 212, S/N",
    complemento: "GALPAO 4, DISTRITO INDUSTRIAL",
    bairro:     "AEROPORTO",
    municipio:  "FEIRA DE SANTANA",
    uf:         "BA",
    cep:        "44052-000",
    pais:       "BRASIL",
  },

  contato: {
    telefone1: "(75) 3602-4900",
    telefone2: null,
    email:     "contato@marambaiafoods.com.br",
  },

  // Regime Simples / MEI (vem do join com tabela simples)
  simples: {
    opcao_simples: false,                     // 'S' / 'N' / null no backend
    data_opcao_simples: null,
    data_exclusao_simples: null,
    opcao_mei:     false,
    data_opcao_mei: null,
    data_exclusao_mei: null,
  },

  // ─── Indicadores temporais (Pythagoras) ────────────────────────────────
  // Estes campos não existem no CNPJá — são o diferencial do produto.
  dt_primeira_carga:     "2023-03",           // empresa.dt_primeira_carga
  dt_ultima_atualizacao: "2026-04",           // empresa.dt_ultima_atualizacao
  ativo_na_base_atual:   true,                // dt_ultima_atualizacao === mes_atual

  // ─── QSA ───────────────────────────────────────────────────────────────
  // socios_ativos / socios_inativos: já vêm separados pelo backend (crud.py).
  // Para cada sócio: qualificacao_atual + qualificacoes_anteriores formam a
  // linha do tempo da participação na empresa.
  socios_ativos: [
    {
      identificador_socio: "PF",              // PF / PJ / Estrangeiro
      cpf_cnpj_socio:      "***.418.204-**",  // RF mascara PF
      nome_socio:          "HELOISA DE ANDRADE QUEIROZ",
      data_entrada:        "2014-03-12",
      faixa_etaria:        "51 a 60 anos",    // cd_faixaetaria → texto
      dt_primeira_carga:   "2023-03",
      dt_ultima_atualizacao: "2026-04",
      qualificacao_atual: {
        codigo: "16",
        descricao: "Presidente",
        desde: "2014-03-12",                  // dt_dataentradasociedade do registro vigente
      },
      qualificacoes_anteriores: [],
    },
    {
      identificador_socio: "PF",
      cpf_cnpj_socio:      "***.227.139-**",
      nome_socio:          "OTAVIO RAMALHO SAMPAIO",
      data_entrada:        "2018-07-01",
      faixa_etaria:        "41 a 50 anos",
      dt_primeira_carga:   "2023-03",
      dt_ultima_atualizacao: "2026-04",
      qualificacao_atual: {
        codigo: "05",
        descricao: "Administrador",
        desde: "2026-05-01",                  // promoção recente
      },
      qualificacoes_anteriores: [
        {
          codigo: "22",
          descricao: "Sócio-Administrador",
          de: "2018-07-01",
          ate: "2026-04-30",                  // saiu_em
        },
        {
          codigo: "49",
          descricao: "Sócio-Administrador",
          de: "2018-07-01",
          ate: "2020-12-31",
        },
      ],
    },
    {
      identificador_socio: "PJ",
      cpf_cnpj_socio:      "08.441.779/0001-92",
      nome_socio:          "CONSTRUTORA BOQUEIRAO LTDA",
      data_entrada:        "2014-03-12",
      faixa_etaria:        null,              // não se aplica
      dt_primeira_carga:   "2023-03",
      dt_ultima_atualizacao: "2026-04",
      qualificacao_atual: {
        codigo: "22",
        descricao: "Sócio",
        desde: "2014-03-12",
      },
      qualificacoes_anteriores: [],
    },
    {
      identificador_socio: "PJ",
      cpf_cnpj_socio:      "29.116.540/0001-17",
      nome_socio:          "FUNDO PINDOBA FIP MULTIESTRATEGIA",
      data_entrada:        "2020-01-15",
      faixa_etaria:        null,
      dt_primeira_carga:   "2023-03",
      dt_ultima_atualizacao: "2026-04",
      qualificacao_atual: {
        codigo: "22",
        descricao: "Sócio",
        desde: "2020-01-15",
      },
      qualificacoes_anteriores: [],
    },
    {
      identificador_socio: "PF",
      cpf_cnpj_socio:      "***.905.338-**",
      nome_socio:          "RICARDO MENDES TAVARES",
      data_entrada:        "2025-11-04",
      faixa_etaria:        "61 a 70 anos",
      dt_primeira_carga:   "2025-12",         // entrou recentemente na base
      dt_ultima_atualizacao: "2026-04",
      qualificacao_atual: {
        codigo: "10",
        descricao: "Diretor",
        desde: "2025-11-04",
      },
      qualificacoes_anteriores: [],
    },
  ],

  // Sócios que estavam presentes em snapshots anteriores mas não no mais recente.
  // dt_ultima_atualizacao < mes_atual → saiu da sociedade.
  socios_inativos: [
    {
      identificador_socio: "PF",
      cpf_cnpj_socio:      "***.553.110-**",
      nome_socio:          "ANTONIO CARLOS PEDREIRA",
      data_entrada:        "2014-03-12",
      faixa_etaria:        "71 a 80 anos",
      dt_primeira_carga:   "2023-03",
      dt_ultima_atualizacao: "2024-04",       // saiu há ~2 anos
      qualificacao_atual: {
        codigo: "10",
        descricao: "Diretor",
        desde: "2014-03-12",
      },
      qualificacoes_anteriores: [],
    },
    {
      identificador_socio: "Estrangeiro",
      cpf_cnpj_socio:      null,              // estrangeiros não têm doc na RF
      nome_socio:          "JAIME ALEJANDRO MORALES",
      data_entrada:        "2017-08-20",
      faixa_etaria:        null,
      dt_primeira_carga:   "2023-03",
      dt_ultima_atualizacao: "2023-11",
      qualificacao_atual: {
        codigo: "22",
        descricao: "Sócio",
        desde: "2017-08-20",
      },
      qualificacoes_anteriores: [],
      pais_origem: "ARGENTINA",
    },
  ],

  // ─── Filiais ───────────────────────────────────────────────────────────
  filiais: [
    {
      cnpj: "47.819.002/0002-51",
      cnpj_ordem: "0002",
      municipio: "SALVADOR", uf: "BA",
      situacao: "Ativa", situacao_data: "2015-06-04",
      data_abertura: "2015-06-04",
      dt_ultima_atualizacao: "2026-04",
    },
    {
      cnpj: "47.819.002/0003-32",
      cnpj_ordem: "0003",
      municipio: "RECIFE", uf: "PE",
      situacao: "Ativa", situacao_data: "2017-02-19",
      data_abertura: "2017-02-19",
      dt_ultima_atualizacao: "2026-04",
    },
    {
      cnpj: "47.819.002/0004-13",
      cnpj_ordem: "0004",
      municipio: "CARIACICA", uf: "ES",
      situacao: "Suspensa",
      situacao_data: "2024-10-22",
      motivo_situacao: "Omissão de declarações",
      data_abertura: "2019-04-11",
      dt_ultima_atualizacao: "2026-04",
    },
    {
      cnpj: "47.819.002/0005-02",
      cnpj_ordem: "0005",
      municipio: "GOIANIA", uf: "GO",
      situacao: "Ativa", situacao_data: "2021-09-30",
      data_abertura: "2021-09-30",
      dt_ultima_atualizacao: "2026-04",
    },
  ],
};

// ─── Buscas recentes (workspace local, não persistido) ───────────────────
window.MOCK_HISTORY = [
  { cnpj: "47.819.002/0001-70", nome: "Marambaia Indústria de Alimentos",  uf: "BA", when: "agora",   active: true },
  { cnpj: "12.548.330/0001-03", nome: "Ipanema Logística Integrada",       uf: "SP", when: "12 min" },
  { cnpj: "08.441.779/0001-92", nome: "Construtora Boqueirão",             uf: "BA", when: "há 1h" },
  { cnpj: "29.116.540/0001-17", nome: "Fundo Pindoba FIP",                 uf: "SP", when: "ontem" },
  { cnpj: "31.774.205/0001-58", nome: "Tecelagem Guanabara",               uf: "RJ", when: "ontem" },
];

// ─── Sugestões para autocomplete (vem do endpoint /empresa/busca) ─────────
window.MOCK_SUGGESTIONS = [
  { cnpj: "47.819.002/0001-70", razao_social: "Marambaia Indústria de Alimentos S.A.", nome_fantasia: "Marambaia Foods", uf: "BA", cnae_principal: "Beneficiamento de arroz", situacao: "Ativa" },
  { cnpj: "47.112.880/0001-51", razao_social: "Marambaia Transportes Ltda",            nome_fantasia: "Marambaia Log",    uf: "BA", cnae_principal: "Transporte rodoviário de carga", situacao: "Ativa" },
  { cnpj: "22.608.114/0001-51", razao_social: "Marambaia Comércio de Grãos Ltda",      nome_fantasia: "Marambaia Grãos",  uf: "PE", cnae_principal: "Comércio atacadista de cereais", situacao: "Ativa" },
  { cnpj: "36.990.271/0001-89", razao_social: "Marambaia Participações S.A.",          nome_fantasia: "Marambaia Part.",  uf: "SP", cnae_principal: "Holdings de instituições não-financeiras", situacao: "Baixada" },
];

// ─── Cenário alternativo: empresa em Recuperação Judicial ────────────────
// Para o tweak "Estado da empresa".
window.MOCK_RJ_OVERRIDE = {
  situacao_especial: "EM RECUPERACAO JUDICIAL",
  situacao_especial_data: "2024-08-12",
};

// ─── Cenário alternativo: matriz baixada, filial ativa ───────────────────
window.MOCK_BAIXADA_OVERRIDE = {
  situacao: "Baixada",
  situacao_data: "2025-03-18",
  motivo_situacao: "Extinção pelo encerramento da liquidação voluntária",
  ativo_na_base_atual: true,
  has_filial_ativa: true,
};
