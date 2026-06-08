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

function treeHeight(data) {
  return Math.max(600, Math.min(4000, countNodes(data) * 45));
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

      top: "3%",
      left: "14%",
      bottom: "3%",
      right: "30%",

      orient: "LR",
      edgeShape: "polyline",
      edgeForkPosition: "55%",

      symbolSize: 7,
      roam: true,

      label: {
        position: "left",
        verticalAlign: "middle",
        align: "right",
        fontSize: labelSize,
        color: "#334155",
        overflow: "truncate",
        width: 210,
      },

      leaves: {
        label: {
          position: "right",
          verticalAlign: "middle",
          align: "left",
          fontSize: labelSize,
          overflow: "truncate",
          width: 240,
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

export function RedeEmpresa({ data }) {
  const ref = useRef(null);
  const treeData = useMemo(() => {
    if (!data) return null;
    return {
      ...data,
      children: (data.children || []).map(socio => ({
        ...socio,
        collapsed: true,
      })),
    };
  }, [data]);

  useTreeChart(ref, treeData, "empresa", 1);

  return <div ref={ref} style={{ width: "100%", height: treeData ? treeHeight(treeData) : 560 }} />;
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
      collapsed: true,
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

  useTreeChart(ref, treeData, "socio", 1);

  return <div ref={ref} style={{ width: "100%", height: treeData ? treeHeight(treeData) : 560 }} />;
}
