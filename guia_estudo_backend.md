# Guia De Estudo Do Backend

Este guia explica o funcionamento da pasta `backend/app` do projeto Busca Empresa.

## Visao Geral

O backend e uma API desenvolvida com FastAPI. Sua responsabilidade e receber requisicoes do frontend, consultar o banco de dados CNPJ, organizar os resultados e devolver respostas JSON.

Fluxo geral:

```text
Frontend React
    |
    | requisicao HTTP
    v
Router FastAPI
    |
    | chama uma funcao
    v
crud.py
    |
    | consulta
    v
SQLAlchemy + SQLite
    |
    | dados encontrados
    v
Schema Pydantic
    |
    | valida e serializa
    v
Resposta JSON para o frontend
```

Exemplo:

```text
GET /api/v1/empresa/12345678000190
    -> routers/empresa.py
    -> crud.get_empresa_by_cnpj()
    -> tabelas empresa, estabelecimento, socio, simples e dominios
    -> schema EmpresaDetalhe
    -> JSON
```

## Estrutura Da Pasta

```text
backend/app/
  __init__.py
  main.py
  database.py
  models.py
  schemas.py
  crud.py
  routers/
    __init__.py
    empresa.py
    socio.py
```

## main.py

E o ponto de entrada da aplicacao FastAPI.

Quando executamos:

```powershell
uvicorn app.main:app
```

o Uvicorn:

1. importa o modulo `app.main`;
2. procura o objeto chamado `app`;
3. inicia um servidor HTTP usando esse objeto FastAPI.

### Carregamento Do `.env`

```python
load_dotenv()
```

Carrega variaveis definidas em `backend/.env`, como:

```env
DATABASE_URL=sqlite:///./cnpj.db
ALLOWED_ORIGINS=http://localhost:5173
```

### Lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
```

O `lifespan` executa tarefas durante a inicializacao e encerramento da aplicacao.

Antes do `yield`, o backend:

1. cria tabelas que ainda nao existem;
2. abre uma sessao com o banco;
3. carrega tabelas de dominio em cache;
4. identifica o mes mais atual processado;
5. fecha a sessao.

```python
Base.metadata.create_all(bind=engine)
crud._load_cache(db)
crud._get_mes_atual(db)
```

O `yield` indica que a inicializacao terminou e a aplicacao pode atender requisicoes.

### Criacao Da Aplicacao

```python
app = FastAPI(title="Busca CNPJ", version="1.0.0", lifespan=lifespan)
```

Cria a aplicacao principal.

### GZip

```python
app.add_middleware(GZipMiddleware, minimum_size=500)
```

Comprime respostas maiores que 500 bytes, diminuindo o trafego enviado ao frontend.

### CORS

CORS define quais sites podem chamar a API pelo navegador.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex or None,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

Sem CORS, o navegador bloquearia o frontend React tentando acessar o backend em outro dominio ou porta.

O backend permite apenas metodos `GET`, porque atualmente a aplicacao realiza somente consultas.

### Inclusao Dos Routers

```python
app.include_router(empresa.router)
app.include_router(socio.router)
```

Isso registra na aplicacao principal todas as rotas definidas nos arquivos:

```text
routers/empresa.py
routers/socio.py
```

Sem `include_router`, as rotas desses arquivos existiriam no codigo, mas nao seriam acessiveis pela API.

### Rotas Gerais

```python
@app.get("/health")
```

Verifica se a API esta funcionando.

```python
@app.get("/api/v1/info")
```

Retorna informacoes gerais, atualmente o mes mais recente da base.

## database.py

Configura a conexao entre a aplicacao e o banco.

### DATABASE_URL

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cnpj.db")
```

Le a URL do banco do ambiente. Se ela nao existir, usa:

```text
sqlite:///./cnpj.db
```

### Engine

```python
engine = create_engine(DATABASE_URL, connect_args=connect_args)
```

A `engine` gerencia as conexoes com o banco.

Ela nao representa uma unica conexao permanentemente aberta. E o componente central usado pelo SQLAlchemy para criar e administrar conexoes.

### check_same_thread

```python
{"check_same_thread": False}
```

