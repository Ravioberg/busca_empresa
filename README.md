# CNPJ Search — Plataforma de Consulta de Dados Públicos

## O que é este projeto

Plataforma web para consulta de empresas e pessoas físicas (sócios) a partir da base pública de dados do CNPJ disponibilizada mensalmente pela Receita Federal do Brasil. O objetivo é entregar uma experiência de consulta limpa e rápida, semelhante ao CNPJá, mas construída do zero com a stack aprendida em aula e com espaço para crescer com funcionalidades próprias ao longo do tempo.

O desenvolvimento é incremental — cada fase entrega algo funcional e utilizável. Não existe grande entrega única no final.

---

## Fonte dos dados

A Receita Federal disponibiliza mensalmente a base completa do CNPJ em arquivos `.zip` que contêm `.csv` dentro. O endereço oficial é o portal de dados abertos do governo: `dados.gov.br`, na seção de Cadastro Nacional da Pessoa Jurídica.

A base é grande (cerca de 85 GB descompactada, 20 GB compactada). O layout oficial de todos os campos está disponível em `gov.br/receitafederal/dados/cnpj-metadados.pdf` e deve ser consultado antes de mapear qualquer model.

### Como os dados estão organizados

A base é composta por arquivos separados para cada entidade. As principais são:

**Empresa** — dados da pessoa jurídica em nível de CNPJ básico (8 dígitos). Contém razão social, natureza jurídica, qualificação do responsável, capital social e porte. É a "cabeça" de cada CNPJ. Não possui nenhuma data de criação ou alteração na base da RF.

**Estabelecimento** — dados de cada unidade física (matriz ou filial). O CNPJ completo de 14 dígitos é formado juntando o CNPJ básico (8 dígitos) com o código de ordem (4 dígitos, sendo 0001 a matriz) e o dígito verificador (2 dígitos). Contém nome fantasia, situação cadastral com sua data, CNAE principal e secundários, endereço completo, telefones e e-mail. Possui `dt_datainicioatividade` e `dt_datasituacaocadastral`.

**Sócios** — quadro societário de cada empresa. Contém nome do sócio ou razão social (quando sócio é PJ), CPF ou CNPJ do sócio, qualificação, data de entrada na sociedade e faixa etária. A RF omite os 3 primeiros dígitos e os 2 dígitos verificadores do CPF por questão de privacidade — buscas por CPF retornam todos os registros que compartilham os mesmos dígitos visíveis. Possui `dt_dataentradasociedade` mas não possui data de saída.

**Simples Nacional** — indica se a empresa é optante pelo Simples e/ou MEI. Possui todas as datas de opção e exclusão tanto do Simples quanto do MEI — este é o único domínio que a RF já data completamente.

Além dessas, há arquivos de domínio (tabelas de apoio) que traduzem códigos para descrições: CNAE, natureza jurídica, qualificação de sócios, motivos de situação cadastral, municípios e países.

O CNPJ básico é o elo de ligação entre todas as tabelas principais. Empresa, estabelecimento, sócios e simples se conectam todos pelo campo `cd_cnpjbasico`.

### Tabelas de domínio — baixar apenas da versão mais recente

As tabelas de domínio são dicionários que traduzem códigos para descrições. Mudam raríssimas vezes — apenas quando o governo cria um novo código ou altera uma descrição. Por isso, ao contrário das tabelas principais, **não precisam ser baixadas de todos os meses** — basta baixar uma vez da versão mais recente e reutilizar.

Tabelas de domínio: `Cnaes`, `Motivos`, `Municipios`, `Naturezas`, `Paises`, `Qualificacoes`.

Tabelas que devem ser baixadas de todos os meses para o histórico: `Empresas`, `Estabelecimentos`, `Socios`, `Simples`.

### Fonte alternativa para download

O site **Casa dos Dados** (`dados-abertos-rf-cnpj.casadosdados.com.br`) mantém uma cópia espelhada de todos os arquivos da RF desde março/2023, com download mais rápido via CDN da Cloudflare. Os arquivos são idênticos aos da RF — é apenas um espelho com melhor infraestrutura de entrega. Para produção, o download deve ser feito diretamente da RF. Para desenvolvimento, a Casa dos Dados é uma alternativa válida e mais rápida.

O histórico disponível na Casa dos Dados cobre de março/2023 até o mês atual, o que representa quase 3 anos de snapshots mensais prontos para processar na Fase 3.

---

## Dicionário de códigos da base

A base da RF usa códigos numéricos em vários campos. Alguns têm tabelas de domínio próprias (como CNAE e qualificação de sócios), outros têm valores fixos documentados apenas no metadado oficial. Abaixo está o dicionário completo de todos os códigos fixos, para que o backend possa traduzir cada valor sem depender de joins adicionais.

### cd_porteempresa — Porte da empresa (tabela Empresa)

```
00 → Não informado
01 → Micro Empresa (ME)
03 → Empresa de Pequeno Porte (EPP)
05 → Demais (inclui médias e grandes empresas)
```

Atenção: não existe código 02 ou 04. Os valores são 00, 01, 03 e 05.

### cd_identificadormatrizfilial — Matriz ou filial (tabela Estabelecimento)

```
1 → Matriz  (cd_cnpjordem = '0001')
2 → Filial  (cd_cnpjordem diferente de '0001')
```

A matriz sempre tem `cd_cnpjordem = '0001'`. Quando a API retorna dados de uma empresa, deve sempre puxar o estabelecimento com `cd_identificadormatrizfilial = 1` como estabelecimento principal. Os dados de situação especial, endereço principal e situação cadastral exibidos no card da empresa vêm sempre da matriz.

### cd_situacaocadastral — Situação cadastral (tabela Estabelecimento)

```
01 → Nula      (registro sem efeito, como se não existisse)
02 → Ativa     (em funcionamento normal)
03 → Suspensa  (atividade suspensa por pendências)
04 → Inapta    (não entregou declarações por 2 anos consecutivos)
08 → Baixada   (encerrada, cancelada ou incorporada)
```

O campo `dt_datasituacaocadastral` já registra a data em que a situação atual foi definida. O campo `cd_motivosituacaocadastral` tem o código do motivo — traduzido pela tabela de domínio `Motivos`.

#### Situação da empresa vs. situação do estabelecimento

No modelo da RF não existe um campo "situação da empresa" — a situação cadastral existe apenas no nível do estabelecimento (CNPJ de 14 dígitos). Por convenção, a situação exibida para uma empresa é sempre a da sua matriz (`cd_cnpjordem = '0001'`), que é o comportamento adotado por sites como o CNPJá e pela própria RF ao consultar o CNPJ completo da matriz.

**Exceções conhecidas (6.648 casos na base de abril/2026):** há empresas em que a matriz está com situação `08 - Baixada` mas possuem pelo menos uma filial com situação `02 - Ativa`. Isso ocorre tipicamente em transferências de sede (a antiga matriz é baixada e uma filial assume o papel de nova sede) ou inconsistências cadastrais da própria RF. Nesses casos, a API exibe a situação da matriz (Baixada), o que é tecnicamente correto mas pode parecer contraditório ao usuário que vê a empresa operando por outra filial.

**Decisão atual:** manter o comportamento padrão (situação = situação da matriz). Os 6.648 casos representam 0,01% do total e são uma inconsistência da fonte de dados, não do sistema. Caso seja necessário tratar esses casos no futuro, a abordagem recomendada é adicionar um campo booleano `fl_tem_filial_ativa` na tabela `empresa`, preenchido uma vez por mês pelo ETL com uma query de GROUP BY, eliminando qualquer JOIN em tempo de requisição.

### nm_situacaoespecial — Situação especial (tabela Estabelecimento)

Este campo **não é um código** — é um texto livre preenchido diretamente pela RF com a descrição da situação. Não há tabela de domínio para ele. Exemplos de valores que aparecem na base:

```
EM RECUPERACAO JUDICIAL
EM LIQUIDACAO JUDICIAL
EM INTERVENCAO
CONCORDATARIA
EM FALENCIA
```

O campo `dt_datasituacaoespecial` registra desde quando a empresa está nessa situação. Quando `nm_situacaoespecial` está vazio, a empresa não tem situação especial. A API deve exibir esse campo apenas quando preenchido, sempre puxando do estabelecimento matriz.

### cd_identificadorsocio — Tipo de sócio (tabela Sócios)

