import { useState } from "react";
import { buscarEmpresaPorCnpj } from "./api";

import Sidebar from "./components/Sidebar";
import Login from "./components/Login";
import HomeSelecao from "./components/HomeSelecao";
import BuscaEmpresa from "./components/BuscaEmpresa";
import BuscaSocio from "./components/BuscaSocio";
import ResultadoEmpresa from "./components/ResultadoEmpresa";
import ResultadoSocio from "./components/ResultadoSocio";
import GrafoRede from "./components/GrafoRede";

export default function App() {
  const [tela, setTela] = useState("home");
  const [telaAnterior, setTelaAnterior] = useState(null);
  const [empresaDetalhe, setEmpresaDetalhe] = useState(null);
  const [socioInicial, setSocioInicial] = useState(null);
  const [grafoRaiz, setGrafoRaiz] = useState(null);
  const [loadingNav, setLoadingNav] = useState(false);

  function irPara(proxTela) {
    setTelaAnterior(tela);
    setTela(proxTela);
  }

  async function abrirEmpresa(cnpjOuDados) {
    if (typeof cnpjOuDados === "object" && cnpjOuDados !== null) {
      setEmpresaDetalhe(cnpjOuDados);
      setTelaAnterior(tela);
      setTela("resultado-empresa");
      return;
    }
    setLoadingNav(true);
    try {
      const dados = await buscarEmpresaPorCnpj(String(cnpjOuDados));
      if (dados) {
        setEmpresaDetalhe(dados);
        setTelaAnterior(tela);
        setTela("resultado-empresa");
      }
    } catch (err) {
      console.error("Erro ao carregar empresa:", err);
    } finally {
      setLoadingNav(false);
    }
  }

  function abrirSocio(item) {
    setSocioInicial(item);
    setTelaAnterior(tela);
    setTela("resultado-socio");
  }

  function abrirGrafo(raiz) {
    setGrafoRaiz(raiz);
    setTelaAnterior(tela);
    setTela("grafo-rede");
  }

  const mostrarSidebar = tela !== "login";

  return (
    <div className="flex min-h-screen bg-background">
      {mostrarSidebar && <Sidebar tela={tela} irPara={irPara} />}

      <div className="flex-1 flex flex-col">
        {loadingNav && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm">
            <div className="bg-white rounded-xl px-8 py-6 shadow-dropdown flex items-center gap-4">
              <span className="material-symbols-outlined text-primary text-[28px] animate-spin">progress_activity</span>
              <span className="text-body-md text-on-surface">Carregando...</span>
            </div>
          </div>
        )}

        {tela === "login" && (
          <Login onLogin={() => irPara("home")} />
        )}

        {tela === "home" && (
          <HomeSelecao
            irParaEmpresa={() => irPara("empresa")}
            irParaSocio={() => irPara("socio")}
          />
        )}

        {tela === "empresa" && (
          <BuscaEmpresa
            onSelecionarEmpresa={abrirEmpresa}
            onVoltar={() => irPara("home")}
          />
        )}

        {tela === "socio" && (
          <BuscaSocio
            onSelecionarSocio={abrirSocio}
            onVoltar={() => irPara("home")}
          />
        )}

        {tela === "resultado-empresa" && (
          <ResultadoEmpresa
            dados={empresaDetalhe}
            onVoltar={() => irPara(telaAnterior || "empresa")}
            onVerSocio={abrirSocio}
            onVerEmpresa={abrirEmpresa}
            onAbrirGrafo={abrirGrafo}
          />
        )}

        {tela === "resultado-socio" && (
          <ResultadoSocio
            socioInicial={socioInicial}
            onVoltar={() => irPara(telaAnterior || "socio")}
            onVerEmpresa={abrirEmpresa}
            onVerSocio={abrirSocio}
            onAbrirGrafo={abrirGrafo}
          />
        )}

        {tela === "grafo-rede" && grafoRaiz && (
          <GrafoRede
            raiz={grafoRaiz}
            onVoltar={() => irPara(telaAnterior || "home")}
            onVerEmpresa={abrirEmpresa}
            onVerSocio={abrirSocio}
          />
        )}
      </div>
    </div>
  );
}
