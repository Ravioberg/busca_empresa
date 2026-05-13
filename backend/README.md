# busca_empresa — Backend

Pipeline de carga da base CNPJ da Receita Federal para SQLite, com atualização incremental mensal.

---

## Visão geral

O backend consome os arquivos ZIP mensais publicados pela Receita Federal em [dados.gov.br](https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj) e os carrega em um banco SQLite local. Cada mês processado representa um snapshot completo do cadastro nacional de empresas.

---

## Estrutura de arquivos

```
backend/
├── carga.py             # pipeline principal de carga
├── models.py            # definição das tabelas (SQLAlchemy)
├── database.py          # configuração da engine e Base
├── reset_carga.py       # limpa dados e controles, mantém domínios e Simples
├── kill_locks.ps1       # encerra processos Python que possam travar o SQLite
├── find_lock.ps1        # identifica qual processo está com lock no cnpj.db
├── cnpj.db              # banco SQLite gerado pelo carga.py
└── .env                 # variáveis de ambiente (opcional)
```

Dados brutos esperados em:
```
busca_empresa/dados-brutos/
├── 2023-03/
│   ├── Empresas0.zip
│   ├── Empresas1.zip
│   ├── ...
│   ├── Estabelecimentos0.zip
│   ├── Socios0.zip
│   └── ...
├── 2023-04/
│   └── ...
└── 2026-04/
    ├── Cnaes.zip
    ├── Municipios.zip
    ├── Naturezas.zip
    ├── Qualificacoes.zip
    ├── Motivos.zip
    ├── Paises.zip
    └── Simples.zip
```

---

## Como executar

```powershell
# Processar todos os meses pendentes
py -3.12 carga.py

# Ver situação de cada mês
py -3.12 carga.py --status

# Processar apenas um mês específico
py -3.12 carga.py --mes 2023-03

# Resetar dados (mantém domínios e Simples) e recomeçar do zero
py -3.12 reset_carga.py
py -3.12 carga.py
```

