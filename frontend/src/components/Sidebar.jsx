const NAV = [
  { icon: "search", label: "Pesquisa", telas: ["home", "empresa", "socio", "resultado-empresa", "resultado-socio"] },
  { icon: "query_stats", label: "Market Analytics" },
  { icon: "verified_user", label: "Due Diligence" },
  { icon: "account_balance_wallet", label: "Portfolio" },
  { icon: "inventory_2", label: "Archive" },
];

export default function Sidebar({ tela, irPara }) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-50 border-r border-slate-200 flex flex-col py-6 px-4 z-40 hidden md:flex">
      <div className="flex items-center gap-3 mb-8 px-2">
        <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center shrink-0">
          <span className="material-symbols-outlined text-on-primary text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
            dataset
          </span>
        </div>
        <div>
          <h1 className="text-lg font-black text-slate-900 leading-tight">Intelligence Suite</h1>
          <p className="text-xs text-slate-500 font-medium">Enterprise Tier</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        {NAV.map((item) => {
          const active = item.telas?.includes(tela);
          return (
            <button
              key={item.label}
              onClick={() => item.telas && irPara("home")}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-semibold tracking-wide uppercase transition-all duration-200 text-left ${
                active
                  ? "bg-white text-blue-600 shadow-sm border-l-4 border-blue-600 rounded-r-lg"
                  : "text-slate-600 hover:bg-slate-100 hover:translate-x-1 border-l-4 border-transparent rounded-r-lg"
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto border-t border-slate-200 pt-4 space-y-1">
        <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-semibold tracking-wide uppercase transition-all duration-200">
          <span className="material-symbols-outlined text-[20px]">help</span>
          <span>Help Center</span>
        </button>
        <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-semibold tracking-wide uppercase transition-all duration-200">
          <span className="material-symbols-outlined text-[20px]">support_agent</span>
          <span>Contact Support</span>
        </button>
        <button className="mt-3 w-full py-2.5 px-4 bg-primary text-on-primary font-semibold rounded-lg text-sm hover:bg-surface-tint transition-colors">
          Upgrade Plan
        </button>
      </div>
    </aside>
  );
}
