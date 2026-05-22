import { useState, useEffect } from "react";
import { fetchInfo } from "../api";

const MESES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];
function fmtMes(ym) {
  if (!ym) return "—";
  const [y, m] = ym.split("-");
  return `${MESES[parseInt(m, 10) - 1]}/${y}`;
}

export default function HomeSelecao({ irParaEmpresa, irParaSocio }) {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    fetchInfo().then(d => d && setInfo(d));
  }, []);

  const cards = [
    {
      icon: "person_search",
      title: "Pesquisar por Sócio",
      desc: "Investigue perfis individuais, identifique conexões e analise afiliações corporativas detalhadas.",
      onClick: irParaSocio,
      accent: "#0085ca",
    },
    {
      icon: "domain",
      title: "Pesquisar por Empresa",
      desc: "Analise estruturas corporativas, acesse dados cadastrais e o quadro societário completo.",
      onClick: irParaEmpresa,
      accent: "#0a6cb8",
    },
  ];

  return (
    <main className="flex-1 md:ml-52 bg-[#f7f9fc] min-h-screen flex flex-col items-center justify-center px-10 py-16 relative overflow-hidden">
      {/* Blur decorativo */}
      <div
        className="absolute top-0 right-0 w-[700px] h-[700px] rounded-full pointer-events-none -translate-y-1/2 translate-x-1/3 blur-[120px]"
        style={{ background: "rgba(0,133,202,0.06)" }}
      />

      <div className="w-full max-w-4xl flex flex-col items-center relative z-10">
        {/* Header */}
        <header className="text-center mb-12 max-w-2xl">
          <h1
            className="text-[38px] font-semibold leading-tight tracking-tight mb-3"
            style={{ fontFamily: "'Inter Tight', Inter, sans-serif", color: "#0f172a" }}
          >
            Iniciar Pesquisa
          </h1>
          <p className="text-[15px] leading-relaxed" style={{ color: "#64748b" }}>
            Selecione o escopo da sua investigação. O sistema otimizará as fontes de dados com base na entidade
            principal escolhida.
          </p>
        </header>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
          {cards.map((card) => (
            <button
              key={card.title}
              onClick={card.onClick}
              className="group relative flex flex-col items-center justify-center p-12 bg-white rounded-xl text-center min-h-[300px] overflow-hidden transition-all duration-300 focus:outline-none"
              style={{
                border: "1.5px solid #e2e8f0",
                boxShadow: "0 2px 8px rgba(15,23,42,0.05)",
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = card.accent;
                e.currentTarget.style.boxShadow = `0 8px 28px rgba(0,133,202,0.12)`;
                e.currentTarget.style.transform = "translateY(-2px)";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = "#e2e8f0";
                e.currentTarget.style.boxShadow = "0 2px 8px rgba(15,23,42,0.05)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              {/* Ícone */}
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center mb-6 transition-transform duration-300 group-hover:scale-110"
                style={{ background: "#0a1f3d" }}
              >
                <span
                  className="material-symbols-outlined text-[30px] text-white"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  {card.icon}
                </span>
              </div>

              {/* Texto */}
              <h2
                className="text-[18px] font-semibold mb-3 transition-colors duration-200"
                style={{ fontFamily: "'Inter Tight', Inter, sans-serif", color: "#0f172a" }}
              >
                {card.title}
              </h2>
              <p className="text-[14px] leading-relaxed max-w-xs" style={{ color: "#64748b" }}>
                {card.desc}
              </p>

              {/* CTA hover */}
              <div
                className="mt-6 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.12em] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style={{ color: card.accent }}
              >
                INICIAR CONSULTA
                <span className="material-symbols-outlined text-[13px]">arrow_forward</span>
              </div>
            </button>
          ))}
        </div>

        {/* Métricas da base */}
        <div
          className="mt-10 flex items-center gap-5 text-[11px]"
          style={{ fontFamily: "'JetBrains Mono', monospace", color: "#94a3b8" }}
        >
          <span>Última base processada:</span>
          <span style={{ color: "#64748b" }}>{fmtMes(info?.mes_atual)}</span>
          <span style={{ color: "#cbd5e1" }}>·</span>
          <span>Base pública RFB</span>
        </div>
      </div>
    </main>
  );
}