### Variáveis de ambiente (.env)

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./cnpj.db` | URL do banco de dados |
| `DADOS_BRUTOS` | `../dados-brutos` | Caminho para a pasta com os ZIPs |

---

## Tabelas do banco

### Convenção de nomenclatura (padrão DW)

Todos os campos seguem o padrão de Data Warehouse com prefixo semântico:

| Prefixo | Significado | Exemplos |
|---|---|---|
| `cd_` | Código / identificador | `cd_cnpjbasico`, `cd_municipio` |
| `nm_` | Nome próprio | `nm_razaosocial`, `nm_municipio` |
| `dt_` | Data | `dt_primeiracarga`, `dt_ultimaatualizacao` |
| `fl_` | Flag booleano (S/N) | `fl_opcaosimples`, `fl_opcaomei` |
| `vl_` | Valor monetário | `vl_capitalsocial` |
| `sg_` | Sigla / abreviação | `sg_uf` |
| `ds_` | Descrição de código | `ds_cnae`, `ds_cnaefiscalsecundaria` |
| `nr_` | Número (telefone etc.) | `nr_telefone1`, `nr_fax` |

### Tabelas principais

#### `empresa`
Dados cadastrais da empresa (CNPJ básico — 8 dígitos).

| Campo | Tipo | Descrição |
|---|---|---|
| `cd_cnpjbasico` | PK | 8 primeiros dígitos do CNPJ |
| `nm_razaosocial` | TEXT | Razão social |
| `cd_naturezajuridica` | TEXT | Código da natureza jurídica |
| `cd_qualificacaoresponsavel` | TEXT | Código de qualificação do responsável |
| `vl_capitalsocial` | TEXT | Capital social declarado |
| `cd_porteempresa` | TEXT | Código do porte (ME, EPP, etc.) |
| `nm_entefederativo` | TEXT | Ente federativo responsável |
| `dt_primeiracarga` | TEXT (YYYY-MM) | Mês em que o registro entrou pela primeira vez no banco |
| `dt_ultimaatualizacao` | TEXT (YYYY-MM) | Último mês em que o registro foi visto no snapshot da RF |

#### `estabelecimento`
Dados de cada estabelecimento (CNPJ completo = basico + ordem).

| Campo | Tipo | Descrição |
|---|---|---|
| `cd_cnpjbasico` + `cd_cnpjordem` | PK composta | Identificam o estabelecimento |
| `cd_cnpjdv` | TEXT | Dígito verificador |
| `cd_identificadormatrizfilial` | TEXT | 1=Matriz, 2=Filial |
| `nm_nomefantasia` | TEXT | Nome fantasia |
| `cd_situacaocadastral` | TEXT | Situação (01=Nula, 02=Ativa, 03=Suspensa, 04=Inapta, 08=Baixada) |
| `dt_datasituacaocadastral` | TEXT | Data da situação cadastral |
| `cd_motivosituacaocadastral` | TEXT | Código do motivo da situação |
| `cd_cnaefiscalprincipal` | TEXT | CNAE principal (7 dígitos) |
| `ds_cnaefiscalsecundaria` | TEXT | CNAEs secundários separados por vírgula |
| `sg_uf` | TEXT | UF |
| `cd_municipio` | TEXT | Código do município (RF) |
| `dt_datainicioatividade` | TEXT | Data de início de atividade |
| `dt_ultimaatualizacao` | TEXT (YYYY-MM) | Último mês visto no snapshot |
| *(demais campos de endereço e contato)* | | |

#### `socio`
Quadro societário de cada empresa.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | PK autoincrement | Chave técnica interna |
| `cd_cnpjbasico` | TEXT | Empresa à qual o sócio pertence |
| `cd_cpfcnpjsocio` | TEXT | CPF/CNPJ do sócio (mascarado) |
| `cd_qualificacaosocio` | TEXT | Código de qualificação do sócio |
| `nm_nomesociorazaosocial` | TEXT | Nome ou razão social do sócio |
| `cd_identificadorsocio` | TEXT | 1=Pessoa Jurídica, 2=Pessoa Física, 3=Estrangeiro |
| `dt_dataentradasociedade` | TEXT | Data de entrada na sociedade |
| `dt_ultimaatualizacao` | TEXT (YYYY-MM) | Último mês visto no snapshot |
| *(demais campos de representante legal)* | | |

**Unicidade real**: `(cd_cnpjbasico, cd_cpfcnpjsocio, cd_qualificacaosocio)` — garantida por `UniqueConstraint`. Um mesmo CPF pode ser sócio de várias empresas; a combinação tripla é o que o identifica.

### Tabelas de domínio (carregadas uma única vez do mês mais recente)

| Tabela | PK | Descrição |
|---|---|---|
| `cnae` | `cd_cnae` | Classificação Nacional de Atividades Econômicas |
| `municipio` | `cd_municipio` | Municípios (código RF → nome) |
| `natureza` | `cd_naturezajuridica` | Naturezas jurídicas |
| `qualificacao` | `cd_qualificacao` | Qualificações de sócios e responsáveis |
| `motivo` | `cd_motivosituacaocadastral` | Motivos de situação cadastral |
| `pais` | `cd_pais` | Países |
| `simples` | `cd_cnpjbasico` | Opção pelo Simples Nacional e MEI |

### Tabelas de controle

| Tabela | Descrição |
|---|---|
| `tb_processamento_mensal` | Um registro por mês processado com status (CONCLUIDO/ERRO) e contadores |
| `tb_checkpoint_carga` | Checkpoints por ZIP dentro de cada mês em processamento |

---

## Regras de negócio

### `dt_primeiracarga`
- Existe **somente na tabela `empresa`**.
- Gravada no **INSERT** com o mês corrente (`:mes`).
- **Nunca atualizada** nas passagens incrementais — o `ON CONFLICT DO UPDATE` propositalmente omite esse campo do `SET`.
- Representa o mês em que a empresa apareceu pela primeira vez neste banco.

### `dt_ultimaatualizacao`
- Existe em `empresa`, `estabelecimento` e `socio`.
- Atualizada em **todos os registros** vistos no snapshot de cada mês, inclusive quando nenhum outro campo mudou.
- Essa atualização é obrigatória: é o único indicador de que o registro ainda está ativo na base da Receita Federal.
- Nos meses incrementais a maioria dos registros só muda este campo — o UPSERT resolve isso em passe único sem scan separado.

### Duplicatas da Receita Federal
A RF pode publicar o mesmo registro em mais de um arquivo ZIP do mesmo mês. O UPSERT `ON CONFLICT DO UPDATE` resolve isso nativamente: a segunda ocorrência de uma mesma chave atualiza o registro com dados idênticos, sem criar duplicatas.

---

## Lógica de processamento

### Fluxo por ZIP

Para cada ZIP de cada tabela principal, o pipeline faz:

```
1. DROP TABLE IF EXISTS tmp_X         → descarta qualquer resíduo de runs anteriores
2. CREATE TABLE tmp_X                 → tmp limpa
3. Lê CSV em chunks de 100.000 linhas → carrega tudo em tmp_X via única raw_connection
4. raw.commit()                       → um único commit por ZIP (não por chunk)
5. CREATE INDEX na tmp_X              → acelera o UPSERT
6. INSERT INTO tabela_principal ... ON CONFLICT DO UPDATE  → UPSERT atômico
7. DROP TABLE tmp_X                   → libera espaço imediatamente
8. Salva checkpoint do ZIP            → marca progresso seguro
```

Cada ZIP tem sua própria tmp, criada e descartada na mesma operação. Não há acúmulo.

### Conexão única por ZIP

Todo o carregamento de chunks de um ZIP usa uma **única `raw_connection` sqlite3 nativa**, com um único `commit()` ao final. Isso elimina a abertura/fechamento de conexão por chunk e o overhead de múltiplos commits parciais — crítico para ZIPs com 40+ chunks.

### UPSERT unificado

O mesmo SQL `INSERT ... ON CONFLICT DO UPDATE` é usado para o **primeiro mês** e para todos os **meses incrementais**:

- **Registro novo**: INSERT com `dt_primeiracarga = :mes` e `dt_ultimaatualizacao = :mes`.
- **Registro existente**: ON CONFLICT atualiza todos os campos + `dt_ultimaatualizacao`, preserva `dt_primeiracarga`.

Isso elimina a necessidade de dois passes separados (UPDATE + INSERT WHERE NOT EXISTS).

#### Por que `WHERE 1=1` antes de `ON CONFLICT`?

O SQLite parser interpreta `FROM tabela ON CONFLICT` como sintaxe de JOIN (`ON` = condição de join). O `WHERE 1=1` fecha a cláusula `FROM` antes que o parser chegue ao `ON CONFLICT`, evitando o erro `near "DO": syntax error`.

```sql
SELECT ... FROM tmp_empresa WHERE 1=1
ON CONFLICT(cd_cnpjbasico) DO UPDATE SET ...
```

### Checkpoints e retomada

O progresso é salvo no banco após cada ZIP concluído com sucesso. Se o script for interrompido a qualquer momento:

- ZIPs com checkpoint → **pulados** na próxima execução.
- ZIP sem checkpoint (interrompido no meio) → a tmp é descartada e o ZIP é **reprocessado do início** — seguro porque o UPSERT é idempotente.
- O mês só é marcado como `CONCLUIDO` após **todos os ZIPs das três tabelas** serem processados com sucesso.

Não há risco de dado perdido ou corrompido ao parar e retomar.

#### Formato dos checkpoints

Os checkpoints de ZIP usam a chave `"tabela::NomeDoZip.zip"` (ex: `"estabelecimento::Estabelecimentos0.zip"`). O código detecta e trata automaticamente dois casos especiais do pipeline anterior:

- **Checkpoint de tabela (formato antigo)**: chave sem `::` (ex: `"empresa"`) indica que a tabela inteira foi concluída pela versão anterior do código — a tabela é pulada.
- **Checkpoints órfãos**: ZIP checkpoints existem mas a tabela está vazia (o UPSERT nunca rodou antes de uma interrupção) — os checkpoints são limpos e o ZIP é reprocessado.

### Primeira carga vs. incrementais

O código não tem dois caminhos separados. A distinção é apenas:

| | Primeiro mês | Meses seguintes |
|---|---|---|
| SQL de carga | `INSERT ... ON CONFLICT DO UPDATE` (igual) | `INSERT ... ON CONFLICT DO UPDATE` (igual) |
| `dt_primeiracarga` | Gravada no INSERT | Ignorada no ON CONFLICT — preservada |
| Índices secundários | Criados em batch ao final | Dropados antes, recriados em batch depois |

### Domínios e Simples

Carregados apenas uma vez, da pasta do mês mais recente (`MES_DOMINIOS = "2026-04"`). Se já houver registros no banco, a etapa é pulada. O `reset_carga.py` não apaga essas tabelas.

---

## Performance e configurações SQLite

O banco opera com WAL mode e os seguintes PRAGMAs aplicados no início de cada sessão:

| PRAGMA | Valor | Efeito |
|---|---|---|
| `journal_mode` | WAL | Leituras não bloqueiam escritas |
| `synchronous` | OFF | Sem fsync — máxima velocidade de escrita para carga em batch |
| `cache_size` | -1048576 | 1 GB de cache de páginas em memória |
| `temp_store` | MEMORY | Tabelas temporárias em RAM |
| `mmap_size` | 4294967296 | Até 4 GB de mapeamento de memória |
| `threads` | 4 | Sort paralelo durante criação de índices |

> **`synchronous = OFF`**: em caso de crash de energia durante um ZIP, aquele ZIP é reprocessado na próxima execução (UPSERT é idempotente). Dados de ZIPs já checkpointados nunca são perdidos.

### Por que chunks de 100.000 linhas?

Os arquivos da RF chegam a dezenas de milhões de linhas por ZIP. Chunks de 100k equilibram uso de memória (cada chunk ocupa ~50-80 MB em RAM) com eficiência de I/O. O commit é único por ZIP — os chunks são só a unidade de leitura/parse do pandas.

### Por que fica mais lento nos meses incrementais?

O UPSERT precisa localizar cada registro pelo índice primário numa tabela de 50M+ linhas — lookup O(log N) por linha. Conforme as tabelas crescem, o tempo aumenta. Cinco otimizações minimizam esse custo:

1. **`ORDER BY PK` no SELECT do UPSERT**: força o SQLite a percorrer o B-tree da tabela principal em ordem sequencial, maximizando o reaproveitamento do cache de páginas e eliminando leituras de disco repetidas.
2. **Drop/recreate de índices secundários por tabela**: os índices de busca (razão social, nome fantasia, CPF) são dropados apenas para as tabelas que têm ZIPs a processar. Se `empresa` já estiver checkpointada, `ix_emp_razao` não é tocado. Cada linha modificada atualiza menos B-trees durante o UPSERT; a recriação em batch após o UPSERT é muito mais eficiente do que atualizações incrementais por linha.
3. **WAL checkpoint após DROP de índices**: logo após dropar os índices de uma tabela, `PRAGMA wal_checkpoint(PASSIVE)` grava as mudanças DDL no arquivo principal e limpa o WAL — o loop de ZIPs começa com WAL pequeno, melhorando o desempenho de leitura durante o UPSERT.
4. **WAL checkpoint antes de recriar índices**: após o loop de ZIPs, o WAL acumula dezenas de milhões de páginas sujas (todos os UPSERTs). Um `wal_checkpoint(PASSIVE)` antes do primeiro CREATE INDEX move essas páginas para o arquivo principal. Sem esse checkpoint, o CREATE INDEX tem que checar o WAL em cada lookup do scan da tabela — potencialmente 2–5× mais lento.
5. **Cache 2 GB + checkpoint entre índices na recriação**: durante `_recriar_indexes_tabela`, o `cache_size` é temporariamente elevado para 2 GB na mesma conexão dos CREATE INDEX, dando ao SQLite mais memória para o sort (evita spill em disco). Um `wal_checkpoint(PASSIVE)` é executado após cada índice criado, mantendo o WAL pequeno para o próximo CREATE INDEX scan.
6. **WAL checkpoint(TRUNCATE) ao fim de cada mês**: o arquivo WAL é truncado após cada mês concluído, evitando que acumule e penalize as leituras dos meses seguintes.

### Lógica de drop/recreate por tabela

O script decide dropar/recriar os índices de uma tabela com base em `tem_trabalho = ck_zip_count < len(zips)`:

- `ck_zip_count` = número de ZIPs com checkpoint salvo para este mês e tabela
- Se todos os ZIPs já têm checkpoint → tabela está concluída → índices **não são tocados**
- Se há ZIPs a processar → índices são dropados antes e recriados depois

Isso evita o custo de dropar/recriar `ix_emp_razao` (53M+ linhas) em meses onde `empresa` já está totalmente processada.

### `_garantir_indexes` — safety net nos meses incrementais

No início de cada mês incremental, `_garantir_indexes` executa `CREATE INDEX IF NOT EXISTS` para todos os 6 índices secundários. Se os índices existem, é um no-op instantâneo. Se um crash anterior deixou algum índice faltando, ele é restaurado antes de qualquer outra operação. Não há custo visível quando os índices já existem.

---

## Scripts auxiliares

### `reset_carga.py`
Limpa as tabelas de dados e controle, mantendo domínios e Simples intactos.

```
Apaga: empresa, estabelecimento, socio,
       tb_checkpoint_carga, tb_processamento_mensal,
       tmp_empresa, tmp_estabelecimento, tmp_socios
Mantém: cnae, municipio, natureza, qualificacao, motivo, pais, simples
```

Use quando quiser recomeçar do zero sem precisar recarregar domínios.

### `kill_locks.ps1`
Encerra todos os processos Python em execução. Útil quando o banco fica travado por um processo anterior.

### `find_lock.ps1`
Lista os processos que têm o arquivo `cnpj.db` aberto.

---

## Dependências Python

```
pandas
sqlalchemy
python-dotenv
```

Versões testadas: Python 3.12, pandas 3.x, SQLAlchemy 2.x.

O pipeline usa `engine.raw_connection()` para obter uma conexão sqlite3 nativa, contornando incompatibilidade entre pandas 3.x e SQLAlchemy 2.x no método `to_sql`.
