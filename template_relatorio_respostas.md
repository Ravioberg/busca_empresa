# Respostas Para O Relatorio IBM8942

Este arquivo reune textos tecnicos e funcionais para preencher o `Template_Relatorio_Projeto_IBM8942.docx`.

Os campos de nome, matricula, cidade, prints, assinaturas, relato do cliente e datas de reuniao ainda precisam ser completados pelo grupo. Onde aparece `[confirmar]`, a informacao depende de decisao do grupo ou do cliente/agente externo.

## Titulo Do Projeto

Busca Empresa

## Subtitulo

Sistema web para consulta de empresas, socios e redes societarias a partir dos dados publicos do CNPJ.

## Resumo

O projeto Busca Empresa consiste no desenvolvimento de uma aplicacao web para consulta e analise de dados publicos do Cadastro Nacional da Pessoa Juridica (CNPJ), publicados pela Receita Federal do Brasil. O problema central atendido e a dificuldade de pesquisar, filtrar e relacionar informacoes societarias em arquivos publicos grandes, fragmentados e de uso pouco amigavel para usuarios finais. O objetivo do sistema e permitir consultas rapidas por nome empresarial, CNPJ, nome de socio e CPF mascarado, alem de apresentar detalhes cadastrais, quadro societario e uma visualizacao em grafo das relacoes entre empresas e socios. A solucao foi desenvolvida com frontend em React e Vite, backend em Python com FastAPI e SQLAlchemy, banco SQLite para desenvolvimento e carga local dos dados, indices B-tree e FTS5 para busca textual otimizada. Tambem foi criado um pipeline de carga para processar os arquivos ZIP mensais da Receita Federal, montar o banco `cnpj.db`, atualizar snapshots mensais e validar indices e tabelas auxiliares. Como resultado, o projeto entrega uma interface de busca em tempo real, paginas de detalhe para empresas e socios, e recursos de exploracao de rede societaria. Para implantacao, esta prevista a utilizacao da Azure, com frontend publicado em servico estatico e backend em servico de aplicacao. Conclui-se que a solucao torna a consulta a dados publicos empresariais mais acessivel, organizada e util para analises exploratorias.

Palavras-chave: CNPJ; Receita Federal; busca empresarial; rede societaria.

## 1 Introducao

O Cadastro Nacional da Pessoa Juridica disponibilizado pela Receita Federal e uma das principais bases publicas para consulta de empresas no Brasil. Apesar de sua relevancia, os dados sao publicados em arquivos grandes, separados por categorias, compactados em ZIP e atualizados mensalmente. Essa estrutura dificulta o uso direto por usuarios que precisam consultar rapidamente uma empresa, identificar socios, verificar situacao cadastral ou entender relacoes entre diferentes CNPJs.

O projeto Busca Empresa foi desenvolvido para transformar esses dados publicos em uma experiencia de pesquisa mais acessivel. A aplicacao permite buscar empresas por CNPJ ou nome, buscar socios por nome ou CPF mascarado, visualizar informacoes cadastrais e explorar conexoes societarias por meio de grafo. A proposta e reduzir a friccao entre a base bruta da Receita Federal e a necessidade pratica de consulta e analise.

O sistema foi construido como uma aplicacao web com separacao entre frontend, backend e processo de carga de dados. O frontend oferece a interface de navegacao e busca em tempo real. O backend concentra as regras de consulta, consolidacao de dados e exposicao da API. O banco de dados e gerado a partir dos arquivos publicos, com indices especificos para desempenho. Este relatorio apresenta primeiro a visao funcional do sistema, depois a arquitetura tecnica, as tecnologias utilizadas, o modelo de dados, os testes realizados e a estrategia prevista de implantacao em nuvem.

## 2 Objetivos

### 2.1 Objetivo Geral

Desenvolver uma aplicacao web para consulta rapida e exploracao de dados publicos de empresas e socios do CNPJ, tornando a base da Receita Federal mais acessivel, pesquisavel e visualmente compreensivel.

### 2.2 Objetivos Especificos

- Criar um pipeline de carga capaz de processar os arquivos ZIP mensais da Receita Federal e gerar o banco `cnpj.db`.
- Implementar buscas por nome empresarial, CNPJ, nome de socio e CPF mascarado.
- Otimizar as consultas para uso em tempo real, com indices relacionais e busca textual FTS5.
- Exibir detalhes cadastrais de empresas, incluindo situacao, endereco, CNAE, capital social e quadro societario.
- Exibir perfil de socios, incluindo empresas vinculadas e situacao dos vinculos encontrados.
- Construir uma visualizacao em grafo para representar conexoes entre empresas e socios.
- Preparar a solucao para implantacao em ambiente Azure.