O SQLite normalmente restringe uma conexao a thread que a criou. Essa opcao permite que o FastAPI utilize o banco em diferentes threads.

### PRAGMAs Do SQLite

Os PRAGMAs configuram o comportamento do SQLite:

```python
PRAGMA journal_mode=WAL
PRAGMA cache_size=-524288
PRAGMA mmap_size=10737418240
PRAGMA synchronous=NORMAL
PRAGMA temp_store=MEMORY
```

- `WAL`: melhora concorrencia entre leituras e escritas.
- `cache_size`: reserva aproximadamente 512 MB para cache de paginas.
- `mmap_size`: permite mapear ate 10 GB do arquivo na memoria virtual.
- `synchronous=NORMAL`: equilibra seguranca e desempenho.
- `temp_store=MEMORY`: tenta manter estruturas temporarias na memoria.

### SessionLocal

```python
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
```

E uma fabrica de sessoes.

Uma sessao e usada para executar consultas e acompanhar operacoes durante uma requisicao.

### Base

```python
Base = declarative_base()
```

E a classe base utilizada pelos models SQLAlchemy.

Todas as classes de tabela herdam de `Base`.

### get_db

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Cria uma sessao para cada requisicao e garante que ela seja fechada no final.

Nos routers, ela e utilizada assim:

```python
db: Session = Depends(get_db)
```

O FastAPI executa automaticamente:

1. chama `get_db`;
2. recebe a sessao produzida pelo `yield`;
3. entrega essa sessao para a funcao da rota;
4. executa o bloco `finally`;
5. fecha a sessao.

Isso e chamado de injecao de dependencia.

## models.py

Define como as tabelas do banco sao representadas no Python pelo SQLAlchemy.

Exemplo:

```python
class Empresa(Base):
    __tablename__ = "empresa"
    cd_cnpjbasico = Column(String(8), primary_key=True)
    nm_razaosocial = Column(String(150))
```

Isso informa:

- a classe Python se chama `Empresa`;
- ela representa a tabela `empresa`;
- `cd_cnpjbasico` e chave primaria;
- `nm_razaosocial` e uma coluna textual.

### Tabelas Principais

#### Empresa

Representa informacoes da pessoa juridica pelo CNPJ basico de oito digitos.

Campos importantes:

- razao social;
- natureza juridica;
- capital social;
- porte;
- primeiro mes de carga;
- ultima atualizacao.

#### Estabelecimento

Representa matriz ou filial.

A chave primaria e composta:

```python
PrimaryKeyConstraint("cd_cnpjbasico", "cd_cnpjordem")
```

O CNPJ completo e formado por:

```text
CNPJ basico + ordem + digito verificador
```

Exemplo:

```text
12345678 + 0001 + 90
```

#### Socio

Representa o vinculo entre uma pessoa ou empresa e um CNPJ basico.

Campos importantes:

- CNPJ basico da empresa;
- nome do socio;
- CPF ou CNPJ anonimizado;
- qualificacao;
- data de entrada;
- ultima atualizacao.

#### Simples

Representa informacoes do Simples Nacional e MEI.

### Tabelas De Dominio

Traduzem codigos para nomes compreensiveis:

- `Cnae`;
- `Municipio`;
- `Natureza`;
- `Qualificacao`;
- `Motivo`;
- `Pais`.

### Tabelas De Controle

- `CheckpointCarga`: registra progresso por tabela e mes.
- `ProcessamentoMensal`: registra status e contadores da carga mensal.

## schemas.py

Define o formato das respostas da API usando Pydantic.

Models e schemas nao sao a mesma coisa:

```text
Model SQLAlchemy = formato da tabela no banco
Schema Pydantic  = formato da entrada ou resposta da API
```

Exemplo:

No banco, o campo e:

```text
nm_razaosocial
```

Na resposta da API, ele aparece como:

```text
razao_social
```

O `crud.py` transforma o formato interno do banco no formato amigavel definido pelos schemas.

### EmpresaListItem

Usado na listagem da pesquisa.

Possui poucos campos para manter a busca rapida:

- CNPJ;
- razao social;
- nome fantasia;
- situacao;
- UF;
- municipio.

### EmpresaDetalhe

Usado ao abrir uma empresa.