```
1 → Pessoa Jurídica   (sócio é outra empresa — CNPJ completo no campo cd_cpfcnpjsocio)
2 → Pessoa Física     (sócio é uma pessoa — CPF mascarado no campo cd_cpfcnpjsocio)
3 → Estrangeiro       (sócio estrangeiro — campo cd_cpfcnpjsocio vazio)
```

Esse código é crítico para a busca por CPF: só faz sentido buscar por CPF em registros com `cd_identificadorsocio = 2`. Quando o sócio é PJ (`cd_identificadorsocio = 1`), o campo `cd_cpfcnpjsocio` contém o CNPJ completo sem mascaramento e a busca é exata.

### cd_faixaetaria — Faixa etária do sócio (tabela Sócios)

Calculado pela RF com base na data de nascimento do CPF do sócio. Só se aplica a sócios pessoa física.

```
0 → Não se aplica (sócio PJ ou estrangeiro)
1 → 0 a 12 anos
2 → 13 a 20 anos
3 → 21 a 30 anos
4 → 31 a 40 anos
5 → 41 a 50 anos
6 → 51 a 60 anos
7 → 61 a 70 anos
8 → 71 a 80 anos
9 → Maior de 80 anos
```

### opcao_pelo_simples e fl_opcaomei — Opção pelo Simples/MEI (tabela Simples)

```
S → Sim (optante)
N → Não (não optante)
  → Em branco: outros casos (empresa que nunca optou ou situação indefinida)
```

### cd_qualificacaoresponsavel — Qualificação do responsável (tabela Empresa)

Traduzido pela tabela de domínio `Qualificacoes`. Os códigos mais comuns na prática:

```
05 → Administrador
08 → Conselheiro de Administração
10 → Diretor
16 → Presidente
21 → Sócio
22 → Sócio Administrador
29 → Titular - Empresa Individual
49 → Sócio-Administrador
```

A lista completa está no arquivo `Qualificacoes.zip` da base.

### Mascaramento do CPF de sócios

Conforme art. 129 § 2º da Lei nº 13.473/2017, a RF oculta os 3 primeiros dígitos e os 2 dígitos verificadores do CPF. Um CPF `123.456.789-09` aparece na base como `***456789**`. A busca por CPF deve usar os dígitos visíveis (posições 4 a 9 do CPF sem formatação) com `LIKE '%456789%'`. O resultado pode retornar mais de uma pessoa com os mesmos dígitos visíveis — a interface deve deixar isso claro ao usuário.

---

### Atenção: CNPJ alfanumérico a partir de julho de 2026

A Receita Federal publicou a Instrução Normativa RFB nº 2.229/2024 determinando que novos CNPJs emitidos a partir de julho de 2026 terão formato alfanumérico (letras e números). CNPJs já existentes não serão alterados. Filiais abertas após essa data poderão receber o novo formato mesmo que a matriz tenha CNPJ numérico.

O impacto direto para este projeto é que todos os campos de CNPJ devem ser armazenados como string desde o início — nunca como inteiro. Isso já é uma decisão técnica prevista, mas o CNPJ alfanumérico torna essa decisão ainda mais crítica e sem exceção.

---

## Estratégia de carga dos dados

### Quais arquivos baixar de cada mês

Nem todos os arquivos precisam ser baixados de todos os meses. A distinção é:

**Baixar apenas do mês mais recente** — tabelas cujo snapshot mais recente já contém todos os registros históricos, ativos ou não:
- `Empresas0-9` — a RF nunca remove um CNPJ básico do arquivo. Empresas encerradas permanecem para sempre. O snapshot mais recente contém todas as empresas que já existiram. O único dado histórico que se perde ao não processar meses anteriores é o `dt_primeira_carga` (quando o CNPJ apareceu pela primeira vez na base pública). Se esse campo não for necessário, um único mês basta.
- `Estabelecimentos0-9` — mesma lógica: estabelecimentos baixados permanecem no snapshot com `cd_situacaocadastral = 08`. O snapshot de qualquer mês recente contém todos os estabelecimentos que já existiram, cada um com `dt_datainicioatividade` fornecida pela própria RF com precisão de dia. Não há nada a ganhar processando meses anteriores.
- `Simples` — a RF já fornece todas as datas de opção e exclusão do Simples e do MEI dentro do próprio registro. Não há nada a ganhar comparando mês a mês.
- `Cnaes`, `Motivos`, `Municipios`, `Naturezas`, `Paises`, `Qualificacoes` — tabelas de domínio que mudam raríssimas vezes.

**Baixar de todos os meses — apenas Sócios** — única tabela em que o histórico depende genuinamente de processar mês a mês:
- `Socios0-9` — quando um sócio sai de uma empresa, ele simplesmente deixa de aparecer no snapshot seguinte. O snapshot mais recente contém apenas os sócios ativos hoje. Para saber quem já foi sócio no passado — pessoas que saíram, empresas que fecharam — é obrigatório processar todos os meses. Cada mês novo acrescenta ao banco os ex-sócios que sumiram do arquivo. O campo `dt_ultima_atualizacao` de cada registro indica o último mês em que aquela pessoa apareceu como sócia ativa na base da RF.

### Volume real do download histórico

Os tamanhos abaixo são referência confirmada do mês de abril/2026:

```
Por mês (só Empresas + Estabelecimentos + Socios):
  Empresas0:            ~494 MB   |  Empresas1-9:   ~74-94 MB cada
  Estabelecimentos0:    ~1.9 GB   |  Estab.1-9:    ~315-350 MB cada
  Socios0:              ~217 MB   |  Socios1-9:    ~47 MB cada
  Total por mês:        ~6.2 GB comprimido

38 meses (março/2023 → abril/2026):
  Total download:       ~235 GB comprimido (mantidos permanentemente)

Banco SQLite de desenvolvimento:
  ~107 milhões de linhas (empresas + estabelecimentos + sócios)
  ~80-100 GB
```

O banco não acumula uma linha por mês — a lógica incremental faz upsert, então cada registro tem sempre uma única linha no banco.

**Espaço necessário em disco:** ~350 GB (ZIPs ~235 GB permanentes + banco SQLite ~100 GB + margem).

### Os ZIPs nunca são deletados

Os arquivos ZIP baixados são mantidos permanentemente na pasta `dados-brutos/`. Eles são a fonte de verdade do projeto — se o banco precisar ser recriado, se o schema mudar, se uma nova base for adicionada, se a lógica do ETL for alterada, ou quando chegar a hora de processar tudo novamente no banco de produção da empresa, basta rodar o script de carga apontando para os arquivos que já estão na máquina. Nunca será necessário baixar tudo de novo.

O script de carga descompacta cada arquivo para uma pasta temporária durante o processamento e limpa essa pasta ao final — mas os ZIPs originais permanecem intocados.

### Estrutura de pastas para o download

O script de processamento espera encontrar os arquivos organizados nesta estrutura. O Claude Code deve criar todas essas pastas automaticamente no início do projeto — o usuário só precisa baixar os arquivos e soltar na pasta do mês correspondente.

```
dados-brutos/
  2023-03/
    Empresas0.zip ... Empresas9.zip
    Estabelecimentos0.zip ... Estabelecimentos9.zip
    Socios0.zip ... Socios9.zip
  2023-04/
    Empresas0.zip ... Empresas9.zip
    Estabelecimentos0.zip ... Estabelecimentos9.zip
    Socios0.zip ... Socios9.zip
  2023-05/  ...
  2023-06/  ...
  2023-07/  ...
  2023-08/  ...
  2023-09/  ...
  2023-10/  ...
  2023-11/  ...
  2023-12/  ...
  2024-01/  ...
  2024-02/  ...
  2024-03/  ...
  2024-04/  ...
  2024-05/  ...
  2024-06/  ...
  2024-07/  ...
  2024-08/  ...
  2024-09/  ...
  2024-10/  ...
  2024-11/  ...
  2024-12/  ...
  2025-01/  ...
  2025-02/  ...
  2025-03/  ...
  2025-04/  ...
  2025-05/  ...
  2025-06/  ...
  2025-07/  ...
  2025-08/  ...
  2025-09/  ...
  2025-10/  ...
  2025-11/  ...
  2025-12/  ...
  2026-01/  ...
  2026-02/  ...
  2026-03/  ...
  2026-04/                        ← mês mais recente
    Empresas0.zip ... Empresas9.zip
    Estabelecimentos0.zip ... Estabelecimentos9.zip
    Socios0.zip ... Socios9.zip
    Simples.zip                   ← só nesta pasta
    Cnaes.zip                     ← só nesta pasta
    Motivos.zip                   ← só nesta pasta
    Municipios.zip                ← só nesta pasta
    Naturezas.zip                 ← só nesta pasta
    Paises.zip                    ← só nesta pasta
    Qualificacoes.zip             ← só nesta pasta
```

