export default function Login({ onLogin }) {
  return (
    <div className="min-h-screen flex overflow-hidden bg-surface-container-lowest">
      {/* Coluna visual esquerda */}
      <div className="hidden lg:flex w-1/2 relative items-end p-[40px] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#0b1c30] via-[#1a3560] to-[#2563eb]" />
        <div
          className="absolute inset-0 opacity-10"
          style={{ backgroundImage: "radial-gradient(circle at 70% 30%, rgba(180,197,255,0.4) 0%, transparent 60%)" }}
        />
        <div className="relative z-10 w-full max-w-lg">
          <h2 className="text-display-lg text-white mb-3">Precision in every query.</h2>
          <p className="text-body-lg text-tertiary-fixed-dim">
            Base pública de dados do CNPJ da Receita Federal. Projetado para analistas que exigem velocidade e precisão.
          </p>
        </div>
      </div>

      {/* Coluna do formulário */}
      <div className="flex-1 flex flex-col justify-center items-center px-space-md sm:px-gutter">
        <div className="w-full max-w-[380px]">
          <div className="mb-space-xl text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-space-sm mb-space-lg">
              <span
                className="material-symbols-outlined text-primary text-[28px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                query_stats
              </span>
              <span className="text-headline-md text-on-surface">CorpIntel</span>
            </div>
            <h1 className="text-headline-md text-on-surface mb-space-xs">Bem-vindo</h1>
            <p className="text-body-md text-on-surface-variant">Acesse o sistema de consulta de dados corporativos.</p>
          </div>

          <form
            className="space-y-space-md"
            onSubmit={(e) => {
              e.preventDefault();
              onLogin();
            }}
          >
            <div>
              <label className="block text-label-caps text-on-surface-variant mb-space-xs uppercase">E-mail</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-space-sm flex items-center pointer-events-none text-outline">
                  <span className="material-symbols-outlined text-[18px]">mail</span>
                </span>
                <input
                  className="block w-full h-[40px] pl-10 pr-space-sm bg-surface-container-low border border-outline-variant rounded text-on-surface text-body-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary placeholder:text-outline transition-colors"
                  placeholder="nome@empresa.com"
                  type="email"
                  defaultValue=""
                />
              </div>
            </div>

            <div>
              <label className="block text-label-caps text-on-surface-variant mb-space-xs uppercase">Senha</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-space-sm flex items-center pointer-events-none text-outline">
                  <span className="material-symbols-outlined text-[18px]">lock</span>
                </span>
                <input
                  className="block w-full h-[40px] pl-10 pr-space-sm bg-surface-container-low border border-outline-variant rounded text-on-surface text-body-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary placeholder:text-outline transition-colors"
                  placeholder="••••••••"
                  type="password"
                />
              </div>
            </div>

            <div className="pt-space-sm">
              <button
                type="submit"
                className="w-full h-[40px] bg-primary text-on-primary text-body-md rounded shadow-sm hover:bg-surface-tint transition-colors flex items-center justify-center gap-space-sm"
              >
                <span>Entrar</span>
                <span className="material-symbols-outlined text-[18px]">arrow_right_alt</span>
              </button>
            </div>
          </form>

          <div className="mt-space-lg text-center">
            <p className="text-body-sm text-on-surface-variant">
              Apenas um protótipo —{" "}
              <button onClick={onLogin} className="text-primary hover:underline">
                acessar sem credenciais
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
