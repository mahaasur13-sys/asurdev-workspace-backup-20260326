import React from 'react';
import { Moon, Sun, Star } from 'lucide-react';

export function AstroWidget() {
  const [astro, setAstro] = React.useState<any>(null);
  
  React.useEffect(() => {
    fetch('/api/astro').then(r => r.json()).then(setAstro).catch(() => {});
  }, []);

  return (
    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
        <Star className="w-4 h-4 text-purple-400" /> Astrology
      </h3>
      {astro ? (
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Moon Phase</span>
            <span>{astro.moon_phase}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Nakshatra</span>
            <span>{astro.nakshatra}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Choghadiya</span>
            <span className={astro.choghadiya_favorable ? 'text-green-400' : 'text-red-400'}>
              {astro.choghadiya}
            </span>
          </div>
        </div>
      ) : (
        <div className="text-slate-500 text-sm">Loading...</div>
      )}
    </div>
  );
}