Fonte dos arquivos: `https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos/`

Cada pasta do site corresponde a uma pasta local. O nome da pasta no site tem o dia exato de publicação (ex: `2026-04-12/`) mas a pasta local usa só o mês (ex: `2026-04/`) — o script extrai o mês/ano do nome da pasta para preencher `dt_primeira_carga` e `dt_ultima_atualizacao`.

### Os três ambientes do projeto

O projeto passa por três ambientes ao longo do seu ciclo de vida. O código nunca muda entre eles — apenas a `DATABASE_URL` e as variáveis de ambiente.

**Ambiente 1 — Desenvolvimento local (SQLite)**

Usado durante todo o desenvolvimento e testes. Banco de dados é um único arquivo `.db` na máquina local. Sem servidor, sem configuração, sem custo.

```
DATABASE_URL=sqlite:///./cnpj.db
ALLOWED_ORIGINS=http://localhost:5173
```

**Ambiente 2 — Azure (entrega acadêmica)**

Usado para a entrega do projeto na faculdade. Deploy completo na nuvem com Azure App Service (backend), Azure SQL Database (banco) e Azure Static Web Apps (frontend). Os dados são carregados no Azure SQL rodando o script de carga com a connection string do Azure.

```
DATABASE_URL=mssql+pyodbc://usuario:senha@servidor.database.windows.net/cnpj
ALLOWED_ORIGINS=https://seu-app.azurestaticapps.net
```

**Ambiente 3 — PostgreSQL da empresa (produção real)**

Destino final do projeto. Banco PostgreSQL na infraestrutura da própria empresa. Os mesmos ZIPs já baixados são usados para carregar os dados — não precisa baixar nada de novo. O SQLite local e o Azure continuam existindo nos seus respectivos propósitos após essa migração.

```
DATABASE_URL=postgresql://usuario:senha@host:5432/cnpj
ALLOWED_ORIGINS=https://dominio-da-empresa.com.br
```

Em todos os casos o processo de carga é idêntico: `alembic upgrade head` para criar as tabelas, script de carga apontando para os ZIPs em `dados-brutos/`, nenhuma mudança no código da aplicação.

### Reprocessamento futuro — só Sócios precisam de todos os meses

Se o banco precisar ser recriado do zero em um novo ambiente (PostgreSQL de produção, por exemplo), a estratégia correta é:

1. **Empresa e Estabelecimento:** processar apenas o mês mais recente disponível. O snapshot mais recente da RF já contém todos os registros históricos com status atual. Estabelecimentos baixados permanecem no arquivo com `cd_situacaocadastral = 08` e `dt_datainicioatividade` fornecida pela RF. Processar 38 meses de Empresa e Estabelecimento geraria exatamente o mesmo banco final — seria trabalho repetido sem ganho.

2. **Sócios:** processar todos os meses disponíveis, do mais antigo ao mais recente. Cada mês agrega ao banco os sócios que existiam naquele período e já não aparecem hoje. Pular meses significa perder o histórico de ex-sócios daquele período para sempre.

3. **Simples e domínios:** processar apenas o mês mais recente, como sempre.

Essa assimetria é a principal lição arquitetural da fase de carga: empresa e estabelecimento são snapshots completos que crescem por substituição, enquanto sócios são snapshots parciais que crescem por acumulação.

### Download manual — decisão para as fases iniciais

Os arquivos são baixados manualmente da Casa dos Dados e colocados nas pastas correspondentes. Não há automação de download nesta fase — o foco é ter a plataforma funcionando e o histórico construído antes de automatizar qualquer coisa.

### Automação futura das atualizações mensais

A Casa dos Dados tem estrutura de diretório Apache padrão, o que torna a automação simples e confiável. No futuro, o script mensal vai:

1. Acessar `dados-abertos-rf-cnpj.casadosdados.com.br/arquivos/` e listar as pastas disponíveis
2. Consultar `tb_processamento_mensal` no banco para saber quais meses já foram processados
3. Identificar pastas novas ainda não processadas
4. Baixar apenas `Empresas0-9`, `Estabelecimentos0-9` e `Socios0-9` do mês novo
5. Processar com a lógica incremental, registrar na tabela de controle e deletar os ZIPs

Não será usado o site oficial da RF para automação — o layout da página muda com frequência e já quebrou scripts anteriores. A Casa dos Dados tem estrutura estável e é o alvo correto para automação.

---

## Estratégia de histórico e atualização incremental

### O problema

A RF não disponibiliza delta de alterações — ela publica a base inteira todo mês, como uma fotografia do estado atual de todos os CNPJs. Para saber o que mudou entre dois meses, é necessário comparar as duas fotografias.

### A solução adotada: campos de presença temporal

Em vez de criar tabelas separadas de histórico ou event logs complexos, a estratégia é adicionar campos de data diretamente nas tabelas principais para rastrear quando cada registro foi visto pela primeira e pela última vez.

**Na tabela `empresa`:** dois campos adicionais.
- `dt_primeira_carga` — mês/ano em que esse CNPJ básico apareceu pela primeira vez na base. Preenchido uma única vez na inserção, nunca atualizado. Formato `YYYY-MM`. Existe porque a tabela empresa não tem nenhuma data na base da RF.
- `dt_ultima_atualizacao` — mês/ano do snapshot mais recente. Atualizado a cada carga mensal.

**Na tabela `estabelecimento`:** um campo adicional.
- `dt_ultima_atualizacao` — mês/ano do snapshot mais recente. Não recebe `dt_primeira_carga` porque já tem `dt_datainicioatividade` fornecida pela RF com precisão de dia.

**Na tabela `socios`:** um campo adicional.
- `dt_ultima_atualizacao` — mês/ano do snapshot mais recente. Não recebe `dt_primeira_carga` porque já tem `dt_dataentradasociedade` fornecida pela RF com precisão de dia.

**Na tabela `simples`:** nenhum campo adicional. A RF já fornece todas as datas relevantes: opção e exclusão do Simples e do MEI.

### O que esses campos permitem responder

"Essa empresa existe desde quando na base?" → `dt_primeira_carga` da tabela empresa.

"Esse CNPJ ainda está ativo na base?" → Se `dt_ultima_atualizacao` é igual ao mês atual, sim. Se ficou para trás, saiu da base.

"Esse sócio ainda faz parte da empresa?" → Se `dt_ultima_atualizacao` do sócio é igual ao mês atual, sim. Se ficou para trás, saiu da sociedade.

"Quando esse sócio entrou?" → `dt_dataentradasociedade`, fornecida pela RF.

"Quando a situação cadastral mudou?" → `dt_datasituacaocadastral`, fornecida pela RF.

"A empresa está em recuperação judicial?" → `nm_situacaoespecial` do estabelecimento matriz, texto livre fornecido pela RF. A data de quando entrou está em `dt_datasituacaoespecial`.

### O que não será rastreado

Não haverá registro do valor anterior de um campo antes de uma alteração. Se uma empresa mudou de razão social, o sistema saberá o nome atual e desde quando o CNPJ está na base, mas não saberá o nome anterior. Essa limitação foi aceita conscientemente para manter a arquitetura simples.

### Chaves naturais — como o sistema identifica cada registro

A chave natural é o conjunto de campos que identifica unicamente um registro na base da RF. É ela que o script usa para decidir se um registro do novo snapshot é uma atualização de algo que já existe no banco ou uma inserção nova.

```
empresa
  chave: cd_cnpjbasico
  (8 dígitos — único por empresa em todo o Brasil)

estabelecimento
  chave: cd_cnpjbasico + cd_cnpjordem + cd_cnpjdv
  (os 14 dígitos completos do CNPJ — único por unidade física)

socios
  chave: cd_cnpjbasico + cd_cpfcnpjsocio + cd_qualificacaosocio
  (empresa + identificador do sócio + qualificação)
```

A chave de sócios inclui `cd_qualificacaosocio` intencionalmente. Isso significa que quando um sócio muda de qualificação — por exemplo de Sócio para Administrador — o sistema trata como saída do registro antigo e entrada de um registro novo, não como atualização. Essa decisão é deliberada e permite rastrear o histórico de qualificações de cada sócio ao longo do tempo, conforme explicado na seção de regras de negócio abaixo.

