import { useState, useEffect } from "react";
import { buscarPerfilSocio } from "../api";

// ─── Helpers ──────────────────────────────────────────────────────────────────
const MESES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];
function fmtMes(ym) {
  if (!ym) return "—";
  const [y, m] = ym.split("-");
  return `${MESES[parseInt(m, 10) - 1]}/${y}`;
}

function iniciais(nome) {
  if (!nome) return "?";
  const parts = nome.trim().split(/\s+/);
  return (parts.length >= 2 ? parts[0][0] + parts[1][0] : parts[0].slice(0, 2)).toUpperCase();
}

const fmtCapital = (v) =>
  v > 0
    ? v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 })
    : "—";

// ─── StatusBadge ──────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    Ativa:    { bg: "#ecfdf5", color: "#15803d", border: "#bbf7d0" },
    Baixada:  { bg: "#fef2f2", color: "#b91c1c", border: "#fecaca" },
    Suspensa: { bg: "#fef3c7", color: "#b45309", border: "#fde68a" },
    Inapta:   { bg: "#fef2f2", color: "#b91c1c", border: "#fecaca" },
  };
  const s = map[status] || { bg: "#f1f5f9", color: "#475569", border: "#e2e8f0" };
  return (
    <span
      className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full"
      style={{ background: s.bg, color: s.color, border: `1px solid ${s.border}` }}
    >
      {status || "—"}
    </span>
  );
}

// ─── QualChip ─────────────────────────────────────────────────────────────────
function QualChip({ label }) {
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium"
      style={{ background: "#eef4f9", color: "#0a5494", border: "1px solid #bfdbfe" }}
    >
      {label}
    </span>
  );
}

// ─── Campo (KV simples) ───────────────────────────────────────────────────────
function Campo({ label, valor, mono }) {
  if (!valor) return null;
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.1em] mb-1" style={{ color: "#94a3b8" }}>
        {label}
      </p>
      <p
        className="text-[14px] font-medium"
        style={{ color: "#0f172a", fontFamily: mono ? "'JetBrains Mono', monospace" : undefined }}
      >
        {valor}
      </p>
    </div>
  );
}

// ─── Secao (card container) ──────────────────────────────────────────────────
function Secao({ titulo, icone, children, acao }) {
  return (
    <div
      className="bg-white rounded-xl overflow-hidden"
      style={{ border: "1px solid #e2e8f0", boxShadow: "0 2px 8px rgba(15,23,42,0.04)" }}
    >
      <div
        className="px-5 py-3.5 flex justify-between items-center border-b"
        style={{ background: "#f8fafc", borderColor: "#e2e8f0" }}
      >
        <h3 className="text-[13px] font-semibold flex items-center gap-2" style={{ color: "#0f172a" }}>
          <span className="material-symbols-outlined text-[17px]" style={{ color: "#0085ca" }}>{icone}</span>
          {titulo}
        </h3>
        {acao}
      </div>
      {children}
    </div>
  );
}

