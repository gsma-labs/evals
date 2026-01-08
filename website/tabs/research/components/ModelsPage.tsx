import React, { useMemo, useState, useEffect } from 'react';

// Organization colors matching the Epoch AI style
const COLORS: Record<string, string> = {
  'Google': '#4DB6AC',
  'OpenAI': '#F48FB1',
  'Meta': '#FFAB91',
  'Anthropic': '#B39DDB',
  'Claude': '#B39DDB',
  'Grok': '#5C6BC0',
  'Qwen': '#81C784',
  'Mistral': '#FF8A65',
  'NetoAI': '#4DD0E1',
  'IBM': '#64B5F6',
  'IBM Granite': '#64B5F6',
  'DeepSeek': '#CE93D8',
  'LiquidAI': '#FFB74D',
  'Microsoft': '#4FC3F7',
  'Swiss AI': '#E57373',
  'ByteDance': '#AED581',
  'Other': '#A1887F',
};

interface LeaderboardEntry {
  rank: number;
  provider: string;
  model: string;
  repo: string;
  mean: number | null;
  teleqna: number | null;
  telelogs: number | null;
  telemath: number | null;
  tsg: number | null;
  teleyaml: number | null;
  tci: number | null;
}

// Parse CSV data
function parseCSV(csvText: string): LeaderboardEntry[] {
  const lines = csvText.trim().split('\n');
  const entries: LeaderboardEntry[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    const values: string[] = [];
    let current = '';
    let inQuotes = false;

    for (let j = 0; j < line.length; j++) {
      const char = line[j];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());

    const extractScore = (val: string): number | null => {
      if (!val || val === '—' || val === '-') return null;
      const match = val.match(/^([\d.]+)/);
      return match ? parseFloat(match[1]) : null;
    };

    const rank = parseInt(values[0], 10);
    if (isNaN(rank)) continue;

    const entry: LeaderboardEntry = {
      rank,
      provider: values[1] || '',
      model: values[2] || '',
      repo: values[3] || '',
      mean: values[4] === '—' ? null : parseFloat(values[4]),
      teleqna: extractScore(values[5]),
      telelogs: extractScore(values[6]),
      telemath: extractScore(values[7]),
      tsg: extractScore(values[8]),
      teleyaml: extractScore(values[9]),
      tci: null,
    };

    // Calculate TCI
    entry.tci = calculateTCI(entry);
    entries.push(entry);
  }

  return entries;
}

// Calculate TCI score
function calculateTCI(entry: LeaderboardEntry): number | null {
  const { teleqna, telelogs, telemath, tsg } = entry;
  const scores = [teleqna, telelogs, telemath, tsg].filter(s => s !== null) as number[];
  if (scores.length < 3) return null;

  const benchmarkDifficulty: Record<string, number> = {
    teleqna: 0.7,
    telelogs: 0.3,
    telemath: 0.4,
    tsg: 0.4,
  };

  const benchmarkSlope: Record<string, number> = {
    teleqna: 1.2,
    telelogs: 1.5,
    telemath: 1.3,
    tsg: 1.2,
  };

  const benchmarks = [
    { key: 'teleqna', value: teleqna },
    { key: 'telelogs', value: telelogs },
    { key: 'telemath', value: telemath },
    { key: 'tsg', value: tsg },
  ];

  let totalWeight = 0;
  let weightedCapability = 0;

  benchmarks.forEach(({ key, value }) => {
    if (value === null) return;
    const score = value / 100;
    const difficulty = 1 - benchmarkDifficulty[key];
    const slope = benchmarkSlope[key];
    const adjustedScore = Math.max(0.01, Math.min(0.99, score));
    const logitScore = Math.log(adjustedScore / (1 - adjustedScore));
    const weight = difficulty * slope;
    weightedCapability += (logitScore + difficulty * 2) * weight;
    totalWeight += weight;
  });

  const rawCapability = weightedCapability / totalWeight;
  const tci = 115 + rawCapability * 20;
  return Math.round(tci * 10) / 10;
}

// Get TCI color based on score
function getTCIColor(tci: number | null): string {
  if (tci === null) return '#999';
  if (tci >= 135) return '#4DB6AC'; // High - teal
  if (tci >= 125) return '#81C784'; // Good - green
  if (tci >= 115) return '#FFB74D'; // Medium - amber
  return '#FFAB91'; // Lower - coral
}