### Fluxo de processamento por mês

O processamento de cada mês segue sempre a mesma ordem e nunca toca nas tabelas principais antes de ter os dados temporários prontos.

```
PASSO 1 — Carregar snapshot novo em tabela temporária
  Lê os CSVs em chunks de 100.000 linhas (encoding latin-1, separador ;)
  Insere em tmp_empresa, tmp_estabelecimento, tmp_socios
  Não toca nas tabelas principais ainda

PASSO 2 — Identificar e processar cada caso pela chave natural

  CASO A: registro existe na tmp E existe no banco (mesma chave natural)
    → É o mesmo registro que continuou na base
    → Atualiza TODOS os campos com os valores novos do snapshot
    → Atualiza dt_ultima_atualizacao para o mês atual
    → dt_primeira_carga permanece intocado (só existe em empresa)

  CASO B: registro existe na tmp mas NÃO existe no banco
    → É um registro novo que entrou na base
    → Insere com todos os campos
    → dt_primeira_carga = mês atual (só em empresa)
    → dt_ultima_atualizacao = mês atual

  CASO C: registro existe no banco mas NÃO existe na tmp
    → Sumiu do snapshot — saiu da base da RF
    → Nenhuma ação — registro permanece no banco
    → dt_ultima_atualizacao fica no último mês em que foi visto
    → Nunca deletar registros do banco

PASSO 3 — Remover tabelas temporárias
  tmp_empresa, tmp_estabelecimento, tmp_socios são dropadas

PASSO 4 — Registrar na tabela de controle
  Insere linha em tb_processamento_mensal com mês, timestamp,
  contagens de inserções/atualizações por tabela e status CONCLUIDO
```

```
PRIMEIRO MÊS (março/2023) — caso especial:
  Não há banco para comparar — tudo é CASO B
  Todos os registros são inseridos como novos
  dt_primeira_carga = '2023-03' (só em empresa)
  dt_ultima_atualizacao = '2023-03'
  Índices criados ao final da carga (nunca durante a inserção)
```

**Checkpoint por tabela na primeira carga (melhoria planejada):**

A primeira carga carrega ~140 milhões de linhas e pode levar 10+ horas. Se interrompida, o mês inteiro é descartado e reprocessado do zero. A melhoria planejada é salvar um checkpoint após cada tabela concluída:

1. Carrega `tmp_empresa` → `INSERT OR IGNORE INTO empresa` → registra checkpoint `empresa_ok` → dropa `tmp_empresa`
2. Carrega `tmp_estabelecimento` → `INSERT OR IGNORE INTO estabelecimento` → registra checkpoint `estabelecimento_ok` → dropa `tmp_estabelecimento`
3. Carrega `tmp_socios` → `INSERT OR IGNORE INTO socio` → registra checkpoint `socios_ok` → dropa `tmp_socios`
4. Cria índices → marca mês como `CONCLUIDO`

Se interrompida após empresa e estabelecimento já concluídos, na próxima execução o script detecta os checkpoints e pula direto para os sócios. Isso evita refazer 6-8 horas de trabalho por causa de uma interrupção no final do processo.

Registros que saem da base nunca são deletados. Ficam com `dt_ultima_atualizacao` no último mês em que foram vistos — essa data é a evidência de quando saíram.

### Tabela de controle de processamento

```
tb_processamento_mensal
  dt_referencia     → mês processado (ex: '2026-05')
  dt_processado     → timestamp de quando o script rodou
  qtd_inseridos_empresa
  qtd_atualizados_empresa
  qtd_inseridos_estabelecimento
  qtd_atualizados_estabelecimento
  qtd_inseridos_socios
  qtd_atualizados_socios
  status            → 'CONCLUIDO' ou 'ERRO'
```

Antes de processar qualquer mês, o script consulta essa tabela. Se o mês já constar como CONCLUIDO, o script pula — evita reprocessamento acidental. Se constar como ERRO, o script limpa as tabelas temporárias e reprocessa do zero para aquele mês.

### Regras de negócio — histórico de qualificações de sócios

Como a chave natural de sócios inclui `cd_qualificacaosocio`, uma mudança de qualificação gera dois registros distintos no banco: o registro antigo com a qualificação anterior fica com `dt_ultima_atualizacao` no último mês em que foi visto, e o registro novo com a qualificação atual é inserido com `dt_primeira_carga` no mês da mudança.

Exemplo — João Silva muda de Sócio para Administrador em maio/2026:

```
BANCO APÓS PROCESSAR MAIO/2026

socios
┌───────────┬─────────────┬────────────────────┬───────────────┬──────────────────────┐
│ cnpjbasico│ cpfcnpjsocio│ cd_qualificacaosocio│ dt_prim_carga │ dt_ultima_atualizacao│
├───────────┼─────────────┼────────────────────┼───────────────┼──────────────────────┤
│ 12345678  │ ***456789** │ 49 - Sócio         │ 2023-03       │ 2026-04              │
│ 12345678  │ ***456789** │ 05 - Administrador │ 2026-05       │ 2026-05              │
└───────────┴─────────────┴────────────────────┴───────────────┴──────────────────────┘
```

A API, ao montar o card de uma empresa, busca todos os registros de sócios pelo `cd_cnpjbasico` e agrupa por `cd_cpfcnpjsocio`. Para cada pessoa, ordena os registros por `dt_ultima_atualizacao` e monta a linha do tempo:

```
João Silva
  Qualificação atual:  Administrador (desde mai/2026)
  Qualificação anterior: Sócio (mar/2023 → abr/2026)
  Ainda na sociedade: sim (dt_ultima_atualizacao = mês atual)
```

Se o sócio tiver saído da empresa completamente — não aparece mais no snapshot com nenhuma qualificação — todos os seus registros ficam com `dt_ultima_atualizacao` desatualizada e a interface exibe:

```
João Silva
  Sócio até abr/2026 (saiu da base)
```

Essa lógica funciona para qualquer número de mudanças de qualificação ao longo do tempo — cada mudança gera um par de registros (saída do antigo, entrada do novo) que juntos contam a história completa da participação daquela pessoa na empresa.

Registros que saem da base nunca são deletados das tabelas principais. Eles ficam com `dt_ultima_atualizacao` no último mês em que foram vistos, o que é a informação histórica disponível.

### Primeira carga — base de abril/2026

A primeira carga não tem histórico anterior para comparar. Todos os registros recebem `dt_primeira_carga = '2026-04'` e `dt_ultima_atualizacao = '2026-04'`. A partir da segunda carga (maio/2026 ou quando a próxima base for baixada), o processo incremental descrito acima entra em funcionamento.

Haverá também uma tabela de controle de processamento com os campos: mês de referência, data e hora de execução, quantidades de inserções e atualizações por tabela, e status da execução. Essa tabela serve para saber quais meses já foram processados e evitar reprocessamento acidental.

---

## Stack tecnológica

Tudo baseado no que foi apresentado nas aulas da disciplina.

**Backend:** FastAPI com Python. Escolhido pela produtividade com type hints, validação automática via Pydantic, documentação Swagger gerada automaticamente e deploy fácil no Azure App Service.

**Banco de dados:** SQLite para desenvolvimento local e Azure SQL Database para produção. A troca entre os dois é feita automaticamente por variável de ambiente — o mesmo código funciona nos dois ambientes. ORM SQLAlchemy com migrations via Alembic.

**Frontend:** React com Vite. Comunicação com o backend via `fetch`. Deploy no Azure Static Web Apps (gratuito, com HTTPS e CDN automáticos, integrado ao GitHub).

**Infraestrutura:** Azure App Service para o backend (PaaS — sem gerenciar servidor), Azure SQL Database (DBaaS — backup automático, escala gerenciada), Azure Static Web Apps para o frontend. Variáveis de ambiente e secrets nunca ficam no código.

---

## Metodologia de desenvolvimento

O projeto segue desenvolvimento ágil incremental. Cada fase é um incremento funcional — ao final de cada uma, existe algo que funciona e pode ser demonstrado. As fases não são sprints fixos com datas, mas sim marcos de funcionalidade.

A ordem de desenvolvimento dentro de cada fase respeita a dependência técnica: banco de dados antes de API, API antes de frontend.

---

## Fase 1 — Plataforma funcionando com a base de abril/2026

