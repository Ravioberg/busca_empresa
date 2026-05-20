#!/usr/bin/env python3
"""
sync_mensal.py — Detecta, baixa e processa novos meses da RF (casadosdados).

Uso:
    py -3.12 backend/sync_mensal.py           # detecta e processa meses novos
    py -3.12 backend/sync_mensal.py --dry-run # lista o que faria sem alterar nada

Seguro para agendador (Task Scheduler / cron):
    - Não faz nada se não há mês novo.
    - Não re-baixa ZIPs já existentes e íntegros.
    - Nunca carrega um mês já marcado como CONCLUIDO no banco.
    - Lock de arquivo previne execuções simultâneas.
    - Tudo registrado em sync_mensal.log.
"""

import os
import re
import sys
import time
import logging
import zipfile
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
BASE_DIR     = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# Resolve paths relativos a BASE_DIR (backend/) para ser consistente com carga.py,
# que sempre roda com cwd=backend/. Evita ambiguidade do diretório de trabalho.
_db_env      = os.getenv("DADOS_BRUTOS")
DADOS_BRUTOS = (BASE_DIR / _db_env).resolve() if _db_env \
               else (BASE_DIR / "../dados-brutos").resolve()

_raw_db_url  = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'cnpj.db'}")
if _raw_db_url.startswith("sqlite:///") and not os.path.isabs(_raw_db_url[len("sqlite:///"):]):
    # Path relativo em URL sqlite — resolve relativo a BASE_DIR
    _rel = _raw_db_url[len("sqlite:///"):]
    DATABASE_URL = f"sqlite:///{(BASE_DIR / _rel).resolve()}"
else:
    DATABASE_URL = _raw_db_url
CARGA_PY      = BASE_DIR / "carga.py"
LOG_FILE      = BASE_DIR / "sync_mensal.log"
LOCK_FILE     = BASE_DIR / "sync_mensal.lock"

SITE_URL      = "https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos/"

MAX_TENTATIVAS = 3
BACKOFF_BASE   = 5           # segundos: 5s → 10s → 20s
CHUNK_SIZE     = 4_194_304   # 4 MB por chunk de leitura
LOG_INTERVALO  = 30          # segundos entre logs de progresso durante download

# ---------------------------------------------------------------------------
# Logging — console (INFO) + arquivo (DEBUG)
# ---------------------------------------------------------------------------
def _setup_logging() -> logging.Logger:
    fmt     = "%(asctime)s  %(levelname)-7s  %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logger  = logging.getLogger("sync_mensal")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt))

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt, datefmt))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

log = _setup_logging()

# ---------------------------------------------------------------------------
# Lock — impede execuções simultâneas
# ---------------------------------------------------------------------------
def _adquirir_lock() -> bool:
    if LOCK_FILE.exists():
        age = time.time() - LOCK_FILE.stat().st_mtime
        if age < 86_400:   # lock com menos de 24h → processo provavelmente em execução
            return False
        log.warning("Lock antigo detectado (>24h) — removendo.")
        LOCK_FILE.unlink()
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True

def _liberar_lock() -> None:
    LOCK_FILE.unlink(missing_ok=True)

# ---------------------------------------------------------------------------
# HTTP — listagem do site
# ---------------------------------------------------------------------------
def _nova_sessao() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "CorpIntel-sync/1.0 (dados-abertos-rf)"
    return s


def _listar_pastas_site(session: requests.Session) -> list[str]:
    """Retorna pastas YYYY-MM-DD disponíveis no site, em ordem crescente."""
    resp = session.get(SITE_URL, timeout=30)
    resp.raise_for_status()
    # Apache directory listing: href="2026-05-10/"
    pastas = re.findall(r'href="(\d{4}-\d{2}-\d{2}/)"', resp.text)
    return sorted(p.rstrip("/") for p in pastas)


def _pastas_para_meses(pastas: list[str]) -> dict[str, str]:
    """
    Mapeia YYYY-MM → pasta YYYY-MM-DD mais recente do site.
    Caso haja mais de uma pasta por mês, mantém a mais recente.
    """
    meses: dict[str, str] = {}
    for pasta in sorted(pastas):
        meses[pasta[:7]] = pasta   # sobrescreve → fica a mais recente
    return meses


def _listar_zips_pasta(session: requests.Session, pasta_url: str) -> list[str]:
    """
    Lista nomes de .zip diretamente na pasta (sem subpastas como regime_tributario/).
    Subpastas têm href="nome/" (com barra), arquivos têm href="nome.zip" (sem barra).
    """
    resp = session.get(pasta_url, timeout=30)
    resp.raise_for_status()
    return re.findall(r'href="([^"/]+\.zip)"', resp.text)

