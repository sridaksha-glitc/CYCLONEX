export function Footer() {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950 py-8 px-4 sm:px-6 lg:px-8 mt-auto text-xs text-slate-400">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-slate-200">CYCLONEX Platform</span>
            <span className="text-slate-600">•</span>
            <span>Version 1.0.0 (Research Prototype)</span>
          </div>
          <p className="text-slate-500 max-w-2xl leading-relaxed text-[11px]">
            <strong>DISCLAIMER:</strong> This platform is a hackathon proof-of-concept and decision-support index.
            It does NOT constitute an official warning. Refer exclusively to the India Meteorological Department (IMD)
            and World Meteorological Organization (WMO) for operational public advisories.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 sm:gap-6 text-slate-400 text-[11px]">
          <div>
            <strong className="text-slate-300 block">Data Sources</strong>
            <span>OpenWeather • IBTrACS • INSAT-3D</span>
          </div>
          <div>
            <strong className="text-slate-300 block">Framework Standards</strong>
            <span>IMD 8-Tier Wind Scale • Atkinson-Holliday</span>
          </div>
          <div>
            <strong className="text-slate-300 block">Architecture</strong>
            <span>FastAPI • Next.js • n8n • Supabase</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