## 3 Relatorio Funcional

### 3.1 Visao Geral E Contexto Do Negocio

O sistema atua no dominio de consulta e analise de dados empresariais publicos. Seu principal insumo e a base de CNPJ da Receita Federal, que contem informacoes sobre empresas, estabelecimentos, socios, CNAEs, natureza juridica, municipios, qualificacoes societarias, Simples Nacional e outros dados cadastrais.

O valor da solucao esta em transformar uma base publica extensa e dificil de manipular em uma ferramenta de pesquisa direta. Em vez de o usuario lidar com arquivos CSV compactados e codigos de dominio, ele pode usar uma interface web para pesquisar entidades, abrir detalhes e navegar por relacoes societarias. A aplicacao e especialmente util para analises preliminares de empresas, identificacao de socios, verificacao de situacao cadastral e compreensao de conexoes entre pessoas e CNPJs.

Cliente/agente externo: `[confirmar nome do cliente/agente externo e contexto especifico apresentado ao IBMEC]`.

### 3.2 Requisitos Funcionais

As tecnicas de levantamento utilizadas foram reunioes do grupo, analise da base publica da Receita Federal, testes exploratorios com o usuario e refinamento iterativo das necessidades durante o desenvolvimento.

- RF01 - O sistema deve permitir a busca de empresas por nome empresarial ou nome fantasia.
- RF02 - O sistema deve permitir a busca direta de empresa por CNPJ.
- RF03 - O sistema deve permitir a busca de socios por nome.
- RF04 - O sistema deve permitir a busca de socios por CPF no formato disponivel na base publica, considerando que a Receita Federal anonimiza parte do CPF.
- RF05 - O sistema deve exibir uma lista de resultados paginada para buscas de empresas e socios.
- RF06 - O sistema deve exibir a pagina de detalhe de uma empresa selecionada.
- RF07 - O sistema deve exibir a pagina de perfil de um socio selecionado.
- RF08 - O sistema deve apresentar o quadro societario de uma empresa.
- RF09 - O sistema deve apresentar empresas associadas a um socio.
- RF10 - O sistema deve representar relacoes entre empresas e socios em formato de grafo.
- RF11 - O sistema deve permitir navegar de uma empresa para seus socios e de um socio para suas empresas relacionadas.
- RF12 - O sistema deve carregar e atualizar a base de dados a partir dos arquivos mensais da Receita Federal.
- RF13 - O sistema deve validar a existencia das tabelas, indices e estruturas de busca necessarias para funcionamento.

### 3.3 Requisitos Nao Funcionais

- RNF01 - Desempenho: as buscas principais devem responder rapidamente para permitir pesquisa em tempo real enquanto o usuario digita.
- RNF02 - Usabilidade: a interface deve ser simples, com separacao clara entre busca de empresa, busca de socio, detalhe e grafo.
- RNF03 - Confiabilidade: o processo de carga deve registrar meses processados, checkpoints e status para reduzir risco de perda de progresso.
- RNF04 - Manutenibilidade: o codigo deve ser separado em frontend, backend, modelos, rotas, camada de CRUD e scripts de carga.
- RNF05 - Atualizacao: o banco deve poder ser reconstruido ou atualizado mensalmente com o snapshot mais recente da Receita Federal.
- RNF06 - Privacidade: o sistema deve respeitar o formato publico da base, na qual CPFs de socios aparecem mascarados.
- RNF07 - Escalabilidade operacional: a arquitetura deve permitir evolucao futura para banco gerenciado em nuvem, como Azure SQL ou PostgreSQL.
- RNF08 - Compatibilidade: a aplicacao deve funcionar em navegador moderno e consumir a API por HTTP.

### 3.4 Casos De Uso E Regras De Negocio

Casos de uso principais:

- Pesquisar empresa por nome: o usuario digita parte do nome empresarial ou fantasia e recebe resultados em tempo real.
- Pesquisar empresa por CNPJ: o usuario informa o CNPJ e acessa diretamente os detalhes da empresa.
- Pesquisar socio por nome: o usuario digita o nome do socio e recebe possiveis correspondencias.
- Pesquisar socio por CPF mascarado: o usuario informa o CPF completo ou os digitos visiveis disponiveis na base publica, e o backend converte a consulta para o padrao mascarado da Receita Federal.
- Visualizar detalhes da empresa: o usuario seleciona uma empresa e ve dados cadastrais, situacao, endereco, CNAE, capital social e socios.
- Visualizar perfil do socio: o usuario seleciona um socio e ve empresas relacionadas.
- Explorar grafo societario: o usuario abre uma visualizacao de rede com empresas e socios conectados.
- Atualizar banco de dados: o operador baixa o snapshot mensal e executa o script de carga para atualizar as tabelas e indices.

Regras de negocio principais:

- A base de CNPJ e tratada como snapshot mensal. Empresas, estabelecimentos, socios, Simples e tabelas de dominio podem mudar a cada mes.
- O campo `dt_ultimaatualizacao` indica o ultimo mes em que um registro foi visto no snapshot processado.
- O campo `dt_primeiracarga`, na tabela `empresa`, preserva o primeiro mes em que a empresa entrou no banco local.
- O CPF de socios e armazenado no formato disponibilizado pela Receita Federal, com anonimização parcial. Portanto, a busca por CPF nao recupera os digitos ocultos, apenas compara com a parte visivel da base publica.
- Para evitar resultados lentos em tempo real, a listagem inicial de socios e leve; informacoes mais completas sao carregadas na tela de perfil.
- O grafo possui limite de profundidade e quantidade de nos para evitar consultas excessivamente pesadas.
- As tabelas de dominio sao usadas para traduzir codigos da Receita Federal para descricoes legiveis.

### 3.5 Descricao Das Funcionalidades

A tela inicial direciona o usuario para os fluxos principais: busca por empresa ou busca por socio. Na busca de empresa, o usuario pode digitar um nome empresarial, nome fantasia ou CNPJ. A aplicacao realiza requisicoes em tempo real para a API e apresenta resultados paginados. Ao selecionar uma empresa, o usuario acessa a pagina de detalhe, com informacoes como razao social, nome fantasia, CNPJ, situacao cadastral, endereco, municipio, UF, CNAE, capital social e quadro societario.

Na busca de socios, o usuario pode procurar por nome ou CPF conforme a disponibilidade da base publica. Como os CPFs sao mascarados pela Receita Federal, o sistema trabalha com os digitos visiveis e evita assumir que possui o CPF completo real em texto aberto. Ao abrir um socio, a aplicacao consulta o perfil completo e mostra empresas relacionadas, vinculos identificados e informacoes consolidadas.

Outra funcionalidade entregue e a visualizacao de rede societaria. A partir de uma empresa ou socio, o sistema monta um grafo com nos de empresas e socios e arestas representando os vinculos societarios encontrados. Essa visualizacao ajuda a identificar conexoes indiretas e navegar entre entidades relacionadas.

No lado operacional, o projeto inclui scripts para criar, atualizar, validar e reparar o banco de dados. O processo de carga le os arquivos ZIP da Receita Federal, cria as tabelas principais, carrega dominios, gera indices e popula estruturas de busca textual. Isso permite que a aplicacao seja atualizada conforme os novos snapshots mensais sejam publicados.

## 4 Relatorio Tecnico

### 4.1 Arquitetura Da Solucao

A solucao foi organizada em tres partes principais: frontend web, backend de API e pipeline de dados.

O frontend foi desenvolvido em React com Vite. Ele e responsavel pela interface do usuario, navegacao entre telas, chamadas HTTP para a API, estados de carregamento, exibicao de resultados e visualizacao de grafo. As principais telas estao separadas em componentes como `BuscaEmpresa`, `BuscaSocio`, `ResultadoEmpresa`, `ResultadoSocio` e `GrafoRede`.

O backend foi desenvolvido em Python com FastAPI. Ele expoe endpoints REST sob o prefixo `/api/v1`, separados por dominio em routers de empresa e socio. As rotas recebem parametros de busca, validam entradas, chamam funcoes da camada `crud.py` e retornam respostas estruturadas. A camada de dados utiliza SQLAlchemy para conexao e modelos principais, alem de SQL otimizado para consultas especificas.

O banco atual do projeto e um SQLite local (`cnpj.db`) gerado a partir dos arquivos publicos da Receita Federal. Para desempenho, foram criados indices B-tree em campos como CNPJ basico, CPF mascarado e nomes, alem de tabelas virtuais FTS5 para busca textual por empresa e socio.

