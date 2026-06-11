# Guia Das Funcoes Do `crud.py`

Este guia explica todas as funcoes presentes em `backend/app/crud.py`.

O `crud.py` funciona como a principal camada de acesso e organizacao dos dados da API. Ele recebe uma sessao do banco, executa consultas, aplica regras de negocio e devolve dicionarios que podem ser convertidos em JSON pelo FastAPI.

Embora o nome CRUD signifique `Create, Read, Update e Delete`, este arquivo realiza principalmente operacoes de leitura. A criacao e atualizacao em massa do banco ficam nos scripts de carga.

## Visao Geral

As funcoes podem ser divididas em cinco grupos:

1. cache e configuracoes;
2. formatacao e normalizacao;
3. organizacao de socios;
4. consultas de empresas e socios;
5. construcao de redes e grafos.

Fluxo comum:

```text
Router
  -> chama uma funcao publica do crud.py
  -> funcao consulta o banco
  -> usa funcoes auxiliares
  -> monta um dicionario
  -> router devolve o resultado
```

As funcoes que comecam com `_` sao consideradas internas. Elas existem para apoiar outras funcoes do arquivo e normalmente nao sao chamadas diretamente pelos routers.

---

# Constantes E Estruturas Globais

## `SITUACAO`

Traduz os codigos de situacao cadastral da Receita Federal:

```python
"01" -> "Nula"
"02" -> "Ativa"
"03" -> "Suspensa"
"04" -> "Inapta"
"08" -> "Baixada"
```

## `PORTE`

Traduz o codigo do porte empresarial:

```python
"01" -> "Micro Empresa"
"03" -> "Empresa de Pequeno Porte"
"05" -> "Grande Porte"
```

## `MATRIZ_FILIAL`

Traduz o identificador de estabelecimento:

```python
"1" -> "Matriz"
"2" -> "Filial"
```

## `FAIXA_ETARIA`

Traduz o codigo de faixa etaria disponibilizado para socios pessoas fisicas.

## `IDENTIFICADOR_SOCIO`

Traduz o tipo do socio:

```python
"1" -> "Pessoa Juridica"
"2" -> "Pessoa Fisica"
"3" -> "Estrangeiro"
```

## `QUALIFICACAO_RANK`

Define uma ordem de importancia para as qualificacoes societarias.

Exemplo:

```text
Presidente vem antes de Diretor
Diretor vem antes de Administrador
Administrador vem antes de Socio
```

Esse ranking e utilizado para ordenar socios e escolher a qualificacao principal apresentada.

## `_cache`

Armazena em memoria tabelas pequenas utilizadas frequentemente:

- qualificacoes;
- CNAEs;
- municipios;
- naturezas juridicas;
- motivos;
- mes mais recente.

O objetivo e evitar varias consultas repetidas ao disco.

---

# Cache E Mes Atual

## `_load_cache(db)`

### Objetivo

Carrega as tabelas de dominio do banco para o dicionario global `_cache`.

### Entrada

```python
db: Session
```

Sessao SQLAlchemy utilizada para consultar o banco.

### Funcionamento

1. verifica se o cache ja foi carregado;
2. consulta cada tabela de dominio;
3. transforma cada tabela em um dicionario;
4. marca `_cache["loaded"]` como verdadeiro.

Exemplo conceitual:

```python
_cache["municipio"]["7107"] = "BRASILIA"
_cache["cnae"]["6204000"] = "Consultoria em tecnologia da informacao"
```

### Retorno

Nao retorna valor. Modifica `_cache`.

### Quem Usa

Quase todas as funcoes publicas de consulta chamam `_load_cache` antes de montar resultados.

---

## `_get_mes_atual(db)`

### Objetivo

Descobrir o snapshot mensal mais recente processado com sucesso.

### Funcionamento

Executa:

```sql
SELECT MAX(dt_referencia)
FROM tb_processamento_mensal
WHERE status = 'CONCLUIDO'
```

O resultado e salvo no cache.

### Importancia

O mes atual e utilizado para decidir se:

- um vinculo societario ainda esta ativo;
- um socio e ex-socio;
- uma empresa ainda aparece no snapshot atual.

### Retorno

Uma string no formato:

```text
YYYY-MM
```

---

# Funcoes De Formatacao E Normalizacao

## `_fmt_cnpj(basico, ordem, dv)`

### Objetivo