# ---------------------------------------------------------------------------
# Download individual com retry, progresso em log e validação CRC
# ---------------------------------------------------------------------------
def _arquivo_ok(path: Path) -> bool:
    """True se o arquivo existe e tem tamanho > 0 (verificação rápida para skip)."""
    return path.exists() and path.stat().st_size > 0


def _preflight(session: requests.Session, pasta_url: str,
               zips: list[str], dest_dir: Path) -> list[str]:
    """
    HEAD em cada arquivo que ainda não existe localmente.
    Retorna lista dos que retornaram 404 (precisam ser baixados mas não estão disponíveis).
    Loga o resultado de cada verificação.
    """
    faltando = []
    for nome in zips:
        dest = dest_dir / nome
        if _arquivo_ok(dest):
            continue   # já baixado — não precisa checar
        url = pasta_url + nome
        try:
            r = session.head(url, timeout=15, allow_redirects=True)
            if r.status_code == 404:
                log.warning(f"  INDISPONIVEL  {nome}  (404 no servidor)")
                faltando.append(nome)
            elif r.status_code != 200:
                log.warning(f"  STATUS {r.status_code}  {nome}")
                faltando.append(nome)
            else:
                size = int(r.headers.get("Content-Length", 0))
                log.debug(f"  disponivel  {nome}  ({size/1e6:.0f} MB)")
        except Exception as exc:
            log.warning(f"  ERRO ao verificar {nome}: {exc}")
            faltando.append(nome)
    return faltando


def _download_zip(session: requests.Session, url: str, dest: Path) -> None:
    """
    Baixa url → dest com:
    - Arquivo .tmp intermediário (rename atômico só após validação)
    - Log de progresso a cada LOG_INTERVALO segundos
    - testzip() após download para garantir integridade CRC
    - Retry com backoff exponencial (BACKOFF_BASE * 2^(tentativa-1))
    Levanta RuntimeError se esgotar MAX_TENTATIVAS.
    """
    tmp = dest.with_suffix(".tmp")

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        tmp.unlink(missing_ok=True)
        try:
            log.info(f"  [{tentativa}/{MAX_TENTATIVAS}] Baixando {dest.name}...")
            with session.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                total   = int(r.headers.get("Content-Length", 0))
                baixado = 0
                t_log   = time.time()

                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        if not chunk:
                            continue
                        f.write(chunk)
                        baixado += len(chunk)
                        if time.time() - t_log >= LOG_INTERVALO:
                            if total:
                                log.info(f"    {dest.name}: "
                                         f"{baixado/total*100:.0f}%  "
                                         f"({baixado/1e9:.2f}/{total/1e9:.2f} GB)")
                            else:
                                log.info(f"    {dest.name}: {baixado/1e9:.2f} GB...")
                            t_log = time.time()

            log.debug(f"    Validando CRC: {dest.name}")
            with zipfile.ZipFile(tmp) as zf:
                primeiro_erro = zf.testzip()
            if primeiro_erro:
                raise ValueError(f"CRC inválido: {primeiro_erro}")

            tmp.rename(dest)
            log.info(f"  OK  {dest.name}  ({dest.stat().st_size/1e9:.2f} GB)")
            return

        except Exception as exc:
            log.warning(f"  Tentativa {tentativa}/{MAX_TENTATIVAS} falhou "
                        f"({dest.name}): {exc}")
            tmp.unlink(missing_ok=True)
            if tentativa < MAX_TENTATIVAS:
                espera = BACKOFF_BASE * (2 ** (tentativa - 1))   # 5s, 10s, 20s
                log.info(f"  Aguardando {espera}s antes de retentar...")
                time.sleep(espera)

    raise RuntimeError(f"Download falhou após {MAX_TENTATIVAS} tentativas: {url}")

# ---------------------------------------------------------------------------
# Banco — meses já concluídos (guarda principal contra dupla carga)
# ---------------------------------------------------------------------------
def _meses_concluidos(engine) -> set[str]:
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(
                "SELECT dt_referencia FROM tb_processamento_mensal "
                "WHERE status = 'CONCLUIDO'"
            )).fetchall()
            return {r[0] for r in rows}
        except Exception:
            return set()   # tabela ainda não existe — banco vazio, tudo é novo

