import { useState, useEffect, useRef } from "react";
import { buscarEmpresaPorCnpj, buscarEmpresaPorNome } from "../api";

const LIMIT = 20;

function ehCnpj(v) {
  return v.replace(/\D/g, "").length === 14;
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
function salvarRecentes(lista) {
  localStorage.setItem("ci_recentes_empresa", JSON.stringify(lista));
}

export default function BuscaEmpresa({ onSelecionarEmpresa, onVoltar }) {
  const [termo, setTermo] = useState("");
  const [lista, setLista] = useState(null);
  const [pagina, setPagina] = useState(0);
  const [ultimoTermo, setUltimoTermo] = useState("");
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
    setErro(null);
    setLoading(true);
    try {
      if (ehCnpj(t)) {
        addRecente(t, "receipt_long");
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
        addRecente(t, "domain");
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

  return (
    <main className="flex-1 md:ml-64 overflow-y-auto bg-surface min-h-screen">
      {/* Header fixo */}
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
        {/* Título */}
        <div className="flex flex-col items-center text-center mb-12 mt-8">
          <h1 className="text-display-lg text-on-surface mb-4 tracking-tight">Pesquisa por Empresa</h1>
          <p className="text-body-lg text-on-surface-variant max-w-2xl">
            Acesse dados corporativos instantaneamente. Busque por Razão Social, Nome Fantasia ou CNPJ para iniciar
            sua análise.
          </p>
        </div>

        {/* Barra de busca */}
        <div className="relative w-full max-w-3xl mx-auto z-20">
          <form onSubmit={buscar}>
            <div className="relative flex items-center w-full h-[72px] rounded-xl bg-surface-container-lowest border border-outline-variant shadow-search focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
              <span
                className={`material-symbols-outlined absolute left-6 text-[28px] transition-colors ${loading ? "text-outline animate-spin" : "text-primary"}`}
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                {loading ? "progress_activity" : "search"}
              </span>
              <input
                ref={inputRef}
                className="w-full h-full pl-[72px] pr-16 bg-transparent border-none outline-none text-body-lg text-on-surface placeholder:text-outline-variant"
                placeholder="Digite o CNPJ ou Nome da Empresa..."
                value={termo}
                onChange={(e) => setTermo(e.target.value)}
                autoFocus
              />
              {termo && (
                <button
                  type="button"
                  onClick={() => { setTermo(""); setLista(null); setErro(null); }}
                  className="absolute right-4 text-outline hover:text-on-surface p-1 rounded-full hover:bg-surface-container transition-colors"
                >
                  <span className="material-symbols-outlined text-[20px]">close</span>
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Erro */}
        {erro && (
          <p className="text-center text-error mt-10 text-body-md">{erro}</p>
        )}

        {/* Pesquisas recentes — só quando campo vazio */}
        {!lista && !loading && termo.trim().length < 3 && (
          <div className="mt-16 max-w-3xl mx-auto">
            <h3 className="text-headline-sm text-on-surface mb-6 flex items-center">
              <span className="material-symbols-outlined mr-2 text-outline">history</span>
              Pesquisas Recentes
            </h3>
            {recentes.length === 0 ? (
              <p className="text-body-sm text-on-surface-variant">Nenhuma pesquisa recente.</p>
            ) : (
              <div className="flex flex-wrap gap-3">
                {recentes.map((r, i) => (
                  <button
                    key={i}
                    onClick={() => setTermo(r.termo)}
                    className="flex items-center px-4 py-2 bg-surface-container-lowest border border-outline-variant rounded-full text-body-sm text-on-surface-variant hover:border-primary hover:text-primary transition-colors shadow-ambient"
                  >
                    <span className="material-symbols-outlined text-[16px] mr-2">{r.icone}</span>
                    {r.termo}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Lista de resultados — permanece visível enquanto novo resultado carrega */}
        {lista && (
          <div className={`mt-8 max-w-3xl mx-auto transition-opacity duration-150 ${loading ? "opacity-50" : "opacity-100"}`}>
            <p className="text-body-sm text-on-surface-variant mb-4">
              {total.toLocaleString("pt-BR")} resultado{total !== 1 ? "s" : ""} para &ldquo;{ultimoTermo}&rdquo;
            </p>
            <div className="flex flex-col gap-3">
              {lista.resultados.map((e) => (
                <button
                  key={e.cnpj_basico}
                  onClick={() => executarBusca(e.cnpj_completo || e.cnpj_basico + "00000001")}
                  className="w-full flex items-center justify-between px-6 py-4 bg-surface-container-lowest rounded-xl border border-outline-variant/30 hover:border-primary/40 hover:bg-primary/5 cursor-pointer transition-all ambient-shadow text-left group"
                >
                  <div className="flex flex-col min-w-0">
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="text-body-md text-on-surface font-semibold group-hover:text-primary transition-colors">
                        {e.razao_social}
                      </span>
                      <StatusChip status={e.situacao_cadastral} />
                    </div>
                    <span className="text-body-sm text-on-surface-variant mt-0.5">
                      {e.cnpj_completo_formatado || e.cnpj_basico}
                      {e.nome_fantasia ? ` · ${e.nome_fantasia}` : ""}
                      {e.municipio_descricao && e.uf ? ` · ${e.municipio_descricao}, ${e.uf}` : ""}
                    </span>
                  </div>
                  <span className="material-symbols-outlined text-outline ml-4 shrink-0">chevron_right</span>
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