Montar o CNPJ completo e o CNPJ formatado.

### Entrada

```text
basico: primeiros 8 digitos
ordem: 4 digitos da matriz ou filial
dv: 2 digitos verificadores
```

### Exemplo

```python
_fmt_cnpj("12345678", "0001", "90")
```

Retorna:

```python
(
    "12345678000190",
    "12.345.678/0001-90",
)
```

---

## `_fmt_date(d)`

### Objetivo

Converter uma data da Receita Federal para o formato brasileiro.

### Exemplo

```text
Entrada:  20260518
Saida:    18/05/2026
```

Se a data estiver vazia, invalida ou for `00000000`, retorna `None`.

---

## `_fmt_mes(m)`

### Objetivo

Converter o mes armazenado como `YYYY-MM` para `MM/YYYY`.

### Exemplo

```text
2026-05 -> 05/2026
```

---

## `_qual_desc(codigo)`

### Objetivo

Obter a descricao de uma qualificacao societaria usando o cache.

### Exemplo

```python
_qual_desc("49")
```

Pode retornar:

```text
Socio-Administrador
```

---

## `_next_month(mes)`

### Objetivo

Calcular o mes seguinte.

### Exemplo

```text
2026-05 -> 06/2026
2026-12 -> 01/2027
```

### Uso

Utilizada para inferir quando uma nova qualificacao societaria pode ter iniciado.

---

## `_normalizar(texto)`

### Objetivo

Preparar um texto para pesquisa textual.

### Funcionamento

1. remove acentos;
2. converte para letras maiusculas.

### Exemplo

```text
Joao Comércio -> JOAO COMERCIO
```

### Uso

Utilizada principalmente nas buscas FTS5.

---

## `_strip_situacao_especial(razao_social, situacao_especial)`

### Objetivo

Remover da razao social textos de situacao especial que podem aparecer duplicados no nome.

### Exemplo Conceitual

```text
Razao social:       EMPRESA EXEMPLO EM LIQUIDACAO
Situacao especial:  LIQUIDACAO
Resultado:          EMPRESA EXEMPLO
```

Ela tenta remover diferentes variacoes do sufixo.

---

## `_build_fts_match(nome_norm)`

### Objetivo

Construir a expressao utilizada pelo FTS5.

### Funcionamento

- separa o nome em palavras;
- ignora palavras menores que tres caracteres;
- escapa aspas;
- junta as palavras para busca.

### Exemplo

```text
Entrada:  BANCO DE INVESTIMENTO MASTER
Saida:    BANCO INVESTIMENTO MASTER
```

A palavra `DE` e ignorada por possuir menos de tres caracteres.

### Retorno

Retorna a expressao FTS ou `None` quando nao existem termos validos.

---

## `_cpf_mascarado_rf(valor)`

### Objetivo

Converter um CPF completo ou os seis digitos visiveis para o formato armazenado pela Receita Federal.

### Formato Do Banco

```text
***240659**
```

### Com CPF Completo

Se o usuario informar 11 digitos, a funcao utiliza os seis digitos centrais:

```text
CPF informado: 12324065900
Resultado:      ***240659**
```

### Com Seis Digitos

```text
Entrada:    240659
Resultado:  ***240659**
```

### Entrada Invalida

Qualquer quantidade diferente de 6 ou 11 digitos retorna `None`.

### Observacao

O sistema nao descobre os digitos ocultos. Ele apenas transforma a entrada para o mesmo formato presente na base publica.

---

## `_socio_list_item(nome, cpf, identificador, faixa)`

### Objetivo

Montar um item leve para a listagem inicial de socios.

### Retorno

```python
{
    "nome_socio": ...,
    "cpf_cnpj_socio": ...,
    "identificador": ...,
    "faixa_etaria": ...,
    "n_ativas": 0,
    "n_inaptas": 0,
    "n_ex": 0,
}
```

### Por Que Os Contadores Sao Zero?

Para manter a pesquisa em tempo real rapida. Calcular todas as empresas de cada socio durante a listagem seria pesado.

Os detalhes completos sao carregados somente quando o usuario abre o perfil.

---

## `_parse_cnaes_secundarios(raw)`

### Objetivo

Transformar uma string de CNAEs secundarios em uma lista estruturada.

### Exemplo

Entrada:

```text
6204000,6311900
```

Saida:

```python
[
    {"codigo": "6204000", "descricao": "..."},
    {"codigo": "6311900", "descricao": "..."},
]
```