Possui informacoes completas:

- cadastro;
- endereco;
- CNAEs;
- Simples;
- socios;
- filiais;
- datas de carga.

### SocioListItem

Usado na listagem inicial de socios.

### ListaResultados

E um schema generico:

```python
class ListaResultados(BaseModel, Generic[T]):
    total: int
    resultados: List[T]
```

Pode representar:

```python
ListaResultados[EmpresaListItem]
ListaResultados[SocioListItem]
```

Resposta:

```json
{
  "total": 100,
  "resultados": []
}
```

### from_attributes

```python
model_config = {"from_attributes": True}
```

Permite que o Pydantic leia valores de objetos e atributos, incluindo objetos SQLAlchemy.

## Routers

Routers definem os endpoints da API.

Eles nao devem concentrar as consultas complexas. Sua funcao principal e:

1. definir a URL;
2. receber parametros;
3. validar parametros;
4. obter a sessao do banco;
5. chamar o CRUD;
6. transformar erros em respostas HTTP;
7. devolver o resultado.

### APIRouter

```python
router = APIRouter(prefix="/api/v1/empresa", tags=["empresa"])
```

O prefixo e adicionado antes de todas as rotas do arquivo.

Exemplo:

```python
@router.get("/busca")
```

vira:

```text
GET /api/v1/empresa/busca
```

As tags organizam a documentacao automatica do Swagger.

### Annotated E Query

```python
nome: Annotated[str, Query(min_length=2)]
```

Define que:

- `nome` deve ser texto;
- vem da query string;
- precisa possuir pelo menos dois caracteres.

Exemplo:

```text
/api/v1/empresa/busca?nome=MASTER
```

### response_model

```python
response_model=ListaResultados[EmpresaListItem]
```

O FastAPI utiliza esse schema para:

- validar a resposta;
- remover campos inesperados;
- documentar o endpoint;
- converter o resultado em JSON.

### HTTPException

```python
raise HTTPException(status_code=404, detail="CNPJ nao encontrado.")
```

Interrompe a funcao e devolve um erro HTTP estruturado.

## Rotas De Empresa

Prefixo:

```text
/api/v1/empresa
```

### Busca Por Nome

```text
GET /api/v1/empresa/busca?nome=MASTER&skip=0&limit=20
```

Chama:

```python
crud.busca_empresa_nome()
```

### Rede Compacta

```text
GET /api/v1/empresa/{cnpj}/rede
```

Chama:

```python
crud.get_empresa_rede()
```

Retorna uma estrutura hierarquica usada pelo mapa compacto.

### Grafo Completo

```text
GET /api/v1/empresa/{cnpj}/grafo?profundidade=2
```

Chama:

```python
crud.get_grafo_rede()
```

Retorna listas de nos e arestas usadas pelo grafo completo.

### Detalhe Por CNPJ

```text
GET /api/v1/empresa/{cnpj}
```

Chama:

```python
crud.get_empresa_by_cnpj()
```

## Rotas De Socio

Prefixo:

```text
/api/v1/socio
```

### Busca

```text
GET /api/v1/socio/busca?nome=GERSON
GET /api/v1/socio/busca?cpf=240659
```

Se receber CPF:

```python
crud.busca_socio_cpf()
```

Caso contrario:

```python
crud.busca_socio_nome()
```

### Perfil

```text
GET /api/v1/socio/perfil?cpf=240659&nome=GERSON
```

Chama:

```python
crud.get_perfil_socio()
```

### Grafo

```text
GET /api/v1/socio/grafo?cpf=240659&nome=GERSON&profundidade=2
```

Chama:

```python
crud.get_grafo_rede()
```

## crud.py

E a camada mais complexa do backend.

Ela concentra:

- consultas ao banco;
- formatacao dos dados;
- traducao de codigos;
- agrupamento de socios;
- busca textual;
- montagem de redes e grafos.

O nome CRUD significa:

```text
Create, Read, Update, Delete
```

Neste projeto, o `crud.py` da API realiza principalmente operacoes de leitura. Criacao e atualizacao em massa ficam nos scripts de carga.

## Blocos Do crud.py

### Cache De Dominios

```python
_load_cache(db)
```

