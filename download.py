#!/usr/bin/env python3
"""
download.py — Download automático da base CNPJ (Casa dos Dados).

Uso:
    py -3.12 download.py                   # baixa todos os meses que faltam
    py -3.12 download.py --mes 2026-04     # baixa apenas um mês específico
    py -3.12 download.py --ultimo          # baixa apenas o mês mais recente
    py -3.12 download.py --listar          # mostra meses disponíveis no site

Dependências:
    py -3.12 -m pip install requests tqdm
"""

import re
import sys
import argparse
from pathlib import Path

# Garante UTF-8 no terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("Instale as dependências: py -3.12 -m pip install requests tqdm")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_URL     = "https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos/"
DADOS_BRUTOS = Path(__file__).parent / "dados-brutos"

# Padrões dos arquivos mensais (Empresas0-9, Estabelecimentos0-9, Socios0-9)
PADROES_MENSAIS = [
    re.compile(r"^Empresas\d+\.zip$",          re.IGNORECASE),
    re.compile(r"^Estabelecimentos\d+\.zip$",  re.IGNORECASE),
    re.compile(r"^Socios\d+\.zip$",            re.IGNORECASE),
]

# Padrões dos arquivos de apoio — só para o mês mais recente
PADROES_DOMINIO = [
    re.compile(r"^Simples.*\.zip$",       re.IGNORECASE),
    re.compile(r"^Cnaes.*\.zip$",         re.IGNORECASE),
    re.compile(r"^Motivos.*\.zip$",       re.IGNORECASE),
    re.compile(r"^Municipios.*\.zip$",    re.IGNORECASE),
    re.compile(r"^Naturezas.*\.zip$",     re.IGNORECASE),
    re.compile(r"^Paises.*\.zip$",        re.IGNORECASE),
    re.compile(r"^Qualificacoes.*\.zip$", re.IGNORECASE),
]

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "Mozilla/5.0 (compatible; cnpj-downloader/1.0)"

# ---------------------------------------------------------------------------
# Funções de descoberta
# ---------------------------------------------------------------------------

def listar_meses_site() -> dict[str, str]:
    """Retorna {YYYY-MM: url_pasta} de todos os meses disponíveis no site."""
    print(f"Consultando {BASE_URL} ...")
    r = SESSION.get(BASE_URL, timeout=30)
    r.raise_for_status()

    # Pastas com formato YYYY-MM-DD/
    links = re.findall(r'href="(\d{4}-\d{2}-\d{2}/?)"', r.text)
    meses: dict[str, str] = {}
    for link in sorted(links):
        mes = link[:7]                         # "2026-04-12/" → "2026-04"
        url = BASE_URL + link.rstrip("/") + "/"
        meses[mes] = url                       # última publicação do mês ganha
    return meses


def listar_arquivos_pasta(url_pasta: str) -> dict[str, str]:
    """Retorna {nome_arquivo: url_completa} de todos os ZIPs na pasta do site."""
    r = SESSION.get(url_pasta, timeout=30)
    r.raise_for_status()
    links = re.findall(r'href="([^"?#/]+\.zip)"', r.text, re.IGNORECASE)
    return {nome: url_pasta + nome for nome in links}


def _tamanho_remoto(url: str) -> int | None:
    try:
        r = SESSION.head(url, timeout=15, allow_redirects=True)
        v = int(r.headers.get("content-length", 0))
        return v if v > 0 else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Download com retomada
# ---------------------------------------------------------------------------

def baixar_arquivo(url: str, destino: Path) -> bool:
    """
    Baixa um arquivo para `destino`.
    Pula se já existir com o mesmo tamanho do servidor.
    Retorna True se baixou, False se pulou.
    """
    tamanho = _tamanho_remoto(url)

    if destino.exists() and tamanho:
        local = destino.stat().st_size
        if local == tamanho:
            print(f"    ✓ {destino.name}  (já completo, {tamanho/1e9:.2f} GB)")
            return False
        print(f"    ↻ {destino.name}  (local {local/1e9:.2f} GB ≠ remoto {tamanho/1e9:.2f} GB — re-baixando)")

    desc = f"    ↓ {destino.name}"
    if tamanho:
        desc += f"  ({tamanho/1e9:.2f} GB)"

    with SESSION.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(destino, "wb") as f, tqdm(
            total=tamanho,
            unit="B", unit_scale=True, unit_divisor=1024,
            desc=desc, leave=True, ncols=90,
        ) as bar:
            for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1 MB
                f.write(chunk)
                bar.update(len(chunk))
    return True


# ---------------------------------------------------------------------------
# Carga de um mês
# ---------------------------------------------------------------------------

