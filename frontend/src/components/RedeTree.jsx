import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";

const COR_ROOT = "#0a1f3d";
const COR_SOCIO = "#0085ca";
const COR_EMPRESA = "#15803d";
const COR_EX = "#64748b";
const COR_INATIVA = "#94a3b8";

function countNodes(node) {
  return 1 + (node.children || []).reduce((sum, child) => sum + countNodes(child), 0);
}

function maxDepth(node) {
  return 1 + Math.max(0, ...(node.children || []).map(maxDepth));
}

function treeHeight(data) {
  return Math.max(760, Math.min(7000, countNodes(data) * 82));
}

function treeWidth(data) {
  const depth = maxDepth(data);
  const total = countNodes(data);
  return Math.max(1120, Math.min(2200, 520 + depth * 360 + total * 6));
}

function nodeColor(node, depth, rootKind) {
  if (depth === 0) return COR_ROOT;

  if (rootKind === "empresa") {
    if (depth === 1) return node.value === "ex_socio" ? COR_EX : COR_SOCIO;
    return node.value === "Ativa" || node.value === "empresa" ? COR_EMPRESA : COR_INATIVA;
  }

  if (depth === 1) return node.value === "empresa" ? COR_EMPRESA : COR_INATIVA;
  return node.value === "ex_socio" ? COR_EX : COR_SOCIO;
}

function styleNode(node, depth, rootKind) {
  const color = nodeColor(node, depth, rootKind);
  const styled = {
    ...node,
    symbolSize: depth === 0 ? 14 : depth === 1 ? 9 : 6,
    itemStyle: { color },
    label: {
      color,
      fontWeight: depth === 0 ? "bold" : undefined,
      position: depth <= 1 ? "left" : undefined,
      align: depth <= 1 ? "right" : undefined,
      distance: depth === 1 ? 10 : undefined,
    },
  };

  if (node.children?.length) {
    styled.children = node.children.map(child => styleNode(child, depth + 1, rootKind));
  }

  return styled;
}

function makeOption(styledData, initialDepth) {
  const totalNodes = countNodes(styledData);
  const labelSize = totalNodes > 90 ? 10 : 11;

  return {
    tooltip: {
      trigger: "item",
      triggerOn: "mousemove",
      formatter: (p) => {
        const detail = p.data.detail || (
          p.data.value && !["root", "socio", "ex_socio", "empresa", "empresa_inativa"].includes(p.data.value)
            ? p.data.value
            : ""
        );
        return detail
          ? `<b>${p.data.name}</b><br/><span style="color:#64748b">${detail}</span>`
          : `<b>${p.data.name}</b>`;
      },
    },
    series: [{
      type: "tree",
      data: [styledData],

      top: 36,
      left: "24%",
      bottom: 36,
      right: "10%",

      orient: "LR",
      edgeShape: "polyline",
      edgeForkPosition: "42%",

      symbolSize: 7,
      roam: true,
      scaleLimit: {
        min: 0.08,
        max: 2.5,
      },

      label: {
        position: "left",
        verticalAlign: "middle",
        align: "right",
        fontSize: labelSize,
        color: "#334155",
        overflow: "truncate",
        width: 240,
      },

      leaves: {
        label: {
          position: "right",
          verticalAlign: "middle",
          align: "left",
          fontSize: labelSize,
          overflow: "truncate",
          width: 280,
        },
      },

      emphasis: { focus: "descendant" },
      expandAndCollapse: true,
      initialTreeDepth: initialDepth,
      animationDuration: 300,
      animationDurationUpdate: 450,
    }],
  };
}

function useTreeChart(ref, data, rootKind, initialDepth) {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current || !data) return undefined;

    chartRef.current?.dispose();
    const chart = echarts.init(ref.current);
    chartRef.current = chart;
    chart.setOption(makeOption(styleNode(data, 0, rootKind), initialDepth));

    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, [data, initialDepth, ref, rootKind]);
}

function Legend({ rootKind }) {
  const items = rootKind === "empresa"
    ? [
        ["Raiz", COR_ROOT],
        ["Sócio atual", COR_SOCIO],
        ["Ex-sócio", COR_EX],
        ["Empresa relacionada", COR_EMPRESA],
      ]
    : [
        ["Raiz", COR_ROOT],
        ["Empresa atual", COR_EMPRESA],
        ["Ex-empresa", COR_INATIVA],
        ["Sócio relacionado", COR_SOCIO],
        ["Ex-sócio relacionado", COR_EX],
      ];

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-3 pt-2 text-[11px] text-slate-500">
      {items.map(([label, color]) => (
        <span key={label} className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
          {label}
        </span>
      ))}
    </div>
  );
}

function TreeViewport({ children, width }) {
  return (
    <div
      className="w-full overflow-hidden cursor-grab active:cursor-grabbing"
      style={{ height: 420 }}
    >
      <div style={{ width: `${width}px`, maxWidth: "none" }}>
        {children}
      </div>
    </div>
  );
}

export function RedeEmpresa({ data }) {
  const ref = useRef(null);
  const treeData = useMemo(() => {
    if (!data) return null;
    return {
      ...data,
      children: data.children || [],
    };
  }, [data]);

  useTreeChart(ref, treeData, "empresa", 2);
  const width = treeData ? treeWidth(treeData) : 1120;
  const height = treeData ? treeHeight(treeData) : 560;

  return (
    <div>
      <Legend rootKind="empresa" />
      <TreeViewport width={width}>
        <div ref={ref} style={{ width: `${width}px`, height }} />
      </TreeViewport>
    </div>
  );
}

export function RedeSocio({ perfil }) {
  const ref = useRef(null);
  const treeData = useMemo(() => {
    if (!perfil) return null;

    const sociosRelacionados = [
      ...(perfil.socios_comuns || []).map(s => ({ ...s, value: "socio", detail: "Socio relacionado" })),
      ...(perfil.ex_socios_comuns || []).map(s => ({ ...s, value: "ex_socio", detail: "Ex-socio relacionado" })),
    ];

    const sociosDaEmpresa = (cnpjBasico) => sociosRelacionados
      .filter(s => (s.cnpjs || []).includes(cnpjBasico))
      .slice(0, 40)
      .map(s => ({
        name: s.nome,
        value: s.value,
        detail: (s.qualificacoes || []).join(", ") || s.detail,
      }));

    const mapEmpresa = (empresa, ativa) => ({
      name: empresa.razao_social || empresa.cnpj_basico,
      value: ativa ? "empresa" : "empresa_inativa",
      detail: ativa ? "Empresa" : "Ex-empresa",
      children: sociosDaEmpresa(empresa.cnpj_basico),
    });

    return {
      name: perfil.info?.nome || "Socio",
      value: "root",
      children: [
        ...(perfil.empresas_ativas || []).map(e => mapEmpresa(e, true)),
        ...(perfil.empresas_inativas || []).map(e => mapEmpresa(e, false)),
      ],
    };
  }, [perfil]);

  useTreeChart(ref, treeData, "socio", 2);
  const width = treeData ? treeWidth(treeData) : 1120;
  const height = treeData ? treeHeight(treeData) : 560;

  return (
    <div>
      <Legend rootKind="socio" />
      <TreeViewport width={width}>
        <div ref={ref} style={{ width: `${width}px`, height }} />
      </TreeViewport>
    </div>
  );
}