As descricoes sao encontradas no cache de CNAEs.

---

# Funcoes De Organizacao Do Historico De Socios

## `_inferir_datas_inicio(registros_ord)`

### Objetivo

Inferir quando cada qualificacao ou cargo de um socio comecou.

### Problema Resolvido

A base informa a data original de entrada na sociedade, mas uma pessoa pode mudar de qualificacao ao longo do tempo.

Exemplo:

```text
2024: Socio
2025: Socio-Administrador
```

A base nem sempre informa diretamente a data exata da mudanca. A funcao utiliza os meses dos snapshots para estimar o inicio.

### Funcionamento

1. recebe registros ordenados do mais recente para o mais antigo;
2. usa a data real de entrada para o registro mais antigo;
3. para mudancas posteriores, utiliza o mes seguinte ao ultimo snapshot da qualificacao anterior;
4. aplica validacoes para evitar datas incoerentes.

### Retorno

Uma lista de datas correspondente aos registros recebidos.

---

## `_processar_grupo_socio(cpf, nome, registros, mes_atual)`

### Objetivo

Consolidar varios registros da mesma pessoa dentro de uma empresa em uma unica estrutura.

### Por Que Existem Varios Registros?

Uma pessoa pode aparecer varias vezes devido a:

- diferentes snapshots mensais;
- diferentes qualificacoes;
- mudancas de cargo;
- repeticoes historicas.

### Funcionamento

1. ordena os registros por mes e importancia da qualificacao;
2. verifica se existe algum registro no mes atual;
3. remove repeticoes consecutivas da mesma qualificacao;
4. infere datas de inicio;
5. define a qualificacao atual;
6. organiza qualificacoes anteriores.

### Retorno

```python
{
    "nome_socio": ...,
    "cpf_cnpj_socio": ...,
    "identificador": ...,
    "faixa_etaria": ...,
    "ativo": True ou False,
    "qualificacao_atual": {...},
    "qualificacoes_anteriores": [...],
}
```

---

## `_agrupar_socios(socios, mes_atual)`

### Objetivo

Agrupar os registros brutos da tabela `socio` em pessoas consolidadas.

### Chave De Agrupamento

```python
(cpf_cnpj_socio, nome_socio)
```

Usar CPF/CNPJ e nome juntos ajuda a evitar mistura de registros.

### Funcionamento

1. agrupa os registros;
2. chama `_processar_grupo_socio` para cada pessoa;
3. separa socios ativos e inativos;
4. ordena pela importancia da qualificacao e pelo nome.

### Retorno

```python
(socios_ativos, socios_inativos)
```

---

# Consultas De Empresa

## `get_empresa_by_cnpj(db, cnpj)`

### Chamada Pelo Router

```text
GET /api/v1/empresa/{cnpj}
```

### Objetivo

Montar o perfil cadastral completo de uma empresa ou estabelecimento.

### Funcionamento

1. carrega o cache e o mes atual;
2. remove caracteres nao numericos do CNPJ;
3. exige exatamente 14 digitos;
4. separa CNPJ basico e ordem;
5. busca o estabelecimento especifico;
6. busca a empresa pelo CNPJ basico;
7. busca informacoes do Simples;
8. busca todos os registros de socios;
9. busca todos os estabelecimentos da empresa;
10. agrupa socios ativos e inativos;
11. traduz codigos usando cache e constantes;
12. monta o dicionario final.

### Tabelas Consultadas

- `empresa`;
- `estabelecimento`;
- `socio`;
- `simples`;
- tabelas de dominio carregadas no cache.

### Retorno

Um dicionario compativel com o schema `EmpresaDetalhe`.

Se o CNPJ for invalido ou nao existir, retorna `None`.

---

## `get_empresa_rede(db, cnpj)`

### Chamada Pelo Router

```text
GET /api/v1/empresa/{cnpj}/rede
```

### Objetivo

Construir a estrutura hierarquica utilizada pelo mapa compacto de relacionamentos de uma empresa.

### Estrutura Construida

```text
Empresa raiz
  -> socios e ex-socios
      -> outras empresas relacionadas a cada socio
```

### Funcionamento

1. limpa o CNPJ e extrai o CNPJ basico;
2. busca a empresa raiz e sua matriz;
3. identifica se a empresa esta encerrada;
4. executa consulta relacionando registros da tabela `socio`;
5. encontra os socios da empresa raiz;
6. encontra outras empresas ligadas aos mesmos socios;
7. diferencia socios e empresas ativos ou antigos;
8. monta uma arvore com `children`.

