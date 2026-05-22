import re
import unicodedata
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import text

from models import Empresa, Estabelecimento, Socio, Simples
from database import is_postgres


SITUACAO = {"01": "Nula", "02": "Ativa", "03": "Suspensa", "04": "Inapta", "08": "Baixada"}
PORTE = {"00": "Não informado", "01": "Micro Empresa", "03": "Empresa de Pequeno Porte", "05": "Grande Porte"}
MATRIZ_FILIAL = {"1": "Matriz", "2": "Filial"}
FAIXA_ETARIA = {
    "0": "Não informada", "1": "0 a 12 anos",  "2": "13 a 20 anos",
    "3": "21 a 30 anos",  "4": "31 a 40 anos", "5": "41 a 50 anos",
    "6": "51 a 60 anos",  "7": "61 a 70 anos", "8": "71 a 80 anos",
    "9": "Mais de 80 anos",
}
IDENTIFICADOR_SOCIO = {"1": "Pessoa Jurídica", "2": "Pessoa Física", "3": "Estrangeiro"}

# Hierarquia de qualificações de sócios (RF): menor número = maior importância.
# Baseado na tabela oficial da Receita Federal + precedência societária brasileira.
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
    "48": 13,  # Sócio Residente/Domiciliado no Brasil
    "47": 14,  # Sócio PJ Domiciliado no Brasil
    "65": 15,  # Sócio PJ (variante)
    "67": 16,  # Sócio PJ (variante)
    "52": 17,  # Sócio com Capital
    "23": 18,  # Sócio Capitalista
    "50": 19,  # Sócio Participante
    "25": 20,  # Sócio Comanditário
    "17": 21,  # Procurador
    "37": 22,  # Sócio PJ Domiciliado no Exterior
    "38": 23,  # Sócio Residente no Exterior
    "21": 24,  # Sócio Aposentado
    "27": 25,  # Sócio Incapaz ou Relativamente Incapaz
    "28": 26,  # Sócio Menor (Assistido/Representado)
}

# ── Cache em memória ───────────────────────────────────────────────────────────
# Tabelas de lookup são carregadas uma vez e nunca mais consultadas no disco.
_cache: dict = {
    "loaded": False,
    "qualificacao": {},   # cd -> ds
    "cnae":         {},   # cd -> ds
    "municipio":    {},   # cd -> nm
    "natureza":     {},   # cd -> ds
    "motivo":       {},   # cd -> ds
    "mes_atual":    None,
}


def _load_cache(db: Session) -> None:
    if _cache["loaded"]:
        return
    for row in db.execute(text("SELECT cd_qualificacao, ds_qualificacao FROM qualificacao")).fetchall():
        _cache["qualificacao"][row[0]] = row[1]
    for row in db.execute(text("SELECT cd_cnae, ds_cnae FROM cnae")).fetchall():
        _cache["cnae"][row[0]] = row[1]
    for row in db.execute(text("SELECT cd_municipio, nm_municipio FROM municipio")).fetchall():
        _cache["municipio"][row[0]] = row[1]
    for row in db.execute(text("SELECT cd_naturezajuridica, ds_naturezajuridica FROM natureza")).fetchall():
        _cache["natureza"][row[0]] = row[1]
    for row in db.execute(text("SELECT cd_motivosituacaocadastral, ds_motivosituacaocadastral FROM motivo")).fetchall():
        _cache["motivo"][row[0]] = row[1]
    _cache["loaded"] = True


