# Processo do Banco CNPJ

Este projeto usa dados publicos mensais da Receita Federal para gerar e atualizar o banco `backend/cnpj.db`.

O script oficial e:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py
```

Se preferir usar o Python global, ele precisa ter as dependencias de `backend/requirements.txt` instaladas.

O `carga.py` substitui o uso separado de `carga2.py` e `criar_indices.py`. O `carga2.py` fica como legado por enquanto.

## Organizacao Dos Dados

A pasta de entrada e `dados-brutos`, com uma subpasta por mes:

```text
busca_empresa/
  dados-brutos/
    2026-05/
      Empresas0.zip
      Empresas1.zip
      Estabelecimentos0.zip
      Estabelecimentos1.zip
      Socios0.zip
      Socios1.zip
      Simples.zip
      Cnaes.zip
      Motivos.zip
      Municipios.zip
      Naturezas.zip
      Paises.zip
      Qualificacoes.zip

    2026-06/
      ...
```

O nome da pasta precisa estar no formato `YYYY-MM`.

O script procura estes padroes:

- `Empresas*.zip`
- `Estabelecimentos*.zip`
- `Socios*.zip`
- `Simples*.zip`
- `Cnaes*.zip`
- `Motivos*.zip`
- `Municipios*.zip`
- `Naturezas*.zip`
- `Paises*.zip`
- `Qualificacoes*.zip`

Arquivos como `Empresas0.zip`, `Empresas1.zip`, etc. sao partes do snapshot daquele mes. O script nao assume que um arquivo e incremental em relacao ao outro; todos os arquivos daquele tipo devem ser processados juntos.

## Como O Banco Fica

Tabelas principais:

- `empresa`: foto atual por CNPJ basico.
- `estabelecimento`: foto atual por CNPJ basico + ordem.
- `socio`: historico consolidado de vinculos societarios por mes processado.
- `simples`: foto atual do Simples/MEI.

Tabelas de dominio:

- `cnae`
- `motivo`
- `municipio`
- `natureza`
- `pais`
- `qualificacao`

Tabelas de controle:

- `tb_processamento_mensal`: status e contadores por mes.
- `tb_checkpoint_carga`: checkpoints por ZIP, para retomar carga interrompida.

Tabelas de busca:

- `fts_empresa`: busca textual por razao social/nome fantasia.
- `fts_socio`: busca textual por nome de socio.

## Se Voce Nao Tem Nada

Existem tres estrategias possiveis.

### Estrategia Recomendada: Historico De Socios

Use quando voce quer um banco bom para o produto, sem baixar todos os snapshots completos antigos.

Organizacao:

```text
dados-brutos/
  2026-03/
    Socios0.zip
    Socios1.zip

  2026-04/
    Socios0.zip
    Socios1.zip

  2026-05/
    Socios0.zip
    Socios1.zip

  2026-06/
    Empresas0.zip
    Empresas1.zip
    Estabelecimentos0.zip
    Estabelecimentos1.zip
    Socios0.zip
    Socios1.zip
    Simples.zip
    Cnaes.zip
    Motivos.zip
    Municipios.zip
    Naturezas.zip
    Paises.zip
    Qualificacoes.zip
```

Meses antigos podem ter apenas `Socios*.zip`. O mes mais recente deve ter o snapshot completo.

Comando:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py init --reset
```

`historico-socios` e a estrategia padrao do `init`.

Comando equivalente explicito:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py init --reset --estrategia historico-socios
```

### Estrategia Rapida: Snapshot Atual

Use quando voce quer subir o sistema rapidamente, sem historico antigo.

Baixe somente o mes mais recente completo:

```text
dados-brutos/
  2026-06/
    Empresas*.zip
    Estabelecimentos*.zip
    Socios*.zip
    Simples*.zip
    Cnaes*.zip
    Motivos*.zip
    Municipios*.zip
    Naturezas*.zip
    Paises*.zip
    Qualificacoes*.zip
```

Comando:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py init --reset --estrategia snapshot-atual
```

Limitacao: o banco tera a foto atual, mas pouco historico para inferir ex-socios e mudancas antigas.

### Estrategia Completa

Use quando voce quer processar tudo de todos os meses baixados.

Organizacao:

```text
dados-brutos/
  2026-03/
    Empresas*.zip
    Estabelecimentos*.zip
    Socios*.zip
    Simples*.zip
    Cnaes*.zip
    ...

  2026-04/
    Empresas*.zip
    Estabelecimentos*.zip
    Socios*.zip
    Simples*.zip
    Cnaes*.zip
    ...
```

