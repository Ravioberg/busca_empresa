import { useState, useEffect, useRef } from "react";
import { buscarSocioPorNome, buscarSocioPorCpf } from "../api";

const LIMIT = 20;

function ehCpf(v) {
  const d = v.replace(/[\s.\-]/g, "");
  return /^\d+$/.test(d) && d.length >= 3 && d.length <= 11;
}

function lerRecentes() {
  try { return JSON.parse(localStorage.getItem("ci_recentes_socio") || "[]"); }
  catch { return []; }
}
function salvarRecentes(lista) {
  localStorage.setItem("ci_recentes_socio", JSON.stringify(lista));
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

export default function BuscaSocio({ onSelecionarSocio, onVoltar }) {
  const [termo, setTermo] = useState("");
  const [lista, setLista] = useState(null);
  const [pagina, setPagina] = useState(0);
  const [ultimoTermo, setUltimoTermo] = useState("");
  const [modoBusca, setModoBusca] = useState("nome");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);
  const [recentes, setRecentes] = useState(lerRecentes);

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

  function addRecente(t, icone) {
    const novo = [{ termo: t, icone }, ...recentes.filter((r) => r.termo !== t)].slice(0, 5);
    setRecentes(novo);
    salvarRecentes(novo);
  }

  async function executarBusca(t) {
    const modo = ehCpf(t) ? "cpf" : "nome";
    setErro(null);
    setLoading(true);
    setModoBusca(modo);
    try {
      const res = modo === "cpf"
        ? await buscarSocioPorCpf(t, 0, LIMIT)
        : await buscarSocioPorNome(t, 0, LIMIT);
      if (res === null) return; // abortado
      setLista(res);
      setUltimoTermo(t);
      setPagina(0);
      addRecente(t, modo === "cpf" ? "badge" : "person_search");
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
  const totalPags = Math.ceil(total / LIMIT);

  return (
    <main className="flex-1 md:ml-64 overflow-y-auto bg-surface min-h-screen">
      <header className="sticky top-0 z-50 flex items-center justify-between px-8 h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-sm">
        <button
          onClick={onVoltar}
          className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors text-body-sm font-medium"
        >
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          Seleção de Pesquisa
        </button>
        <span className="text-xl font-black text-slate-900 hidden md:block">CorpIntel</span>
        <div className="w-40" />
      </header>

      <div className="max-w-[1000px] mx-auto w-full px-4 md:px-8 py-10">
        <div className="flex flex-col items-center text-center mb-12 mt-8">
          <h1 className="text-display-lg text-on-surface mb-4 tracking-tight">Pesquisa por Sócio</h1>
          <p className="text-body-lg text-on-surface-variant max-w-2xl">
            Verifique e analise sócios, beneficiários e partes interessadas via CPF ou nome completo.
          </p>
          <p className="text-body-sm text-on-surface-variant mt-2 flex items-center gap-1 max-w-xl text-center">
            <span className="material-symbols-outlined text-[14px] text-outline shrink-0">info</span>
            A RF oculta os 3 primeiros e 2 últimos dígitos do CPF. Ao digitar um CPF completo a busca tenta automaticamente os dígitos do meio. Um CPF pode retornar mais de uma pessoa.
          </p>
        </div>

        {/* Barra de busca */}
        <div className="relative w-full max-w-3xl mx-auto z-20">
          <form onSubmit={buscar}>
            <div className="relative flex items-center w-full h-[72px] rounded-xl bg-surface-container-lowest border-2 border-outline-variant shadow-search focus-within:border-primary focus-within:ring-4 focus-within:ring-primary-fixed-dim/30 transition-all">
              <span className={`absolute left-6 text-[28px] transition-colors ${loading ? "text-outline animate-spin" : "text-on-surface-variant"}`}>
                <span className="material-symbols-outlined text-[28px]">
                  {loading ? "progress_activity" : "search"}
                </span>
              </span>
              <input
                ref={inputRef}
                className="w-full h-full pl-[72px] pr-20 bg-transparent border-none outline-none text-headline-md text-on-surface placeholder:text-outline-variant placeholder:font-normal"
                placeholder="Digite o CPF ou Nome do Sócio..."
                value={termo}
                onChange={(e) => setTermo(e.target.value)}
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
              <div className="flex items-center gap-3 mb-space-md">
                <div className="p-2 bg-tertiary-fixed rounded-lg text-on-tertiary-fixed">
                  <span className="material-symbols-outlined">history</span>
                </div>
                <h3 className="text-headline-sm text-on-surface">Investigações Recentes</h3>
              </div>
              {recentes.length === 0 ? (
                <p className="text-body-sm text-on-surface-variant">Nenhuma pesquisa recente.</p>
              ) : (
                <div className="flex flex-col gap-2">
                  {recentes.map((r, i) => (
                    <button
                      key={i}
                      onClick={() => setTermo(r.termo)}
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
              {total.toLocaleString("pt-BR")} resultado{total !== 1 ? "s" : ""} para &ldquo;{ultimoTermo}&rdquo;
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
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="text-body-md text-on-surface font-semibold group-hover:text-primary transition-colors">
                        {s.nome_socio}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 text-body-sm text-on-surface-variant">
                      <span className="font-mono text-[13px]">{s.cpf_cnpj_socio}</span>
                      {s.qualificacao_descricao && (
                        <><span className="w-1 h-1 rounded-full bg-outline-variant" /><span>{s.qualificacao_descricao}</span></>
                      )}
                      {s.data_entrada && (
                        <><span className="w-1 h-1 rounded-full bg-outline-variant" /><span>Entrada: {s.data_entrada}</span></>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-body-sm text-on-surface">{s.razao_social || s.cnpj_basico}</span>
                      {s.cnpj_completo_formatado && (
                        <span className="font-mono text-[13px] text-outline">({s.cnpj_completo_formatado})</span>
                      )}
                      {s.situacao_cadastral && <StatusChip status={s.situacao_cadastral} />}
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
