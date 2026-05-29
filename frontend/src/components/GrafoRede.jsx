import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { buscarGrafoEmpresa, buscarGrafoSocio } from "../api";

// Cores por índice de categoria (mesma ordem do backend GRAFO_CATEGORIAS)
const CAT_COLORS = [
  "#16a34a", // 0 Empresa Ativa
  "#d97706", // 1 Empresa Suspensa
  "#dc2626", // 2 Empresa Inapta
  "#64748b", // 3 Empresa Baixada/Nula
  "#0085ca", // 4 Sócio atual
  "#cbd5e1", // 5 Ex-sócio
];

const PROFUNDIDADES = [1, 2, 3, 4];

function montarOption(data) {
  const small = data.nodes.length <= 55;

  const nodes = data.nodes.map((n) => ({
    id: n.id,
    name: n.name,
    category: n.category,
    symbol: n.tipo === "empresa" ? "roundRect" : "circle",
    symbolSize: n.is_root ? 30 : n.tipo === "empresa" ? 17 : 12,
    value: n.tipo === "empresa" ? n.situacao : (n.category === 4 ? "Sócio atual" : "Ex-sócio"),
    label: { show: n.is_root || small },
    itemStyle: n.is_root ? { borderColor: "#0a1f3d", borderWidth: 3 } : undefined,
    _tipo: n.tipo,
    _cnpj: n.cnpj_completo,
    _cpf: n.cpf,
    _nome: n.name,
  }));

  const links = data.links.map((l) => ({
    source: l.source,
    target: l.target,
    lineStyle: l.ativo
      ? { width: 1.2, opacity: 0.55 }
      : { width: 1, opacity: 0.3, type: "dashed" },
  }));

  const categories = data.categories.map((c, i) => ({
    name: c.name,
    itemStyle: { color: CAT_COLORS[i] },
  }));

  return {
    tooltip: {
      trigger: "item",
      formatter: (p) =>
        p.dataType === "node"
          ? `<b>${p.data.name}</b>${p.data.value ? `<br/><span style="color:#64748b">${p.data.value}</span>` : ""}`
          : "",
    },
    legend: [
      {
        data: categories.map((c) => c.name),
        bottom: 8,
        itemWidth: 12,
        itemHeight: 12,
        textStyle: { fontSize: 11, color: "#64748b" },
      },
    ],
    animationDuration: 900,
    animationEasingUpdate: "quinticInOut",
    series: [
      {
        type: "graph",
        layout: "force",
        roam: true,
        draggable: true,
        data: nodes,
        links,
        categories,
        force: {
          repulsion: small ? 220 : 90,
          edgeLength: small ? [60, 160] : [30, 110],
          gravity: 0.08,
          friction: 0.18,
        },
        emphasis: { focus: "adjacency", label: { show: true } },
        label: {
          position: "right",
          fontSize: 11,
          color: "#334155",
          formatter: "{b}",
        },
        labelLayout: { hideOverlap: true },
        scaleLimit: { min: 0.2, max: 5 },
        lineStyle: { color: "source", curveness: 0.12 },
      },
    ],
    thumbnail: {
      show: true,
      right: 12,
      bottom: 36,
      width: "16%",
      height: "16%",
      windowStyle: { color: "rgba(0,133,202,0.12)", borderColor: "#0085ca", borderWidth: 1 },
    },
  };
}

