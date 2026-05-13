import { useState } from "react";

function StatusBadge({ status }) {
  const map = {
    Ativa: "bg-green-50 text-green-700 border-green-200",
    Baixada: "bg-red-50 text-red-700 border-red-200",
    Suspensa: "bg-yellow-50 text-yellow-700 border-yellow-200",
    Inapta: "bg-red-50 text-red-700 border-red-200",
  };
  const cls = map[status] || "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span className={`px-2.5 py-1 text-label-caps rounded-full border ${cls}`}>
      {status?.toUpperCase() || "—"}
    </span>
  );
}

function Campo({ label, valor }) {
  if (!valor) return null;
  return (
    <div>
      <p className="text-label-caps text-tertiary mb-1">{label.toUpperCase()}</p>
      <p className="text-body-lg text-on-surface font-medium">{valor}</p>
    </div>
  );
}

function Secao({ titulo, icone, children, acao }) {
  return (
    <div className="bg-surface-container-lowest rounded-xl ambient-shadow border border-slate-200 overflow-hidden">
      <div className="p-space-md border-b border-slate-100 bg-slate-50 flex justify-between items-center">
        <h3 className="text-headline-sm text-on-surface flex items-center">
          <span className="material-symbols-outlined text-primary mr-2">{icone}</span>
          {titulo}
        </h3>
        {acao}
      </div>
      {children}
    </div>
  );
}

function iniciais(nome) {
  if (!nome) return "?";
  const parts = nome.trim().split(" ");
  return parts.length >= 2 ? parts[0][0] + parts[1][0] : parts[0][0];
}

const CORES = ["bg-blue-100 text-blue-700", "bg-slate-100 text-slate-700", "bg-purple-100 text-purple-700", "bg-green-100 text-green-700"];