**Objetivo:** fazer a plataforma funcionar de ponta a ponta com dados reais da Receita Federal, rodando na máquina local. Esta é a primeira entrega — foco total em consulta funcionando, sem nenhuma lógica de histórico ou incremental.

### Carga inicial

Os arquivos ZIP de abril/2026 são baixados manualmente do portal `dados.gov.br` e colocados em uma pasta local. Um script Python simples lê essa pasta, descompacta os CSVs e insere os dados no banco SQLite em blocos de 100.000 linhas para não estourar memória. Os CSVs da RF não têm cabeçalho — as colunas devem ser nomeadas manualmente no script seguindo o layout oficial (`cnpj-metadados.pdf`). A leitura usa `pandas.read_csv()` com `chunksize=100000`, `encoding='latin-1'` e `sep=';'`. Índices são criados ao final da carga, nunca durante.

Os campos de data adicionados (`dt_primeira_carga` e `dt_ultima_atualizacao`) já existem nos models desde o início para não exigir migration futura, mas na Fase 1 são apenas preenchidos com `'2026-04'` para todos os registros sem nenhuma lógica de comparação. Não há tabela temporária, não há diff, não há processamento incremental — é uma carga direta e única.

### O que será construído

**Models SQLAlchemy:** uma classe Python para cada tabela da base, mapeando fielmente o schema da RF. As tabelas `empresa`, `estabelecimento` e `socios` já incluem os campos de data adicionais desde o início. O SQLAlchemy cria as tabelas automaticamente na primeira execução. As migrations com Alembic versionam qualquer mudança de schema futura.

**API FastAPI:** organizada em routers separados por domínio (empresa e sócio). Schemas Pydantic de resposta separados dos models do banco. Endpoints usam `async def`. CORS configurado desde o início.

**Endpoints da Fase 1:**

`GET /health` — health check obrigatório. Retorna status e timestamp.

`GET /api/v1/empresa/{cnpj}` — recebe CNPJ com 14 dígitos com ou sem formatação. Retorna dados completos: dados da empresa, endereço do estabelecimento, CNAE traduzido para descrição, lista de sócios com qualificação e situação no Simples. O backend monta a resposta juntando empresa + estabelecimento + socios + simples + tabelas de domínio em uma única chamada no `crud.py`.

`GET /api/v1/empresa/busca?nome={termo}&skip=0&limit=20` — busca por razão social ou nome fantasia com busca parcial case-insensitive, retorna lista paginada com total de resultados.

`GET /api/v1/socio/busca?cpf={cpf}&skip=0&limit=20` — busca pelos dígitos visíveis do CPF. A interface deixa claro que o CPF é parcial e pode retornar mais de uma pessoa.

`GET /api/v1/socio/busca?nome={nome}&skip=0&limit=20` — busca por nome de sócio com busca parcial, paginada.

**Frontend React:** uma única página com campo de busca inteligente que detecta o tipo de entrada automaticamente. 14 caracteres alfanuméricos → CNPJ. Somente dígitos entre 6 e 11 caracteres → CPF. Qualquer outra coisa → busca por nome. Resultado exibido em cards. Um arquivo `api.js` centraliza todos os `fetch`.

### Critérios para considerar a Fase 1 concluída

Digitar um CNPJ real e ver os dados completos. Buscar uma empresa pelo nome e receber uma lista paginada. Buscar um sócio pelo CPF e ver todas as empresas em que aparece. Tudo rodando com a base de abril/2026 no SQLite local, sem erros.

---

## Fase 2 — Deploy no Azure (entrega acadêmica)

**Objetivo:** subir tudo para o Azure para a entrega do projeto na faculdade, sem mudar nenhuma linha de código — apenas configuração.

O banco SQLite é substituído pelo Azure SQL Database. A connection string vai numa variável de ambiente do App Service — o `os.getenv()` no `database.py` já está preparado para isso desde a Fase 1. As migrations do Alembic são rodadas uma vez contra o banco do Azure. O frontend vai para o Azure Static Web Apps com deploy automático via GitHub a cada push na branch main. O `VITE_API_URL` no `.env.production` aponta para a URL real do App Service. O CORS é atualizado para aceitar apenas o domínio real do frontend — nunca `*` em produção.

Os dados são carregados no Azure SQL rodando o mesmo script de carga com a `DATABASE_URL` apontando para o Azure — os mesmos ZIPs locais são usados, não é necessário baixar nada de novo.

### Critérios para considerar a Fase 2 concluída

Qualquer pessoa com o link consegue fazer uma consulta. Os dados persistem entre restarts. O frontend tem HTTPS e está acessível publicamente.

---

## Fase 3 — Histórico incremental completo

**Objetivo:** processar todos os meses disponíveis desde março/2023 até o mês atual, construindo o histórico real de entradas e saídas de empresas, estabelecimentos e sócios.

O histórico será construído **antes** da Fase 1 entrar em produção — a decisão foi fazer o histórico completo desde o início, não retroativamente. O processo é: baixar mês a mês da Casa dos Dados ou da RF, processar com a lógica incremental descrita acima (março/2023 como primeira carga, meses seguintes como upsert), e deletar os ZIPs após processar cada mês para não acumular espaço em disco.

Ao final, o campo `dt_primeira_carga` de cada empresa refletirá o mês real em que apareceu pela primeira vez na base pública, e `dt_ultima_atualizacao` de todos os registros refletirá o último mês em que foram vistos.

A partir daqui a plataforma processa as novas bases mensais conforme a RF publica, mantendo os dados atualizados e o histórico crescendo mês a mês.

**Arquivos necessários por mês:** apenas `Empresas0-9`, `Estabelecimentos0-9` e `Socios0-9`. `Simples` e as tabelas de domínio são carregadas apenas uma vez da versão mais recente.

**Espaço mínimo necessário em disco:** ~120 GB livres (banco ~100 GB + espaço para processar um mês por vez).

---

## Performance e busca — decisões técnicas

### SQLite em desenvolvimento — otimizações aplicadas

O SQLite não foi projetado para bancos de 37+ GB com múltiplas tabelas de dezenas de milhões de linhas. Para torná-lo viável durante o desenvolvimento, as seguintes otimizações foram aplicadas:

**Pragmas de conexão** (aplicados automaticamente via event listener do SQLAlchemy em `database.py`):
```
PRAGMA journal_mode=WAL         — leituras concorrentes sem bloquear escritas
PRAGMA cache_size=-524288       — 512 MB de cache de páginas em memória
PRAGMA mmap_size=10737418240    — 10 GB de memória virtual mapeada para o arquivo
PRAGMA synchronous=NORMAL       — reduz fsync sem comprometer integridade
PRAGMA temp_store=MEMORY        — operações temporárias (sorts, joins) em RAM
```

**Cache em memória das tabelas de lookup**: as tabelas `qualificacao`, `cnae`, `municipio`, `natureza` e `motivo` são carregadas inteiras para dicionários Python na primeira requisição e reutilizadas indefinidamente. Isso elimina dezenas de queries por requisição — um detalhe por empresa envolvia 10-15 queries em tabelas pequenas que passaram a ser 0.

**Eliminação de N+1 queries**: o código original fazia uma query separada para cada CNAE secundário e para cada qualificação de sócio. O `crud.py` foi reescrito para resolver todos esses lookups via dicionário em memória, sem tocar no banco.

**Cache de `mes_atual`**: a data do mês mais recente processado (usada para determinar se um sócio está ativo) era consultada a cada requisição. Agora é cacheada em memória e atualizada apenas quando muda.

### Busca por texto — por que LIKE '%termo%' não usa índice

Índices B-tree só ajudam quando o padrão começa com caracteres fixos (`LIKE 'petro%'`). Com wildcard à esquerda (`LIKE '%petro%'`), o banco não tem como saber em qual parte do índice procurar — é sempre full table scan.

Com 67 milhões de empresas e 30 milhões de sócios, isso resulta em queries de minutos.

### Solução SQLite: FTS5 com tokenizador trigram

O SQLite tem um motor de busca de texto embutido (FTS5) que, com o tokenizador `trigram`, divide cada palavra em sequências de 3 caracteres e indexa todas elas:

```
"PETROBRAS" → "PET", "ETR", "TRO", "ROB", "OBR", "BRA", "RAS"
```

Uma busca por "PETRO" encontra os trigrams "PET", "ETR", "TRO" no índice invertido e localiza todas as linhas que os contêm — sem ler linha por linha. Resultado em menos de 1 segundo para qualquer substring.