export default function GrafoRede({ raiz, onVoltar, onVerEmpresa, onVerSocio }) {
  const ref = useRef(null);
  const chartRef = useRef(null);
  const [profundidade, setProfundidade] = useState(2);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);

  // Busca o grafo quando raiz ou profundidade mudam
  useEffect(() => {
    let cancel = false;
    async function load() {
      setLoading(true);
      setErro(null);
      try {
        const d =
          raiz.tipo === "empresa"
            ? await buscarGrafoEmpresa(raiz.cnpj, profundidade)
            : await buscarGrafoSocio(raiz.cpf, raiz.nome, profundidade);
        if (!cancel) {
          if (!d) setErro("Rede não encontrada.");
          else setData(d);
        }
      } catch (e) {
        if (!cancel) setErro(e.message);
      } finally {
        if (!cancel) setLoading(false);
      }
    }
    load();
    return () => { cancel = true; };
  }, [raiz, profundidade]);

  // Renderiza o gráfico
  useEffect(() => {
    if (!ref.current || !data) return;
    chartRef.current?.dispose();
    const chart = echarts.init(ref.current);
    chartRef.current = chart;
    chart.setOption(montarOption(data));

    chart.on("dblclick", (p) => {
      if (p.dataType !== "node") return;
      if (p.data._tipo === "empresa" && p.data._cnpj) {
        onVerEmpresa && onVerEmpresa(p.data._cnpj);
      } else if (p.data._tipo === "socio") {
        onVerSocio && onVerSocio({ nome_socio: p.data._nome, cpf_cnpj_socio: p.data._cpf });
      }
    });

    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, [data, onVerEmpresa, onVerSocio]);

  const totalNos = data?.nodes?.length || 0;
  const totalLinks = data?.links?.length || 0;

  return (
    <main className="flex-1 md:ml-52 bg-[#f7f9fc] min-h-screen flex flex-col">
      {/* Header */}
      <header
        className="sticky top-0 z-30 flex items-center justify-between px-8 h-14 bg-white/90 backdrop-blur-md border-b"
        style={{ borderColor: "#e2e8f0" }}
      >
        <button
          onClick={onVoltar}
          className="flex items-center gap-2 text-[13px] font-medium transition-colors"
          style={{ color: "#64748b" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "#0085ca")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "#64748b")}
        >
          <span className="material-symbols-outlined text-[17px]">arrow_back</span>
          Voltar
        </button>
        <div className="flex items-center gap-2 text-[12px]" style={{ color: "#94a3b8" }}>
          <span className="material-symbols-outlined text-[15px]">hub</span>
          <span className="hidden sm:inline">Rede societária</span>
        </div>
      </header>

      {/* Barra de controles */}
      <div
        className="flex items-center justify-between gap-4 flex-wrap px-8 py-3 bg-white border-b"
        style={{ borderColor: "#e2e8f0" }}
      >
        <div className="min-w-0">
          <h1
            className="text-[18px] font-semibold leading-tight truncate"
            style={{ fontFamily: "'Inter Tight', Inter, sans-serif", color: "#0f172a" }}
          >
            {raiz.label || "Rede"}
          </h1>
          <p className="text-[12px]" style={{ color: "#94a3b8" }}>
            {loading
              ? "Montando rede..."
              : `${totalNos} nós · ${totalLinks} conexões${data?.truncado ? " · limite atingido" : ""}`}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[12px] font-medium" style={{ color: "#64748b" }}>
            Conexões (saltos)
          </span>
          <div className="flex rounded-lg overflow-hidden" style={{ border: "1px solid #e2e8f0" }}>
            {PROFUNDIDADES.map((p) => {
              const ativo = p === profundidade;
              return (
                <button
                  key={p}
                  onClick={() => setProfundidade(p)}
                  disabled={loading}
                  className="px-3.5 py-1.5 text-[13px] font-semibold transition-colors disabled:opacity-50"
                  style={{
                    background: ativo ? "#0085ca" : "#fff",
                    color: ativo ? "#fff" : "#64748b",
                    borderLeft: p === PROFUNDIDADES[0] ? "none" : "1px solid #e2e8f0",
                  }}
                >
                  {p}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Canvas do grafo */}
      <div className="relative flex-1">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center gap-3 text-[13px]" style={{ color: "#94a3b8", background: "rgba(247,249,252,0.6)" }}>
            <span className="material-symbols-outlined animate-spin text-[22px]" style={{ color: "#0085ca" }}>progress_activity</span>
            Montando rede societária...
          </div>
        )}
        {erro && !loading && (
          <div className="absolute inset-0 flex items-center justify-center text-[14px]" style={{ color: "#b91c1c" }}>
            {erro}
          </div>
        )}
        <div ref={ref} style={{ width: "100%", height: "100%", minHeight: 500 }} />

        {/* Dica */}
        {!loading && !erro && data && (
          <div
            className="absolute top-3 left-3 px-3 py-1.5 rounded-lg text-[11px] flex items-center gap-1.5"
            style={{ background: "rgba(255,255,255,0.9)", border: "1px solid #e2e8f0", color: "#94a3b8" }}
          >
            <span className="material-symbols-outlined text-[13px]">touch_app</span>
            Clique duplo num nó para abrir · arraste para reposicionar
          </div>
        )}
      </div>
    </main>
  );
}