Para a implantacao em nuvem, a proposta e utilizar Azure. O frontend pode ser publicado no Azure Static Web Apps, enquanto o backend pode ser executado no Azure App Service. O banco, em uma evolucao de producao, pode ser migrado para um servico gerenciado como Azure SQL Database ou Azure Database for PostgreSQL, usando o script de migracao existente como base para evolucao futura. O fluxo de requisicao sera: navegador do usuario -> frontend publicado -> API FastAPI -> banco de dados.

### 4.2 Tecnologias E Ferramentas

- Python: linguagem utilizada no backend e nos scripts de carga dos dados publicos.
- FastAPI: framework para construcao da API REST, com validacao de parametros e documentacao automatica.
- SQLAlchemy: camada de modelagem e conexao com o banco de dados.
- SQLite: banco utilizado no desenvolvimento local e na versao atual do projeto, adequado para prototipacao e consultas locais.
- FTS5: recurso do SQLite usado para busca textual otimizada por nome de empresa e socio.
- Pandas: usado no pipeline de carga para leitura e processamento dos arquivos CSV extraidos dos ZIPs.
- python-dotenv: usado para carregar variaveis de ambiente como `DATABASE_URL` e `DADOS_BRUTOS`.
- React: biblioteca utilizada para construir a interface do usuario.
- Vite: ferramenta de desenvolvimento e build do frontend.
- Tailwind CSS: utilitario de estilos usado na interface.
- ECharts: biblioteca usada para renderizar o grafo de rede societaria.
- Git e GitHub: versionamento do codigo e colaboracao do grupo.
- Azure: plataforma prevista para deploy do frontend, backend e futura persistencia gerenciada.

### 4.3 Modelagem De Dados E De Classes

O modelo de dados foi baseado nas tabelas publicas do CNPJ da Receita Federal. As principais entidades sao:

- `empresa`: representa a pessoa juridica no nivel de CNPJ basico, com razao social, natureza juridica, qualificacao do responsavel, capital social, porte e controle de carga.
- `estabelecimento`: representa matriz ou filial, com CNPJ completo formado por CNPJ basico, ordem e digito verificador, alem de nome fantasia, situacao cadastral, CNAE, endereco e contatos.
- `socio`: representa vinculos societarios entre pessoas ou empresas e um CNPJ basico, contendo nome do socio, CPF/CNPJ mascarado, qualificacao, data de entrada e faixa etaria.
- `simples`: registra informacoes de opcao pelo Simples Nacional e MEI.
- `cnae`, `municipio`, `natureza`, `qualificacao`, `motivo` e `pais`: tabelas de dominio usadas para traduzir codigos da base publica.
- `tb_processamento_mensal`: controla os meses processados e seus contadores.
- `tb_checkpoint_carga`: registra checkpoints por etapa de carga.
- `fts_empresa` e `fts_socio`: estruturas auxiliares de busca textual.

Relacionamentos principais:

- `empresa.cd_cnpjbasico` se relaciona com `estabelecimento.cd_cnpjbasico`.
- `empresa.cd_cnpjbasico` se relaciona com `socio.cd_cnpjbasico`.
- `empresa.cd_cnpjbasico` se relaciona com `simples.cd_cnpjbasico`.
- `estabelecimento.cd_cnaefiscalprincipal` se relaciona com `cnae.cd_cnae`.
- `estabelecimento.cd_municipio` se relaciona com `municipio.cd_municipio`.
- `empresa.cd_naturezajuridica` se relaciona com `natureza.cd_naturezajuridica`.
- `socio.cd_qualificacaosocio` se relaciona com `qualificacao.cd_qualificacao`.

No diagrama de classes, devem aparecer as classes SQLAlchemy definidas em `backend/app/models.py`, alem dos principais modulos de aplicacao: routers de empresa e socio, camada `crud.py`, configuracao de banco em `database.py` e aplicacao FastAPI em `main.py`.

Sugestao de legenda: Figura X - Modelo de dados simplificado do sistema Busca Empresa.

### 4.4 Padroes De Projeto E Organizacao Do Codigo