Comando:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py init --reset --estrategia completo
```

Essa estrategia e a mais pesada. Ela so vale a pena se voce realmente tiver todos os snapshots completos e quiser processar tudo.

## Atualizacao Mensal

Se o banco ja esta perfeito ate maio e saiu junho:

1. Crie a pasta:

```text
dados-brutos/2026-06/
```

2. Coloque o snapshot completo de junho dentro dela:

- `Empresas*.zip`
- `Estabelecimentos*.zip`
- `Socios*.zip`
- `Simples*.zip`
- `Cnaes*.zip`
- `Motivos*.zip`
- `Municipios*.zip`
- `Naturezas*.zip`
- `Paises*.zip`
- `Qualificacoes*.zip`

3. Rode:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py atualizar --mes 2026-06
```

Se junho for a pasta mais recente em `dados-brutos`, tambem pode rodar:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py atualizar
```

4. Confira:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py status
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py validar
```

## Validar O Banco Atual

Para checar se o `backend/cnpj.db` atual esta pronto para uso:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py validarf
```

O esperado e terminar com:

```text
Resultado: OK
```

Se aparecer `FALHOU`, leia as linhas acima. Exemplos comuns:

- `fts_empresa FALHOU`: a busca por empresa por nome pode retornar errado ou vazio.
- `fts_socio FALHOU`: a busca por socio por nome pode ficar lenta ou quebrar.
- `indice ... FALHOU`: alguma consulta pode ficar lenta.

Para ver quais meses ja foram processados:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py status
```

## Corrigir Banco Atual Sem Recriar Tudo

Se o banco ja existe, mas a validacao aponta FTS ou indices faltando, prefira reparar busca/indices sem reprocessar os ZIPs:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/tools/reparar_busca.py
```

Esse script:

- cria indices de busca faltantes;
- recria `fts_empresa` se ela nao existir ou estiver vazia;
- recria `fts_socio` se ela nao existir ou estiver vazia;
- valida o resultado.

Para forcar recriacao das duas FTS:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/tools/reparar_busca.py --force-fts
```

Para forcar apenas empresa:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/tools/reparar_busca.py --force-fts-empresa
```

Para forcar apenas socio:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/tools/reparar_busca.py --force-fts-socio
```

Outra opcao, mais pesada, e reprocessar o ultimo mes ja carregado com `--force`.

Exemplo, se o banco esta ate `2026-05`:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py atualizar --mes 2026-05 --force
```

Isso reprocessa o snapshot completo daquele mes, recria indices/FTS ao final e roda validacao. Use quando voce quer reconstruir tambem os dados daquele mes, nao apenas reparar busca.

Se voce quer testar o fluxo sem recriar FTS, use:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py atualizar --mes 2026-05 --force --sem-fts
```

Mas antes de usar as buscas do sistema, rode novamente sem `--sem-fts`.

## Outros Comandos

Retomar uma carga inicial interrompida, sem apagar tabelas:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py init
```

Reprocessar um mes ja concluido:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py atualizar --mes 2026-06 --force
```

Pular FTS em teste rapido:

```powershell
.\backend\venv\Scripts\python.exe backend/scripts/carga/carga.py atualizar --mes 2026-06 --sem-fts
```

Antes de usar as buscas do sistema, rode uma carga sem `--sem-fts` ou ajuste a FTS.

## O Que Cada Carga Faz

Para cada mes processado, o script:

1. Cria tabelas temporarias por ZIP.
2. Le os CSVs em chunks.
3. Faz UPSERT em `empresa`, `estabelecimento` e/ou `socio`.
4. Recarrega `simples` e dominios quando os ZIPs existem naquele mes.
5. Atualiza `tb_processamento_mensal`.
6. Recria indices secundarios quando necessario.
7. Recria `fts_empresa` e `fts_socio` ao final, exceto se usar `--sem-fts`.
8. Valida tabelas, indices e FTS.

## Observacoes Importantes

- CPF/CNPJ de socio pessoa fisica vem mascarado pela Receita, por exemplo `***240659**`.
- A tabela `socio` precisa preservar historico suficiente para inferir vinculos ativos, ex-socios e mudancas de qualificacao.
- `empresa`, `estabelecimento`, `simples` e dominios representam a foto atual do ultimo mes completo processado.
- A criacao das FTS pode demorar bastante em banco grande.
- O comando `validar` deve retornar OK antes de considerar o banco pronto para uso.

## Busca No Sistema

A tela de busca funciona como autocomplete em tempo real. Por isso, a listagem inicial precisa ser leve:

- busca de empresa por nome usa `fts_empresa`;
- busca de socio por nome usa `fts_socio`;
- busca de socio por CPF aceita CPF completo ou os 6 digitos visiveis do CPF mascarado;
- a lista de socios nao calcula contadores pesados de empresas ativas/inaptas/anteriores;
- os detalhes completos aparecem quando o usuario abre o perfil do socio.

Se o total aparecer como "Mais de 10.000 resultados", isso e intencional: a busca rapida evita contar todos os resultados em nomes muito comuns para manter a interface responsiva.