O script `criar_indices.py` cria as tabelas virtuais FTS5 (`fts_empresa` e `fts_socio`) com os dados de nome de empresa e nome de sócio. **Este script precisa ser rodado uma vez após a carga e demora 30-60 minutos** devido ao volume de dados. Enquanto não existirem as tabelas FTS5, o sistema usa LIKE como fallback (lento).

Custo: ~20-30 GB adicionais em disco para armazenar o índice invertido.

### Solução PostgreSQL: ILIKE com GIN pg_trgm

O PostgreSQL tem o equivalente nativo do trigram via a extensão `pg_trgm`. Ao contrário do SQLite (que exige uma tabela virtual separada), no PostgreSQL basta criar um índice GIN na coluna original:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_empresa_razao_trgm ON empresa USING GIN(nm_razaosocial gin_trgm_ops);
```

Depois disso, uma query normal com `ILIKE '%petro%'` usa o índice automaticamente. Sem tabela extra, sem manutenção adicional, sem script separado.

**Comparação:**

| | SQLite + FTS5 | PostgreSQL + pg_trgm |
|---|---|---|
| Busca por substring | `FTS5 MATCH 'termo'` | `campo ILIKE '%termo%'` |
| Tabela extra | sim (fts_empresa, fts_socio) | não |
| Disco adicional | ~20-30 GB | ~5-10 GB |
| Tempo de criação | 30-60 min | 5-15 min |
| Velocidade de busca | < 1 segundo | < 200 ms |

### Detecção automática do banco no código

`database.py` expõe a função `is_postgres()`. O `crud.py` usa essa função para escolher automaticamente a estratégia de busca correta:

```
PostgreSQL → ILIKE (usa GIN pg_trgm automaticamente)
SQLite com FTS5 → FTS5 MATCH (rápido)
SQLite sem FTS5 → LIKE fallback (lento, temporário)
```

A troca entre SQLite e PostgreSQL é feita apenas mudando `DATABASE_URL` no `.env` — nenhum outro arquivo precisa ser alterado.

---

## Fase 4 — Migração para produção real (PostgreSQL da empresa)

**Objetivo:** migrar o projeto do Azure para a infraestrutura definitiva da empresa, usando o banco PostgreSQL corporativo.

### Estratégia de migração — copiar do SQLite, não reprocessar os ZIPs

**Decisão técnica:** quando chegar a hora de popular o banco PostgreSQL de produção, **não** se deve rodar o `carga.py` novamente apontando para o PostgreSQL. Reprocessar 38 meses de ZIPs levaria as mesmas 40-80 horas do processo de desenvolvimento.

A abordagem correta é **migrar os dados diretamente do SQLite já populado para o PostgreSQL**, tabela por tabela. Isso reduz o tempo de migração de dias para algumas horas.

O script de migração vai:
1. Conectar simultaneamente no SQLite local e no PostgreSQL de produção
2. Ler cada tabela do SQLite em chunks de 100.000 linhas
3. Inserir no PostgreSQL com `ON CONFLICT DO NOTHING`
4. Registrar o progresso por tabela para poder retomar se interrompido

Os ZIPs em `dados-brutos/` continuam sendo a fonte de verdade — se o PostgreSQL precisar ser recriado do zero, basta rodar o `carga.py` apontando para ele. Mas para a migração inicial, copiar do SQLite é sempre a escolha certa.

### Passos completos no dia da migração

```
1. Alterar DATABASE_URL no .env para o PostgreSQL de produção
2. Rodar: py -3.12 migrar_para_postgres.py
   → Cria tabelas, ativa pg_trgm, cria índices GIN e B-tree