O projeto segue uma organizacao em camadas. O frontend fica em `frontend/`, separado do backend. No backend, a aplicacao FastAPI fica em `backend/app/`, com `main.py` para configuracao da aplicacao, `routers/` para endpoints HTTP, `schemas.py` para modelos de resposta, `models.py` para tabelas SQLAlchemy, `database.py` para conexao e injecao de sessao, e `crud.py` para consultas e regras de acesso aos dados.

Essa estrutura se aproxima do padrao MVC em uma versao adaptada para APIs: os componentes React fazem a camada de apresentacao, os routers funcionam como controllers, o `crud.py` atua como camada de servico/repositorio, e os models representam a camada de dados. A injecao de dependencia do FastAPI e usada para fornecer a sessao de banco aos endpoints.

Nos scripts, a pasta `backend/scripts/carga/` concentra o processo oficial de criacao e atualizacao do banco. A pasta `backend/scripts/tools/` contem utilitarios auxiliares, como reparo de indices e estruturas de busca.

### 4.5 Metodologia Agil E Versionamento (Git)

O desenvolvimento ocorreu de forma incremental, com ciclos curtos de implementacao, teste e ajuste. As tarefas foram organizadas em torno de entregas funcionais: carga da base, criacao do backend, criacao do frontend, busca de empresas, busca de socios, detalhe de entidades, grafo de rede e otimizacoes de desempenho.

O Git foi utilizado para versionamento do codigo. As alteracoes foram registradas em commits com mensagens descritivas, separando melhorias de infraestrutura de banco, ajustes de desempenho e alteracoes de frontend. Exemplos de commits recentes incluem organizacao do pipeline de carga do banco CNPJ e otimizacao da busca de socios em tempo real.

Estrategia de branches e pull requests: `[confirmar como o grupo esta usando GitHub: main direto, branches por feature ou PRs]`.

### 4.6 Testes E Validacao

A validacao foi realizada por testes manuais, execucao dos scripts de verificacao do banco e testes de build do frontend. No banco de dados, o comando de validacao verifica se as tabelas principais, tabelas de dominio, indices e estruturas FTS existem e estao prontas para uso. Tambem foi criado o utilitario `reparar_busca.py`, capaz de recriar indices e popular estruturas de busca quando necessario.

No backend, foram testadas consultas por CNPJ, nome de empresa, nome de socio, CPF mascarado, perfil de socio e grafo. As otimizacoes mais recentes reduziram o custo da busca em tempo real, especialmente evitando consultas completas desnecessarias na listagem inicial de socios e usando FTS5 para nomes.

No frontend, foi executado o build com Vite para verificar se a aplicacao compila corretamente. Tambem foram feitos testes exploratorios navegando pelos principais fluxos: tela inicial, busca de empresa, resultado de empresa, busca de socio, resultado de socio e grafo de rede.

Limitacao atual: ainda nao ha uma suite automatizada completa de testes unitarios e de integracao. Essa e uma melhoria recomendada para a proxima etapa do projeto.

### 4.7 Implantacao Na Nuvem E CI/CD

A implantacao prevista sera realizada na Azure. A proposta e publicar o frontend React no Azure Static Web Apps, configurando a variavel `VITE_API_URL` para apontar para o backend. O backend FastAPI sera implantado no Azure App Service, com variaveis de ambiente como `DATABASE_URL`, `ALLOWED_ORIGINS` e caminho/configuracao do banco.

Para a versao de producao, recomenda-se avaliar a migracao do SQLite local para um banco gerenciado na Azure, como Azure SQL Database ou Azure Database for PostgreSQL. Isso melhora disponibilidade, backup, concorrencia e operacao em nuvem. O projeto ja possui um script de apoio para migracao para PostgreSQL, que pode servir como base para essa evolucao.

O CI/CD pode ser configurado pelo GitHub Actions ou pela integracao nativa do Azure Static Web Apps e App Service. O pipeline recomendado inclui: instalar dependencias, executar build do frontend, validar/importar backend, e publicar artefatos no ambiente Azure. A URL final da aplicacao ainda deve ser preenchida apos o deploy.

URL publicada: `[preencher apos deploy na Azure]`.

## 5 Evidencias De Visitas Tecnicas E Reunioes Com O Cliente

Esta secao depende das evidencias reais do grupo. Inserir fotos, prints de reuniao, atas ou registros de conversa com o cliente/agente externo.

Sugestao de texto:

Durante o desenvolvimento, o grupo realizou reunioes de alinhamento para compreender o problema, validar as funcionalidades desejadas e acompanhar a evolucao do sistema. As evidencias abaixo documentam os encontros e discussoes realizados com o agente externo.