# ---------------------------------------------------------------------------
# Atualizar MES_DOMINIOS em carga.py
# ---------------------------------------------------------------------------
def _mes_dominios_atual() -> str | None:
    txt = CARGA_PY.read_text(encoding="utf-8")
    m   = re.search(r'^MES_DOMINIOS\s*=\s*"(\d{4}-\d{2})"', txt, re.MULTILINE)
    return m.group(1) if m else None


def _atualizar_mes_dominios(novo_mes: str) -> None:
    atual = _mes_dominios_atual()
    if atual is None:
        log.warning("  MES_DOMINIOS não encontrado em carga.py — sem atualização.")
        return
    if novo_mes <= atual:
        log.info(f"  MES_DOMINIOS={atual} (sem alteração necessária).")
        return
    conteudo = CARGA_PY.read_text(encoding="utf-8")
    novo     = re.sub(
        r'^(MES_DOMINIOS\s*=\s*)"(\d{4}-\d{2})"',
        rf'\g<1>"{novo_mes}"',
        conteudo, count=1, flags=re.MULTILINE,
    )
    CARGA_PY.write_text(novo, encoding="utf-8")
    log.info(f"  MES_DOMINIOS atualizado: {atual} → {novo_mes}")

# ---------------------------------------------------------------------------
# Meses locais disponíveis (mesma lógica de _listar_meses_disponiveis em carga.py)
# ---------------------------------------------------------------------------
_PADRAO_MES = re.compile(r"^\d{4}-\d{2}$")

def _meses_locais() -> list[str]:
    if not DADOS_BRUTOS.exists():
        return []
    return sorted(
        p.name for p in DADOS_BRUTOS.iterdir()
        if p.is_dir() and _PADRAO_MES.match(p.name) and any(p.glob("Empresas*.zip"))
    )

# ---------------------------------------------------------------------------
# Lógica principal
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Sync mensal CNPJ — CorpIntel")
    parser.add_argument("--dry-run", action="store_true",
                        help="Lista o que faria sem baixar nem processar nada")
    args    = parser.parse_args()
    dry_run = args.dry_run

    if not dry_run:
        if not _adquirir_lock():
            log.warning("Outra instância em execução (lock ativo). Abortando.")
            sys.exit(0)   # exit 0 — sobreposição não é erro para o agendador

    try:
        _executar(dry_run)
    finally:
        if not dry_run:
            _liberar_lock()