### Retorno

Um dicionario hierarquico utilizado por `RedeTree.jsx`.

Essa resposta atualmente nao possui schema Pydantic especifico.

---

## `busca_empresa_nome(db, nome, skip=0, limit=20, known_total=0)`

### Chamada Pelo Router

```text
GET /api/v1/empresa/busca
```

### Objetivo

Pesquisar empresas por razao social ou nome fantasia.

### Parametros

- `nome`: termo pesquisado;
- `skip`: quantidade de resultados ignorados;
- `limit`: quantidade maxima devolvida;
- `known_total`: total conhecido pelo frontend para evitar recalculo.

### Estrategias De Busca

#### PostgreSQL

Quando o banco e PostgreSQL, utiliza consultas adequadas ao PostgreSQL, como `ILIKE`.

#### SQLite Com FTS5

Quando a tabela `fts_empresa` existe e possui dados:

1. normaliza o nome;
2. monta a expressao FTS;
3. busca candidatos rapidamente;
4. prioriza correspondencias mais relevantes.

#### Fallback Sem FTS

Se FTS nao estiver disponivel, utiliza `LIKE`, que e mais lento.

### Ordenacao De Relevancia

A funcao prioriza aproximadamente:

1. correspondencia exata;
2. nome iniciando pelo termo;
3. termo no inicio de alguma parte;
4. termo presente em outra posicao;
5. situacao cadastral e nome.

### Retorno

```python
{
    "total": ...,
    "resultados": [...],
}
```

Compativel com:

```python
ListaResultados[EmpresaListItem]
```

---

## `_empresa_rows_to_list(rows)`

### Objetivo

Converter linhas retornadas por uma consulta SQL de empresas em dicionarios da listagem.

### Funcionamento

Para cada linha:

- formata o CNPJ;
- traduz a situacao cadastral;
- remove texto duplicado de situacao especial;
- traduz municipio;
- monta um item de resultado.

### Uso

Utilizada por `busca_empresa_nome`.

---

# Funcoes De Verificacao De FTS

## `_fts_empresa_exists(db)`

### Objetivo

Verificar se `fts_empresa` existe e possui pelo menos um registro.

### Por Que Verificar Dados Tambem?

Uma tabela FTS vazia existe tecnicamente, mas nao consegue realizar buscas.

### Retorno

```python
True ou False
```

---

## `_fts_socio_exists(db)`

Possui o mesmo objetivo de `_fts_empresa_exists`, mas verifica `fts_socio`.

---

# Grafo Completo

## `get_grafo_rede(db, cnpj=None, cpf=None, nome=None, profundidade=2)`

### Chamada Pelos Routers

```text
GET /api/v1/empresa/{cnpj}/grafo
GET /api/v1/socio/grafo
```

### Objetivo

Construir o grafo completo de relacionamentos, iniciando por uma empresa ou por um socio.

### Modelo Do Grafo

O grafo e bipartido:

```text
Empresa <-> Socio
```

Existem dois tipos principais de nos:

- empresa;
- socio.

As arestas representam vinculos societarios.

Nao existe uma aresta direta socio-socio. Dois socios ficam indiretamente relacionados quando compartilham uma empresa.

### Busca Em Largura

A funcao utiliza BFS, busca em largura.

Exemplo iniciando por empresa:

```text
N0: empresa pesquisada
N1: socios dessa empresa
N2: outras empresas desses socios
N3: outros socios dessas empresas
```

### Funcoes Internas Locais

Dentro de `get_grafo_rede`, existem pequenas funcoes auxiliares locais usadas somente durante a construcao:

- adicionar empresa ao conjunto de nos;
- adicionar socio ao conjunto de nos;
- adicionar ligacao sem duplicar;
- separar consultas em blocos.

Elas nao existem fora de `get_grafo_rede`.

### Funcionamento Geral

1. identifica a entidade raiz;
2. adiciona a raiz aos nos;
3. mantem conjuntos de entidades ja visitadas;
4. consulta relacionamentos do nivel atual;
5. adiciona novos nos e ligacoes;
6. repete ate atingir a profundidade solicitada ou acabar a rede;
7. informa o nivel alcancado.

### Consultas Em Blocos

