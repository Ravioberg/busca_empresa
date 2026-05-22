import { useState, useEffect } from "react";
import { fetchInfo } from "../api";

const MESES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];

function fmtMes(ym) {
  if (!ym) return "—";
  const [y, m] = ym.split("-");
  return `${MESES[parseInt(m, 10) - 1]}/${y}`;
}

function lerRecentes() {
  const parse = (key) => {
    try { return JSON.parse(localStorage.getItem(key) || "[]"); }
    catch { return []; }
  };
  const empresa = parse("ci_recentes_empresa").map(r => ({ ...r, tipo: "empresa" }));
  const socio   = parse("ci_recentes_socio").map(r => ({ ...r, tipo: "socio" }));
  return [...empresa, ...socio].slice(0, 7);
}

const NAV = [
  { icon: "domain",        label: "Busca Empresa", tela: "empresa", telas: ["empresa", "resultado-empresa"] },
  { icon: "person_search", label: "Busca Sócio",   tela: "socio",   telas: ["socio",   "resultado-socio"]   },
];

const S = {
  sidebar:      { background: "#0a1f3d" },
  divider:      { borderColor: "rgba(255,255,255,0.07)" },
  brandMark:    { background: "#0085ca", fontFamily: "'Inter Tight', Inter, sans-serif" },
  brandName:    { fontFamily: "'Inter Tight', Inter, sans-serif" },
  sectionLabel: { color: "#475569", letterSpacing: "0.12em" },
  navActive:    { background: "rgba(0,133,202,0.14)", color: "#dee7f0", borderLeft: "3px solid #0085ca" },
  navIdle:      { color: "#64748b", borderLeft: "3px solid transparent" },
  recentText:   { color: "#64748b" },
  footerVal:    { color: "#4a5d7a", fontFamily: "'JetBrains Mono', monospace" },
};

export default function Sidebar({ tela, irPara }) {
  const [info, setInfo]       = useState(null);
  const [recentes, setRecentes] = useState([]);

  useEffect(() => {
    setRecentes(lerRecentes());
    fetchInfo().then(d => d && setInfo(d));
  }, [tela]);

  return (
    <aside
      style={S.sidebar}
      className="fixed left-0 top-0 h-screen w-52 flex flex-col z-40 hidden md:flex select-none"
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-[18px] border-b shrink-0" style={S.divider}>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-white font-bold text-[17px]"
          style={S.brandMark}
        >
          π
        </div>
        <div>
          <div className="text-white font-semibold text-[15px] leading-tight" style={S.brandName}>
            Pythagoras
          </div>
          <div className="text-[10.5px] font-medium uppercase tracking-widest mt-px" style={S.sectionLabel}>
            CNPJ Intelligence
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="px-3 pt-4 pb-2 shrink-0 space-y-0.5">
        {NAV.map(item => {
          const active = item.telas.includes(tela);
          return (
            <button
              key={item.label}
              onClick={() => irPara(item.tela)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-[13px] font-medium text-left rounded-lg transition-colors"
              style={active ? S.navActive : S.navIdle}
            >
              <span className="material-symbols-outlined text-[17px]">{item.icon}</span>
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Buscas recentes */}
      {recentes.length > 0 && (
        <div className="px-3 pt-4 flex-1 overflow-y-auto border-t sidebar-scroll" style={S.divider}>
          <div className="px-3 mb-2 flex items-center justify-between">
            <span className="text-[9.5px] font-semibold uppercase" style={S.sectionLabel}>
              Buscas recentes
            </span>
            <span className="text-[9.5px]" style={S.sectionLabel}>{recentes.length}</span>
          </div>
          {recentes.map((r, i) => (
            <button
              key={i}
              onClick={() => irPara(r.tipo)}
              className="w-full flex items-center gap-2.5 px-3 py-[7px] rounded-lg text-left transition-colors hover:bg-white/5"
            >
              <span
                className="material-symbols-outlined text-[15px] shrink-0"
                style={S.recentText}
              >
                {r.icone}
              </span>
              <span className="text-[12px] truncate" style={S.recentText}>{r.termo}</span>
            </button>
          ))}
        </div>
      )}

      {/* Footer — métricas da base */}
      <div className="px-5 py-4 border-t shrink-0" style={S.divider}>
        <div className="text-[9.5px] font-semibold uppercase mb-1" style={S.sectionLabel}>
          Base RFB
        </div>
        <div className="text-[12px]" style={S.footerVal}>
          {info?.mes_atual ? fmtMes(info.mes_atual) : "—"}
        </div>
      </div>
    </aside>
  );
}