def _get_mes_atual(db: Session) -> str:
    if _cache["mes_atual"]:
        return _cache["mes_atual"]
    row = db.execute(
        text("SELECT MAX(dt_referencia) FROM tb_processamento_mensal WHERE status = 'CONCLUIDO'")
    ).scalar()
    _cache["mes_atual"] = row or "2026-04"
    return _cache["mes_atual"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_cnpj(basico: str, ordem: str, dv: str) -> tuple[str, str]:
    completo  = f"{basico}{ordem}{dv}"
    formatado = f"{basico[:2]}.{basico[2:5]}.{basico[5:8]}/{ordem}-{dv}"
    return completo, formatado


def _fmt_date(d: str | None) -> str | None:
    if not d or len(d) != 8 or d == "00000000":
        return None
    return f"{d[6:8]}/{d[4:6]}/{d[0:4]}"


def _fmt_mes(m: str | None) -> str | None:
    if not m or len(m) != 7:
        return m
    return f"{m[5:7]}/{m[0:4]}"


def _qual_desc(codigo: str | None) -> str | None:
    return _cache["qualificacao"].get(codigo) if codigo else None


def _next_month(mes: str) -> str:
    """'YYYY-MM' → 'MM/YYYY' do mês seguinte (data inferida de início do próximo cargo)."""
    year, month = int(mes[:4]), int(mes[5:7])
    month += 1
    if month > 12:
        month, year = 1, year + 1
    return f"{month:02d}/{year}"


def _normalizar(texto: str) -> str:
    """Remove acentos e converte para uppercase — usado na busca FTS5."""
    if not texto:
        return ""
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode("ascii").upper()


def _build_fts_match(nome_norm: str) -> str | None:
    """Constrói query FTS5: cada palavra >= 3 chars como AND implícito.
    Retorna None se nenhuma palavra atende ao mínimo do tokenizador trigram."""
    palavras = [p.replace('"', '""') for p in nome_norm.split() if len(p) >= 3]
    return " ".join(palavras) if palavras else None


def _parse_cnaes_secundarios(raw: str | None) -> list:
    if not raw or not raw.strip():
        return []
    return [
        {"codigo": cod, "descricao": _cache["cnae"].get(cod)}
        for cod in (c.strip() for c in raw.split(","))
        if cod
    ]


def _agrupar_socios(socios: list, mes_atual: str) -> tuple[list, list]:
    grupos: dict[tuple, list] = defaultdict(list)
    for s in socios:
        chave = (s.cd_cpfcnpjsocio or "", s.nm_nomesociorazaosocial or "")
        grupos[chave].append(s)

    ativos, inativos = [], []

    for (cpf, nome), registros in grupos.items():
        # Sort: mês mais recente primeiro; dentro do mesmo mês, cargo de maior hierarquia primeiro
        registros_ord = sorted(
            registros,
            key=lambda r: (r.dt_ultimaatualizacao or "", -QUALIFICACAO_RANK.get(r.cd_qualificacaosocio, 99)),
            reverse=True,
        )
        ativo = any(r.dt_ultimaatualizacao == mes_atual for r in registros_ord)

        # Deduplica snapshots mensais consecutivos com a mesma qualificação.
        # A RF republica o mesmo registro todo mês sem troca de cargo — isso não é histórico real.
        deduped = []
        for rec in registros_ord:
            if not deduped or deduped[-1].cd_qualificacaosocio != rec.cd_qualificacaosocio:
                deduped.append(rec)
        registros_ord = deduped
        n = len(registros_ord)

        # Inferir data de início de cada cargo:
        # - Cargo mais antigo (índice n-1 na lista DESC): data real de entrada na empresa
        # - Cargos mais recentes: mês seguinte ao fim do cargo anterior
        # Isso evita mostrar a data de entrada na empresa para todos os cargos
        start_dates = [None] * n
        start_dates[n - 1] = _fmt_date(registros_ord[n - 1].dt_dataentradasociedade)
        for i in range(n - 2, -1, -1):
            prev_ultima = registros_ord[i + 1].dt_ultimaatualizacao
            curr_ultima = registros_ord[i].dt_ultimaatualizacao
            if not prev_ultima:
                pass  # fica None
            elif prev_ultima == curr_ultima:
                # Troca de cargo dentro do mesmo ciclo mensal da RF
                start_dates[i] = _fmt_mes(curr_ultima)
            else:
                candidate = _next_month(prev_ultima)
                # Guard: se a data inferida for posterior ao último mês do próprio registro,
                # "desde" ficaria depois de "saiu em" — usa o mês real da última aparição.
                cand_ym = f"{candidate[3:7]}-{candidate[:2]}" if len(candidate) == 7 else ""
                if cand_ym > (curr_ultima or ""):
                    start_dates[i] = _fmt_mes(curr_ultima) if curr_ultima else None
                else:
                    start_dates[i] = candidate

        qualificacao_atual = None
        qualificacoes_anteriores = []

        for i, r in enumerate(registros_ord):
            is_current = r.dt_ultimaatualizacao == mes_atual
            item = {
                "codigo":       r.cd_qualificacaosocio,
                "descricao":    _qual_desc(r.cd_qualificacaosocio),
                "data_entrada": start_dates[i],
                "saiu_em":      None if is_current else _fmt_mes(r.dt_ultimaatualizacao),
            }
            if qualificacao_atual is None:
                qualificacao_atual = item
            else:
                qualificacoes_anteriores.append(item)

        ref = registros_ord[0]
        pessoa = {
            "nome_socio":               nome,
            "cpf_cnpj_socio":           cpf,
            "identificador":            IDENTIFICADOR_SOCIO.get(ref.cd_identificadorsocio, ref.cd_identificadorsocio),
            "faixa_etaria":             FAIXA_ETARIA.get(ref.cd_faixaetaria, ref.cd_faixaetaria),
            "ativo":                    ativo,
            "qualificacao_atual":       qualificacao_atual,
            "qualificacoes_anteriores": qualificacoes_anteriores,
        }
        (ativos if ativo else inativos).append(pessoa)

    def _rank(p: dict) -> int:
        qa = p.get("qualificacao_atual")
        return QUALIFICACAO_RANK.get(qa["codigo"] if qa else None, 99)

    ativos.sort(key=lambda p: (_rank(p), p["nome_socio"] or ""))
    inativos.sort(key=lambda p: (_rank(p), p["nome_socio"] or ""))
    return ativos, inativos


# ── Empresa por CNPJ ──────────────────────────────────────────────────────────

def get_empresa_by_cnpj(db: Session, cnpj: str) -> dict | None:
    _load_cache(db)
    mes_atual = _get_mes_atual(db)

    cnpj_clean = re.sub(r"\D", "", cnpj)
    if len(cnpj_clean) != 14:
        return None

    cnpj_basico = cnpj_clean[:8]
    cnpj_ordem  = cnpj_clean[8:12]

    estab = db.query(Estabelecimento).filter(
        Estabelecimento.cd_cnpjbasico == cnpj_basico,
        Estabelecimento.cd_cnpjordem  == cnpj_ordem,
    ).first()
    if not estab:
        return None

    empresa    = db.query(Empresa).filter(Empresa.cd_cnpjbasico == cnpj_basico).first()
    simples    = db.query(Simples).filter(Simples.cd_cnpjbasico == cnpj_basico).first()
    socios_raw = db.query(Socio).filter(Socio.cd_cnpjbasico == cnpj_basico).all()
    outros_estabs = (
        db.query(Estabelecimento)
        .filter(Estabelecimento.cd_cnpjbasico == cnpj_basico)
        .order_by(Estabelecimento.cd_cnpjordem)
        .all()
    )

    cnpj_completo, cnpj_formatado = _fmt_cnpj(cnpj_basico, estab.cd_cnpjordem, estab.cd_cnpjdv or "")

    socios_ativos, socios_inativos = _agrupar_socios(socios_raw, mes_atual)

    cd_nat  = empresa.cd_naturezajuridica if empresa else None
    cd_mot  = estab.cd_motivosituacaocadastral
    cd_qual = empresa.cd_qualificacaoresponsavel if empresa else None

    return {
        "cnpj_basico":                       cnpj_basico,
        "cnpj_completo":                     cnpj_completo,
        "cnpj_completo_formatado":           cnpj_formatado,
        "razao_social":                      empresa.nm_razaosocial if empresa else None,
        "nome_fantasia":                     estab.nm_nomefantasia or None,
        "natureza_juridica_codigo":          cd_nat,
        "natureza_juridica_descricao":       _cache["natureza"].get(cd_nat),
        "qualificacao_responsavel_codigo":   cd_qual,
        "qualificacao_responsavel_descricao": _qual_desc(cd_qual),
        "capital_social":                    empresa.vl_capitalsocial if empresa else None,
        "porte":                             PORTE.get(empresa.cd_porteempresa, empresa.cd_porteempresa) if empresa else None,
        "ente_federativo":                   empresa.nm_entefederativo if empresa else None,
        "situacao_cadastral":                SITUACAO.get(estab.cd_situacaocadastral, estab.cd_situacaocadastral),
        "data_situacao":                     _fmt_date(estab.dt_datasituacaocadastral),
        "motivo_situacao":                   _cache["motivo"].get(cd_mot, cd_mot),
        "situacao_especial":                 estab.nm_situacaoespecial or None,
        "data_situacao_especial":            _fmt_date(estab.dt_datasituacaoespecial),
        "data_inicio":                       _fmt_date(estab.dt_datainicioatividade),
        "matriz_filial":                     MATRIZ_FILIAL.get(estab.cd_identificadormatrizfilial, estab.cd_identificadormatrizfilial),
        "tipo_logradouro":                   estab.nm_tipologradouro,
        "logradouro":                        estab.nm_logradouro,
        "numero":                            estab.nm_numero,
        "complemento":                       estab.nm_complemento or None,
        "bairro":                            estab.nm_bairro,
        "cep":                               estab.cd_cep,
        "uf":                                estab.sg_uf,
        "municipio_codigo":                  estab.cd_municipio,
        "municipio_descricao":               _cache["municipio"].get(estab.cd_municipio),
        "ddd1":                              estab.cd_ddd1,
        "telefone1":                         estab.nr_telefone1,
        "ddd2":                              estab.cd_ddd2 or None,
        "telefone2":                         estab.nr_telefone2 or None,
        "email":                             estab.nm_email or None,
        "cnae_principal_codigo":             estab.cd_cnaefiscalprincipal,
        "cnae_principal_descricao":          _cache["cnae"].get(estab.cd_cnaefiscalprincipal),
        "cnae_secundarios":                  _parse_cnaes_secundarios(estab.ds_cnaefiscalsecundaria),
        "opcao_simples":                     simples.fl_opcaosimples if simples else None,
        "data_opcao_simples":                _fmt_date(simples.dt_dataopcaosimples) if simples else None,
        "data_exclusao_simples":             _fmt_date(simples.dt_dataexclusaosimples) if simples else None,
        "opcao_mei":                         simples.fl_opcaomei if simples else None,
        "data_opcao_mei":                    _fmt_date(simples.dt_dataopcaomei) if simples else None,
        "data_exclusao_mei":                 _fmt_date(simples.dt_dataexclusaomei) if simples else None,
        "socios_ativos":                     socios_ativos,
        "socios_inativos":                   socios_inativos,
        "filiais": [
            {
                "cnpj_completo":           _fmt_cnpj(cnpj_basico, f.cd_cnpjordem, f.cd_cnpjdv or "")[0],
                "cnpj_completo_formatado": _fmt_cnpj(cnpj_basico, f.cd_cnpjordem, f.cd_cnpjdv or "")[1],
                "nome_fantasia":           f.nm_nomefantasia or None,
                "tipo":                    MATRIZ_FILIAL.get(f.cd_identificadormatrizfilial, f.cd_identificadormatrizfilial),
                "situacao_cadastral":      SITUACAO.get(f.cd_situacaocadastral, f.cd_situacaocadastral),
                "data_inicio":             _fmt_date(f.dt_datainicioatividade),
                "uf":                      f.sg_uf,
                "municipio":               _cache["municipio"].get(f.cd_municipio),
                "cnae_principal_codigo":   f.cd_cnaefiscalprincipal,
                "cnae_principal_descricao": _cache["cnae"].get(f.cd_cnaefiscalprincipal),
                "atual":                   f.cd_cnpjordem == cnpj_ordem,
            }
            for f in outros_estabs
        ],
        "dt_primeira_carga":                 empresa.dt_primeiracarga if empresa else None,
        "dt_ultima_atualizacao":             empresa.dt_ultimaatualizacao if empresa else None,
    }


# ── Busca empresa por nome ────────────────────────────────────────────────────

def _fts_empresa_exists(db: Session) -> bool:
    return db.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='fts_empresa'"
    )).fetchone() is not None