3. Migrar dados do SQLite ou re-rodar o carga.py
4. Subir uvicorn — o sistema detecta PostgreSQL automaticamente e usa ILIKE
5. Sem nenhuma outra mudança de código
```

### Compatibilidades do código já garantidas

- `ILIKE` no lugar de `LOWER(...) LIKE` — já implementado via `is_postgres()`
- `INSERT OR IGNORE` → `INSERT ... ON CONFLICT DO NOTHING` — tratado no `carga.py`
- `autoincrement=True` → `SERIAL`/`BIGSERIAL` — mapeamento automático do SQLAlchemy
- Todas as queries usam `text()` parametrizado — sem SQL hardcoded para SQLite

PostgreSQL é o banco definitivo para esse volume — lida bem com 100+ milhões de linhas, busca com `pg_trgm` é nativa e rápida, e é amplamente suportado em ambientes corporativos.

### Critérios para considerar a Fase 4 concluída

O projeto está rodando na infraestrutura da empresa com dados completos e busca por nome em menos de 200ms. O Azure pode ser mantido como staging ou descomissionado.

---

## Fase 5 — Enriquecimento e funcionalidades extras

Esta fase é definida à medida que as anteriores ficam prontas. Algumas direções possíveis:

**ETL automatizado:** script que acessa o portal da RF, identifica a base mais recente e faz o download e processamento sem intervenção manual. Integrado ao processo incremental para rodar mensalmente. Esta é a automação do processo que nas fases anteriores é feito manualmente.

**Grafo de relacionamentos:** dado um CNPJ ou CPF, mostrar visualmente as conexões entre a pessoa e as empresas em que participa, e entre essas empresas e seus outros sócios. Requer uma tabela de vínculos dedicada para performance.

**Exportação:** botão para baixar o resultado de uma consulta em CSV ou JSON.

**API pública com autenticação:** rate limiting e autenticação via token. Secrets gerenciados pelo Azure Key Vault.

**Monitoramento:** Azure Application Insights para logs e métricas.

---

## Requisitos funcionais

RF01 — O sistema deve permitir buscar uma empresa pelo CNPJ completo e retornar todos os seus dados cadastrais, endereço, CNAE, sócios e situação no Simples Nacional.

RF02 — O sistema deve permitir buscar empresas por nome com busca parcial e retornar lista paginada.

RF03 — O sistema deve permitir buscar sócios por CPF (dígitos visíveis) e retornar todas as empresas em que a pessoa aparece.

RF04 — O sistema deve permitir buscar sócios por nome com busca parcial.

RF05 — O sistema deve indicar claramente quando um CNPJ não é encontrado na base.

RF06 — O sistema deve exibir estado de carregamento enquanto a consulta está em andamento.

RF07 — O sistema deve exibir, na consulta de empresa, desde quando ela está presente na base da RF e quando foi vista pela última vez.

RF08 — O sistema deve exibir, na consulta de sócio, se ele ainda aparece na base atual ou se saiu em alguma atualização anterior.

---

## Requisitos não funcionais

RNF01 — O endpoint de consulta por CNPJ deve responder em menos de 2 segundos para 95% das requisições, após a criação dos índices.

RNF02 — Nenhuma credencial pode estar no código ou no repositório Git.

RNF03 — O mesmo código deve funcionar em ambiente local (SQLite) e em produção (Azure SQL) apenas trocando variáveis de ambiente.

RNF04 — O frontend deve ser responsivo e funcionar em dispositivos móveis.

RNF05 — A API deve ter documentação automática acessível em `/docs`.

RNF06 — Todos os campos de CNPJ devem ser armazenados como string, nunca como inteiro, para suportar o novo formato alfanumérico que entra em vigor em julho de 2026.

---

## User stories da Fase 1

**US01** — "Como analista, quero digitar um CNPJ e ver instantaneamente todos os dados cadastrais da empresa, para não precisar acessar o site da Receita Federal manualmente."

Critérios de aceitação: dado que o CNPJ está na base local, quando o usuário digita o CNPJ e pressiona buscar, então a página exibe razão social, situação cadastral, endereço, CNAE principal, lista de sócios e situação no Simples em menos de 2 segundos.

**US02** — "Como jornalista, quero buscar um CPF e ver em quais empresas aquela pessoa é sócia, para investigar vínculos societários."

Critérios de aceitação: dado que os dígitos visíveis do CPF constam na base, quando o usuário informa o CPF na busca, então a página lista todas as empresas em que aquele CPF aparece como sócio, com nome, qualificação e data de entrada. A interface exibe aviso de que o CPF é parcial e pode retornar mais de uma pessoa.

**US03** — "Como desenvolvedor, quero que a busca por nome retorne resultados parciais paginados, para não travar a interface com milhares de resultados de uma vez."

Critérios de aceitação: dado que o usuário digita um termo de busca por nome, quando a busca é executada, então a API retorna no máximo 20 resultados por página com informação do total encontrado, e o frontend exibe controles de navegação entre páginas.

---

## Decisões do site 1.0 — o que o sistema entrega hoje

### Consulta de empresa (por CNPJ)

O endpoint `GET /api/v1/empresa/{cnpj}` retorna um objeto único montado pelo `crud.py` juntando cinco tabelas (empresa, estabelecimento, simples, e lookups em memória). Todas as decodificações de código são feitas no backend — o frontend recebe apenas strings legíveis.

**Sócios** são retornados em dois grupos separados:
- `socios_ativos` — sócios cujo `dt_ultima_atualizacao` bate com o mês mais recente processado
- `socios_inativos` — sócios que apareceram na base em algum mês anterior mas não no mais recente (saíram da empresa)

Dentro de cada sócio, as qualificações são organizadas em:
- `qualificacao_atual` — o registro com `dt_ultima_atualizacao = mes_atual`
- `qualificacoes_anteriores` — registros anteriores ordenados por data, cada um com `saiu_em` indicando o último mês em que aquela qualificação foi vista

O frontend exibe os sócios ativos diretamente e os inativos em seção colapsável "Ex-Sócios". Cada sócio tem botão para expandir o histórico de qualificações.

**CNAE secundário** era armazenado como string de códigos separados por vírgula. O backend quebra essa string, consulta cada código no cache de CNAE em memória e retorna um array de objetos `{codigo, descricao}`. O frontend exibe na tabela de atividade econômica.

**Códigos decodificados no backend** (nunca chegam como número ao frontend):
- `cd_situacaocadastral` → "Ativa", "Baixada", "Suspensa", "Inapta", "Nula"
- `cd_porteempresa` → "Micro Empresa", "EPP", "Demais", "Não informado"
- `cd_identificadormatrizfilial` → "Matriz", "Filial"
- `cd_naturezajuridica` → descrição completa (via cache da tabela natureza)
- `cd_motivosituacaocadastral` → descrição completa (via cache da tabela motivo)
- `cd_cnaefiscalprincipal` e secundários → descrição completa (via cache da tabela cnae)
- `cd_municipio` → nome do município (via cache da tabela municipio)
- `cd_qualificacaosocio` → descrição da qualificação (via cache da tabela qualificacao)
- `cd_faixaetaria` → "21 a 30 anos", "31 a 40 anos", etc.
- `cd_identificadorsocio` → "Pessoa Física", "Pessoa Jurídica", "Estrangeiro"

**Campos não decodificados no backend** (tratados diretamente no frontend):
- `fl_opcaosimples` e `fl_opcaomei` chegam como "S", "N" ou null — o frontend trata com comparação direta

### Consulta de sócio (por nome ou CPF)

O endpoint retorna uma lista flat de registros `SocioListItem` — um por linha na tabela socio. O frontend (`ResultadoSocio.jsx`) agrupa esses registros por `cnpj_basico` para montar uma visão por empresa.

Para cada empresa, o agrupamento determina:
- Se o vínculo é ativo: qualquer registro do grupo com `is_ativo = true`
- Qualificação atual: o registro com `is_ativo = true`
- Qualificações anteriores: os registros com `is_ativo = false`, ordenados por `dt_ultima`

O frontend exibe dois painéis: "Vínculos Ativos" e "Ex-Vínculos" (colapsável). Cada empresa tem botão para expandir histórico de qualificações e botão para navegar para o detalhe da empresa.

### Por que o sistema antigo (Django + PostgreSQL) era rápido

O sistema anterior da empresa consultava PostgreSQL com match exato em nome + CPF simultaneamente — um índice B-tree normal resolve isso em milissegundos. O novo sistema faz busca por substring parcial em 30-67 milhões de linhas, que é um problema fundamentalmente diferente e mais difícil. A velocidade do sistema antigo vinha do PostgreSQL e do tipo de busca, não de nenhuma técnica especial. Com a migração para PostgreSQL e índices GIN pg_trgm, o novo sistema supera o anterior.

---

## Decisões técnicas para o Claude Code

**Primeira tarefa obrigatória — criar a estrutura de pastas de dados.** Antes de qualquer código, o Claude Code deve criar a pasta `dados-brutos/` com todas as subpastas de meses de março/2023 até abril/2026. O usuário vai baixar manualmente os arquivos da Casa dos Dados (`https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos/`) e soltar em cada pasta correspondente. As pastas devem seguir o padrão `YYYY-MM` (ex: `2023-03`, `2023-04`). Dentro de cada pasta o usuário colocará os ZIPs de `Empresas0-9`, `Estabelecimentos0-9` e `Socios0-9`. Na pasta `2026-04` especificamente também vão `Simples.zip`, `Cnaes.zip`, `Motivos.zip`, `Municipios.zip`, `Naturezas.zip`, `Paises.zip` e `Qualificacoes.zip`. Criar um `README_DADOS.txt` dentro de `dados-brutos/` explicando o que colocar em cada pasta.

```
dados-brutos/
  README_DADOS.txt
  2023-03/   2023-04/   2023-05/   2023-06/
  2023-07/   2023-08/   2023-09/   2023-10/
  2023-11/   2023-12/   2024-01/   2024-02/
  2024-03/   2024-04/   2024-05/   2024-06/
  2024-07/   2024-08/   2024-09/   2024-10/
  2024-11/   2024-12/   2025-01/   2025-02/
  2025-03/   2025-04/   2025-05/   2025-06/
  2025-07/   2025-08/   2025-09/   2025-10/
  2025-11/   2025-12/   2026-01/   2026-02/
  2026-03/   2026-04/
```

**ETL em chunks obrigatório.** Os CSVs da RF não têm cabeçalho. As colunas devem ser nomeadas manualmente no script seguindo o layout oficial (`cnpj-metadados.pdf`). Leitura com `pandas.read_csv()`, `chunksize=100000`, `encoding='latin-1'`, `sep=';'`.

**Índices são críticos e devem ser criados após a carga.** Campos obrigatórios: `cd_cnpjbasico` em todas as tabelas principais, `nm_razaosocial`, `nm_nomefantasia`, `cd_cpfcnpjsocio`, `nm_nomesociorazaosocial`. Criar durante a inserção degrada muito a performance — sempre criar no final.

**CNPJ é sempre string.** Todos os campos de código da base (CNPJ básico, ordem, DV, CPF de sócio, códigos de domínio) devem ser armazenados como string. Zeros à esquerda são significativos. O novo formato alfanumérico de julho/2026 reforça essa obrigatoriedade.

**Campos de data adicionados às tabelas principais.** `empresa` recebe `dt_primeira_carga` (String, formato `YYYY-MM`, preenchido uma vez na inserção) e `dt_ultima_atualizacao` (String, formato `YYYY-MM`, atualizado a cada carga). `estabelecimento` e `socios` recebem apenas `dt_ultima_atualizacao`. A tabela `simples` não recebe campos adicionais pois a RF já fornece todas as datas necessárias.

**Busca por nome case-insensitive.** No SQLite: `LOWER(campo) LIKE LOWER('%termo%')`. No Azure SQL: depende do collation. O `crud.py` deve abstrair isso detectando o banco pela connection string.

**Paginação obrigatória em todas as buscas por nome e por sócio.** Parâmetros `skip` e `limit` em todos os endpoints de listagem. Sem paginação, uma busca por "SILVA" retorna milhões de registros.

**Schemas Pydantic separados dos models SQLAlchemy.** O `response_model` da API nunca é o model do banco. O `crud.py` faz os joins e monta um dicionário que o schema Pydantic valida antes de retornar ao cliente.

**Health check obrigatório.** O endpoint `GET /health` deve existir desde o primeiro commit. O Azure App Service depende dele para monitoramento e auto-restart.

**Variáveis de ambiente para tudo sensível.** `DATABASE_URL` e `ALLOWED_ORIGINS` ficam no `.env` local (no `.gitignore`) e no App Settings do Azure em produção. O `python-dotenv` carrega o `.env` localmente.

**Separação absoluta entre frontend e backend.** O frontend nunca acessa o banco. Toda lógica de join, formatação de CNPJ, decodificação de códigos e regras de negócio ficam no backend. O arquivo `api.js` centraliza todos os `fetch` — nenhum componente React faz fetch diretamente.

---

## Implementações e decisões da sessão atual

### Cache no startup — não na primeira requisição

O cache de qualificações, CNAEs, municípios, naturezas, motivos e o mês atual eram carregados na primeira requisição que precisasse deles, causando 2–3 s de latência na primeira chamada. Isso foi corrigido usando o `lifespan` do FastAPI para carregar tudo no startup do servidor:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        crud._load_cache(db)
        crud._get_mes_atual(db)
    finally:
        db.close()
    yield

app = FastAPI(title="Busca CNPJ", version="1.0.0", lifespan=lifespan)
```

