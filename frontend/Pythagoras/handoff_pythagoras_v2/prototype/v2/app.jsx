// ═══════════════════════════════════════════════════════════════════════
// Pythagoras v2 — main app
// ═══════════════════════════════════════════════════════════════════════
const { useState, useEffect, useRef, useMemo } = React;

// ─── Sidebar ──────────────────────────────────────────────────────────
function Sidebar({ activeCnpj, onPick }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">π</div>
        <div>
          <div className="brand-name">Pythagoras</div>
          <div className="brand-sub">CNPJ Intelligence</div>
        </div>
      </div>

      <div className="side-group">
        <div className="side-group-label">
          <span>Buscas recentes</span>
          <span className="count">{MOCK_HISTORY.length}</span>
        </div>
        {MOCK_HISTORY.map(h => (
          <div
            key={h.cnpj}
            className={`side-item ${h.cnpj === activeCnpj ? 'active' : ''}`}
            onClick={() => onPick?.(h)}
          >
            <div className="hist-left">
              <span className="hist-nome">{h.nome}</span>
              <span className="hist-meta">{h.cnpj} · {h.uf}</span>
            </div>
            <span className="hist-when">{h.when}</span>
          </div>
        ))}
      </div>

      <div className="side-footer">
        <span className="base-label">Base RFB</span>
        <span className="base-val">{fmtMonth(MOCK_BASE.mes_atual)}</span>
        <span style={{ marginTop: 4 }}>
          {(MOCK_BASE.total_empresas / 1_000_000).toFixed(1)}M empresas ·
          {' '}{(MOCK_BASE.total_socios / 1_000_000).toFixed(1)}M sócios
        </span>
      </div>
    </aside>
  );
}