def _fts_socio_exists(db: Session) -> bool:
    return db.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='fts_socio'"
    )).fetchone() is not None


def busca_empresa_nome(db: Session, nome: str, skip: int = 0, limit: int = 20, known_total: int = 0) -> dict:
    _load_cache(db)

    # ── 1. Detecção de CNPJ numérico (3–14 dígitos) ──────────────────────────
    # Só ativa se a entrada for exclusivamente dígitos e pontuação de CNPJ
    cnpj_digits = re.sub(r"\D", "", nome)
    if 3 <= len(cnpj_digits) <= 14 and re.match(r'^[\d.\-/\s]+$', nome.strip()):
        basico = cnpj_digits[:8]  # primeiros 8 dígitos = cd_cnpjbasico
        n_digits = len(cnpj_digits)
        if n_digits < 8:
            # Prefixo: busca todos os CNPJs básicos que começam com os dígitos
            order_sql = """
                ORDER BY CASE WHEN est.cd_situacaocadastral = '02' THEN 0 ELSE 1 END,
                         e.cd_cnpjbasico
                LIMIT :limit OFFSET :skip
            """
            where_sql = "WHERE e.cd_cnpjbasico LIKE :partial"
            params = {"partial": cnpj_digits + "%", "limit": limit, "skip": skip}
            count_params = {"partial": cnpj_digits + "%"}
            count_sql = "SELECT COUNT(*) FROM empresa WHERE cd_cnpjbasico LIKE :partial"
        else:
            # 8–14 dígitos: busca exata pelo CNPJ básico (primeiros 8)
            where_sql = "WHERE e.cd_cnpjbasico = :basico"
            order_sql = """
                ORDER BY CASE WHEN est.cd_situacaocadastral = '02' THEN 0 ELSE 1 END,
                         e.nm_razaosocial
                LIMIT :limit OFFSET :skip
            """
            params = {"basico": basico, "limit": limit, "skip": skip}
            count_params = {"basico": basico}
            count_sql = "SELECT COUNT(*) FROM empresa WHERE cd_cnpjbasico = :basico"

        rows = db.execute(text(f"""
            SELECT e.cd_cnpjbasico, e.nm_razaosocial,
                   est.cd_cnpjordem, est.cd_cnpjdv, est.nm_nomefantasia,
                   est.cd_situacaocadastral, est.sg_uf, est.cd_municipio
            FROM empresa e
            LEFT JOIN estabelecimento est
                ON e.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
            {where_sql}
            {order_sql}
        """), params).fetchall()
        total = db.execute(text(count_sql), count_params).scalar() or 0
        return {"total": total, "resultados": _empresa_rows_to_list(rows)}

    nome_norm = _normalizar(nome)
    match = _build_fts_match(nome_norm)

    if is_postgres():
        # PostgreSQL: ILIKE usa o índice GIN pg_trgm automaticamente
        termo = f"%{nome}%"
        total = db.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT 1
                FROM empresa e
                LEFT JOIN estabelecimento est
                    ON e.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
                WHERE e.nm_razaosocial ILIKE :termo
                   OR est.nm_nomefantasia ILIKE :termo
                LIMIT 10001
            ) t
        """), {"termo": termo}).scalar() or 0

        rows = db.execute(text("""
            SELECT e.cd_cnpjbasico, e.nm_razaosocial,
                   est.cd_cnpjordem, est.cd_cnpjdv, est.nm_nomefantasia,
                   est.cd_situacaocadastral, est.sg_uf, est.cd_municipio
            FROM empresa e
            LEFT JOIN estabelecimento est
                ON e.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
            WHERE e.nm_razaosocial ILIKE :termo
               OR est.nm_nomefantasia ILIKE :termo
            ORDER BY
                CASE
                    WHEN e.nm_razaosocial ILIKE :nome OR est.nm_nomefantasia ILIKE :nome                           THEN 0
                    WHEN e.nm_razaosocial ILIKE :nome || ' %' OR est.nm_nomefantasia ILIKE :nome || ' %'           THEN 1
                    WHEN e.nm_razaosocial ILIKE :nome || '%' OR est.nm_nomefantasia ILIKE :nome || '%'             THEN 2
                    ELSE 3
                END,
                CASE WHEN est.cd_situacaocadastral = '02' THEN 0 ELSE 1 END,
                e.nm_razaosocial
            LIMIT :limit OFFSET :skip
        """), {"termo": termo, "nome": nome, "limit": limit, "skip": skip}).fetchall()

    elif match is not None and _fts_empresa_exists(db):
        # SQLite: FTS5 trigram — tier exato/prefixo/contém + ativas primeiro
        if known_total > 0:
            total = known_total
        else:
            total = db.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT 1 FROM fts_empresa WHERE fts_empresa MATCH :match LIMIT 10001
                )
            """), {"match": match}).scalar() or 0

        rows = db.execute(text("""
            WITH fts AS (
                SELECT cd_cnpjbasico, nm_razaosocial, nm_nomefantasia,
                       cd_situacaocadastral, fl_matriz, rank AS fts_rank,
                       CASE
                           WHEN nm_razaosocial = :nome_norm
                             OR nm_nomefantasia = :nome_norm                                       THEN 0
                           WHEN nm_razaosocial LIKE :nome_norm || ' %'
                             OR nm_nomefantasia LIKE :nome_norm || ' %'                            THEN 1
                           WHEN nm_razaosocial LIKE :nome_norm || '%'
                             OR nm_nomefantasia LIKE :nome_norm || '%'                             THEN 2
                           ELSE 3
                       END AS tier
                FROM fts_empresa
                WHERE fts_empresa MATCH :match
                ORDER BY tier,
                         CASE WHEN cd_situacaocadastral = '02' THEN 0 ELSE 1 END,
                         CASE WHEN fl_matriz = '1' THEN 0 ELSE 1 END,
                         rank
                LIMIT :limit OFFSET :skip
            )
            SELECT fts.cd_cnpjbasico, e.nm_razaosocial,
                   est.cd_cnpjordem, est.cd_cnpjdv, est.nm_nomefantasia,
                   est.cd_situacaocadastral, est.sg_uf, est.cd_municipio
            FROM fts
            JOIN empresa e ON fts.cd_cnpjbasico = e.cd_cnpjbasico
            LEFT JOIN estabelecimento est
                ON fts.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
        """), {
            "match": match, "nome_norm": nome_norm, "limit": limit, "skip": skip,
        }).fetchall()

    else:
        # SQLite fallback lento (sem FTS5 ou termo muito curto)
        termo = f"%{nome.lower()}%"
        if known_total > 0:
            total = known_total
        else:
            total = db.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT 1
                    FROM empresa e
                    LEFT JOIN estabelecimento est
                        ON e.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
                    WHERE lower(e.nm_razaosocial) LIKE :termo
                       OR lower(est.nm_nomefantasia) LIKE :termo
                    LIMIT 10001
                )
            """), {"termo": termo}).scalar() or 0

        rows = db.execute(text("""
            SELECT e.cd_cnpjbasico, e.nm_razaosocial,
                   est.cd_cnpjordem, est.cd_cnpjdv, est.nm_nomefantasia,
                   est.cd_situacaocadastral, est.sg_uf, est.cd_municipio
            FROM empresa e
            LEFT JOIN estabelecimento est
                ON e.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
            WHERE lower(e.nm_razaosocial) LIKE :termo
               OR lower(est.nm_nomefantasia) LIKE :termo
            ORDER BY
                CASE
                    WHEN lower(e.nm_razaosocial) = lower(:nome)              THEN 0
                    WHEN lower(e.nm_razaosocial) LIKE lower(:nome) || ' %'   THEN 1
                    WHEN lower(e.nm_razaosocial) LIKE lower(:nome) || '%'    THEN 2
                    ELSE 3
                END,
                CASE WHEN est.cd_situacaocadastral = '02' THEN 0 ELSE 1 END,
                e.nm_razaosocial
            LIMIT :limit OFFSET :skip
        """), {"termo": termo, "nome": nome, "limit": limit, "skip": skip}).fetchall()

    return {"total": total, "resultados": _empresa_rows_to_list(rows)}


def _empresa_rows_to_list(rows) -> list:
    resultados = []
    for r in rows:
        cnpj_completo = cnpj_formatado = None
        if r.cd_cnpjordem and r.cd_cnpjdv:
            cnpj_completo, cnpj_formatado = _fmt_cnpj(r.cd_cnpjbasico, r.cd_cnpjordem, r.cd_cnpjdv)
        resultados.append({
            "cnpj_basico":             r.cd_cnpjbasico,
            "cnpj_completo":           cnpj_completo,
            "cnpj_completo_formatado": cnpj_formatado,
            "razao_social":            r.nm_razaosocial,
            "nome_fantasia":           r.nm_nomefantasia or None,
            "situacao_cadastral":      SITUACAO.get(r.cd_situacaocadastral, r.cd_situacaocadastral),
            "uf":                      r.sg_uf,
            "municipio_descricao":     _cache["municipio"].get(r.cd_municipio),
        })
    return resultados


# ── Busca sócio ───────────────────────────────────────────────────────────────

def _socio_pessoa_to_list(rows) -> list:
    return [
        {
            "nome_socio":     r.nm_nomesociorazaosocial,
            "cpf_cnpj_socio": r.cd_cpfcnpjsocio,
            "identificador":  IDENTIFICADOR_SOCIO.get(r.cd_identificadorsocio, r.cd_identificadorsocio),
            "faixa_etaria":   FAIXA_ETARIA.get(r.cd_faixaetaria, r.cd_faixaetaria),
            "n_ativas":       r.n_ativas,
            "n_inaptas":      r.n_inaptas,
            "n_ex":           r.n_ex,
        }
        for r in rows
    ]


# Grupo por pessoa (nome+cpf), faixa etária do registro mais recente via ROW_NUMBER.
# max_dt_empresa = última vez que a pessoa apareceu naquela empresa; se == mes_atual → ativa.
# Situação da empresa também conta: Baixada (08) e Nula (01) são ex mesmo no dump atual,
# pois a RF republica sócios dessas empresas todo mês sem que o vínculo seja real.
_SOCIO_PESSOA_SQL = """\
WITH filtered AS (
    SELECT nm_nomesociorazaosocial, cd_cpfcnpjsocio, cd_faixaetaria, cd_identificadorsocio,
           dt_ultimaatualizacao, cd_cnpjbasico
    FROM socio WHERE {where}
),
ranked AS (
    SELECT f.nm_nomesociorazaosocial, f.cd_cpfcnpjsocio, f.cd_faixaetaria, f.cd_identificadorsocio,
           f.dt_ultimaatualizacao, f.cd_cnpjbasico,
           est.cd_situacaocadastral,
           MAX(f.dt_ultimaatualizacao) OVER (PARTITION BY f.nm_nomesociorazaosocial, f.cd_cpfcnpjsocio,
                                             f.cd_cnpjbasico) AS max_dt_empresa,
           ROW_NUMBER() OVER (PARTITION BY f.nm_nomesociorazaosocial, f.cd_cpfcnpjsocio
                              ORDER BY f.dt_ultimaatualizacao DESC) AS rn
    FROM filtered f
    LEFT JOIN estabelecimento est
        ON f.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
)
SELECT nm_nomesociorazaosocial, cd_cpfcnpjsocio,
       MAX(CASE WHEN rn = 1 THEN cd_faixaetaria END)        AS cd_faixaetaria,
       MAX(CASE WHEN rn = 1 THEN cd_identificadorsocio END) AS cd_identificadorsocio,
       COUNT(DISTINCT CASE WHEN max_dt_empresa =  :mes_atual
                            AND COALESCE(cd_situacaocadastral,'01') NOT IN ('01','03','04','08') THEN cd_cnpjbasico END) AS n_ativas,
       COUNT(DISTINCT CASE WHEN max_dt_empresa =  :mes_atual
                            AND COALESCE(cd_situacaocadastral,'01') IN ('03','04') THEN cd_cnpjbasico END) AS n_inaptas,
       COUNT(DISTINCT CASE WHEN max_dt_empresa != :mes_atual
                             OR COALESCE(cd_situacaocadastral,'08') IN ('01','08') THEN cd_cnpjbasico END) AS n_ex
