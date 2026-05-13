export default function HomeSelecao({ irParaEmpresa, irParaSocio }) {
  return (
    <main className="flex-1 md:ml-64 bg-background min-h-screen flex flex-col items-center justify-center p-[40px] relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/3 pointer-events-none" />

      <div className="w-full max-w-[1440px] flex flex-col items-center relative z-10">
        <header className="text-center mb-space-xl max-w-2xl">
          <h1 className="text-display-lg text-on-surface mb-space-sm tracking-tight">Iniciar Pesquisa</h1>
          <p className="text-body-lg text-on-surface-variant">
            Selecione o escopo da sua investigação. O sistema otimizará as fontes de dados com base na entidade
            principal escolhida.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg w-full max-w-4xl">
          {/* Card Sócio */}
          <button
            onClick={irParaSocio}
            className="group relative flex flex-col items-center justify-center p-space-xl bg-surface-container-lowest rounded-xl ambient-shadow border border-outline-variant/30 hover:-translate-y-1 hover:shadow-ambient-hover transition-all duration-300 text-center min-h-[320px] overflow-hidden focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            <div className="absolute -right-20 -top-20 w-64 h-64 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors duration-500 pointer-events-none" />
            <div className="w-16 h-16 rounded-full bg-secondary-fixed flex items-center justify-center mb-space-lg group-hover:scale-110 transition-transform duration-300">
              <span
                className="material-symbols-outlined text-[32px] text-primary"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                person_search
              </span>
            </div>
            <h2 className="text-headline-md text-on-surface mb-space-sm group-hover:text-primary transition-colors">
              Pesquisar por Sócio
            </h2>
            <p className="text-body-md text-on-surface-variant max-w-xs">
              Investigue perfis individuais, identifique conexões e analise afiliações corporativas detalhadas.
            </p>
            <div className="mt-space-lg flex items-center gap-1 text-label-caps text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              INICIAR CONSULTA
              <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
            </div>
          </button>

          {/* Card Empresa */}
          <button
            onClick={irParaEmpresa}
            className="group relative flex flex-col items-center justify-center p-space-xl bg-surface-container-lowest rounded-xl ambient-shadow border border-outline-variant/30 hover:-translate-y-1 hover:shadow-ambient-hover transition-all duration-300 text-center min-h-[320px] overflow-hidden focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            <div className="absolute -left-20 -bottom-20 w-64 h-64 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors duration-500 pointer-events-none" />
            <div className="w-16 h-16 rounded-full bg-secondary-fixed flex items-center justify-center mb-space-lg group-hover:scale-110 transition-transform duration-300">
              <span
                className="material-symbols-outlined text-[32px] text-primary"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                domain
              </span>
            </div>
            <h2 className="text-headline-md text-on-surface mb-space-sm group-hover:text-primary transition-colors">
              Pesquisar por Empresa
            </h2>
            <p className="text-body-md text-on-surface-variant max-w-xs">
              Analise estruturas corporativas, acesse dados cadastrais e o quadro societário completo.
            </p>
            <div className="mt-space-lg flex items-center gap-1 text-label-caps text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              INICIAR CONSULTA
              <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
            </div>
          </button>
        </div>
      </div>
    </main>
  );
}