// ─── Search bar ────────────────────────────────────────────────────────
function SearchBar({ value, onChange, onSubmit, autoFocus, placeholder, compact }) {
  const [focused, setFocused] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const raw = (value || '').replace(/\D/g, '');
  const valid = validCNPJ(value);
  const validity = raw.length === 0 ? 'idle' : (valid ? 'ok' : (raw.length === 14 ? 'bad' : 'idle'));
  const ref = useRef(null);
  useEffect(() => { if (autoFocus) ref.current?.focus(); }, [autoFocus]);

  const filtered = useMemo(() => {
    if (!value) return [];
    const digits = raw;
    const txt = value.toLowerCase().trim();
    return MOCK_SUGGESTIONS.filter(s => {
      if (digits.length >= 2 && s.cnpj.replace(/\D/g,'').startsWith(digits)) return true;
      if (s.razao_social.toLowerCase().includes(txt) || s.nome_fantasia.toLowerCase().includes(txt)) return true;
      return false;
    }).slice(0, 4);
  }, [value, raw]);

  const showPop = focused && filtered.length > 0;

  const handleKey = (e) => {
    if (e.key === 'Enter') {
      if (showPop && filtered[activeIdx]) onSubmit?.(filtered[activeIdx].cnpj);
      else onSubmit?.(value);
    } else if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(filtered.length - 1, i + 1)); }
    else if (e.key === 'ArrowUp')   { e.preventDefault(); setActiveIdx(i => Math.max(0, i - 1)); }
  };

  return (
    <div className="searchbar-wrap">
      <div className="searchbar">
        <span className="sb-icon"><Icon.search /></span>
        <input
          ref={ref}
          value={value}
          onChange={(e)=>onChange(maskCNPJ(e.target.value))}
          onFocus={()=>setFocused(true)}
          onBlur={()=>setTimeout(()=>setFocused(false), 160)}
          onKeyDown={handleKey}
          placeholder={placeholder || "CNPJ, razão social ou nome fantasia…"}
          inputMode="numeric"
          spellCheck={false}
        />
        <span className={`sb-validity ${validity}`}>
          {validity === 'ok'   && <>Válido</>}
          {validity === 'bad'  && <>Inválido</>}
          {validity === 'idle' && raw.length > 0 && <>{raw.length}/14</>}
          {validity === 'idle' && raw.length === 0 && <>14 dígitos</>}
        </span>
        {!compact && <span className="sb-kbd">↵</span>}
      </div>

      {showPop && (
        <div className="sb-pop">
          <div className="sb-pop-head">
            <span>{filtered.length} sugestões</span>
            <span>↑ ↓ ↵</span>
          </div>
          {filtered.map((s, i) => (
            <div
              key={s.cnpj}
              className={`sb-pop-item ${i === activeIdx ? 'active' : ''}`}
              onMouseEnter={()=>setActiveIdx(i)}
              onMouseDown={(e)=>{ e.preventDefault(); onSubmit?.(s.cnpj); }}
            >
              <div className="nome">{s.razao_social}</div>
              <div className="cnpj mono">{s.cnpj}</div>
              <div className="cnae">{s.cnae_principal} · {s.nome_fantasia}</div>
              <div className="uf mono">{s.uf}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Idle state ────────────────────────────────────────────────────────
function IdleState({ query, setQuery, onSubmit }) {
  const hints = [
    "47.819.002/0001-70",
    "marambaia",
    "12.548.330/0001-03",
    "fundo pindoba",
  ];
  return (
    <div className="idle">
      <div className="idle-mark"><Icon.building /></div>
      <h1>Inteligência cadastral sobre empresas brasileiras.</h1>
      <p>Consulta direta à base mensal da Receita Federal, com histórico de presença e quadro societário rastreado mês a mês desde março de 2023.</p>
      <div className="idle-search">
        <SearchBar value={query} onChange={setQuery} onSubmit={onSubmit} autoFocus />
      </div>
      <div className="idle-hints">
        {hints.map(h => (
          <span key={h} className="hint-chip" onClick={()=>{ setQuery(maskCNPJ(h)); onSubmit(h); }}>
            {h}
          </span>
        ))}
      </div>
      <div className="idle-base">
        <div className="item">
          <span className="lbl">Base atual</span>
          <span className="val">{fmtMonth(MOCK_BASE.mes_atual)}</span>
        </div>
        <div className="sep" />
        <div className="item">
          <span className="lbl">Empresas</span>
          <span className="val">{(MOCK_BASE.total_empresas / 1_000_000).toFixed(1)}M</span>
        </div>
        <div className="sep" />
        <div className="item">
          <span className="lbl">Sócios indexados</span>
          <span className="val">{(MOCK_BASE.total_socios / 1_000_000).toFixed(1)}M</span>
        </div>
        <div className="sep" />
        <div className="item">
          <span className="lbl">Histórico desde</span>
          <span className="val">mar/2023</span>
        </div>
      </div>
    </div>
  );
}

// ─── Loading state ─────────────────────────────────────────────────────
function LoadingState({ cnpj }) {
  return (
    <div className="loading">
      <div className="loading-bar">
        <span className="dot" />
        <span>Consultando · {cnpj}</span>
      </div>
      <div className="section">
        <div className="section-body">
          <div className="skel" style={{ width: 260, height: 18 }} />
          <div className="skel" style={{ width: 180, height: 10, marginTop: 12 }} />
          <div className="skel skel-block" />
        </div>
      </div>
      <div className="section">
        <div className="section-body">
          <div className="skel skel-line" style={{ width: '40%' }} />
          <div className="skel skel-line" style={{ width: '70%' }} />
          <div className="skel skel-line" style={{ width: '55%' }} />
        </div>
      </div>
    </div>
  );
}

// ─── Error state ───────────────────────────────────────────────────────
function ErrorState({ cnpj, onBack }) {
  return (
    <div className="errstate">
      <div className="errstate-mark"><Icon.alert /></div>
      <h2>Nenhum CNPJ encontrado</h2>
      <p>Não localizamos nenhum registro para <code>{cnpj}</code> na base de {fmtMonth(MOCK_BASE.mes_atual)}. Verifique os dígitos verificadores ou busque pela razão social.</p>
      <button className="btn" onClick={onBack}>Voltar</button>
    </div>
  );
}

// ─── Identificador socio → label/avatar tone ───────────────────────────
function socioTypeMeta(id) {
  if (id === 'PJ')         return { label: 'Pessoa Jurídica', cls: 'pj',    short: 'PJ' };
  if (id === 'Estrangeiro')return { label: 'Estrangeiro',     cls: 'estr',  short: 'EX' };
  return { label: 'Pessoa Física', cls: '', short: 'PF' };
}

// ─── Socio row with expandable qualification history ───────────────────
function SocioRow({ socio, inactive, mesAtual }) {
  const [open, setOpen] = useState(false);
  const meta = socioTypeMeta(socio.identificador_socio);

  const hasHistory = (socio.qualificacoes_anteriores || []).length > 0;
  const changedRecently = hasHistory && socio.qualificacao_atual.desde &&
    socio.qualificacao_atual.desde >= `${parseInt(mesAtual.split('-')[0]) - 1}-${mesAtual.split('-')[1]}-01`;

  return (
    <>
      <div
        className={`qsa-row ${inactive ? 'inactive' : ''} ${open ? 'expanded' : ''}`}
        onClick={()=>setOpen(o => !o)}
      >
        <div className={`qsa-avatar ${meta.cls}`}>
          {meta.short === 'PJ'  ? <Icon.building /> :
           meta.short === 'EX' ? <Icon.globe />    :
           initials(socio.nome_socio)}
        </div>

        <div className="qsa-main">
          <div className="qsa-nome">
            {socio.nome_socio}
            {changedRecently && <span className="changed-badge">mudou</span>}
            {hasHistory && !changedRecently && <span className="changed-badge" style={{ background:'transparent', color:'var(--ink-3)', border:'1px solid var(--line)' }}>{socio.qualificacoes_anteriores.length + 1} qualif.</span>}
          </div>
          <div className="qsa-qual">
            <span className="qual-name">{socio.qualificacao_atual.descricao}</span>
            <span className="qual-type">{meta.short}</span>
            {socio.faixa_etaria && <span className="qual-faixa">· {socio.faixa_etaria}</span>}
            {socio.pais_origem  && <span className="qual-faixa">· {socio.pais_origem}</span>}
          </div>
        </div>

        <div className="qsa-cpf">
          {socio.cpf_cnpj_socio || <span style={{ opacity: 0.5 }}>—</span>}
        </div>

        {inactive ? (
          <div className="qsa-when exited">
            <div>saiu em</div>
            <div className="when-strong">{fmtMonth(socio.dt_ultima_atualizacao)}</div>
          </div>
        ) : (
          <div className="qsa-when">
            <div>desde</div>
            <div className="when-strong">{fmtDate(socio.qualificacao_atual.desde)}</div>
          </div>
        )}
      </div>

      {open && (
        <div className="qsa-history">
          <div className="history-title">Histórico de qualificações</div>
          <div className="history-tl">
            <div className="history-row current">
              <div className="qual">
                <span className="code">{socio.qualificacao_atual.codigo}</span>
                {socio.qualificacao_atual.descricao}
              </div>
              <div className="span mono">
                {inactive
                  ? `${fmtMonth(socio.dt_primeira_carga)} → ${fmtMonth(socio.dt_ultima_atualizacao)}`
                  : `desde ${fmtDate(socio.qualificacao_atual.desde)}`}
              </div>
            </div>
            {(socio.qualificacoes_anteriores || []).map((q, i) => (
              <div key={i} className="history-row">
                <div className="qual">
                  <span className="code">{q.codigo}</span>
                  {q.descricao}
                </div>
                <div className="span mono">
                  {fmtDate(q.de)} → {fmtDate(q.ate)}
                </div>
              </div>
            ))}
            <div className="history-row" style={{ marginTop: 4 }}>
              <div className="qual" style={{ fontSize: 11, color: 'var(--ink-3)', fontWeight: 400, fontFamily: 'var(--font-mono)', letterSpacing: '0.04em' }}>
                Entrada na sociedade: {fmtDate(socio.data_entrada)}
              </div>
              <div></div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ─── Result page (Resultado da Empresa) ────────────────────────────────
function Result({ company, sections }) {
  const ativasFiliais   = company.filiais.filter(f => f.situacao === 'Ativa').length;
  const totalSocios     = company.socios_ativos.length;
  const exSocios        = company.socios_inativos.length;
  const idade           = yearsSince(company.data_abertura);

  // Banner: matriz baixada com filial ativa
  const showMatrizBaixadaWarning = company.situacao === 'Baixada' && company.has_filial_ativa;

  return (
    <div>
      {/* Header */}
      <div className="result-head">
        {/* Banner crítico: Recuperação Judicial, Falência, etc. */}
        {company.situacao_especial && (
          <div className="special-banner">
            <span className="ico"><Icon.alert /></span>
            <span className="label">Situação Especial</span>
            <span>{company.situacao_especial}</span>
            <span className="when mono">desde {fmtDate(company.situacao_especial_data)}</span>
          </div>
        )}

        {/* Banner informativo: matriz baixada mas tem filial ativa */}
        {showMatrizBaixadaWarning && (
          <div className="info-banner">
            <span className="ico"><Icon.info /></span>
            <span><span className="label">Atenção</span> A matriz está baixada, mas há pelo menos uma filial com situação Ativa. Verifique se houve transferência de sede.</span>
          </div>
        )}

        <div className="result-head-top">
          <div className="company-logo">{initials(company.nome_fantasia || company.razao_social)}</div>
          <div className="company-title">
            <div className="company-eyebrow">
              <Copyable value={company.cnpj}>{company.cnpj}</Copyable>
              <span className="sep">·</span>
              <StatusPill tone={situacaoTone(company.situacao)}>{company.situacao}</StatusPill>
              <span className="sep">·</span>
              <span>{company.matriz ? 'Matriz' : 'Filial'}</span>
              {company.motivo_situacao && (
                <>
                  <span className="sep">·</span>
                  <span style={{ color: 'var(--ink-2)' }}>{company.motivo_situacao}</span>
                </>
              )}
            </div>
            <h1 className="company-name">{company.razao_social}</h1>
            <div className="company-fantasia">{company.nome_fantasia}</div>
          </div>
          <div className="result-head-actions">
            <button className="btn navy" disabled title="Em breve">
              <Icon.network /> Ver rede
            </button>
            <button className="btn primary"><Icon.download /> Exportar PDF</button>
          </div>
        </div>

        {/* Temporal indicators */}
        <div className="temporal-bar">
          <div className="temporal-cell">
            <span className="lbl">Vista pela 1ª vez</span>
            <span className="val">
              {fmtMonth(company.dt_primeira_carga)}
              <span className="sub">{yearsSince(company.dt_primeira_carga + '-01')}+ anos</span>
            </span>
          </div>
          <div className="temporal-cell">
            <span className="lbl">Última atualização</span>
            <span className="val">
              {fmtMonth(company.dt_ultima_atualizacao)}
              <span className="sub">{company.ativo_na_base_atual ? 'na base atual' : 'fora da base'}</span>
            </span>
          </div>
          <div className="temporal-cell">
            <span className="lbl">Quadro societário</span>
            <span className="val">
              {totalSocios}
              <span className="sub">{exSocios > 0 ? `+ ${exSocios} ex-sócios` : 'sem mudanças'}</span>
            </span>
          </div>
          <div className="temporal-cell">
            <span className="lbl">Abertura</span>
            <span className="val mono">
              {fmtDate(company.data_abertura)}
              <span className="sub">{idade} anos</span>
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="content">
        <div className="grid-two">
          <div>
            {/* Quadro societário — coração do produto */}
            {sections.qsa && (
              <div className="section">
                <SectionHeader
                  label="Quadro societário e administrativo"
                  count={totalSocios + exSocios}
                  actions={<button className="btn ghost small"><Icon.download /> CSV</button>}
                />

                <div className="qsa-group">
                  <span className="gl">
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--ok)', display: 'inline-block' }} />
                    Sócios ativos
                  </span>
                  <span className="gc">{totalSocios}</span>
                </div>
                {company.socios_ativos.map((s, i) => (
                  <SocioRow key={i} socio={s} mesAtual={MOCK_BASE.mes_atual} />
                ))}

                {exSocios > 0 && (
                  <>
                    <div className="qsa-group inactive">
                      <span className="gl">
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--ink-4)', display: 'inline-block' }} />
                        Ex-sócios
                        <span style={{ fontSize: 9.5, fontWeight: 400, color: 'var(--ink-3)', letterSpacing: 0, textTransform: 'none', marginLeft: 4 }}>
                          (não constam na base de {fmtMonth(MOCK_BASE.mes_atual)})
                        </span>
                      </span>
                      <span className="gc">{exSocios}</span>
                    </div>
                    {company.socios_inativos.map((s, i) => (
                      <SocioRow key={`x-${i}`} socio={s} inactive mesAtual={MOCK_BASE.mes_atual} />
                    ))}
                  </>
                )}
              </div>
            )}

            {/* Identificação */}
            {sections.identificacao && (
              <div className="section">
                <SectionHeader label="Identificação cadastral" />
                <div className="kv-grid">
                  <KV label="CNPJ" mono copy={company.cnpj}>{company.cnpj}</KV>
                  <KV label="Situação cadastral">
                    <StatusPill tone={situacaoTone(company.situacao)}>{company.situacao}</StatusPill>
                    <span style={{ marginLeft: 8, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)' }}>
                      desde {fmtDate(company.situacao_data)}
                    </span>
                  </KV>
                  <KV label="Natureza jurídica">{company.natureza_juridica}</KV>
                  <KV label="Porte">{company.porte}</KV>
                  <KV label="Data de abertura" mono>{fmtDate(company.data_abertura)}</KV>
                  <KV label="Capital social" mono>{fmtBRL(company.capital_social)}</KV>
                  <KV label="Qualificação do responsável">{company.qualificacao_responsavel}</KV>
                  <KV label="Optante Simples / MEI">
                    <span style={{ display: 'inline-flex', gap: 6 }}>
                      <StatusPill tone={company.simples.opcao_simples ? 'ok' : 'neutral'}>
                        Simples {company.simples.opcao_simples ? '· Sim' : '· Não'}
                      </StatusPill>
                      <StatusPill tone={company.simples.opcao_mei ? 'ok' : 'neutral'}>
                        MEI {company.simples.opcao_mei ? '· Sim' : '· Não'}
                      </StatusPill>
                    </span>
                  </KV>
                </div>
              </div>
            )}

            {/* CNAEs */}
            {sections.cnaes && (
              <div className="section">
                <SectionHeader label="Atividades econômicas" count={company.cnae_secundarios.length + 1} />
                <div className="cnae primary">
                  <span className="cnae-code mono">{company.cnae_principal.codigo}</span>
                  <span className="cnae-desc">
                    {company.cnae_principal.descricao}
                    <span className="cnae-badge">Principal</span>
                  </span>
                </div>
                {company.cnae_secundarios.map(c => (
                  <div key={c.codigo} className="cnae">
                    <span className="cnae-code mono">{c.codigo}</span>
                    <span className="cnae-desc">{c.descricao}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Endereço */}
            {sections.endereco && (
              <div className="section">
                <SectionHeader label="Endereço da matriz" actions={
                  <a className="btn ghost small" target="_blank" rel="noopener"
                     href={`https://www.google.com/maps?q=${encodeURIComponent([company.endereco.logradouro, company.endereco.municipio, company.endereco.uf].join(', '))}`}>
                    Abrir no Maps
                  </a>
                } />
                <div className="kv-grid">
                  <KV label="Logradouro">{company.endereco.logradouro}</KV>
                  <KV label="Complemento">{company.endereco.complemento}</KV>
                  <KV label="Bairro">{company.endereco.bairro}</KV>
                  <KV label="Município / UF">{company.endereco.municipio}, {company.endereco.uf}</KV>
                  <KV label="CEP" mono copy={company.endereco.cep}>{company.endereco.cep}</KV>
                  <KV label="País">{company.endereco.pais}</KV>
                </div>
              </div>
            )}

            {/* Contato */}
            {sections.contato && (
              <div className="section">
                <SectionHeader label="Contato" />
                <div className="kv-grid">
                  <KV label="Telefone 1" mono copy={company.contato.telefone1}>{company.contato.telefone1 || '—'}</KV>
                  <KV label="Telefone 2" mono>{company.contato.telefone2 || '—'}</KV>
                  <KV label="E-mail" copy={company.contato.email}>{company.contato.email}</KV>
                </div>
              </div>
            )}

            {/* Filiais */}
            {sections.filiais && company.filiais.length > 0 && (
              <div className="section">
                <SectionHeader label="Filiais" count={company.filiais.length} actions={
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)' }}>
                    {ativasFiliais} ativas · {company.filiais.length - ativasFiliais} demais
                  </span>
                } />
                {company.filiais.map(f => (
                  <div className="filial" key={f.cnpj}>
                    <div>
                      <div className="filial-cnpj">{f.cnpj}</div>
                      <div className="filial-cidade">{f.municipio}</div>
                    </div>
                    <div className="filial-uf">{f.uf}</div>
                    <StatusPill tone={situacaoTone(f.situacao)}>{f.situacao}</StatusPill>
                    <button className="btn ghost small">Abrir <Icon.chevron /></button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right column */}
          <div>
            {/* Temporal context card */}
            <div className="temporal-card">
              <div className="tc-label"><span className="dot" /> Pythagoras · Histórico</div>
              <div className="tc-title">Presença na base RFB</div>
              <div className="tc-rows">
                <div className="tc-row">
                  <span className="tc-key">1ª vez vista</span>
                  <span className="tc-val">{fmtMonth(company.dt_primeira_carga)}</span>
                </div>
                <div className="tc-row">
                  <span className="tc-key">Última atualização</span>
                  <span className="tc-val">{fmtMonth(company.dt_ultima_atualizacao)}</span>
                </div>
                <div className="tc-row">
                  <span className="tc-key">Base atual processada</span>
                  <span className="tc-val">{fmtMonth(MOCK_BASE.mes_atual)}</span>
                </div>
                <div className="tc-row">
                  <span className="tc-key">Sócios rastreados</span>
                  <span className="tc-val">{totalSocios + exSocios} <span className="subtle">({totalSocios} hoje)</span></span>
                </div>
                <div className="tc-row">
                  <span className="tc-key">Snapshots no histórico</span>
                  <span className="tc-val">38 <span className="subtle">meses</span></span>
                </div>
              </div>
            </div>

            {/* Future feature placeholder */}
            <div className="future-card">
              <div className="fc-eyebrow">Em desenvolvimento · v3</div>
              <div className="fc-title">Rede de sócios e empresas</div>
              <div className="fc-desc">
                Visualização de conexões de 2º grau — sócios em comum, fundos compartilhados,
                holdings. Disponível na próxima fase.
              </div>
              <div className="fc-mini">
                <svg width="180" height="120" viewBox="0 0 240 160" fill="none">
                  <g stroke="#2a4a82" strokeWidth="1" opacity="0.5">
                    <line x1="120" y1="80" x2="50" y2="35"/>
                    <line x1="120" y1="80" x2="190" y2="35"/>
                    <line x1="120" y1="80" x2="35" y2="120"/>
                    <line x1="120" y1="80" x2="100" y2="140"/>
                    <line x1="120" y1="80" x2="200" y2="125"/>
                  </g>
                  <circle cx="120" cy="80" r="22" fill="#0a6cb8"/>
                  <text x="120" y="84" textAnchor="middle" fill="white" fontSize="9" fontFamily="Inter Tight" fontWeight="600">EMPRESA</text>
                  <circle cx="50" cy="35" r="12" fill="#3d6cb0"/>
                  <circle cx="190" cy="35" r="12" fill="#3d6cb0"/>
                  <circle cx="35" cy="120" r="10" fill="#0a6cb8"/>
                  <circle cx="100" cy="140" r="8" fill="#0a6cb8"/>
                  <circle cx="200" cy="125" r="14" fill="#01244a"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Tweaks panel (slim) ───────────────────────────────────────────────
function TweaksPanel({ enabled, tweaks, setTweak }) {
  const [open, setOpen] = useState(true);
  if (!enabled) return null;

  if (!open) {
    return (
      <div className="tweaks collapsed" onClick={()=>setOpen(true)} title="Tweaks">
        <Icon.sliders />
      </div>
    );
  }

  return (
    <div className="tweaks">
      <div className="tweaks-head">
        <span className="t-title"><span className="dot" /> Tweaks</span>
        <button className="btn ghost icon-only small" onClick={()=>setOpen(false)}><Icon.x /></button>
      </div>
      <div className="tweaks-body">
        <div className="twk-row">
          <div className="twk-label"><span>Estado</span></div>
          <div className="seg">
            {[
              ['result','Resultado'],
              ['idle','Início'],
              ['loading','Loading'],
              ['error','Erro'],
            ].map(([m,l]) => (
              <button key={m} className={tweaks.state === m ? 'active' : ''} onClick={()=>setTweak('state', m)}>{l}</button>
            ))}
          </div>
        </div>

        <div className="twk-row">
          <div className="twk-label"><span>Cenário da empresa</span></div>
          <div className="seg">
            {[
              ['normal','Normal'],
              ['rj','Recup. Jud.'],
              ['baixada','Matriz baixada'],
            ].map(([m,l]) => (
              <button key={m} className={tweaks.scenario === m ? 'active' : ''} onClick={()=>setTweak('scenario', m)}>{l}</button>
            ))}
          </div>
        </div>

        <div className="twk-row">
          <div className="twk-label"><span>Seções visíveis</span></div>
          <div className="twk-checks">
            {[
              ['qsa','Quadro societário (Ativos / Ex-sócios)'],
              ['identificacao','Identificação cadastral'],
              ['cnaes','Atividades econômicas (CNAEs)'],
              ['endereco','Endereço'],
              ['contato','Contato'],
              ['filiais','Filiais'],
            ].map(([k,l]) => (
              <label key={k} className="twk-check">
                <input type="checkbox" checked={!!tweaks.sections[k]} onChange={(e)=>setTweak('sections', { ...tweaks.sections, [k]: e.target.checked })} />
                <span>{l}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// App shell
// ═══════════════════════════════════════════════════════════════════════
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "state": "result",
  "scenario": "normal",
  "sections": {
    "qsa": true,
    "identificacao": true,
    "cnaes": true,
    "endereco": true,
    "contato": true,
    "filiais": true
  }
}/*EDITMODE-END*/;

function App() {
  const [tweaks, setTweaks] = useState(TWEAK_DEFAULTS);
  const [tweaksEnabled, setTweaksEnabled] = useState(false);
  const [query, setQuery] = useState(maskCNPJ(MOCK_COMPANY.cnpj_raw));
  const [state, setState] = useState('result');
  const [errorCnpj, setErrorCnpj] = useState('');

  useEffect(() => { setState(tweaks.state); }, [tweaks.state]);

  // Tweaks protocol
  useEffect(() => {
    const handler = (e) => {
      if (e.data?.type === '__activate_edit_mode')   setTweaksEnabled(true);
      if (e.data?.type === '__deactivate_edit_mode') setTweaksEnabled(false);
    };
    window.addEventListener('message', handler);
    window.parent.postMessage({ type: '__edit_mode_available' }, '*');
    return () => window.removeEventListener('message', handler);
  }, []);

  const setTweak = (k, v) => {
    const next = { ...tweaks, [k]: v };
    setTweaks(next);
    window.parent.postMessage({ type: '__edit_mode_set_keys', edits: { [k]: v } }, '*');
  };

  // Apply scenario overrides to MOCK_COMPANY
  const company = useMemo(() => {
    let c = { ...MOCK_COMPANY };
    if (tweaks.scenario === 'rj')      Object.assign(c, MOCK_RJ_OVERRIDE);
    if (tweaks.scenario === 'baixada') Object.assign(c, MOCK_BAIXADA_OVERRIDE);
    return c;
  }, [tweaks.scenario]);

  const doSearch = (input) => {
    const raw = (input || '').replace(/\D/g, '');
    const masked = maskCNPJ(raw);
    setQuery(masked);
    setState('loading');
    setTimeout(() => {
      if (raw === MOCK_COMPANY.cnpj_raw) setState('result');
      else { setErrorCnpj(masked || raw); setState('error'); }
    }, 700);
  };

  return (
    <div className="app">
      <Sidebar
        activeCnpj={state === 'result' ? MOCK_COMPANY.cnpj : null}
        onPick={(h)=>{ setQuery(h.cnpj); doSearch(h.cnpj); }}
      />
      <main className="main">
        {state !== 'idle' && (
          <div className="topbar">
            <div className="crumbs">
              <span>Workspace</span>
              <span className="sep">/</span>
              <span>Consultas</span>
              <span className="sep">/</span>
              <span className="cur">
                {state === 'result' ? company.nome_fantasia
                 : state === 'loading' ? 'Consultando…'
                 : 'Erro'}
              </span>
            </div>
            <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
              <SearchBar value={query} onChange={setQuery} onSubmit={doSearch} compact />
            </div>
            <div className="topbar-actions">
              <button className="btn"><Icon.plus /> Nova consulta</button>
            </div>
          </div>
        )}

        {state === 'idle'    && <IdleState query={query} setQuery={setQuery} onSubmit={doSearch} />}
        {state === 'loading' && <LoadingState cnpj={query} />}
        {state === 'error'   && <ErrorState cnpj={errorCnpj} onBack={()=>{ setState('idle'); setQuery(''); }} />}
        {state === 'result'  && <Result company={company} sections={tweaks.sections} />}
      </main>

      <TweaksPanel enabled={tweaksEnabled} tweaks={tweaks} setTweak={setTweak} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