FROM ranked
GROUP BY nm_nomesociorazaosocial, cd_cpfcnpjsocio
{order}
LIMIT :limit OFFSET :skip\
"""


def busca_socio_nome(db: Session, nome: str, skip: int = 0, limit: int = 20, known_total: int = 0) -> dict:
    _load_cache(db)
    mes_atual = _get_mes_atual(db)
    nome_norm = _normalizar(nome)
    match = _build_fts_match(nome_norm)

    if is_postgres():
        termo = f"%{nome}%"
        if known_total > 0:
            total = known_total
        else:
            total = db.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT nm_nomesociorazaosocial, cd_cpfcnpjsocio
                    FROM socio WHERE nm_nomesociorazaosocial ILIKE :termo LIMIT 10001
                ) t
            """), {"termo": termo}).scalar() or 0
        order = """ORDER BY
                CASE WHEN nm_nomesociorazaosocial ILIKE :nome       THEN 0
                     WHEN nm_nomesociorazaosocial ILIKE :nome||' %' THEN 1
                     WHEN nm_nomesociorazaosocial ILIKE :nome||'%'  THEN 2
                     ELSE 3 END, nm_nomesociorazaosocial"""
        rows = db.execute(text(_SOCIO_PESSOA_SQL.format(
            where="nm_nomesociorazaosocial ILIKE :termo", order=order)),
            {"termo": termo, "nome": nome, "mes_atual": mes_atual, "limit": limit, "skip": skip}).fetchall()

    elif match is not None and _fts_socio_exists(db):
        if known_total > 0:
            total = known_total
        else:
            total = db.execute(text("""
                WITH fts AS (SELECT rowid_ref FROM fts_socio WHERE fts_socio MATCH :match LIMIT 100000)
                SELECT COUNT(DISTINCT s.nm_nomesociorazaosocial || '|' || COALESCE(s.cd_cpfcnpjsocio,''))
                FROM socio s JOIN fts ON s.id = fts.rowid_ref
            """), {"match": match}).scalar() or 0
        first_word = next((w for w in nome_norm.split() if len(w) >= 3), nome_norm)

        # ── Phase 1: página de pessoas únicas com ranking ─────────────────
        # O LIMIT 50000 aqui serve apenas para encontrar QUEM aparece na página —
        # não precisa ser exato. As contagens de empresas são calculadas na Phase 2.
        page_persons = db.execute(text("""
            WITH prefix_raw AS (
                SELECT nm_nomesociorazaosocial, cd_cpfcnpjsocio,
                       cd_faixaetaria, cd_identificadorsocio,
                       CASE
                           WHEN nm_nomesociorazaosocial = :nome_norm             THEN 0
                           WHEN nm_nomesociorazaosocial LIKE :nome_norm || ' %'  THEN 1
                           WHEN nm_nomesociorazaosocial LIKE :nome_norm || '%'   THEN 2
                           WHEN nm_nomesociorazaosocial LIKE :first_word || ' %' THEN 3
                           ELSE 4
                       END AS tier
                FROM socio
                WHERE nm_nomesociorazaosocial LIKE :first_word || '%'
                LIMIT 50000
            ),
            prefix AS (
                SELECT nm_nomesociorazaosocial, cd_cpfcnpjsocio,
                       MAX(cd_faixaetaria)        AS cd_faixaetaria,
                       MAX(cd_identificadorsocio) AS cd_identificadorsocio,
                       MIN(tier) AS tier
                FROM prefix_raw
                GROUP BY nm_nomesociorazaosocial, cd_cpfcnpjsocio
            ),
            fts_raw AS (
                SELECT rowid_ref FROM fts_socio WHERE fts_socio MATCH :match LIMIT 3000
            ),
            fts_other AS (
                SELECT s.nm_nomesociorazaosocial, s.cd_cpfcnpjsocio,
                       MAX(s.cd_faixaetaria)        AS cd_faixaetaria,
                       MAX(s.cd_identificadorsocio) AS cd_identificadorsocio,
                       5 AS tier
                FROM socio s JOIN fts_raw f ON s.id = f.rowid_ref
                WHERE s.nm_nomesociorazaosocial NOT LIKE :first_word || '%'
                GROUP BY s.nm_nomesociorazaosocial, s.cd_cpfcnpjsocio
            ),
            all_persons AS (
                SELECT * FROM prefix
                UNION ALL
                SELECT * FROM fts_other
            )
            SELECT nm_nomesociorazaosocial, cd_cpfcnpjsocio,
                   MAX(cd_faixaetaria)        AS cd_faixaetaria,
                   MAX(cd_identificadorsocio) AS cd_identificadorsocio,
                   MIN(tier) AS best_tier
            FROM all_persons
            GROUP BY nm_nomesociorazaosocial, cd_cpfcnpjsocio
            ORDER BY best_tier, nm_nomesociorazaosocial
            LIMIT :limit OFFSET :skip
        """), {"match": match, "nome_norm": nome_norm, "first_word": first_word,
               "limit": limit, "skip": skip}).fetchall()

        if not page_persons:
            return {"total": total, "resultados": []}

        # ── Phase 2: contagens EXATAS para as pessoas da página ───────────
        # Lookup por (nome, cpf) exato — sem LIMIT, sem truncamento de histórico.
        bind2: dict = {"mes_atual": mes_atual}
        val_parts: list = []
        for i, r in enumerate(page_persons):
            bind2[f"n{i}"] = r.nm_nomesociorazaosocial
            bind2[f"c{i}"] = r.cd_cpfcnpjsocio
            val_parts.append(f"(:n{i}, :c{i})")

        count_rows = db.execute(text(f"""
            WITH persons(nome, cpf) AS (VALUES {", ".join(val_parts)}),
            empresa_data AS (
                SELECT s.nm_nomesociorazaosocial AS nome,
                       s.cd_cpfcnpjsocio        AS cpf,
                       s.cd_cnpjbasico,
                       MAX(s.dt_ultimaatualizacao)   AS max_dt,
                       MAX(est.cd_situacaocadastral) AS situacao
                FROM socio s
                JOIN persons p
                    ON s.nm_nomesociorazaosocial = p.nome
                   AND s.cd_cpfcnpjsocio IS p.cpf
                LEFT JOIN estabelecimento est
                    ON s.cd_cnpjbasico = est.cd_cnpjbasico
                   AND est.cd_cnpjordem = '0001'
                GROUP BY s.nm_nomesociorazaosocial, s.cd_cpfcnpjsocio, s.cd_cnpjbasico
            )
            SELECT nome, cpf,
                   COUNT(DISTINCT CASE WHEN max_dt =  :mes_atual
                                        AND COALESCE(situacao,'01') NOT IN ('01','03','04','08')
                                        THEN cd_cnpjbasico END) AS n_ativas,
                   COUNT(DISTINCT CASE WHEN max_dt =  :mes_atual
                                        AND COALESCE(situacao,'01') IN ('03','04')
                                        THEN cd_cnpjbasico END) AS n_inaptas,
                   COUNT(DISTINCT CASE WHEN max_dt != :mes_atual
                                        OR  COALESCE(situacao,'08') IN ('01','08')
                                        THEN cd_cnpjbasico END) AS n_ex
            FROM empresa_data
            GROUP BY nome, cpf
        """), bind2).fetchall()

        counts_map = {(r.nome, r.cpf): r for r in count_rows}
        rows_result = []
        for p in page_persons:
            c = counts_map.get((p.nm_nomesociorazaosocial, p.cd_cpfcnpjsocio))
            rows_result.append({
                "nome_socio":     p.nm_nomesociorazaosocial,
                "cpf_cnpj_socio": p.cd_cpfcnpjsocio,
                "identificador":  IDENTIFICADOR_SOCIO.get(p.cd_identificadorsocio, p.cd_identificadorsocio),
                "faixa_etaria":   FAIXA_ETARIA.get(p.cd_faixaetaria, p.cd_faixaetaria),
                "n_ativas":  c.n_ativas  if c else 0,
                "n_inaptas": c.n_inaptas if c else 0,
                "n_ex":      c.n_ex      if c else 0,
            })
        return {"total": total, "resultados": rows_result}

    else:
        termo = f"%{nome.lower()}%"
        if known_total > 0:
            total = known_total
        else:
            total = db.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT nm_nomesociorazaosocial, cd_cpfcnpjsocio
                    FROM socio WHERE lower(nm_nomesociorazaosocial) LIKE :termo LIMIT 10001
                )
            """), {"termo": termo}).scalar() or 0
        order = """ORDER BY
                CASE WHEN lower(nm_nomesociorazaosocial) = lower(:nome)            THEN 0
                     WHEN lower(nm_nomesociorazaosocial) LIKE lower(:nome)||' %'   THEN 1
                     WHEN lower(nm_nomesociorazaosocial) LIKE lower(:nome)||'%'    THEN 2
                     ELSE 3 END, nm_nomesociorazaosocial"""
        rows = db.execute(text(_SOCIO_PESSOA_SQL.format(
            where="lower(nm_nomesociorazaosocial) LIKE :termo", order=order)),
            {"termo": termo, "nome": nome, "mes_atual": mes_atual, "limit": limit, "skip": skip}).fetchall()

    return {"total": total, "resultados": _socio_pessoa_to_list(rows)}


def busca_socio_cpf(db: Session, cpf: str, skip: int = 0, limit: int = 20, known_total: int = 0) -> dict:
    _load_cache(db)
    mes_atual = _get_mes_atual(db)
    cpf_clean = re.sub(r"\D", "", cpf)
    like_op = "ILIKE" if is_postgres() else "LIKE"

    termo1 = f"%{cpf_clean}%"
    cpf_sem3 = cpf_clean[3:] if len(cpf_clean) > 3 else cpf_clean
    termo2 = f"%{cpf_sem3}%"
    where = f"(cd_cpfcnpjsocio {like_op} :t1 OR cd_cpfcnpjsocio {like_op} :t2)"

    if known_total > 0:
        total = known_total
    else:
        total = db.execute(text(f"""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT nm_nomesociorazaosocial, cd_cpfcnpjsocio
                FROM socio WHERE {where} LIMIT 10001
            ) t
        """), {"t1": termo1, "t2": termo2}).scalar() or 0

    rows = db.execute(text(_SOCIO_PESSOA_SQL.format(
        where=f"(cd_cpfcnpjsocio {like_op} :t1 OR cd_cpfcnpjsocio {like_op} :t2)",
        order="ORDER BY nm_nomesociorazaosocial")),
        {"t1": termo1, "t2": termo2, "mes_atual": mes_atual, "limit": limit, "skip": skip}).fetchall()

    return {"total": total, "resultados": _socio_pessoa_to_list(rows)}


# ── Perfil completo de sócio ──────────────────────────────────────────────────

def get_perfil_socio(db: Session, cpf: str | None = None, nome: str | None = None) -> dict | None:
    _load_cache(db)
    mes_atual = _get_mes_atual(db)
    like_op = "ILIKE" if is_postgres() else "LIKE"

    # Chave forte: nome+cpf sempre que ambos disponíveis — impede mistura de homônimos.
    nome_exact = None
    if cpf and nome:
        cpf_clean  = re.sub(r"\D", "", cpf)
        nome_exact = nome.upper()
        find_where   = (f"s.nm_nomesociorazaosocial = :nome_exact "
                        f"AND s.cd_cpfcnpjsocio {like_op} :person_id")
        person_where = find_where
        person_id  = f"%{cpf_clean}%"
        person_id2 = person_id
    elif cpf:
        cpf_clean  = re.sub(r"\D", "", cpf)
        cpf_sem3   = cpf_clean[3:] if len(cpf_clean) > 3 else cpf_clean
        find_where   = (f"(s.cd_cpfcnpjsocio {like_op} :person_id "
                        f"OR s.cd_cpfcnpjsocio {like_op} :person_id2)")
        person_where = f"s.cd_cpfcnpjsocio {like_op} :person_id"
        person_id  = f"%{cpf_clean}%"
        person_id2 = f"%{cpf_sem3}%"
    else:
        find_where   = "s.nm_nomesociorazaosocial = :person_id"
        person_where = find_where
        person_id  = (nome or "").upper()
        person_id2 = person_id

    _bind = {"person_id": person_id, "person_id2": person_id2}
    if nome_exact:
        _bind["nome_exact"] = nome_exact

    # ── 1. Todos os registros desta pessoa ────────────────────────────────
    socios_raw = db.execute(text(f"""
        SELECT s.cd_cnpjbasico, s.cd_qualificacaosocio, s.dt_dataentradasociedade,
               s.cd_identificadorsocio, s.cd_faixaetaria, s.dt_ultimaatualizacao,
               s.nm_nomesociorazaosocial, s.cd_cpfcnpjsocio,
               e.nm_razaosocial, e.vl_capitalsocial, e.cd_porteempresa,
               est.cd_cnpjordem, est.cd_cnpjdv, est.cd_situacaocadastral,
               est.dt_datasituacaocadastral,
               est.sg_uf, est.cd_municipio, est.cd_cnaefiscalprincipal,
               est.ds_cnaefiscalsecundaria
        FROM socio s
        LEFT JOIN empresa e ON s.cd_cnpjbasico = e.cd_cnpjbasico
        LEFT JOIN estabelecimento est
            ON s.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
        WHERE {find_where}
        ORDER BY s.dt_ultimaatualizacao DESC
        LIMIT 500
    """), _bind).fetchall()

    if not socios_raw:
        return None

    r0 = socios_raw[0]
    info = {
        "nome":         r0.nm_nomesociorazaosocial,
        "cpf":          r0.cd_cpfcnpjsocio,
        "tipo":         IDENTIFICADOR_SOCIO.get(r0.cd_identificadorsocio, "—"),
        "faixa_etaria": FAIXA_ETARIA.get(r0.cd_faixaetaria) if r0.cd_faixaetaria else None,
    }

    # ── 2. Ativas vs inativas ─────────────────────────────────────────────
    # A RF republica sócios de empresas encerradas todo mês, então dt_ultimaatualizacao == mes_atual
    # não é suficiente. Baixada (08) e Nula (01) = empresa encerrada = ex-sócio.
    # Suspensa (03) e Inapta (04) ainda existem legalmente → sócio continua ativo.
    _ENCERRADAS = {'01', '08'}
    cnpjs_ativos   = {r.cd_cnpjbasico for r in socios_raw
                      if r.dt_ultimaatualizacao == mes_atual
                      and r.cd_situacaocadastral not in _ENCERRADAS}
    cnpjs_inativos = {r.cd_cnpjbasico for r in socios_raw if r.cd_cnpjbasico not in cnpjs_ativos}

    # ── 3. Cards de empresa ───────────────────────────────────────────────
    empresa_records: dict = {}
    for r in socios_raw:
        empresa_records.setdefault(r.cd_cnpjbasico, []).append(r)

    def _build_card(cnpj, records, is_ativo):
        recs = sorted(records, key=lambda x: x.dt_ultimaatualizacao or "", reverse=True)
        latest = recs[0]
        quals = []
        for rec in recs:
            desc = _qual_desc(rec.cd_qualificacaosocio) or rec.cd_qualificacaosocio
            if desc and desc not in quals:
                quals.append(desc)
        try:
            capital = float((latest.vl_capitalsocial or "0").replace(",", "."))
        except Exception:
            capital = 0.0
        cnpj_fmt = None
        if latest.cd_cnpjordem and latest.cd_cnpjdv:
            _, cnpj_fmt = _fmt_cnpj(cnpj, latest.cd_cnpjordem, latest.cd_cnpjdv)

        dt_sit = latest.dt_datasituacaocadastral or ""
        dt_ent = recs[-1].dt_dataentradasociedade or ""
        if is_ativo:
            saiu_em = None
        elif latest.cd_situacaocadastral in ('01', '08'):
            # Só usa a data de fechamento se for cronologicamente posterior à entrada.
            # Se for anterior, é inconsistência da RF (QSA atualizado após o fechamento).
            saiu_em = _fmt_date(dt_sit) if dt_sit and (not dt_ent or dt_sit >= dt_ent) else None
        else:
            saiu_em = _fmt_mes(recs[0].dt_ultimaatualizacao)

        return {
            "cnpj_basico":              cnpj,
            "cnpj_completo_formatado":  cnpj_fmt,
            "razao_social":             latest.nm_razaosocial,
            "situacao_cadastral":       SITUACAO.get(latest.cd_situacaocadastral, latest.cd_situacaocadastral),
            "ativo":                    is_ativo,
            "qualificacoes":            quals,
            "data_entrada":             _fmt_date(recs[-1].dt_dataentradasociedade),
            "saiu_em":                  saiu_em,
            "capital_social":           capital,
            "porte":                    PORTE.get(latest.cd_porteempresa, "Não informado"),
            "uf":                       latest.sg_uf,
            "municipio":                _cache["municipio"].get(latest.cd_municipio, latest.cd_municipio),
            "cnae_principal_codigo":    latest.cd_cnaefiscalprincipal,
            "cnae_principal_descricao": _cache["cnae"].get(latest.cd_cnaefiscalprincipal),
            "cnaes_secundarios_raw":    latest.ds_cnaefiscalsecundaria or "",
        }

    empresas_ativas   = sorted([_build_card(c, empresa_records[c], True)  for c in cnpjs_ativos],
                                key=lambda x: x["razao_social"] or "")
    empresas_inativas = sorted([_build_card(c, empresa_records[c], False) for c in cnpjs_inativos],
                                key=lambda x: x["razao_social"] or "")

    # ── 4. Porte / capital acumulado ──────────────────────────────────────
    capital_total: float = sum(e["capital_social"] for e in empresas_ativas)
    por_porte: dict = {}
    for e in empresas_ativas:
        por_porte[e["porte"]] = por_porte.get(e["porte"], 0) + 1

    # ── 5. CNAEs ─────────────────────────────────────────────────────────
    cnae_princ: dict = {}
    for e in empresas_ativas:
        cod = e["cnae_principal_codigo"]
        if cod:
            cnae_princ[cod] = cnae_princ.get(cod, 0) + 1

    cnaes_principais = sorted(
        [{"codigo": k, "descricao": _cache["cnae"].get(k), "count": v} for k, v in cnae_princ.items()],
        key=lambda x: -x["count"]
    )[:20]

    cnae_sec: dict = {}
    for e in empresas_ativas:
        for cod in e["cnaes_secundarios_raw"].split(","):
            cod = cod.strip()
            if cod and cod not in cnae_princ:
                cnae_sec[cod] = cnae_sec.get(cod, 0) + 1

    cnaes_secundarios = sorted(
        [{"codigo": k, "descricao": _cache["cnae"].get(k), "count": v} for k, v in cnae_sec.items()],
        key=lambda x: -x["count"]
    )[:20]

    # ── 6. Qualificações próprias ─────────────────────────────────────────
    qual_count: dict = {}
    for r in socios_raw:
        desc = _qual_desc(r.cd_qualificacaosocio) or r.cd_qualificacaosocio or "—"
        qual_count[desc] = qual_count.get(desc, 0) + 1
    qualificacoes_proprias = sorted(
        [{"descricao": k, "count": v} for k, v in qual_count.items()],
        key=lambda x: -x["count"]
    )

    def _socios_rede(cnpjs_set, extra_where=""):
        if not cnpjs_set:
            return []
        # cd_cnpjbasico é sempre 8 dígitos numéricos — interpolação segura
        in_clause = ",".join(f"'{c}'" for c in cnpjs_set)
        rede_bind = {"person_id": person_id, "mes_atual": mes_atual}
        if nome_exact:
            rede_bind["nome_exact"] = nome_exact
        rows = db.execute(text(f"""
            SELECT s.nm_nomesociorazaosocial, s.cd_cpfcnpjsocio,
                   COUNT(DISTINCT s.cd_cnpjbasico) AS n_comuns,
                   GROUP_CONCAT(DISTINCT s.cd_qualificacaosocio) AS quals
            FROM socio s
            WHERE s.cd_cnpjbasico IN ({in_clause})
              AND NOT ({person_where})
              {extra_where}
            GROUP BY s.nm_nomesociorazaosocial, s.cd_cpfcnpjsocio
            ORDER BY n_comuns DESC, s.nm_nomesociorazaosocial
            LIMIT 100
        """), rede_bind).fetchall()
        result = []
        for row in rows:
            quals = []
            for q in (row.quals or "").split(","):
                desc = _qual_desc(q.strip()) or q.strip()
                if desc and desc not in quals:
                    quals.append(desc)
            result.append({
                "nome": row.nm_nomesociorazaosocial,
                "cpf":  row.cd_cpfcnpjsocio,
                "empresas_em_comum": row.n_comuns,
                "qualificacoes": quals,
            })
        return result

    socios_comuns    = _socios_rede(cnpjs_ativos,   "AND s.dt_ultimaatualizacao = :mes_atual")
    ex_socios_comuns = _socios_rede(cnpjs_inativos)

    return {
        "info":                   info,
        "empresas_ativas":        empresas_ativas,
        "empresas_inativas":      empresas_inativas,
        "socios_comuns":          socios_comuns,
        "ex_socios_comuns":       ex_socios_comuns,
        "qualificacoes_proprias": qualificacoes_proprias,
        "cnaes_principais":       cnaes_principais,
        "cnaes_secundarios":      cnaes_secundarios,
        "porte_acumulado": {
            "capital_total": capital_total,
            "por_porte":     por_porte,
        },
    }
