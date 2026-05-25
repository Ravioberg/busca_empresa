import { useEffect, useRef } from "react";
import * as echarts from "echarts";

// Cores por profundidade e tipo
const COR_ROOT    = "#0a1f3d";
const COR_SOCIO   = "#0085ca";
const COR_ATIVA   = "#15803d";
const COR_INATIVA = "#94a3b8";
const COR_GROUP   = "#64748b";

function styleEmpresaNode(node, depth) {
  const n = { ...node };
  if (depth === 0) {
    n.symbolSize = 14;
    n.itemStyle  = { color: COR_ROOT };
    n.label      = { fontWeight: "bold", color: COR_ROOT };
  } else if (depth === 1) {
    n.symbolSize = 9;
    n.itemStyle  = { color: COR_SOCIO };
    n.label      = { color: COR_SOCIO };
  } else {
    const ativa  = node.value === "Ativa";
    n.symbolSize = 6;
    n.itemStyle  = { color: ativa ? COR_ATIVA : COR_INATIVA };
    n.label      = { color: ativa ? COR_ATIVA : COR_INATIVA };
  }
  if (node.children?.length) {
    n.children = node.children.map(c => styleEmpresaNode(c, depth + 1));
  }
  return n;
}

function styleSocioNode(node, depth) {
  const n = { ...node };
  if (depth === 0) {
    n.symbolSize = 14;
    n.itemStyle  = { color: COR_ROOT };
    n.label      = { fontWeight: "bold", color: COR_ROOT };
  } else if (depth === 1) {
    // grupo: "Empresas" ou "Sócios em Comum"
    n.symbolSize = 8;
    n.itemStyle  = { color: COR_GROUP };
    n.label      = { fontWeight: "600", color: COR_GROUP };
  } else {
    const isSocio = node.value === "socio";
    n.symbolSize  = 6;
    n.itemStyle   = { color: isSocio ? COR_SOCIO : COR_ATIVA };
    n.label       = { color: isSocio ? COR_SOCIO : COR_ATIVA };
  }
  if (node.children?.length) {
    n.children = node.children.map(c => styleSocioNode(c, depth + 1));
  }
  return n;
}

function makeOption(styledData, initialDepth) {
  return {
    tooltip: {
      trigger: "item",
      triggerOn: "mousemove",
      formatter: (p) => p.data.value && p.data.value !== "root" && p.data.value !== "socio"
        ? `<b>${p.data.name}</b><br/><span style="color:#64748b">${p.data.value}</span>`
        : `<b>${p.data.name}</b>`,
    },
    series: [{
      type: "tree",
      data: [styledData],
      top: "3%",
      left: "18%",
      bottom: "3%",
      right: "22%",
      orient: "LR",
      symbolSize: 7,
      roam: true,
      label: {
        position: "left",
        verticalAlign: "middle",
        align: "right",
        fontSize: 11,
        color: "#334155",
      },
      leaves: {
        label: {
          position: "right",
          verticalAlign: "middle",
          align: "left",
          fontSize: 11,
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

export function RedeEmpresa({ data }) {
  const ref      = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current || !data) return;
    chartRef.current?.dispose();
    const chart = echarts.init(ref.current);
    chartRef.current = chart;
    chart.setOption(makeOption(styleEmpresaNode(data, 0), 1));
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); chart.dispose(); };
  }, [data]);

  return <div ref={ref} style={{ width: "100%", height: 560 }} />;
}

export function RedeSocio({ perfil }) {
  const ref      = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current || !perfil) return;

    const empresasAtivas = (perfil.empresas_ativas || []).map(e => ({
      name:  e.razao_social || e.cnpj_basico,
      value: "empresa",
    }));
    const empresasInativas = (perfil.empresas_inativas || []).map(e => ({
      name:  e.razao_social || e.cnpj_basico,
      value: "empresa_inativa",
    }));
    const sociosComuns = (perfil.socios_comuns || []).map(s => ({
      name:  s.nome,
      value: "socio",
    }));
    const exSociosComuns = (perfil.ex_socios_comuns || []).map(s => ({
      name:  s.nome,
      value: "socio",
    }));

    const nome = perfil.info?.nome || "Sócio";

    const children = [];
    if (empresasAtivas.length) {
      children.push({ name: `Empresas Ativas (${empresasAtivas.length})`, value: "group", children: empresasAtivas });
    }
    if (empresasInativas.length) {
      children.push({ name: `Ex-Empresas (${empresasInativas.length})`, value: "group", children: empresasInativas });
    }
    if (sociosComuns.length) {
      children.push({ name: `Sócios em Comum (${sociosComuns.length})`, value: "group", children: sociosComuns });
    }
    if (exSociosComuns.length) {
      children.push({ name: `Ex-Sócios em Comum (${exSociosComuns.length})`, value: "group", children: exSociosComuns });
    }

    const root = { name: nome, value: "root", children };

    chartRef.current?.dispose();
    const chart = echarts.init(ref.current);
    chartRef.current = chart;
    chart.setOption(makeOption(styleSocioNode(root, 0), 2));
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); chart.dispose(); };
  }, [perfil]);

  return <div ref={ref} style={{ width: "100%", height: 560 }} />;
}
