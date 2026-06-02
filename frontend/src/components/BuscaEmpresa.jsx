import { useState, useEffect, useRef } from "react";
import { buscarEmpresaPorCnpj, buscarEmpresaPorNome } from "../api";

const LIMIT = 20;

function ehCnpj(v) {
  return v.replace(/\D/g, "").length === 14;
}

function validCNPJ(v) {
  const d = (v || "").replace(/\D/g, "");
  if (d.length !== 14) return false;
  if (/^(\d)\1+$/.test(d)) return false;
  const calc = (base) => {
    let sum = 0;
    const w = base.length === 12
      ? [5,4,3,2,9,8,7,6,5,4,3,2]
      : [6,5,4,3,2,9,8,7,6,5,4,3,2];
    for (let i = 0; i < base.length; i++) sum += parseInt(base[i], 10) * w[i];
    const r = sum % 11;
    return r < 2 ? 0 : 11 - r;
  };
  const d1 = calc(d.slice(0, 12));
  const d2 = calc(d.slice(0, 13));
  return d1 === parseInt(d[12], 10) && d2 === parseInt(d[13], 10);
}

function StatusChip({ status }) {
  const map = {
    Ativa: "bg-green-100 text-green-800 border-green-200",
    Baixada: "bg-red-100 text-red-800 border-red-200",
    Suspensa: "bg-yellow-100 text-yellow-800 border-yellow-200",
    Inapta: "bg-red-100 text-red-800 border-red-200",
  };
  const cls = map[status] || "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider border ${cls}`}>
      {status || "—"}
    </span>
  );
}

function lerRecentes() {
  try { return JSON.parse(localStorage.getItem("ci_recentes_empresa") || "[]"); }
  catch { return []; }
}