def _executar(dry_run: bool) -> None:
    log.info("=" * 60)
    log.info(f"sync_mensal {'[DRY-RUN] ' if dry_run else ''}"
             f"início: {datetime.now():%Y-%m-%d %H:%M:%S}")
    log.info(f"dados-brutos : {DADOS_BRUTOS}")
    log.info(f"banco        : {DATABASE_URL}")
    log.info("=" * 60)

    if not DADOS_BRUTOS.exists():
        log.error(f"DADOS_BRUTOS não encontrado: {DADOS_BRUTOS}")
        sys.exit(1)

    # ── 1. Pastas disponíveis no site ────────────────────────────────────────
    session = _nova_sessao()
    log.info("Consultando casadosdados...")
    try:
        pastas   = _listar_pastas_site(session)
        mapa_mes = _pastas_para_meses(pastas)
    except Exception as exc:
        log.error(f"Falha ao acessar o site: {exc}")
        sys.exit(1)

    log.info(f"  Site: {len(mapa_mes)} meses disponíveis — "
             f"mais recente: {max(mapa_mes)}")

    # ── 2. Meses já CONCLUIDOS no banco — guarda principal ───────────────────
    sqlite_args = {"check_same_thread": False, "timeout": 30} \
                  if DATABASE_URL.startswith("sqlite") else {}
    engine     = create_engine(DATABASE_URL, connect_args=sqlite_args)
    concluidos = _meses_concluidos(engine)
    engine.dispose()
    log.info(f"  Banco: {len(concluidos)} mês(es) CONCLUIDO(s).")

    # ── 3. Meses novos = estão no site mas não no banco ──────────────────────
    novos = sorted(mes for mes in mapa_mes if mes not in concluidos)
    if not novos:
        log.info("Nenhum mês novo. Até a próxima verificação.")
        log.info("=" * 60)
        return

    log.info(f"  Novo(s) a processar: {', '.join(novos)}")

    # ── DRY-RUN: apenas lista, sem alterar nada ───────────────────────────────
    if dry_run:
        for mes in novos:
            pasta_url = SITE_URL + mapa_mes[mes] + "/"
            try:
                zips = _listar_zips_pasta(session, pasta_url)
            except Exception as exc:
                log.warning(f"  [{mes}] Erro ao listar arquivos: {exc}")
                continue
            dest_dir = DADOS_BRUTOS / mes
            dest_dir.mkdir(parents=True, exist_ok=True)
            log.info(f"  [{mes}]  pasta={mapa_mes[mes]}  {len(zips)} ZIP(s):")
            indisponiveis = _preflight(session, pasta_url, zips, dest_dir)
            for z in zips:
                dest = dest_dir / z
                if _arquivo_ok(dest):
                    status = "ok (skip)"
                elif z in indisponiveis:
                    status = "INDISPONIVEL"
                else:
                    status = "BAIXAR"
                log.info(f"    {status:<14} {z}")
            if indisponiveis:
                log.warning(f"  [{mes}] Mes bloqueado: {len(indisponiveis)} arquivo(s) indisponivel(is).")
        log.info("[dry-run] Nenhuma alteracao realizada.")
        log.info("=" * 60)
        return

    # ── 4. Download dos ZIPs ─────────────────────────────────────────────────
    falhas: list[str] = []
    meses_ok: list[str] = []

    for mes in novos:
        pasta_site = mapa_mes[mes]
        pasta_url  = SITE_URL + pasta_site + "/"
        dest_dir   = DADOS_BRUTOS / mes

        log.info(f"\n{'-'*50}")
        log.info(f"Verificando {mes}  (pasta site: {pasta_site})")

        try:
            zips = _listar_zips_pasta(session, pasta_url)
        except Exception as exc:
            log.error(f"  Erro ao listar arquivos de {pasta_site}: {exc}")
            falhas.append(mes)
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"  {len(zips)} arquivo(s) no site — verificando disponibilidade...")

        # Preflight: HEAD em tudo que falta antes de baixar qualquer coisa.
        # Se qualquer arquivo não estiver disponível, pula o mês inteiro.
        indisponiveis = _preflight(session, pasta_url, zips, dest_dir)
        if indisponiveis:
            log.warning(f"  [{mes}] {len(indisponiveis)} arquivo(s) indisponivel(is) "
                        f"no servidor: {', '.join(indisponiveis)}")
            log.warning(f"  [{mes}] Nenhum download iniciado. "
                        f"Voltara na proxima execucao.")
            continue   # exit 0 abaixo — não é erro, é retry

        # Todos disponíveis → baixa apenas o que ainda não existe localmente
        log.info(f"  Todos disponiveis — iniciando download...")
        mes_com_erro = False
        for nome_zip in zips:
            dest = dest_dir / nome_zip
            if _arquivo_ok(dest):
                log.info(f"  SKIP  {nome_zip}")
                continue
            try:
                _download_zip(session, pasta_url + nome_zip, dest)
            except RuntimeError as exc:
                log.error(f"  FALHA {nome_zip}: {exc}")
                mes_com_erro = True
                break

        if mes_com_erro:
            log.error(f"  [{mes}] Download interrompido por erro.")
            falhas.append(mes)
        else:
            log.info(f"  [{mes}] Download completo.")
            meses_ok.append(mes)

    # ── 5. Atualizar MES_DOMINIOS para o mês mais recente disponível ─────────
    locais = _meses_locais()
    if locais:
        log.info(f"\n{'-'*50}")
        _atualizar_mes_dominios(max(locais))

    # ── 6. Executar carga.py ─────────────────────────────────────────────────
    if meses_ok:
        log.info(f"\n{'-'*50}")
        log.info("Executando carga.py...")
        t0     = time.time()
        result = subprocess.run([sys.executable, str(CARGA_PY)], cwd=str(BASE_DIR))
        m, s   = divmod(int(time.time() - t0), 60)

        if result.returncode != 0:
            log.error(f"carga.py terminou com erro (codigo {result.returncode}) "
                      f"em {m}m {s}s")
            sys.exit(1)

        log.info(f"carga.py concluido em {m}m {s}s")

    # ── 7. Resumo e código de saída ───────────────────────────────────────────
    log.info(f"\n{'='*60}")
    if meses_ok:
        log.info(f"SUCESSO  — carregado(s): {', '.join(meses_ok)}")
    if falhas:
        log.error(f"FALHA    — erro de download: {', '.join(falhas)}")
    if not meses_ok and not falhas:
        log.info("Nenhum mes novo completo disponivel. Voltara na proxima execucao.")
    log.info("=" * 60)

    if falhas:
        sys.exit(1)   # erro real — agendador deve alertar
    # sem falhas → exit 0 (inclui caso em que arquivos ainda não foram publicados)


if __name__ == "__main__":
    main()