export default function ModelsPage(): JSX.Element {
  const [data, setData] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'tci' | 'mean' | 'name'>('tci');
  const [selectedProviders, setSelectedProviders] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch('/open_telco/data/telecom-llm-leaderboard.csv')
      .then(response => {
        if (!response.ok) throw new Error('Failed to load data');
        return response.text();
      })
      .then(csvText => {
        const parsed = parseCSV(csvText);
        setData(parsed);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Get unique providers
  const providers = useMemo(() => {
    const unique = [...new Set(data.map(d => d.provider))].sort();
    return unique;
  }, [data]);

  // Filter and sort data
  const filteredData = useMemo(() => {
    let result = [...data];

    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(d =>
        d.model.toLowerCase().includes(query) ||
        d.provider.toLowerCase().includes(query)
      );
    }

    // Filter by provider
    if (selectedProviders.size > 0) {
      result = result.filter(d => selectedProviders.has(d.provider));
    }

    // Sort
    result.sort((a, b) => {
      if (sortBy === 'tci') {
        if (a.tci === null && b.tci === null) return 0;
        if (a.tci === null) return 1;
        if (b.tci === null) return -1;
        return b.tci - a.tci;
      }
      if (sortBy === 'mean') {
        if (a.mean === null && b.mean === null) return 0;
        if (a.mean === null) return 1;
        if (b.mean === null) return -1;
        return b.mean - a.mean;
      }
      return a.model.localeCompare(b.model);
    });

    return result;
  }, [data, searchQuery, selectedProviders, sortBy]);

  const toggleProvider = (provider: string) => {
    setSelectedProviders(prev => {
      const next = new Set(prev);
      if (next.has(provider)) {
        next.delete(provider);
      } else {
        next.add(provider);
      }
      return next;
    });
  };

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>Loading models...</div>;
  }

  if (error) {
    return <div style={{ padding: '40px', textAlign: 'center', color: '#E60000' }}>Error: {error}</div>;
  }

  return (
    <div style={{ display: 'flex', gap: '40px', padding: '20px 0' }}>
      {/* Main content */}
      <div style={{ flex: 1 }}>
        <div style={{ marginBottom: '24px', color: '#666', fontSize: '15px' }}>
          {filteredData.length} models
        </div>

        {/* Model list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
          {filteredData.map((model, idx) => (
            <div
              key={`${model.provider}-${model.model}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 0',
                borderBottom: '1px solid #eee',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* Provider icon placeholder */}
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  backgroundColor: COLORS[model.provider] || COLORS['Other'],
                  opacity: 0.8,
                }} />
                <div>
                  <div style={{ fontWeight: '600', fontSize: '15px', color: '#1a1a1a' }}>
                    {model.model}
                  </div>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <span style={{
                      fontSize: '12px',
                      padding: '2px 8px',
                      backgroundColor: '#f5f5f5',
                      borderRadius: '4px',
                      color: '#555',
                    }}>
                      {model.provider}
                    </span>
                  </div>
                </div>
              </div>

              {/* TCI Score */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  backgroundColor: getTCIColor(model.tci),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: '600',
                  fontSize: '14px',
                }}>
                  {model.tci !== null ? Math.round(model.tci) : '—'}
                </div>
                <span style={{ fontSize: '12px', color: '#888' }}>TCI</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sidebar - Search & Filter */}
      <div style={{ width: '280px', flexShrink: 0 }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', color: '#1a1a1a' }}>
          Search & Filter
        </h3>

        {/* Search input */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            border: '1px solid #e0e0e0',
            borderRadius: '8px',
            padding: '8px 12px',
          }}>
            <input
              type="text"
              placeholder="Search models"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                flex: 1,
                border: 'none',
                outline: 'none',
                fontSize: '14px',
                backgroundColor: 'transparent',
              }}
            />
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
          </div>
        </div>

        {/* Sort by */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: '#888', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Sort by:
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'tci' | 'mean' | 'name')}
            style={{
              width: '100%',
              padding: '10px 12px',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              fontSize: '14px',
              backgroundColor: 'white',
              cursor: 'pointer',
            }}
          >
            <option value="tci">Telco Capability Index</option>
            <option value="mean">Mean Score</option>
            <option value="name">Name</option>
          </select>
        </div>

        {/* Developer filter */}
        <div>
          <div style={{ fontSize: '11px', fontWeight: '600', color: '#888', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Developer
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
            {providers.map(provider => (
              <label
                key={provider}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  color: '#333',
                }}
              >
                <input
                  type="checkbox"
                  checked={selectedProviders.has(provider)}
                  onChange={() => toggleProvider(provider)}
                  style={{
                    width: '16px',
                    height: '16px',
                    cursor: 'pointer',
                  }}
                />
                {provider}
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