export default function BuscaEmpresa({ onSelecionarEmpresa, onVoltar }) {
  const [termo, setTermo] = useState("");
  const [lista, setLista] = useState(null);
  const [pagina, setPagina] = useState(0);
  const [ultimoTermo, setUltimoTermo] = useState("");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);
  // Recentes refletem cliques em perfil (gravados via App.jsx).
  const [recentes] = useState(lerRecentes);

  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  /* Busca ao digitar — debounce 400 ms, mínimo 3 caracteres */
  useEffect(() => {
    const t = termo.trim();
    if (t.length < 3) {
      setLista(null);
      setErro(null);
      return;
    }
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => executarBusca(t), 400);
    return () => clearTimeout(debounceRef.current);
  }, [termo]);

  async function executarBusca(t) {
    setErro(null);
    setLoading(true);
    try {
      if (ehCnpj(t)) {
        const res = await buscarEmpresaPorCnpj(t);
        if (res === null) return; // abortado
        if (!res) { setErro("CNPJ não encontrado na base."); return; }
        onSelecionarEmpresa(res);
      } else {
        const res = await buscarEmpresaPorNome(t, 0, LIMIT);
        if (res === null) return; // abortado
        setLista(res);
        setUltimoTermo(t);
        setPagina(0);
      }
    } catch (err) { setErro(err.message); }
    finally { setLoading(false); }
  }

  function buscar(e) {
    e?.preventDefault();
    const t = termo.trim();
    if (!t || t.length < 3) return;
    clearTimeout(debounceRef.current);
    executarBusca(t);
  }

  async function mudarPagina(nova) {
    setLoading(true);
    setErro(null);
    try {
      const res = await buscarEmpresaPorNome(ultimoTermo, nova, LIMIT, total);
      if (res === null) return;
      setLista(res);
      setPagina(nova);
    } catch (err) { setErro(err.message); }
    finally { setLoading(false); }
  }

  const total = lista?.total || 0;
  const totalPags = Math.ceil(total / LIMIT);

  const raw = termo.replace(/\D/g, "");
  const looksLikeCnpj = raw.length > 0 && /^[\d.\-/]+$/.test(termo.trim());
  const cnpjValidity = looksLikeCnpj
    ? (raw.length === 14 ? (validCNPJ(raw) ? "ok" : "bad") : "typing")
    : null;

  return (
    <main className="flex-1 md:ml-52 overflow-y-auto bg-[#f7f9fc] min-h-screen">
      {/* Header fixo */}
      <header className="sticky top-0 z-50 flex items-center justify-between px-8 h-14 bg-white/90 backdrop-blur-md border-b border-[#e2e8f0]">
        <button
          onClick={onVoltar}
          className="flex items-center gap-2 text-[13px] font-medium transition-colors"
          style={{ color: "#64748b" }}
          onMouseEnter={e => e.currentTarget.style.color = "#0085ca"}
          onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
        >
          <span className="material-symbols-outlined text-[17px]">arrow_back</span>
          Seleção de Pesquisa
        </button>
        <div className="w-32" />
      </header>

      <div className="max-w-[1000px] mx-auto w-full px-4 md:px-8 py-10">
        {/* Título */}
        <div className="flex flex-col items-center text-center mb-12 mt-8">
          <h1
            className="text-[38px] font-semibold leading-tight tracking-tight mb-3"
            style={{ fontFamily: "'Inter Tight', Inter, sans-serif", color: "#0f172a" }}
          >
            Pesquisa por Empresa
          </h1>
          <p className="text-[15px] leading-relaxed max-w-2xl" style={{ color: "#64748b" }}>
            Busque por Razão Social, Nome Fantasia ou CNPJ para iniciar sua análise.
          </p>
          <div className="mt-2 flex items-center gap-2 px-3 py-1.5 rounded-full text-[12px]" style={{ background: "#f1f5f9", color: "#64748b" }}>
            <span className="material-symbols-outlined text-[13px]" style={{ color: "#94a3b8" }}>info</span>
            CNPJ exemplo:
            <span style={{ fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em", color: "#0f172a" }}>
              00.000.000/0001-00
            </span>
          </div>
        </div>

        {/* Barra de busca */}
        <div className="relative w-full max-w-3xl mx-auto z-20">
          <form onSubmit={buscar}>
            <div
              className="relative flex items-center w-full h-[68px] rounded-xl bg-white transition-all"
              style={{ border: "1.5px solid #e2e8f0", boxShadow: "0 2px 8px rgba(15,23,42,0.05)" }}
              onFocus={() => {}}
            >
              <span
                className={`material-symbols-outlined absolute left-5 text-[26px] transition-colors ${loading ? "animate-spin" : ""}`}
                style={{ color: loading ? "#94a3b8" : "#0085ca", fontVariationSettings: "'FILL' 1" }}
              >
                {loading ? "progress_activity" : "search"}
              </span>
              <input
                ref={inputRef}
                className="w-full h-full pl-[62px] pr-36 bg-transparent border-none outline-none text-[16px] text-[#0f172a] placeholder:text-[#94a3b8]"
                placeholder="Digite o CNPJ ou Nome da Empresa..."
                value={termo}
                onChange={(e) => setTermo(e.target.value)}
                onFocus={e => e.currentTarget.closest("div").style.borderColor = "#0085ca"}
                onBlur={e => e.currentTarget.closest("div").style.borderColor = "#e2e8f0"}
                autoFocus
              />
              <div className="absolute right-4 flex items-center gap-2">
                {/* Badge de validade CNPJ */}
                {cnpjValidity === "ok" && (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200">
                    Válido
                  </span>
                )}
                {cnpjValidity === "bad" && (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-red-50 text-red-600 border border-red-200">
                    Inválido
                  </span>
                )}
                {cnpjValidity === "typing" && (
                  <span className="text-[11px] font-medium" style={{ color: "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>
                    {raw.length}/14
                  </span>
                )}
                {termo && (
                  <button
                    type="button"
                    onClick={() => { setTermo(""); setLista(null); setErro(null); }}
                    className="p-1 rounded-full transition-colors"
                    style={{ color: "#94a3b8" }}
                    onMouseEnter={e => e.currentTarget.style.color = "#0f172a"}
                    onMouseLeave={e => e.currentTarget.style.color = "#94a3b8"}
                  >
                    <span className="material-symbols-outlined text-[18px]">close</span>
                  </button>
                )}
              </div>
            </div>
          </form>
        </div>

        {/* Erro */}
        {erro && (
          <p className="text-center mt-10 text-[14px]" style={{ color: "#b91c1c" }}>{erro}</p>
        )}

        {/* Pesquisas recentes — só quando campo vazio */}
        {!lista && !loading && termo.trim().length < 3 && (
          <div className="w-full max-w-3xl mx-auto mt-[60px] grid grid-cols-1 md:grid-cols-3 gap-gutter">
            <div className="md:col-span-3 bg-surface-container-lowest rounded-xl p-space-lg shadow-ambient border border-surface-variant">
              <div className="flex items-center gap-3 mb-space-md">
                <div className="p-2 bg-tertiary-fixed rounded-lg text-on-tertiary-fixed">
                  <span className="material-symbols-outlined">history</span>
                </div>
                <h3 className="text-headline-sm text-on-surface">Pesquisas Recentes</h3>
              </div>
              {recentes.length === 0 ? (
                <p className="text-body-sm text-on-surface-variant">Nenhuma pesquisa recente.</p>
              ) : (
                <div className="flex flex-col gap-2">
                  {recentes.map((r, i) => (
                    <button
                      key={i}
                      onClick={() => r.cnpj
                        ? onSelecionarEmpresa(r.cnpj)
                        : setTermo(r.termo)}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-container transition-colors group text-left"
                    >
                      <div className="flex items-center gap-3">
                        <span className="material-symbols-outlined text-outline-variant group-hover:text-primary transition-colors">
                          {r.icone}
                        </span>
                        <span className="text-body-sm text-on-surface font-medium">{r.termo}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Lista de resultados */}
        {lista && (
          <div className={`mt-8 max-w-3xl mx-auto transition-opacity duration-150 ${loading ? "opacity-50" : "opacity-100"}`}>
            <p className="text-[13px] mb-4" style={{ color: "#94a3b8" }}>
              {total.toLocaleString("pt-BR")} resultado{total !== 1 ? "s" : ""} para &ldquo;{ultimoTermo}&rdquo;
            </p>
            <div className="flex flex-col gap-2.5">
              {lista.resultados.map((e) => (
                <button
                  key={e.cnpj_basico}
                  onClick={() => executarBusca(e.cnpj_completo || e.cnpj_basico + "00000001")}
                  className="w-full flex items-center justify-between px-5 py-4 bg-white rounded-xl cursor-pointer transition-all text-left group"
                  style={{ border: "1.5px solid #e2e8f0", boxShadow: "0 1px 4px rgba(15,23,42,0.04)" }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = "#0085ca"; e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,133,202,0.1)"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = "#e2e8f0"; e.currentTarget.style.boxShadow = "0 1px 4px rgba(15,23,42,0.04)"; }}
                >
                  <div className="flex flex-col min-w-0 gap-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[14px] font-semibold" style={{ color: "#0f172a" }}>
                        {e.razao_social}
                      </span>
                      <StatusChip status={e.situacao_cadastral} />
                      {e.situacao_especial && (
                        <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full border" style={{ background: "#fff7ed", color: "#c2410c", borderColor: "#fed7aa" }}>
                          {e.situacao_especial}
                        </span>
                      )}
                    </div>
                    <span className="text-[13px]" style={{ color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
                      {e.cnpj_completo_formatado || e.cnpj_basico}
                      {e.nome_fantasia ? <span style={{ fontFamily: "inherit" }}> · {e.nome_fantasia}</span> : ""}
                      {e.municipio_descricao && e.uf ? ` · ${e.municipio_descricao}, ${e.uf}` : ""}
                    </span>
                  </div>
                  <span className="material-symbols-outlined ml-4 shrink-0" style={{ color: "#cbd5e1" }}>chevron_right</span>
                </button>
              ))}
            </div>

            {totalPags > 1 && (
              <div className="flex items-center justify-center gap-4 mt-6">
                <button
                  onClick={() => mudarPagina(pagina - LIMIT)}
                  disabled={pagina === 0 || loading}
                  className="px-4 py-2 bg-white rounded text-[13px] font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{ border: "1px solid #e2e8f0", color: "#334155" }}
                >
                  ← Anterior
                </button>
                <span className="text-[13px]" style={{ color: "#94a3b8" }}>
                  Página {Math.floor(pagina / LIMIT) + 1} de {totalPags}
                </span>
                <button
                  onClick={() => mudarPagina(pagina + LIMIT)}
                  disabled={pagina + LIMIT >= total || loading}
                  className="px-4 py-2 bg-white rounded text-[13px] font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{ border: "1px solid #e2e8f0", color: "#334155" }}
                >
                  Próxima →
                </button>
              </div>
            )}
          </div>
        )}

        {loading && !lista && (
          <p className="text-center mt-10 text-[14px]" style={{ color: "#94a3b8" }}>Consultando...</p>
        )}
      </div>
    </main>
  );
}