Carrega tabelas pequenas de dominio em memoria:

- CNAEs;
- municipios;
- naturezas;
- qualificacoes;
- motivos;
- paises.

Em vez de consultar essas tabelas repetidamente, o backend acessa dicionarios em memoria.

Exemplo conceitual:

```python
_cache["municipio"]["7107"] -> "BRASILIA"
```

### Mes Atual

```python
_get_mes_atual(db)
```

Descobre o snapshot mais recente processado.

Ele e importante para diferenciar:

- socio ativo;
- ex-socio;
- empresa ainda presente;
- vinculo antigo.

### Funcoes De Formatacao

```python
_fmt_cnpj()
_fmt_date()
_fmt_mes()
_normalizar()
_parse_cnaes_secundarios()
```

Transformam os dados brutos em formatos adequados para o frontend.

### CPF Anonimizado

```python
_cpf_mascarado_rf()
```

A Receita Federal fornece CPF aproximadamente neste formato:

```text
***240659**
```

Se o usuario informar o CPF completo, a funcao extrai os seis digitos centrais e monta o formato pesquisavel.

Exemplo conceitual:

```text
CPF completo: 12324065900
Parte visivel: 240659
Busca no banco: ***240659**
```

Isso nao significa que o sistema conhece os digitos ocultos.

### Busca Textual FTS5

```python
_build_fts_match()
_fts_empresa_exists()
_fts_socio_exists()
```

FTS significa Full-Text Search.

As tabelas FTS permitem pesquisar nomes de maneira muito mais rapida do que:

```sql
WHERE lower(nome) LIKE '%termo%'
```

O CRUD verifica se a tabela FTS existe e possui dados. Caso nao exista, utiliza uma busca alternativa mais lenta.

### Detalhe Da Empresa

```python
get_empresa_by_cnpj()
```

Fluxo simplificado:

1. limpa o CNPJ;
2. separa CNPJ basico e ordem;
3. encontra o estabelecimento solicitado;
4. encontra a empresa pelo CNPJ basico;
5. carrega informacoes do Simples;
6. busca todos os socios relacionados;
7. agrupa socios ativos e inativos;
8. busca outras filiais;
9. traduz codigos usando cache;
10. monta um dicionario compatível com `EmpresaDetalhe`.

### Busca De Empresas Por Nome

```python
busca_empresa_nome()
```

Utiliza:

- normalizacao de texto;
- FTS5 quando disponivel;
- priorizacao de correspondencias exatas;
- priorizacao de prefixos;
- situacao cadastral;
- paginacao.

`skip` indica quantos resultados pular.

`limit` indica quantos resultados devolver.

`known_total` evita recalcular o total quando o frontend ja conhece esse valor.

### Agrupamento De Socios

```python
_agrupar_socios()
_processar_grupo_socio()
```

Um mesmo socio pode possuir varios registros:

- diferentes empresas;
- diferentes qualificacoes;
- diferentes snapshots mensais.

Essas funcoes consolidam os registros para apresentar uma pessoa de maneira organizada.

### Busca De Socios

```python
busca_socio_nome()
busca_socio_cpf()
```

A busca por nome utiliza FTS5.

A busca por CPF utiliza comparacao exata com o formato anonimizado.

A listagem inicial e propositalmente leve. Informacoes mais pesadas sao carregadas somente ao abrir o perfil.

Isso e uma forma de lazy loading:

```text
primeiro carrega o necessario para listar
depois carrega detalhes quando o usuario solicita
```

### Perfil Do Socio

```python
get_perfil_socio()
```

Busca e consolida:

- dados do socio;
- empresas atuais;
- empresas antigas;
- capital acumulado;
- qualificacoes;
- socios em comum;
- ex-socios em comum.

Quando nome e CPF estao disponiveis, utiliza ambos para reduzir mistura entre homonimos.

### Rede Compacta

```python
get_empresa_rede()
```

Retorna uma estrutura em arvore:

```text
Empresa raiz
  -> socios
      -> outras empresas
```

Essa estrutura e consumida pelo componente `RedeTree.jsx`.

### Grafo Completo

```python
get_grafo_rede()
```

Retorna:

```json
{
  "nodes": [],
  "links": [],
  "categories": []
}
```