As consultas sao divididas em blocos para evitar ultrapassar limites de parametros do SQLite.

### Retorno

```python
{
    "root_id": ...,
    "nodes": [...],
    "links": [...],
    "categories": [...],
    "profundidade": ...,
    "nivel_alcancado": ...,
}
```

Esse formato e consumido por `GrafoRede.jsx`.

Atualmente nao existe schema Pydantic especifico para essa resposta.

---

# Consultas De Socios

## `_socio_pessoa_to_list(rows)`

### Objetivo

Converter linhas SQL consolidadas de socios em itens para a listagem.

### Retorno Por Pessoa

```python
{
    "nome_socio": ...,
    "cpf_cnpj_socio": ...,
    "identificador": ...,
    "faixa_etaria": ...,
    "n_ativas": ...,
    "n_inaptas": ...,
    "n_ex": ...,
}
```

### Uso

Utilizada nas buscas que calculam contadores completos.

---

## `busca_socio_nome(db, nome, skip=0, limit=20, known_total=0)`

### Chamada Pelo Router

```text
GET /api/v1/socio/busca?nome=...
```

### Objetivo

Pesquisar pessoas ou empresas que aparecem como socios pelo nome.

### Funcionamento No SQLite Com FTS

1. normaliza o nome;
2. cria a expressao FTS;
3. busca ate um limite de candidatos em `fts_socio`;
4. junta os candidatos com a tabela `socio`;
5. agrupa registros por nome e CPF/CNPJ;
6. prioriza correspondencias exatas e prefixos;
7. devolve uma listagem leve.

### Por Que A Listagem E Leve?

Para responder rapidamente enquanto o usuario digita.

Ela evita calcular todas as empresas relacionadas de cada resultado. Esses dados ficam para `get_perfil_socio`.

### Fallback

Sem FTS, utiliza `LIKE`, com consultas mais pesadas.

### Retorno

```python
{
    "total": ...,
    "resultados": [...],
}
```

Compativel com:

```python
ListaResultados[SocioListItem]
```

---

## `busca_socio_cpf(db, cpf, skip=0, limit=20, known_total=0)`

### Chamada Pelo Router

```text
GET /api/v1/socio/busca?cpf=...
```

### Objetivo

Pesquisar socios pelo CPF anonimizado.

### Funcionamento

1. transforma o valor informado usando `_cpf_mascarado_rf`;
2. se o CPF for invalido, retorna lista vazia;
3. conta pessoas distintas com aquele CPF mascarado;
4. agrupa registros por nome e CPF;
5. devolve resultados paginados.

### Comparacao

A busca utiliza igualdade:

```sql
WHERE cd_cpfcnpjsocio = :cpf
```

Nao utiliza busca parcial.

### Por Que Pode Retornar Varias Pessoas?

Como o CPF e parcialmente anonimizado, pessoas diferentes podem possuir os mesmos seis digitos visiveis.

---

# Perfil Completo De Socio

## `get_perfil_socio(db, cpf=None, nome=None)`

### Chamada Pelo Router

```text
GET /api/v1/socio/perfil
```

### Objetivo

Montar um perfil detalhado de uma pessoa ou empresa que aparece como socio.

### Identificacao Da Pessoa

Existem tres formas:

#### Nome E CPF

E a forma mais forte, pois reduz a mistura entre homonimos.

#### Somente CPF

Usa o CPF anonimizado.

#### Somente Nome

Usa correspondencia exata pelo nome normalizado.

### Etapa 1: Buscar Todos Os Registros

Busca toda a historia do socio, sem aplicar `LIMIT`.

As linhas ja incluem informacoes das tabelas:

- `socio`;
- `empresa`;
- `estabelecimento`.

### Etapa 2: Separar Empresas Ativas E Inativas

Uma empresa e considerada ativa para o perfil quando:

- o vinculo aparece no mes atual;
- a empresa nao esta Nula nem Baixada.

Suspensa e Inapta ainda sao consideradas existentes juridicamente.

### Etapa 3: Construir Cards De Empresa

A funcao interna `_build_card`, definida dentro de `get_perfil_socio`, monta cada empresa apresentada no perfil.

Ela organiza:

- CNPJ;
- razao social;
- situacao;
- qualificacoes;
- entrada e saida;
- capital social;
- porte;
- municipio;
- CNAEs.

### Etapa 4: Calcular Capital E Porte

Calcula:

