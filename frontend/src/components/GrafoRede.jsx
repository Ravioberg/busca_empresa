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

// Conjunto de nós destacados: selecionados ∪ vizinhos diretos dos selecionados.
function computeHighlight(selectedIds, links) {
  const result = new Set(selectedIds);
  if (selectedIds.size === 0) return result;
  for (const l of links) {
    if (selectedIds.has(l.source)) result.add(l.target);
    if (selectedIds.has(l.target)) result.add(l.source);
  }
  return result;
}

function montarOption(data, selectedIds) {
  const small = data.nodes.length <= 55;
  const noSelection = selectedIds.size === 0;
  const highlightSet = noSelection ? null : computeHighlight(selectedIds, data.links);

  const nodes = data.nodes.map((n) => {
    const isHighlight = noSelection || highlightSet.has(n.id);
    const isSelected = selectedIds.has(n.id);
    const baseBorder = n.is_root ? { borderColor: "#0a1f3d", borderWidth: 3 } : {};
    const selectedBorder = isSelected
      ? { borderColor: "#0085ca", borderWidth: 3, shadowBlur: 14, shadowColor: "rgba(0,133,202,0.55)" }
      : {};
    return {
      id: n.id,
      name: n.name,
      category: n.category,
      symbol: n.tipo === "empresa" ? "roundRect" : "circle",
      symbolSize: n.is_root ? 30 : n.tipo === "empresa" ? 17 : 12,
      value: n.tipo === "empresa" ? n.situacao : (n.category === 4 ? "Sócio atual" : "Ex-sócio"),
      label: { show: n.is_root || small || isSelected },
      itemStyle: {
        ...baseBorder,
        ...selectedBorder,
        opacity: isHighlight ? 1 : 0.15,
      },
      _tipo: n.tipo,
      _cnpj: n.cnpj_completo,
      _cpf: n.cpf,
      _nome: n.name,
    };
  });

  const links = data.links.map((l) => {
    const isHighlight = noSelection || (highlightSet.has(l.source) && highlightSet.has(l.target));
    const base = l.ativo
      ? { width: 1.2, opacity: 0.55 }
      : { width: 1, opacity: 0.3, type: "dashed" };
    return {
      source: l.source,
      target: l.target,
      lineStyle: isHighlight ? base : { ...base, opacity: 0.05 },
    };
  });

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
        // Área de display = área onde o roam (pan/zoom) captura eventos.
        // Defaults são ~15% de margem, criando uma "caixa interativa" pequena no centro.
        // Zeramos os 4 lados para o roam funcionar em todo o canvas — a legenda
        // renderiza por cima sem subtrair a área interativa.
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        // roam built-in do ECharts é limitado ao bbox dos nós — implementamos
        // pan/zoom manualmente abaixo via zrender + dispatchAction.
        roam: false,
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
        // Range amplo de zoom — permite afastar muito (n=4 grande caber em tela) e aproximar bem.
        scaleLimit: { min: 0.02, max: 20 },
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
  const [selectedIds, setSelectedIds] = useState(() => new Set());

  // Ref com links atualizados para o handler de clique (que é registrado uma vez por init).
  const linksRef = useRef([]);
  useEffect(() => { linksRef.current = data?.links || []; }, [data]);

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

  // Limpa seleção quando troca de grafo
  useEffect(() => {
    setSelectedIds(prev => prev.size === 0 ? prev : new Set());
  }, [data]);

  // Renderiza / re-inicializa o gráfico quando o dado muda
  useEffect(() => {
    if (!ref.current || !data) return;
    chartRef.current?.dispose();
    const chart = echarts.init(ref.current);
    chartRef.current = chart;
    chart.setOption(montarOption(data, selectedIds));

    // Click único: marca/encadeia
    chart.on("click", (p) => {
      if (p.dataType !== "node") return;
      const id = p.data.id;
      setSelectedIds(prev => {
        if (prev.size === 0) return new Set([id]);
        if (prev.has(id)) return prev;
        const hl = computeHighlight(prev, linksRef.current);
        if (!hl.has(id)) return prev; // só permite encadear pelos vizinhos visíveis
        return new Set([...prev, id]);
      });
    });

    // Dblclick: abre a página da empresa/sócio
    chart.on("dblclick", (p) => {
      if (p.dataType !== "node") return;
      if (p.data._tipo === "empresa" && p.data._cnpj) {
        onVerEmpresa && onVerEmpresa(p.data._cnpj);
      } else if (p.data._tipo === "socio") {
        onVerSocio && onVerSocio({ nome_socio: p.data._nome, cpf_cnpj_socio: p.data._cpf });
      }
    });

    // ── Pan/zoom customizado (substitui roam built-in) ──────────────────────
    // Usamos zrender + dispatchAction porque o roam built-in do ECharts só
    // captura eventos perto dos nós, criando "zona morta" no resto do canvas.
    const zr = chart.getZr();
    let panning = false;
    let lastX = 0, lastY = 0;

    const onPanStart = (e) => {
      // Se está em cima de um nó, deixa o ECharts cuidar (draggable de nó).
      if (e.target) return;
      panning = true;
      lastX = e.offsetX;
      lastY = e.offsetY;
    };
    const onPanMove = (e) => {
      if (!panning) return;
      const dx = e.offsetX - lastX;
      const dy = e.offsetY - lastY;
      lastX = e.offsetX;
      lastY = e.offsetY;
      chart.dispatchAction({ type: "graphRoam", dx, dy });
    };
    const onPanEnd = () => { panning = false; };

    const onWheel = (e) => {
      const native = e.event;
      if (native && native.preventDefault) native.preventDefault();
      const delta = native ? (native.deltaY ?? -native.wheelDelta ?? 0) : 0;
      if (delta === 0) return;
      const zoom = delta < 0 ? 1.15 : 0.87;
      chart.dispatchAction({
        type: "graphRoam",
        zoom,
        originX: e.offsetX,
        originY: e.offsetY,
      });
    };

    zr.on("mousedown",  onPanStart);
    zr.on("mousemove",  onPanMove);
    zr.on("mouseup",    onPanEnd);
    zr.on("mousewheel", onWheel);
    // Fallback: se soltar o mouse fora do canvas, encerra o pan.
    const onDocMouseUp = () => { panning = false; };
    document.addEventListener("mouseup", onDocMouseUp);

    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      document.removeEventListener("mouseup", onDocMouseUp);
      window.removeEventListener("resize", onResize);
      chart.dispose();
      chartRef.current = null;
    };
  // selectedIds inicial é considerado apenas na primeira render; mudanças propagam pelo effect abaixo
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, onVerEmpresa, onVerSocio]);

  // Atualiza apenas os estilos quando a seleção muda (sem reinit, preserva o layout do force)
  useEffect(() => {
    if (!chartRef.current || !data) return;
    chartRef.current.setOption(montarOption(data, selectedIds));
  }, [selectedIds, data]);

  const totalNos = data?.nodes?.length || 0;
  const totalLinks = data?.links?.length || 0;

  return (
    <main className="md:ml-52 md:w-[calc(100%-13rem)] bg-[#f7f9fc] h-screen flex flex-col overflow-hidden">
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
          {selectedIds.size > 0 && (
            <button
              onClick={() => setSelectedIds(new Set())}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-colors"
              style={{ background: "#fef2f2", color: "#b91c1c", border: "1px solid #fecaca" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#fee2e2")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#fef2f2")}
            >
              <span className="material-symbols-outlined text-[14px]">close</span>
              Limpar seleção ({selectedIds.size})
            </button>
          )}
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
            className="absolute top-3 left-3 px-3 py-1.5 rounded-lg text-[11px] flex items-center gap-1.5 pointer-events-none"
            style={{ background: "rgba(255,255,255,0.9)", border: "1px solid #e2e8f0", color: "#94a3b8" }}
          >
            <span className="material-symbols-outlined text-[13px]">touch_app</span>
            Clique para marcar caminho · duplo-clique abre · arraste para mover
          </div>
        )}
      </div>
    </main>
  );
}