Ele utiliza BFS, busca em largura.

Exemplo iniciando por empresa:

```text
N0: empresa raiz
N1: socios da empresa
N2: outras empresas desses socios
N3: socios dessas empresas
```

A profundidade define quantos niveis devem ser percorridos.

O grafo e bipartido:

```text
empresa <-> socio
```

Nao existe uma aresta direta socio-socio. Dois socios aparecem relacionados indiretamente quando compartilham uma empresa.

## Fluxos Para Decorar

### Pesquisar Empresa Por Nome

```text
BuscaEmpresa.jsx
 -> api.js
 -> GET /api/v1/empresa/busca
 -> routers/empresa.py
 -> crud.busca_empresa_nome()
 -> fts_empresa + empresa + estabelecimento
 -> ListaResultados[EmpresaListItem]
 -> frontend
```

### Abrir Empresa

```text
Resultado selecionado
 -> GET /api/v1/empresa/{cnpj}
 -> routers/empresa.py
 -> crud.get_empresa_by_cnpj()
 -> empresa + estabelecimento + socio + simples + dominios
 -> EmpresaDetalhe
 -> ResultadoEmpresa.jsx
```

### Pesquisar Socio

```text
BuscaSocio.jsx
 -> api.js
 -> GET /api/v1/socio/busca
 -> routers/socio.py
 -> busca_socio_nome() ou busca_socio_cpf()
 -> SocioListItem
 -> frontend
```

### Abrir Grafo

```text
Botao Rede completa
 -> api.js
 -> endpoint /grafo
 -> crud.get_grafo_rede()
 -> nodes + links
 -> GrafoRede.jsx
```

## Perguntas Que Podem Cair

### Qual e a diferenca entre model e schema?

Model representa a tabela do banco. Schema define o formato validado da entrada ou resposta da API.

### Para que serve um router?

Organiza endpoints relacionados, recebe parametros, chama a camada de negocio e devolve respostas HTTP.

### O que e injecao de dependencia?

E quando o FastAPI fornece automaticamente algo que uma rota necessita. No projeto, ele fornece uma sessao do banco por meio de `Depends(get_db)`.

### Por que fechar a sessao do banco?

Para liberar conexoes e recursos, evitando vazamentos.

### O que e FTS5?

E o mecanismo de busca textual completa do SQLite, utilizado para acelerar pesquisas por nomes.

### Por que usar cache para tabelas de dominio?

Porque sao pequenas e consultadas frequentemente. Mantendo-as em memoria, evitamos consultas repetidas.

### Por que a busca inicial de socio nao calcula tudo?

Porque seria lenta. A listagem devolve informacoes leves, e os detalhes sao carregados ao abrir o perfil.

### O que e CORS?

E uma politica do navegador que controla quais origens podem acessar uma API.

### O que e middleware?

E uma camada executada ao redor das requisicoes e respostas. O projeto usa middleware para CORS e compressao GZip.

### O que e BFS?

Busca em largura. Explora primeiro todos os nos de um nivel antes de seguir para o proximo.

### Por que usar somente GET?

Porque a API atual e de consulta. A carga e atualizacao do banco sao feitas por scripts separados.

### Por que SQLite?

Porque e simples, local, nao exige servidor separado e funciona bem para prototipacao e muitas consultas de leitura. A limitacao aparece em concorrencia elevada e implantacao distribuida.

### Qual e a funcao do backend?

Receber requisicoes do frontend, validar parametros, consultar e relacionar os dados do banco e devolver respostas JSON estruturadas.

## Como Estudar

Nao tente decorar todo o `crud.py`.

Estude nesta ordem:

1. entenda o fluxo geral;
2. entenda `main.py`;
3. entenda `database.py`;
4. compare `models.py` e `schemas.py`;
5. leia os routers;
6. escolha tres funcoes do CRUD:
   - `get_empresa_by_cnpj`;
   - `busca_socio_nome`;
   - `get_grafo_rede`;
7. acompanhe uma requisicao do frontend ate o banco e de volta.

Para praticar, abra:

```text
http://localhost:8000/docs
```

O Swagger permite testar cada endpoint e observar parametros e respostas.
