import { useState, useEffect, useRef } from "react";
import { buscarSocioPorNome, buscarSocioPorCpf } from "../api";

const LIMIT = 20;

function ehCpf(v) {
  const d = v.replace(/[\s.\-]/g, "");
  return /^\d+$/.test(d) && d.length >= 6 && d.length <= 11;
}

function cpfEmDigitacao(v) {
  const d = v.replace(/[\s.\-]/g, "");
  return /^\d+$/.test(d) && d.length > 0 && d.length < 6;
}

function lerRecentes() {
  try { return JSON.parse(localStorage.getItem("ci_recentes_socio") || "[]"); }
  catch { return []; }
}


export default function BuscaSocio({ onSelecionarSocio, onVoltar }) {
  const [termo, setTermo] = useState("");
  const [lista, setLista] = useState(null);
  const [pagina, setPagina] = useState(0);
  const [ultimoTermo, setUltimoTermo] = useState("");
  const [modoBusca, setModoBusca] = useState("nome");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);
  // Recentes refletem cliques em perfil (gravados via App.jsx).
  const [recentes, setRecentes] = useState(lerRecentes);

  const inputRef = useRef(null);
  const debounceRef = useRef(null);
  const searchIdRef = useRef(0);

  /* Busca ao digitar — debounce 400 ms, mínimo 3 caracteres */
  useEffect(() => {
    const t = termo.trim();
    if (t.length < 3) {
      setLista(null);
      setErro(null);
      return;
    }
    if (cpfEmDigitacao(t)) {
      setLista(null);
      setErro(null);
      return;
    }
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => executarBusca(t), 400);
    return () => clearTimeout(debounceRef.current);
  }, [termo]);

  async function executarBusca(t) {
    const myId = ++searchIdRef.current;
    const modo = ehCpf(t) ? "cpf" : "nome";
    setErro(null);
    setLoading(true);
    setModoBusca(modo);
    try {
      const res = modo === "cpf"
        ? await buscarSocioPorCpf(t, 0, LIMIT)
        : await buscarSocioPorNome(t, 0, LIMIT);
      if (res === null || myId !== searchIdRef.current) return;
      setLista(res);
      setUltimoTermo(t);
      setPagina(0);
    } catch (err) {
      if (myId === searchIdRef.current) setErro(err.message);
    } finally {
      if (myId === searchIdRef.current) setLoading(false);
    }
  }

  function buscar(e) {
    e?.preventDefault();
    const t = termo.trim();
    if (!t || t.length < 3) return;
    clearTimeout(debounceRef.current);
    executarBusca(t);
  }

  function limparHistorico() {
    localStorage.removeItem("ci_recentes_socio");
    setRecentes([]);
  }

  async function mudarPagina(nova) {
    setLoading(true);
    try {
      const res = modoBusca === "cpf"
        ? await buscarSocioPorCpf(ultimoTermo, nova, LIMIT, total)
        : await buscarSocioPorNome(ultimoTermo, nova, LIMIT, total);
      if (res === null) return;
      setLista(res);
      setPagina(nova);
    } catch (err) { setErro(err.message); }
    finally { setLoading(false); }
  }

  const total = lista?.total || 0;
  const totalAproximado = total >= 10000;
  const totalPags = Math.ceil(total / LIMIT);

  return (
    <main className="flex-1 md:ml-52 overflow-y-auto bg-[#f7f9fc] min-h-screen">
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
        <div className="flex flex-col items-center text-center mb-12 mt-8">
          <h1
            className="text-[38px] font-semibold leading-tight tracking-tight mb-3"
            style={{ fontFamily: "'Inter Tight', Inter, sans-serif", color: "#0f172a" }}
          >
            Pesquisa por Sócio
          </h1>
          <p className="text-[15px] leading-relaxed max-w-2xl" style={{ color: "#64748b" }}>
            Verifique e analise sócios, beneficiários e partes interessadas via CPF ou nome completo.
          </p>
          <div className="mt-2 flex items-center gap-2 px-3 py-1.5 rounded-full text-[12px]" style={{ background: "#f1f5f9", color: "#64748b" }}>
            <span className="material-symbols-outlined text-[13px]" style={{ color: "#94a3b8" }}>info</span>
            CPF na base RFB:
            <span style={{ fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em" }}>
              <span style={{ color: "#94a3b8" }}>***.</span>
              <span style={{ color: "#0f172a" }}>000</span>
              <span style={{ color: "#94a3b8" }}>.</span>
              <span style={{ color: "#0f172a" }}>000</span>
              <span style={{ color: "#94a3b8" }}>-**</span>
            </span>
          </div>
        </div>

        {/* Barra de busca */}
        <div className="relative w-full max-w-3xl mx-auto z-20">
          <form onSubmit={buscar}>
            <div
              className="relative flex items-center w-full h-[68px] rounded-xl bg-white transition-all"
              style={{ border: "1.5px solid #e2e8f0", boxShadow: "0 2px 8px rgba(15,23,42,0.05)" }}
            >
              <span
                className={`material-symbols-outlined absolute left-5 text-[26px] transition-colors ${loading ? "animate-spin" : ""}`}
                style={{ color: loading ? "#94a3b8" : "#0085ca", fontVariationSettings: "'FILL' 1" }}
              >
                {loading ? "progress_activity" : "search"}
              </span>
              <input
                ref={inputRef}
                className="w-full h-full pl-[62px] pr-16 bg-transparent border-none outline-none text-[16px] text-[#0f172a] placeholder:text-[#94a3b8]"
                placeholder="Digite o CPF completo, 6 dígitos visíveis ou Nome do Sócio..."
                value={termo}
                onChange={(e) => setTermo(e.target.value)}
                onFocus={e => e.currentTarget.closest("div").style.borderColor = "#0085ca"}
                onBlur={e => e.currentTarget.closest("div").style.borderColor = "#e2e8f0"}
                autoFocus
              />
              <div className="absolute right-4 flex items-center gap-2">
                {termo && (
                  <button
                    type="button"
                    onClick={() => { setTermo(""); setLista(null); setErro(null); }}
                    className="text-outline hover:text-on-surface p-1 rounded-full hover:bg-surface-container transition-colors"
                  >
                    <span className="material-symbols-outlined text-[20px]">close</span>
                  </button>
                )}
              </div>
            </div>
          </form>
        </div>

        {/* Erro */}
        {erro && <p className="text-center text-error mt-10 text-body-md">{erro}</p>}

        {/* Pesquisas recentes */}
        {!lista && !loading && termo.trim().length < 3 && (
          <div className="w-full max-w-3xl mx-auto mt-[60px] grid grid-cols-1 md:grid-cols-3 gap-gutter">
            <div className="md:col-span-3 bg-surface-container-lowest rounded-xl p-space-lg shadow-ambient border border-surface-variant">
              <div className="flex items-center justify-between gap-3 mb-space-md">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-tertiary-fixed rounded-lg text-on-tertiary-fixed">
                    <span className="material-symbols-outlined">history</span>
                  </div>
                  <h3 className="text-headline-sm text-on-surface">Pesquisas Recentes</h3>
                </div>
                {recentes.length > 0 && (
                  <button
                    type="button"
                    onClick={limparHistorico}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-body-sm font-medium text-on-surface-variant hover:text-error hover:bg-error/10 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[17px]">delete</span>
                    Limpar Histórico
                  </button>
                )}
              </div>
              {recentes.length === 0 ? (
                <p className="text-body-sm text-on-surface-variant">Nenhuma pesquisa recente.</p>
              ) : (
                <div className="flex flex-col gap-2">
                  {recentes.map((r, i) => (
                    <button
                      key={i}
                      onClick={() => (r.nome || r.cpf)
                        ? onSelecionarSocio({ nome_socio: r.nome || r.termo, cpf_cnpj_socio: r.cpf })
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

        {/* Lista de resultados — permanece visível enquanto novo resultado carrega */}
        {lista && (
          <div className={`mt-8 max-w-3xl mx-auto transition-opacity duration-150 ${loading ? "opacity-50" : "opacity-100"}`}>
            <p className="text-body-sm text-on-surface-variant mb-4">
              {totalAproximado
                ? `Mais de ${total.toLocaleString("pt-BR")} resultados`
                : `${total.toLocaleString("pt-BR")} resultado${total !== 1 ? "s" : ""}`}{" "}
              para &ldquo;{ultimoTermo}&rdquo;
            </p>
            <div className="flex flex-col gap-3">
              {lista.resultados.map((s, i) => (
                <button
                  key={i}
                  onClick={() => onSelecionarSocio(s)}
                  className="w-full flex items-center gap-4 px-6 py-4 bg-surface-container-lowest rounded-xl border border-outline-variant/30 hover:border-primary/40 hover:bg-primary/5 transition-all ambient-shadow text-left group"
                >
                  <div className="w-10 h-10 rounded-full bg-secondary-fixed text-primary flex items-center justify-center shrink-0 font-bold text-sm">
                    {(s.nome_socio || "?").charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-body-md text-on-surface font-semibold group-hover:text-primary transition-colors">
                      {s.nome_socio}
                    </span>
                    <div className="flex items-center gap-2 mt-0.5 text-body-sm text-on-surface-variant">
                      <span className="font-mono text-[13px]">{s.cpf_cnpj_socio}</span>
                      {s.identificador === "Pessoa Jurídica" || s.identificador === "Estrangeiro" ? (
                        <><span className="w-1 h-1 rounded-full bg-outline-variant" /><span>{s.identificador}</span></>
                      ) : s.faixa_etaria && s.faixa_etaria !== "Não informada" ? (
                        <><span className="w-1 h-1 rounded-full bg-outline-variant" /><span>{s.faixa_etaria}</span></>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2 mt-1.5">
                      {s.n_ativas > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200 text-[11px] font-medium">
                          <span className="material-symbols-outlined text-[11px]">verified</span>
                          {s.n_ativas} ativa{s.n_ativas !== 1 ? "s" : ""}
                        </span>
                      )}
                      {s.n_inaptas > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-[11px] font-medium">
                          <span className="material-symbols-outlined text-[11px]">warning</span>
                          {s.n_inaptas} inapta{s.n_inaptas !== 1 ? "s" : ""}
                        </span>
                      )}
                      {s.n_ex > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 border border-slate-200 text-[11px] font-medium">
                          <span className="material-symbols-outlined text-[11px]">history</span>
                          {s.n_ex} anterior{s.n_ex !== 1 ? "es" : ""}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-outline ml-2 shrink-0">chevron_right</span>
                </button>
              ))}
            </div>

            {totalPags > 1 && (
              <div className="flex items-center justify-center gap-4 mt-6">
                <button
                  onClick={() => mudarPagina(pagina - LIMIT)}
                  disabled={pagina === 0 || loading}
                  className="px-4 py-2 bg-white border border-outline-variant rounded text-on-surface text-body-sm font-medium hover:bg-surface-container disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  ← Anterior
                </button>
                <span className="text-body-sm text-on-surface-variant">
                  Página {Math.floor(pagina / LIMIT) + 1} de {totalPags}
                </span>
                <button
                  onClick={() => mudarPagina(pagina + LIMIT)}
                  disabled={pagina + LIMIT >= total || loading}
                  className="px-4 py-2 bg-white border border-outline-variant rounded text-on-surface text-body-sm font-medium hover:bg-surface-container disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Próxima →
                </button>
              </div>
            )}
          </div>
        )}

        {/* Placeholder "Consultando" apenas na primeira busca (sem lista ainda) */}
        {loading && !lista && (
          <p className="text-center text-on-surface-variant mt-10 text-body-md">Consultando...</p>
        )}
      </div>
    </main>
  );
}