Figura X - Reuniao de alinhamento com o cliente/agente externo em `[data]`, realizada em `[local ou plataforma]`.

## 6 Telas Da Aplicacao

Sugestoes de prints para inserir:

- Tela inicial de selecao entre busca de empresa e busca de socio.
- Tela de busca de empresas com resultados em tempo real.
- Tela de detalhe de empresa.
- Tela de busca de socios.
- Tela de perfil de socio.
- Tela de grafo de rede societaria.

Sugestoes de legendas:

- Figura X - Tela inicial da aplicacao Busca Empresa.
- Figura X - Busca de empresas por nome ou CNPJ.
- Figura X - Detalhamento cadastral de uma empresa selecionada.
- Figura X - Busca de socios por nome ou CPF mascarado.
- Figura X - Perfil de socio com empresas relacionadas.
- Figura X - Grafo de relacoes societarias entre empresas e socios.

## 7 Relato Final Do Cliente

Esta secao precisa ser preenchida com o feedback real do cliente/agente externo.

Sugestao de estrutura:

O cliente/agente externo avaliou que a solucao `[descrever percepcao real]`. Segundo o relato, o sistema contribui para `[descrever valor percebido]`, pois permite `[descrever funcionalidades valorizadas]`. Como pontos de melhoria, foram citados `[descrever melhorias, se houver]`.

Relato assinado: anexar no ANEXO A.

## 8 Conclusao

O projeto Busca Empresa atingiu o objetivo de criar uma aplicacao web para consulta e exploracao de dados publicos do CNPJ. A solucao permite pesquisar empresas e socios, visualizar detalhes cadastrais e analisar relacoes societarias por meio de um grafo interativo. Alem da interface, foi desenvolvido um processo de carga para transformar os arquivos mensais da Receita Federal em um banco consultavel, com indices e estruturas de busca adequadas ao uso em tempo real.

Entre os principais resultados, destacam-se a separacao clara entre frontend e backend, a criacao de endpoints especificos para empresas e socios, a organizacao do banco `cnpj.db`, a documentacao do processo de carga mensal e as otimizacoes realizadas no `crud.py` para melhorar a velocidade das pesquisas. O projeto tambem ficou preparado para evoluir para uma implantacao em Azure.

Como limitacoes, a busca por CPF depende do formato anonimizado da Receita Federal, o que impede identificar todos os digitos reais do documento. Alem disso, a versao atual ainda utiliza SQLite local, adequado para desenvolvimento e prototipacao, mas que deve ser substituido ou complementado por banco gerenciado em nuvem para uso em producao. Outra melhoria futura e a criacao de testes automatizados mais completos.

Como trabalhos futuros, recomenda-se aprimorar a experiencia do frontend, permitir refinamento combinado por nome e CPF, melhorar a visualizacao do grafo, criar dashboards analiticos, implementar autenticacao completa caso necessario e finalizar a estrategia de deploy com CI/CD na Azure.

## Referencias

BRASIL. Receita Federal do Brasil. Cadastro Nacional da Pessoa Juridica - CNPJ: dados publicos. Disponivel em: https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj. Acesso em: `[preencher data de acesso]`.

FASTAPI. FastAPI documentation. Disponivel em: https://fastapi.tiangolo.com/. Acesso em: `[preencher data de acesso]`.

MICROSOFT. Azure App Service documentation. Disponivel em: https://learn.microsoft.com/azure/app-service/. Acesso em: `[preencher data de acesso]`.

MICROSOFT. Azure Static Web Apps documentation. Disponivel em: https://learn.microsoft.com/azure/static-web-apps/. Acesso em: `[preencher data de acesso]`.

REACT. React documentation. Disponivel em: https://react.dev/. Acesso em: `[preencher data de acesso]`.

SQLITE. SQLite FTS5 Extension. Disponivel em: https://www.sqlite.org/fts5.html. Acesso em: `[preencher data de acesso]`.

VITE. Vite documentation. Disponivel em: https://vite.dev/. Acesso em: `[preencher data de acesso]`.

## Anexos

ANEXO A - Documentacao assinada pelo agente externo.

ANEXO B - Diagrama de arquitetura da solucao.

ANEXO C - Modelo de dados simplificado.

ANEXO D - Evidencias adicionais do processo de carga e validacao do banco.