// ─── EmpresaTable ─────────────────────────────────────────────────────────────
function EmpresaTable({ empresas, onVerEmpresa, showSaiu = false }) {
  if (!empresas.length) return (
    <p className="p-5 text-[13px]" style={{ color: "#94a3b8" }}>Nenhuma empresa encontrada.</p>
  );
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
            <th className="text-[10px] font-semibold uppercase tracking-[0.1em] p-3 pl-5" style={{ color: "#94a3b8" }}>Empresa</th>
            <th className="text-[10px] font-semibold uppercase tracking-[0.1em] p-3" style={{ color: "#94a3b8" }}>Qualificação</th>
            <th className="text-[10px] font-semibold uppercase tracking-[0.1em] p-3" style={{ color: "#94a3b8" }}>Porte</th>
            <th className="text-[10px] font-semibold uppercase tracking-[0.1em] p-3" style={{ color: "#94a3b8" }}>
              {showSaiu ? "Período" : "Entrada"}
            </th>
            <th className="p-3 pr-5 w-12" />
          </tr>
        </thead>
        <tbody>
          {empresas.map((e, i) => (
            <tr
              key={e.cnpj_basico || i}
              className="border-b transition-colors"
              style={{ borderColor: "#f1f5f9" }}
              onMouseEnter={ev => ev.currentTarget.style.background = "#f8fafc"}
              onMouseLeave={ev => ev.currentTarget.style.background = ""}
            >
              <td className="p-3 pl-5 align-top">
                <div className="text-[13px] font-semibold" style={{ color: "#0f172a" }}>
                  {e.razao_social || e.cnpj_basico}
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-[12px]" style={{ color: "#64748b" }}>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                    {e.cnpj_completo_formatado || e.cnpj_basico}
                  </span>
                  {e.situacao_cadastral && <StatusBadge status={e.situacao_cadastral} />}
                  {e.uf && <span>{e.uf}</span>}
                </div>
              </td>
              <td className="p-3 align-top">
                <div className="flex flex-wrap gap-1">
                  {(e.qualificacoes || []).slice(0, 2).map((q, j) => (
                    <QualChip key={j} label={q} />
                  ))}
                  {(e.qualificacoes || []).length > 2 && (
                    <span className="text-[11px]" style={{ color: "#94a3b8" }}>+{e.qualificacoes.length - 2}</span>
                  )}
                </div>
              </td>
              <td className="p-3 align-top text-[12px]" style={{ color: "#64748b" }}>{e.porte}</td>
              <td className="p-3 align-top text-[12px]">
                {showSaiu ? (
                  <div className="flex flex-col gap-0.5">
                    {e.data_entrada && (
                      <span className="flex items-center gap-1" style={{ color: "#15803d" }}>
                        <span className="material-symbols-outlined text-[13px]">login</span>
                        {e.data_entrada}
                      </span>
                    )}
                    {e.saiu_em && (
                      <span className="flex items-center gap-1" style={{ color: "#ef4444" }}>
                        <span className="material-symbols-outlined text-[13px]">logout</span>
                        {e.saiu_em}
                      </span>
                    )}
                  </div>
                ) : (
                  e.data_entrada && (
                    <span className="flex items-center gap-1" style={{ color: "#15803d" }}>
                      <span className="material-symbols-outlined text-[13px]">login</span>
                      {e.data_entrada}
                    </span>
                  )
                )}
              </td>
              <td className="p-3 pr-5 align-middle">
                <button
                  onClick={() => onVerEmpresa && onVerEmpresa(
                    e.cnpj_completo_formatado
                      ? e.cnpj_completo_formatado.replace(/\D/g, "")
                      : e.cnpj_basico + "000100"
                  )}
                  className="text-[12px] font-semibold hover:underline"
                  style={{ color: "#0085ca" }}
                >
                  Ver
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── SocioTable ───────────────────────────────────────────────────────────────
function SocioTable({ socios, onVerSocio }) {
  if (!socios.length) return (
    <p className="p-5 text-[13px]" style={{ color: "#94a3b8" }}>Nenhum sócio encontrado.</p>
  );
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
            <th className="text-[10px] font-semibold uppercase tracking-[0.1em] p-3 pl-5" style={{ color: "#94a3b8" }}>Nome</th>
            <th className="text-[10px] font-semibold uppercase tracking-[0.1em] p-3" style={{ color: "#94a3b8" }}>Qualificações</th>
            <th className="text-[10px] font-semibold uppercase tracking-[0.1em] p-3" style={{ color: "#94a3b8" }}>Empresas em comum</th>
            <th className="p-3 pr-5 w-12" />
          </tr>
        </thead>
        <tbody>
          {socios.map((s, i) => (
            <tr
              key={i}
              className="border-b transition-colors"
              style={{ borderColor: "#f1f5f9" }}
              onMouseEnter={ev => ev.currentTarget.style.background = "#f8fafc"}
              onMouseLeave={ev => ev.currentTarget.style.background = ""}
            >
              <td className="p-3 pl-5 align-top">
                <div className="text-[13px] font-semibold" style={{ color: "#0f172a" }}>{s.nome}</div>
                <div className="text-[12px] mt-0.5" style={{ color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
                  {s.cpf}
                </div>
              </td>
              <td className="p-3 align-top">
                <div className="flex flex-wrap gap-1">
                  {(s.qualificacoes || []).slice(0, 2).map((q, j) => (
                    <QualChip key={j} label={q} />
                  ))}
                  {(s.qualificacoes || []).length > 2 && (
                    <span className="text-[11px]" style={{ color: "#94a3b8" }}>+{s.qualificacoes.length - 2}</span>
                  )}
                </div>
              </td>
              <td className="p-3 align-middle">
                <span
                  className="inline-flex items-center justify-center w-7 h-7 rounded-full font-bold text-sm"
                  style={{ background: "#eef4f9", color: "#0085ca" }}
                >
                  {s.empresas_em_comum}
                </span>
              </td>
              <td className="p-3 pr-5 align-middle">
                {onVerSocio && (
                  <button
                    onClick={() => onVerSocio({ nome_socio: s.nome, cpf_cnpj_socio: s.cpf })}
                    className="text-[12px] font-semibold hover:underline"
                    style={{ color: "#0085ca" }}
                  >
                    Ver
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── ResultadoSocio ───────────────────────────────────────────────────────────
export default function ResultadoSocio({ socioInicial, onVoltar, onVerEmpresa, onVerSocio }) {
  const [perfil, setPerfil]         = useState(null);
  const [loading, setLoading]       = useState(true);
  const [erro, setErro]             = useState(null);
  const [exInativos, setExInativos] = useState(false);
  const [exSocios, setExSocios]     = useState(false);

  const cpf  = socioInicial?.cpf_cnpj_socio || "";
  const nome = socioInicial?.nome_socio || "";

  useEffect(() => {
    let cancelled = false;
    async function carregar() {
      setLoading(true);
      setErro(null);
      try {
        const res = await buscarPerfilSocio(nome ? null : (cpf || null), nome || null);
        if (cancelled) return;
        if (!res) { setErro("Perfil não encontrado."); return; }
        setPerfil(res);
      } catch (err) {
        if (cancelled) return;
        setErro(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    carregar();
    return () => { cancelled = true; };
  }, [cpf, nome]);

  const info      = perfil?.info || {};
  const porte     = perfil?.porte_acumulado || {};
  const nAtivo    = perfil?.empresas_ativas?.length || 0;
  const nInativo  = perfil?.empresas_inativas?.length || 0;
  const nSocios   = perfil?.socios_comuns?.length || 0;
  const nExSocios = perfil?.ex_socios_comuns?.length || 0;

  return (
    <main className="flex-1 md:ml-64 bg-[#f7f9fc] min-h-screen">

      {/* Sticky header */}
      <header
        className="sticky top-0 z-30 flex items-center justify-between px-8 h-14 bg-white/90 backdrop-blur-md border-b"
        style={{ borderColor: "#e2e8f0" }}
      >
        <button
          onClick={onVoltar}
          className="flex items-center gap-2 text-[13px] font-medium transition-colors"
          style={{ color: "#64748b" }}
          onMouseEnter={e => e.currentTarget.style.color = "#0085ca"}
          onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
        >
          <span className="material-symbols-outlined text-[17px]">arrow_back</span>
          Voltar à busca
        </button>
        {info.cpf && (
          <div className="text-[12px]" style={{ color: "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>
            {info.cpf}
          </div>
        )}
      </header>

      <div className="p-4 md:p-10 max-w-[1400px] mx-auto space-y-6">

        {/* Loading */}
        {loading && !perfil && (
          <div className="flex items-center justify-center py-32">
            <span className="material-symbols-outlined text-[32px] animate-spin" style={{ color: "#94a3b8" }}>
              progress_activity
            </span>
          </div>
        )}

        {/* Erro */}
        {erro && (
          <div
            className="flex items-center gap-3 px-5 py-3 rounded-xl text-[13px] font-medium"
            style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#b91c1c" }}
          >
            <span className="material-symbols-outlined text-[18px]">error</span>
            {erro}
          </div>
        )}

        {perfil && (
          <>
            {/* Hero */}
            <div
              className="bg-white rounded-xl px-8 py-6"
              style={{ border: "1px solid #e2e8f0", boxShadow: "0 2px 8px rgba(15,23,42,0.04)" }}
            >
              <div className="flex items-start gap-5">
                {/* Avatar navy */}
                <div
                  className="w-14 h-14 rounded-xl flex items-center justify-center shrink-0 text-white font-bold text-xl select-none"
                  style={{ background: "#0a1f3d", fontFamily: "'Inter Tight', Inter, sans-serif" }}
                >
                  {iniciais(info.nome || nome)}
                </div>

                {/* Nome e meta */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1" style={{ color: "#94a3b8", fontSize: 12 }}>
                    {info.cpf && (
                      <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>{info.cpf}</span>
                    )}
                    {info.tipo && info.tipo !== "Pessoa Física" && (
                      <><span>·</span><span>{info.tipo}</span></>
                    )}
                    {info.faixa_etaria && info.faixa_etaria !== "Não informada" && (
                      <><span>·</span><span>{info.faixa_etaria}</span></>
                    )}
                  </div>
                  <h1
                    className="text-[26px] font-semibold leading-tight tracking-tight"
                    style={{ fontFamily: "'Inter Tight', Inter, sans-serif", color: "#0f172a" }}
                  >
                    {info.nome || nome || "—"}
                  </h1>
                  <p className="text-[14px] mt-0.5" style={{ color: "#64748b" }}>
                    Análise de Vínculos Societários
                  </p>
                </div>
              </div>

              {/* Barra de métricas */}
              <div
                className="grid grid-cols-2 md:grid-cols-4 gap-0 mt-6 pt-5 border-t"
                style={{ borderColor: "#e2e8f0" }}
              >
                {[
                  { label: "Empresas ativas",   val: String(nAtivo),   sub: null },
                  { label: "Ex-vínculos",        val: String(nInativo), sub: null },
                  { label: "Sócios em comum",   val: String(nSocios),  sub: nExSocios > 0 ? `+ ${nExSocios} ex` : null },
                  { label: "Capital acumulado", val: fmtCapital(porte.capital_total), sub: null },
                ].map((cell, i) => (
                  <div
                    key={i}
                    className="px-5 py-3 border-l first:border-l-0"
                    style={{ borderColor: "#e2e8f0" }}
                  >
                    <div className="text-[10px] font-semibold uppercase tracking-[0.1em] mb-1" style={{ color: "#94a3b8" }}>
                      {cell.label}
                    </div>
                    <div className="text-[15px] font-semibold" style={{ color: "#0f172a", fontFamily: "'JetBrains Mono', monospace" }}>
                      {cell.val}
                      {cell.sub && (
                        <span className="ml-2 text-[12px] font-normal" style={{ color: "#94a3b8" }}>{cell.sub}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Grid principal */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* Coluna principal (2/3) */}
              <div className="lg:col-span-2 space-y-6">

                {/* Empresas Ativas */}
                <Secao titulo={`Empresas Ativas (${nAtivo})`} icone="verified">
                  <EmpresaTable empresas={perfil.empresas_ativas || []} onVerEmpresa={onVerEmpresa} />
                </Secao>

                {/* Sócios em Comum */}
                <Secao titulo={`Sócios em Comum (${nSocios})`} icone="group">
                  <SocioTable socios={perfil.socios_comuns || []} onVerSocio={onVerSocio} />
                </Secao>

                {/* Ex-Empresas (collapsível) */}
                {nInativo > 0 && (
                  <div
                    className="bg-white rounded-xl overflow-hidden"
                    style={{ border: "1px solid #e2e8f0", boxShadow: "0 2px 8px rgba(15,23,42,0.04)" }}
                  >
                    <button
                      onClick={() => setExInativos(v => !v)}
                      className="w-full px-5 py-3.5 flex justify-between items-center border-b transition-colors"
                      style={{ background: "#f8fafc", borderColor: "#e2e8f0" }}
                      onMouseEnter={e => e.currentTarget.style.background = "#f1f5f9"}
                      onMouseLeave={e => e.currentTarget.style.background = "#f8fafc"}
                    >
                      <h3 className="text-[13px] font-semibold flex items-center gap-2" style={{ color: "#64748b" }}>
                        <span className="material-symbols-outlined text-[17px]" style={{ color: "#94a3b8" }}>history</span>
                        Ex-Empresas ({nInativo})
                      </h3>
                      <span className="material-symbols-outlined text-[17px]" style={{ color: "#94a3b8" }}>
                        {exInativos ? "expand_less" : "expand_more"}
                      </span>
                    </button>
                    {exInativos && (
                      <EmpresaTable empresas={perfil.empresas_inativas || []} onVerEmpresa={onVerEmpresa} showSaiu />
                    )}
                  </div>
                )}

                {/* Ex-Sócios em Comum (collapsível) */}
                {nExSocios > 0 && (
                  <div
                    className="bg-white rounded-xl overflow-hidden"
                    style={{ border: "1px solid #e2e8f0", boxShadow: "0 2px 8px rgba(15,23,42,0.04)" }}
                  >
                    <button
                      onClick={() => setExSocios(v => !v)}
                      className="w-full px-5 py-3.5 flex justify-between items-center border-b transition-colors"
                      style={{ background: "#f8fafc", borderColor: "#e2e8f0" }}
                      onMouseEnter={e => e.currentTarget.style.background = "#f1f5f9"}
                      onMouseLeave={e => e.currentTarget.style.background = "#f8fafc"}
                    >
                      <h3 className="text-[13px] font-semibold flex items-center gap-2" style={{ color: "#64748b" }}>
                        <span className="material-symbols-outlined text-[17px]" style={{ color: "#94a3b8" }}>group_off</span>
                        Ex-Sócios em Comum ({nExSocios})
                      </h3>
                      <span className="material-symbols-outlined text-[17px]" style={{ color: "#94a3b8" }}>
                        {exSocios ? "expand_less" : "expand_more"}
                      </span>
                    </button>
                    {exSocios && (
                      <SocioTable socios={perfil.ex_socios_comuns} onVerSocio={onVerSocio} />
                    )}
                  </div>
                )}

                {/* CNAEs */}
                {(perfil.cnaes_principais?.length > 0 || perfil.cnaes_secundarios?.length > 0) && (
                  <Secao titulo="CNAEs das Empresas" icone="category">
                    <div className="p-5 space-y-4">
                      {perfil.cnaes_principais?.length > 0 && (
                        <>
                          <p className="text-[10px] font-semibold uppercase tracking-[0.1em]" style={{ color: "#94a3b8" }}>
                            Principais
                          </p>
                          <div className="flex flex-col gap-2">
                            {perfil.cnaes_principais.map(({ codigo, descricao, count }) => (
                              <div key={codigo} className="flex items-start justify-between gap-2">
                                <div>
                                  <span className="text-[11px] mr-2" style={{ color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
                                    {codigo}
                                  </span>
                                  <span className="text-[13px]" style={{ color: "#0f172a" }}>{descricao || "—"}</span>
                                </div>
                                <span className="text-[11px] shrink-0" style={{ color: "#94a3b8" }}>{count}×</span>
                              </div>
                            ))}
                          </div>
                        </>
                      )}
                      {perfil.cnaes_secundarios?.length > 0 && (
                        <>
                          <p className="text-[10px] font-semibold uppercase tracking-[0.1em] mt-2" style={{ color: "#94a3b8" }}>
                            Secundários
                          </p>
                          <div className="flex flex-col gap-2">
                            {perfil.cnaes_secundarios.map(({ codigo, descricao, count }) => (
                              <div key={codigo} className="flex items-start justify-between gap-2">
                                <div>
                                  <span className="text-[11px] mr-2" style={{ color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
                                    {codigo}
                                  </span>
                                  <span className="text-[13px]" style={{ color: "#0f172a" }}>{descricao || "—"}</span>
                                </div>
                                <span className="text-[11px] shrink-0" style={{ color: "#94a3b8" }}>{count}×</span>
                              </div>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </Secao>
                )}
              </div>

              {/* Coluna lateral (1/3) */}
              <div className="space-y-6">

                {/* Identificação */}
                <Secao titulo="Identificação" icone="badge">
                  <div className="p-5 space-y-4">
                    <Campo label="Nome"        valor={info.nome} />
                    <Campo label="CPF/CNPJ"    valor={info.cpf} mono />
                    <Campo label="Tipo"         valor={info.tipo} />
                    <Campo label="Faixa Etária" valor={info.faixa_etaria !== "Não informada" ? info.faixa_etaria : null} />
                  </div>
                </Secao>

                {/* Resumo numérico */}
                <Secao titulo="Resumo" icone="analytics">
                  <div className="p-5 grid grid-cols-2 gap-5">
                    {[
                      { label: "Empresas ativas", value: nAtivo,    color: "#15803d" },
                      { label: "Ex-vínculos",     value: nInativo,  color: "#94a3b8" },
                      { label: "Sócios comuns",   value: nSocios,   color: "#0085ca" },
                      { label: "Ex-sócios comuns",value: nExSocios, color: "#94a3b8" },
                    ].map(({ label, value, color }) => (
                      <div key={label}>
                        <span className="text-3xl font-bold tracking-tight block" style={{ color, fontFamily: "'JetBrains Mono', monospace" }}>
                          {value}
                        </span>
                        <span className="text-[11px]" style={{ color: "#94a3b8" }}>{label}</span>
                      </div>
                    ))}
                  </div>
                </Secao>

                {/* Capital Acumulado */}
                <Secao titulo="Capital Acumulado" icone="account_balance">
                  <div className="p-5">
                    <div
                      className="text-[20px] font-bold mb-3"
                      style={{ color: "#0f172a", fontFamily: "'JetBrains Mono', monospace" }}
                    >
                      {fmtCapital(porte.capital_total)}
                    </div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.1em] mb-2" style={{ color: "#94a3b8" }}>
                      Por porte
                    </p>
                    <div className="flex flex-col gap-1.5">
                      {Object.entries(porte.por_porte || {}).map(([p, n]) => (
                        <div key={p} className="flex items-center justify-between text-[13px]">
                          <span style={{ color: "#64748b" }}>{p}</span>
                          <span className="font-medium" style={{ color: "#0f172a" }}>
                            {n} empresa{n !== 1 ? "s" : ""}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </Secao>

                {/* Qualificações Exercidas */}
                {perfil.qualificacoes_proprias?.length > 0 && (
                  <Secao titulo="Qualificações Exercidas" icone="military_tech">
                    <div className="p-5 flex flex-col gap-3">
                      {perfil.qualificacoes_proprias.map(({ descricao, count }) => (
                        <div key={descricao} className="flex items-center justify-between">
                          <QualChip label={descricao} />
                          <span className="text-[11px]" style={{ color: "#94a3b8" }}>{count}×</span>
                        </div>
                      ))}
                    </div>
                  </Secao>
                )}

                {/* Pythagoras · Histórico */}
                <div
                  className="rounded-xl overflow-hidden"
                  style={{ background: "#0a1f3d", border: "1px solid rgba(255,255,255,0.06)" }}
                >
                  <div className="px-5 py-4 border-b" style={{ borderColor: "rgba(255,255,255,0.07)" }}>
                    <div
                      className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em]"
                      style={{ color: "#4a6fa8" }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#0085ca" }} />
                      Pythagoras · Histórico
                    </div>
                    <div
                      className="text-[14px] font-semibold mt-1"
                      style={{ color: "#dee7f0", fontFamily: "'Inter Tight', Inter, sans-serif" }}
                    >
                      Vínculos rastreados
                    </div>
                  </div>
                  <div className="px-5 py-4 space-y-3">
                    {[
                      { key: "Empresas ativas",   val: String(nAtivo) },
                      { key: "Ex-vínculos",       val: String(nInativo), sub: `(${nAtivo + nInativo} total)` },
                      { key: "Sócios em comum",   val: String(nSocios) },
                      { key: "Capital acumulado", val: fmtCapital(porte.capital_total) },
                    ].map((row, i) => (
                      <div key={i} className="flex items-center justify-between text-[12px]">
                        <span style={{ color: "#4a6fa8" }}>{row.key}</span>
                        <span style={{ color: "#dee7f0", fontFamily: "'JetBrains Mono', monospace" }}>
                          {row.val}
                          {row.sub && <span className="ml-1.5" style={{ color: "#4a6fa8" }}>{row.sub}</span>}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