function SocioRow({ socio, idx, onVerSocio, mostrarHistorico }) {
  const [expandido, setExpandido] = useState(false);
  const temHistorico = socio.qualificacoes_anteriores?.length > 0;

  return (
    <>
      <tr className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
        <td className="p-space-sm pl-space-md text-on-surface font-medium">
          <div className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold mr-3 text-xs ${CORES[idx % CORES.length]}`}>
              {iniciais(socio.nome_socio)}
            </div>
            <div>
              <div>{socio.nome_socio}</div>
              {socio.faixa_etaria && socio.faixa_etaria !== "Não informada" && (
                <div className="text-xs text-on-surface-variant">{socio.faixa_etaria}</div>
              )}
            </div>
          </div>
        </td>
        <td className="p-space-sm font-mono text-mono-data text-on-surface-variant">
          {socio.cpf_cnpj_socio || "—"}
        </td>
        <td className="p-space-sm text-on-surface">
          <div>{socio.qualificacao_atual?.descricao || "—"}</div>
          {socio.qualificacao_atual?.data_entrada && (
            <div className="text-xs text-on-surface-variant flex items-center gap-1 mt-0.5">
              <span className="material-symbols-outlined text-[12px] text-green-600">login</span>
              desde {socio.qualificacao_atual.data_entrada}
            </div>
          )}
          {mostrarHistorico && !socio.ativo && socio.qualificacoes_anteriores?.[0]?.saiu_em && (
            <div className="text-xs text-on-surface-variant flex items-center gap-1 mt-0.5">
              <span className="material-symbols-outlined text-[12px] text-red-400">logout</span>
              saiu em {socio.qualificacoes_anteriores[0].saiu_em}
            </div>
          )}
          {temHistorico && (
            <button
              onClick={() => setExpandido(v => !v)}
              className="text-xs text-primary hover:underline mt-1 flex items-center gap-0.5"
            >
              <span className="material-symbols-outlined text-[13px]">{expandido ? "expand_less" : "expand_more"}</span>
              {expandido ? "Ocultar histórico" : `Ver histórico (${socio.qualificacoes_anteriores.length})`}
            </button>
          )}
        </td>
        <td className="p-space-sm pr-space-md text-right">
          <button
            onClick={() => onVerSocio && onVerSocio(socio)}
            className="text-primary hover:text-primary-container text-body-sm font-medium"
          >
            Investigar
          </button>
        </td>
      </tr>
      {expandido && socio.qualificacoes_anteriores.map((q, qi) => (
        <tr key={qi} className="bg-slate-50/50 border-b border-slate-100">
          <td className="pl-16 py-2 text-xs text-on-surface-variant" colSpan={2}>
            Qualificação anterior
          </td>
          <td className="py-2 text-xs text-on-surface-variant">
            {q.descricao || "—"}
            {q.data_entrada && <span className="ml-2">desde {q.data_entrada}</span>}
            {q.saiu_em && <span className="ml-2 text-red-400">até {q.saiu_em}</span>}
          </td>
          <td />
        </tr>
      ))}
    </>
  );
}

export default function ResultadoEmpresa({ dados, onVoltar, onVerSocio }) {
  const [exInativos, setExInativos] = useState(false);

  if (!dados) return null;

  const telefone =
    dados.ddd1 && dados.telefone1
      ? `(${dados.ddd1}) ${dados.telefone1}${dados.ddd2 && dados.telefone2 ? ` / (${dados.ddd2}) ${dados.telefone2}` : ""}`
      : null;

  const enderecoLinha1 = [dados.tipo_logradouro, dados.logradouro, dados.numero && `nº ${dados.numero}`].filter(Boolean).join(" ");
  const enderecoLinha2 = [dados.complemento, dados.bairro].filter(Boolean).join(", ");
  const enderecoLinha3 = [dados.municipio_descricao, dados.uf].filter(Boolean).join(" - ");

  const sociosAtivos   = dados.socios_ativos   || [];
  const sociosInativos = dados.socios_inativos || [];
  const totalSocios    = sociosAtivos.length + sociosInativos.length;
  const empresaEncerrada = dados.situacao_cadastral === "Baixada" || dados.situacao_cadastral === "Nula";
  const labelAtivos = empresaEncerrada ? "Sócios até o Fechamento" : "Sócios Ativos";

  return (
    <main className="flex-1 md:ml-64 bg-background min-h-screen">
      {/* Header mobile */}
      <header className="md:hidden sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200 h-16 flex items-center justify-between px-4">
        <button onClick={onVoltar} className="text-slate-500 hover:text-slate-900">
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <span className="text-xl font-bold text-slate-900">CorpIntel</span>
        <div className="w-8" />
      </header>

      {/* Header web */}
      <header className="hidden md:flex sticky top-0 z-30 bg-white/80 backdrop-blur-md h-16 items-center justify-between px-8 border-b border-slate-200 shadow-sm">
        <div className="text-xl font-bold text-slate-900">CorpIntel</div>
        <div className="flex items-center space-x-4 text-slate-500">
          <span className="material-symbols-outlined cursor-pointer hover:text-slate-900">notifications</span>
        </div>
      </header>

      <div className="p-4 md:p-[40px] max-w-[1440px] mx-auto space-y-gutter">
        {/* Breadcrumb */}
        <div className="flex items-center space-x-2 text-on-surface-variant text-body-sm">
          <button onClick={onVoltar} className="hover:text-primary transition-colors flex items-center">
            <span className="material-symbols-outlined text-[18px] mr-1">arrow_back</span>
            Voltar à busca
          </button>
          <span>/</span>
          <span className="text-on-surface font-medium">Perfil da Empresa</span>
        </div>

        {/* Hero card */}
        <div className="bg-surface-container-lowest rounded-xl ambient-shadow p-6 md:p-8 border border-slate-200 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-6 opacity-5 pointer-events-none">
            <span className="material-symbols-outlined" style={{ fontSize: "120px" }}>domain</span>
          </div>
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 relative z-10">
            <div>
              <div className="flex items-center space-x-3 mb-2 flex-wrap gap-y-1">
                <h2 className="text-headline-md text-on-surface">{dados.razao_social}</h2>
                <StatusBadge status={dados.situacao_cadastral} />
              </div>
              {dados.nome_fantasia && (
                <p className="text-body-md text-on-surface-variant mb-1">{dados.nome_fantasia}</p>
              )}
              <p className="font-mono text-mono-data text-on-surface-variant">
                CNPJ: {dados.cnpj_completo_formatado || dados.cnpj_completo}
              </p>
              {dados.situacao_especial && (
                <p className="mt-1 text-body-sm text-amber-700 font-medium">
                  ⚠ {dados.situacao_especial}
                  {dados.data_situacao_especial && ` (desde ${dados.data_situacao_especial})`}
                </p>
              )}
            </div>
            <div className="mt-4 md:mt-0">
              <span className="px-3 py-1.5 bg-surface-container text-on-surface-variant rounded-full text-body-sm border border-outline-variant">
                {dados.matriz_filial || "—"}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-6 border-t border-slate-100 relative z-10">
            <Campo label="Capital Social" valor={dados.capital_social} />
            <Campo label="Início de Atividade" valor={dados.data_inicio} />
            <Campo label="Situação desde" valor={dados.data_situacao} />
            <Campo label="Sede" valor={enderecoLinha3 || null} />
          </div>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
          {/* Coluna principal */}
          <div className="lg:col-span-2 space-y-gutter">

            {/* CNAEs */}
            <Secao titulo="Atividade Econômica (CNAE)" icone="work">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="text-label-caps text-tertiary p-space-sm pl-space-md w-28">CÓDIGO</th>
                      <th className="text-label-caps text-tertiary p-space-sm">DESCRIÇÃO</th>
                      <th className="text-label-caps text-tertiary p-space-sm pr-space-md w-24">TIPO</th>
                    </tr>
                  </thead>
                  <tbody className="text-body-sm">
                    {dados.cnae_principal_codigo && (
                      <tr className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors border-l-4 border-primary">
                        <td className="p-space-sm pl-space-md font-mono text-mono-data text-on-surface-variant">
                          {dados.cnae_principal_codigo}
                        </td>
                        <td className="p-space-sm text-on-surface font-medium">
                          {dados.cnae_principal_descricao || dados.cnae_principal_codigo}
                        </td>
                        <td className="p-space-sm pr-space-md">
                          <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[10px] text-label-caps rounded-full border border-blue-200">
                            PRIMÁRIA
                          </span>
                        </td>
                      </tr>
                    )}
                    {(dados.cnae_secundarios || []).map((cnae, i) => (
                      <tr key={i} className="border-b border-slate-100 border-l-4 border-transparent hover:bg-slate-50/50 transition-colors">
                        <td className="p-space-sm pl-space-md font-mono text-mono-data text-on-surface-variant">
                          {cnae.codigo}
                        </td>
                        <td className="p-space-sm text-on-surface">
                          {cnae.descricao || cnae.codigo}
                        </td>
                        <td className="p-space-sm pr-space-md">
                          <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-[10px] text-label-caps rounded-full">
                            SECUNDÁRIA
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Secao>

            {/* QSA — Sócios Ativos / até o Fechamento */}
            <Secao titulo={`Quadro Societário — ${labelAtivos} (${sociosAtivos.length})`} icone="groups">
              {sociosAtivos.length === 0 ? (
                <p className="p-space-md text-body-sm text-on-surface-variant">
                  {empresaEncerrada ? "Nenhum sócio registrado até o fechamento." : "Nenhum sócio ativo cadastrado."}
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200">
                        <th className="text-label-caps text-tertiary p-space-sm pl-space-md">NOME</th>
                        <th className="text-label-caps text-tertiary p-space-sm">DOCUMENTO</th>
                        <th className="text-label-caps text-tertiary p-space-sm">QUALIFICAÇÃO</th>
                        <th className="text-label-caps text-tertiary p-space-sm pr-space-md text-right">AÇÃO</th>
                      </tr>
                    </thead>
                    <tbody className="text-body-sm">
                      {sociosAtivos.map((s, i) => (
                        <SocioRow key={i} socio={s} idx={i} onVerSocio={onVerSocio} mostrarHistorico={false} />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Secao>

            {/* QSA — Ex-Sócios */}
            {sociosInativos.length > 0 && (
              <div className="bg-surface-container-lowest rounded-xl ambient-shadow border border-slate-200 overflow-hidden">
                <button
                  onClick={() => setExInativos(v => !v)}
                  className="w-full p-space-md border-b border-slate-100 bg-slate-50 flex justify-between items-center hover:bg-slate-100 transition-colors"
                >
                  <h3 className="text-headline-sm text-on-surface-variant flex items-center">
                    <span className="material-symbols-outlined text-on-surface-variant mr-2">person_off</span>
                    Ex-Sócios ({sociosInativos.length})
                  </h3>
                  <span className="material-symbols-outlined text-on-surface-variant">
                    {exInativos ? "expand_less" : "expand_more"}
                  </span>
                </button>
                {exInativos && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200">
                          <th className="text-label-caps text-tertiary p-space-sm pl-space-md">NOME</th>
                          <th className="text-label-caps text-tertiary p-space-sm">DOCUMENTO</th>
                          <th className="text-label-caps text-tertiary p-space-sm">ÚLTIMA QUALIFICAÇÃO</th>
                          <th className="text-label-caps text-tertiary p-space-sm pr-space-md text-right">AÇÃO</th>
                        </tr>
                      </thead>
                      <tbody className="text-body-sm">
                        {sociosInativos.map((s, i) => (
                          <SocioRow key={i} socio={s} idx={i} onVerSocio={onVerSocio} mostrarHistorico={true} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Simples / MEI */}
            <Secao titulo="Simples Nacional / MEI" icone="receipt_long">
              <div className="p-space-md grid grid-cols-2 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-label-caps text-tertiary mb-1">SIMPLES NACIONAL</p>
                  <p className="text-body-lg text-on-surface font-medium">
                    {dados.opcao_simples === "S" ? (
                      <span className="px-2 py-0.5 bg-green-50 text-green-700 text-[11px] font-bold rounded-full border border-green-200">OPTANTE</span>
                    ) : dados.opcao_simples === "N" ? "Não optante" : "—"}
                  </p>
                </div>
                <div>
                  <p className="text-label-caps text-tertiary mb-1">MEI</p>
                  <p className="text-body-lg text-on-surface font-medium">
                    {dados.opcao_mei === "S" ? (
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[11px] font-bold rounded-full border border-blue-200">MEI</span>
                    ) : dados.opcao_mei === "N" ? "Não" : "—"}
                  </p>
                </div>
                {dados.data_opcao_simples   && <Campo label="Opção Simples"    valor={dados.data_opcao_simples} />}
                {dados.data_exclusao_simples && <Campo label="Exclusão Simples" valor={dados.data_exclusao_simples} />}
                {dados.data_opcao_mei        && <Campo label="Opção MEI"        valor={dados.data_opcao_mei} />}
                {dados.data_exclusao_mei     && <Campo label="Exclusão MEI"     valor={dados.data_exclusao_mei} />}
              </div>
            </Secao>
          </div>

          {/* Coluna lateral */}
          <div className="space-y-gutter">
            {/* Estabelecimento */}
            <Secao titulo="Estabelecimento" icone="location_on">
              <div className="p-space-md">
                <ul className="space-y-4">
                  <li className="flex items-start">
                    <span className="material-symbols-outlined text-primary text-base mt-0.5 mr-2">store</span>
                    <div>
                      <p className="text-body-sm font-semibold text-on-surface">{dados.matriz_filial || "Matriz"}</p>
                      {enderecoLinha1 && <p className="text-body-sm text-on-surface-variant">{enderecoLinha1}</p>}
                      {enderecoLinha2 && <p className="text-body-sm text-on-surface-variant">{enderecoLinha2}</p>}
                      {enderecoLinha3 && <p className="text-body-sm text-on-surface-variant">{enderecoLinha3}</p>}
                      {dados.cep && <p className="font-mono text-[11px] text-tertiary mt-1">CEP: {dados.cep}</p>}
                    </div>
                  </li>
                  {telefone && (
                    <li className="flex items-center gap-2 pt-3 border-t border-slate-100 text-body-sm text-on-surface">
                      <span className="material-symbols-outlined text-outline text-[16px]">call</span>
                      {telefone}
                    </li>
                  )}
                  {dados.email && (
                    <li className="flex items-center gap-2 text-body-sm text-on-surface truncate">
                      <span className="material-symbols-outlined text-outline text-[16px]">mail</span>
                      {dados.email}
                    </li>
                  )}
                </ul>
              </div>
            </Secao>

            {/* Identificação */}
            <Secao titulo="Identificação" icone="info">
              <div className="p-space-md space-y-4">
                <Campo label="Natureza Jurídica"          valor={dados.natureza_juridica_descricao} />
                <Campo label="Porte"                       valor={dados.porte} />
                <Campo label="Qualificação do Responsável" valor={dados.qualificacao_responsavel_descricao} />
                <Campo label="Motivo da Situação"          valor={dados.motivo_situacao} />
                {dados.dt_primeira_carga && (
                  <div>
                    <p className="text-label-caps text-tertiary mb-1">NA BASE RF DESDE</p>
                    <p className="text-body-sm text-on-surface">{dados.dt_primeira_carga}</p>
                  </div>
                )}
              </div>
            </Secao>
          </div>
        </div>
      </div>
    </main>
  );
}