- soma do capital social das empresas ativas;
- quantidade de empresas por porte.

Esse valor representa capital declarado das empresas relacionadas, nao patrimonio pessoal do socio.

### Etapa 5: Consolidar CNAEs

Conta os CNAEs principais e secundarios mais frequentes nas empresas ativas.

### Etapa 6: Consolidar Qualificacoes

Conta quantas vezes cada qualificacao aparece na historia da pessoa.

### Etapa 7: Encontrar Socios Em Comum

A funcao interna `_socios_rede` encontra outras pessoas que aparecem nas mesmas empresas.

Ela monta:

- socios em comum nas empresas ativas;
- ex-socios ou socios relacionados a empresas antigas.

### Retorno

```python
{
    "info": {...},
    "empresas_ativas": [...],
    "empresas_inativas": [...],
    "socios_comuns": [...],
    "ex_socios_comuns": [...],
    "qualificacoes_proprias": [...],
    "cnaes_principais": [...],
    "cnaes_secundarios": [...],
    "porte_acumulado": {...},
}
```

Atualmente essa resposta nao possui schema Pydantic especifico.

---

# Sobre A Repeticao Na Tabela `socio`

Sim, uma pessoa que participa de varias empresas aparece varias vezes na tabela `socio`.

Cada linha representa principalmente um vinculo:

```text
Socio X Empresa X Qualificacao X Snapshot
```

Exemplo:

```text
EMPRESA A | GERSON | ***240659** | SOCIO
EMPRESA B | GERSON | ***240659** | ADMINISTRADOR
EMPRESA C | GERSON | ***240659** | SOCIO-ADMINISTRADOR
```

A mesma pessoa tambem pode aparecer mais de uma vez na mesma empresa quando existem registros historicos de qualificacoes ou snapshots diferentes.

Por isso, funcoes como estas sao necessarias:

```python
_processar_grupo_socio()
_agrupar_socios()
get_perfil_socio()
```

Elas transformam varios registros brutos em uma visao consolidada da pessoa.

Importante: a tabela `socio` nao e uma tabela de pessoas unicas. Ela e uma tabela de vinculos societarios.

---

# Resumo Das Funcoes

| Funcao | Responsabilidade |
|---|---|
| `_load_cache` | Carrega tabelas de dominio em memoria |
| `_get_mes_atual` | Identifica o snapshot mais recente |
| `_fmt_cnpj` | Monta e formata CNPJ |
| `_fmt_date` | Formata data |
| `_fmt_mes` | Formata mes |
| `_qual_desc` | Traduz qualificacao |
| `_next_month` | Calcula proximo mes |
| `_normalizar` | Remove acentos e coloca texto em maiusculas |
| `_strip_situacao_especial` | Limpa situacao especial da razao social |
| `_build_fts_match` | Constroi expressao FTS |
| `_cpf_mascarado_rf` | Converte CPF para formato publico |
| `_socio_list_item` | Monta item leve de socio |
| `_parse_cnaes_secundarios` | Estrutura CNAEs secundarios |
| `_inferir_datas_inicio` | Infere inicio de qualificacoes |
| `_processar_grupo_socio` | Consolida registros de um socio |
| `_agrupar_socios` | Separa socios ativos e inativos |
| `get_empresa_by_cnpj` | Monta detalhe completo de empresa |
| `get_empresa_rede` | Monta arvore compacta da empresa |
| `get_grafo_rede` | Monta grafo completo por BFS |
| `_fts_empresa_exists` | Verifica FTS de empresas |
| `_fts_socio_exists` | Verifica FTS de socios |
| `busca_empresa_nome` | Pesquisa empresas por nome |
| `_empresa_rows_to_list` | Converte linhas em itens de empresa |
| `_socio_pessoa_to_list` | Converte linhas em itens de socio |
| `busca_socio_nome` | Pesquisa socios por nome |
| `busca_socio_cpf` | Pesquisa socios por CPF anonimizado |
| `get_perfil_socio` | Monta perfil completo do socio |

---

# Funcoes Chamadas Diretamente Pelos Routers

```python
crud.busca_empresa_nome()
crud.get_empresa_by_cnpj()
crud.get_empresa_rede()
crud.get_grafo_rede()
crud.busca_socio_nome()
crud.busca_socio_cpf()
crud.get_perfil_socio()
```

As demais funcoes existem para apoiar essas consultas principais.