Resultado: tempo de resposta uniforme desde a primeira consulta — requisito não-funcional de consistência.

### FTS5 — busca com hierarquia de relevância (tiered ranking)

A busca por nome retornava resultados em ordem BM25 pura, o que nem sempre colocava a empresa mais provável no topo. Solução: um `CASE` dentro de um CTE FTS5 que classifica os resultados em tiers antes de ordenar pelo rank BM25:

| Tier | Condição | Exemplo |
|------|----------|---------|
| 0 | Nome exato (case-insensitive) | busca "PETROBRAS" → "PETROBRAS" |
| 1 | Começa com a palavra exata + espaço | busca "PETRO" → "PETRO MINERACAO LTDA" |
| 2 | Começa com o prefixo | busca "PETRO" → "PETROBRAS SA" |
| 3 | Contém em qualquer posição | busca "PETRO" → "DISTRIBUIDORA PETRO LTDA" |

O padrão CTE é necessário porque FTS5 não permite usar alias de tabela junto com `MATCH` e `rank` na mesma query — usar `FROM fts_empresa f WHERE f MATCH ...` falha. A solução é referenciar a tabela FTS5 diretamente dentro do CTE e fazer os joins externamente:

```sql
WITH fts AS (
    SELECT cd_cnpjbasico, nm_razaosocial,
           CASE
               WHEN upper(nm_razaosocial) = upper(:nome)            THEN 0
               WHEN upper(nm_razaosocial) LIKE upper(:nome) || ' %' THEN 1
               WHEN upper(nm_razaosocial) LIKE upper(:nome) || '%'  THEN 2
               ELSE 3
           END AS tier
    FROM fts_empresa WHERE fts_empresa MATCH :match
    ORDER BY tier, rank LIMIT :limit OFFSET :skip
)
SELECT ... FROM fts JOIN empresa e ON fts.cd_cnpjbasico = e.cd_cnpjbasico ...
```

O mesmo padrão se aplica ao `fts_socio`.

### Hierarquia de qualificações de sócios (QUALIFICACAO_RANK)

Dicionário em `crud.py` que mapeia código RF → prioridade (menor = mais importante). Usado para duas finalidades:

1. **Ordenação do quadro societário** — Presidente aparece antes de Sócio Participante
2. **Desempate dentro do mesmo mês** — quando uma pessoa tem dois registros com o mesmo `dt_ultimaatualizacao`, o registro de maior hierarquia (menor rank) é tratado como `qualificacao_atual`

```python
QUALIFICACAO_RANK: dict[str, int] = {
    "16": 1,   # Presidente
    "10": 2,   # Diretor
    "05": 3,   # Administrador
    "22": 4,   # Sócio-Administrador
    "08": 5,   # Conselheiro de Administração
    "26": 6,   # Sócio-Gerente
    "29": 7,   # Sócio Ostensivo
    "49": 8,   # Sócio-Ostensivo (variante)
    "24": 9,   # Sócio Comanditado
    "30": 10,  # Sócio-Titular EIRELI
    "31": 11,  # Responsável
    "20": 12,  # Sócio
    ...
}
```

### _agrupar_socios — lógica completa de agrupamento e histórico

Agrupa registros da tabela `socio` por `(cd_cpfcnpjsocio, nm_nomesociorazaosocial)`. Para cada pessoa:

**1. Ordenação dos registros:**
```python
registros_ord = sorted(
    registros,
    key=lambda r: (r.dt_ultimaatualizacao or "", -QUALIFICACAO_RANK.get(r.cd_qualificacaosocio, 99)),
    reverse=True,
)
```
Mês mais recente primeiro; dentro do mesmo mês, cargo de maior hierarquia primeiro (negativo + reverse).

**2. Determina se está ativo:**
```python
ativo = any(r.dt_ultimaatualizacao == mes_atual for r in registros_ord)
```

**3. Inferência de data de início de cada cargo:**

A RF não publica data de início de qualificação. Só publica `dt_dataentradasociedade` (entrada na empresa) e `dt_ultimaatualizacao` (último mês que apareceu). A inferência segue três regras:

| Situação | Regra | Resultado |
|----------|-------|-----------|
| Cargo mais antigo (índice `n-1`) | Data real de entrada na empresa da RF | `"dd/mm/aaaa"` |
| Meses **diferentes** entre registros consecutivos | Primeiro mês após o fim do cargo anterior | `_next_month(prev_ultima)` |
| **Mesmo mês** entre registros consecutivos | Troca ocorreu dentro do mesmo ciclo mensal | `_fmt_mes(curr_ultima)` (mesmo mês) |
| `dt_ultimaatualizacao` ausente | Não inferível | `None` |

**Por que `_next_month` para meses diferentes:** Se a RF publicou "Administrador" pela última vez em nov/2023 e "Sócio-Adm" a partir de dez/2023, o cargo novo começou em dez/2023. Usar nov seria contraditório — o RF ainda publicava o cargo antigo naquele mês.

**Por que o próprio mês quando coincide:** Se dois registros têm o mesmo `dt_ultimaatualizacao`, a troca de cargo e a saída (ou manutenção) ocorreram dentro do mesmo ciclo mensal. Usar `_next_month` criaria uma data de início posterior à data de saída — contradição impossível. Usar o próprio mês é a representação correta.

Código do loop de inferência:
```python
start_dates = [None] * n
start_dates[n - 1] = _fmt_date(registros_ord[n - 1].dt_dataentradasociedade)
for i in range(n - 2, -1, -1):
    prev_ultima = registros_ord[i + 1].dt_ultimaatualizacao
    curr_ultima = registros_ord[i].dt_ultimaatualizacao
    if not prev_ultima:
        pass  # fica None
    elif prev_ultima == curr_ultima:
        start_dates[i] = _fmt_mes(curr_ultima)
    else:
        start_dates[i] = _next_month(prev_ultima)
```

**4. Montagem de qualificacao_atual e qualificacoes_anteriores:**
- Primeiro registro após ordenação → `qualificacao_atual` (independente de ser ativo ou inativo)
- Demais → `qualificacoes_anteriores`
- `saiu_em`: `None` se `is_current`, caso contrário `_fmt_mes(dt_ultimaatualizacao)`

### Situação cadastral — labels do quadro societário

A distinção ativo/inativo usa sempre `mes_atual` como referência independentemente da situação cadastral da empresa. Apenas os **labels** mudam:

| Situação | Label "ativos" | Label seção inativos |
|----------|----------------|----------------------|
| Ativa, Suspensa, Inapta | Sócios Ativos | Ex-Sócios |
| **Baixada, Nula** | **Sócios até o Fechamento** | Ex-Sócios |

**Por que Suspensa/Inapta seguem a lógica de Ativa:** essas situações significam que a empresa ainda existe — apenas com restrições (pendências fiscais, falta de declarações). Ela continua tendo sócios ativos.

**Por que Baixada/Nula são diferentes:** a empresa foi efetivamente encerrada. A RF continua publicando os sócios de empresas Baixadas em todos os dumps mensais enquanto esses sócios não saírem formalmente — o fechamento da empresa não remove os sócios automaticamente da base. Por isso a distinção no label é necessária: quem continua aparecendo na base de uma Baixada são "sócios até o fechamento", não "sócios ativos".

### Caso de teste canônico

**CURINGA EMPREENDIMENTOS IMOBILIARIOS LTDA** — CNPJ `00.041.327/0001-01`

- **Roberto Wassita Curi** — 3 trocas de cargo ao longo dos meses, sócio ativo atual
- **Eduardo Cury** — 2 cargos, sócio ativo atual
- **Karina Wassita Curi Cunha** — 2 cargos, ex-sócia. Caso especial: trocou de cargo E saiu da empresa no mesmo mês (12/2024) → `start_dates` usa `_fmt_mes` (mesmo mês) em vez de `_next_month`

Cobre todos os cenários: ativo com histórico, ex-sócio com histórico, troca de cargo no mesmo mês da saída.
