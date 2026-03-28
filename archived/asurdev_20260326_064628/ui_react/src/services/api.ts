const API_BASE = '/api';

export const api = {
  // Trading analysis
  async analyze(symbol: string, action: string) {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, action })
    });
    return res.json();
  },

  async getAgents() {
    const res = await fetch(`${API_BASE}/agents`);
    return res.json();
  },

  async submitFeedback(agentId: string, rating: number, comment: string) {
    return fetch(`${API_BASE}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: agentId, rating, comment })
    });
  },

  async getPerformance() {
    const res = await fetch(`${API_BASE}/performance`);
    return res.json();
  },

  // Legacy astro endpoint
  async getAstro() {
    const res = await fetch(`${API_BASE}/astro`);
    return res.json();
  },

  // === CHART ENDPOINTS (Swiss Ephemeris) ===

  async computeChart(params: {
    date: string;
    time: string;
    lat: number;
    lon: number;
    ayanamsa?: string;
    zodiac?: string;
    house_system?: string;
    compute_houses?: boolean;
    compute_panchanga?: boolean;
    compute_choghadiya?: boolean;
    compute_ashtakavarga?: boolean;
  }) {
    const res = await fetch(`${API_BASE}/chart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getPlanetPositions(date?: string, time?: string, lat?: number, lon?: number) {
    const params = new URLSearchParams();
    if (date) params.set('date', date);
    if (time) params.set('time', time);
    if (lat != null) params.set('lat', String(lat));
    if (lon != null) params.set('lon', String(lon));
    
    const res = await fetch(`${API_BASE}/chart/positions?${params}`);
    return res.json();
  },

  async getPanchanga(date?: string, time?: string, lat?: number, lon?: number) {
    const params = new URLSearchParams();
    if (date) params.set('date', date);
    if (time) params.set('time', time);
    if (lat != null) params.set('lat', String(lat));
    if (lon != null) params.set('lon', String(lon));
    
    const res = await fetch(`${API_BASE}/chart/panchanga?${params}`);
    return res.json();
  },

  async getChoghadiya(date?: string, time?: string, lat?: number, lon?: number) {
    const params = new URLSearchParams();
    if (date) params.set('date', date);
    if (time) params.set('time', time);
    if (lat != null) params.set('lat', String(lat));
    if (lon != null) params.set('lon', String(lon));
    
    const res = await fetch(`${API_BASE}/chart/choghadiya?${params}`);
    return res.json();
  },

  async getCurrentAstro(lat?: number, lon?: number) {
    const params = new URLSearchParams();
    if (lat != null) params.set('lat', String(lat));
    if (lon != null) params.set('lon', String(lon));
    
    const res = await fetch(`${API_BASE}/astro/current?${params}`);
    return res.json();
  }
};

// Types
export interface ChartRequest {
  date: string;
  time: string;
  lat: number;
  lon: number;
  ayanamsa?: string;
  zodiac?: string;
  house_system?: string;
  compute_houses?: boolean;
  compute_panchanga?: boolean;
  compute_choghadiya?: boolean;
  compute_ashtakavarga?: boolean;
}

export interface PlanetPosition {
  lon: number;
  lat: number;
  speed: number;
  declination: number;
  rasi: number;
  sign: string;
}

export interface PanchangaData {
  vara: string;
  vara_index: number;
  tithi: string;
  tithi_number: number;
  tithi_paksha: string;
  nakshatra: string;
  nakshatra_number: number;
  nakshatra_pada: number;
  yoga: string;
  yoga_number: number;
  yoga_category: string;
  sunrise: string;
  sunset: string;
}

export interface ChoghadiyaEntry {
  name: string;
  period: string;
  favorable: boolean;
  quality: string;
  description: string;
}

export interface ChartResult {
  status: string;
  input: {
    date: string;
    time: string;
    lat: number;
    lon: number;
    ayanamsa: string;
    zodiac: string;
    house_system: string;
  };
  positions: Record<string, PlanetPosition>;
  houses: Record<string, number>;
  panchanga: PanchangaData;
  choghadiya: ChoghadiyaEntry[];
  ashtakavarga?: Record<string, any>;
  calculation_time_ms: number;
  timestamp: string;
}