def _filtrar(arquivos_site: dict[str, str], padroes: list) -> dict[str, str]:
    """Retorna apenas os arquivos cujo nome bate com algum dos padrões."""
    return {
        nome: url
        for nome, url in arquivos_site.items()
        if any(p.match(nome) for p in padroes)
    }


def baixar_mes(mes: str, url_pasta: str, incluir_dominio: bool = False):
    pasta_local = DADOS_BRUTOS / mes
    pasta_local.mkdir(parents=True, exist_ok=True)

    print(f"\n{'-'*60}")
    print(f"  Mes: {mes}  ->  {url_pasta}")

    try:
        arquivos_site = listar_arquivos_pasta(url_pasta)
    except Exception as e:
        print(f"  ERRO ao listar pasta: {e}")
        return

    alvos = _filtrar(arquivos_site, PADROES_MENSAIS)
    if incluir_dominio:
        alvos.update(_filtrar(arquivos_site, PADROES_DOMINIO))

    esperados = 30 + (7 if incluir_dominio else 0)
    print(f"  {len(arquivos_site)} ZIPs no site | {len(alvos)} selecionados | esperado: {esperados}")

    if len(alvos) < esperados:
        faltam = esperados - len(alvos)
        print(f"  AVISO: {faltam} arquivo(s) não encontrado(s) para este mês no site.")

    baixados = 0
    for nome in sorted(alvos):
        try:
            if baixar_arquivo(alvos[nome], pasta_local / nome):
                baixados += 1
        except Exception as e:
            print(f"  ERRO ao baixar {nome}: {e}")

    print(f"  {baixados} arquivo(s) baixado(s), {len(alvos)-baixados} já existiam.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download da base CNPJ — Casa dos Dados")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mes",    metavar="YYYY-MM", help="Baixa apenas este mês")
    group.add_argument("--ultimo", action="store_true", help="Baixa apenas o mês mais recente")
    group.add_argument("--listar", action="store_true", help="Lista meses disponíveis e sai")
    parser.add_argument("--sim",   action="store_true", help="Confirma download sem perguntar")
    args = parser.parse_args()

    try:
        meses_site = listar_meses_site()
    except Exception as e:
        print(f"ERRO ao acessar o site: {e}")
        sys.exit(1)

    if not meses_site:
        print("Nenhum mês encontrado no site. Verifique a URL ou a conexão.")
        sys.exit(1)

    if args.listar:
        print(f"\n{len(meses_site)} meses disponíveis no site:\n")
        for mes, url in sorted(meses_site.items()):
            pasta_local = DADOS_BRUTOS / mes
            zips_locais = len(list(pasta_local.glob("*.zip"))) if pasta_local.exists() else 0
            status = f"{zips_locais:2d} ZIPs locais" if zips_locais else "vazio"
            print(f"  {mes}  {status}")
        return

    mes_mais_recente = max(meses_site)

    if args.mes:
        if args.mes not in meses_site:
            print(f"Mês '{args.mes}' não encontrado no site.")
            print(f"Disponíveis: {', '.join(sorted(meses_site))}")
            sys.exit(1)
        incluir_dominio = (args.mes == mes_mais_recente)
        baixar_mes(args.mes, meses_site[args.mes], incluir_dominio)

    elif args.ultimo:
        print(f"Mês mais recente: {mes_mais_recente}")
        baixar_mes(mes_mais_recente, meses_site[mes_mais_recente], incluir_dominio=True)

    else:
        # Baixa todos os meses que faltam (têm pasta local mas não têm 30 ZIPs)
        faltam = []
        for mes, url in sorted(meses_site.items()):
            pasta_local = DADOS_BRUTOS / mes
            esperados = 37 if mes == mes_mais_recente else 30
            zips_locais = len(list(pasta_local.glob("*.zip"))) if pasta_local.exists() else 0
            if zips_locais < esperados:
                faltam.append((mes, url))

        if not faltam:
            print("Todos os meses já estão completos.")
            return

        print(f"\n{len(faltam)} mês(es) a baixar (do total de {len(meses_site)} disponíveis):\n")
        for mes, _ in faltam:
            pasta_local = DADOS_BRUTOS / mes
            zips = len(list(pasta_local.glob("*.zip"))) if pasta_local.exists() else 0
            esperados = 37 if mes == mes_mais_recente else 30
            print(f"  {mes}  ({zips}/{esperados} ZIPs)")

        if not args.sim:
            resp = input("\nConfirmar download? [s/N] ").strip().lower()
            if resp != "s":
                print("Cancelado.")
                return

        for mes, url in faltam:
            incluir_dominio = (mes == mes_mais_recente)
            baixar_mes(mes, url, incluir_dominio)

    print("\nDownload concluído.")


if __name__ == "__main__":
    main()
