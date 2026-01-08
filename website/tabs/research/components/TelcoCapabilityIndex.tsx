import React, { useMemo, useState, useEffect } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Label,
  LabelList,
} from 'recharts';

// Organization colors matching the Epoch AI style
const COLORS: Record<string, string> = {
  'Google': '#4DB6AC',      // Teal
  'OpenAI': '#F48FB1',      // Pink
  'Meta': '#FFAB91',        // Orange/coral
  'Anthropic': '#B39DDB',   // Purple
  'Claude': '#B39DDB',      // Purple (alias for Anthropic)
  'Grok': '#5C6BC0',        // Dark blue/indigo
  'Qwen': '#81C784',        // Green
  'Mistral': '#FF8A65',     // Deep orange
  'NetoAI': '#4DD0E1',      // Cyan
  'IBM': '#64B5F6',         // Light blue
  'IBM Granite': '#64B5F6', // Light blue
  'DeepSeek': '#CE93D8',    // Light purple
  'LiquidAI': '#FFB74D',    // Amber
  'Microsoft': '#4FC3F7',   // Sky blue
  'Swiss AI': '#E57373',    // Red
  'ByteDance': '#AED581',   // Light green
  'Other': '#A1887F',       // Brown/tan
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
}

// Parse CSV data from telecom-llm-leaderboard.csv
function parseCSV(csvText: string): LeaderboardEntry[] {
  const lines = csvText.trim().split('\n');
  const entries: LeaderboardEntry[] = [];

  // Skip header row
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    // Parse CSV properly handling quoted fields
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

    // Extract numeric value from strings like "82.51 (raw)"
    const extractScore = (val: string): number | null => {
      if (!val || val === '—' || val === '-') return null;
      const match = val.match(/^([\d.]+)/);
      return match ? parseFloat(match[1]) : null;
    };

    const rank = parseInt(values[0], 10);
    if (isNaN(rank)) continue;

    entries.push({
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
    });
  }

  return entries;
}

// Calculate TCI score using IRT-inspired methodology
// Using only: TeleQnA, TeleLogs, TeleMath, 3GPP-TSG (excluding TeleYAML)
function calculateTCI(entry: LeaderboardEntry): number | null {
  const { teleqna, telelogs, telemath, tsg } = entry;

  // Need at least 3 scores to calculate TCI
  const scores = [teleqna, telelogs, telemath, tsg].filter(s => s !== null) as number[];
  if (scores.length < 3) return null;

  // Benchmark difficulties (estimated based on average scores - lower avg = harder)
  const benchmarkDifficulty: Record<string, number> = {
    teleqna: 0.7,   // Easier - higher avg scores
    telelogs: 0.3,  // Harder - lower avg scores
    telemath: 0.4,  // Medium-hard
    tsg: 0.4,       // Medium-hard
  };

  // Benchmark slopes (how discriminating each benchmark is)
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

  // Scale to ECI-like range (roughly 90-150)
  const rawCapability = weightedCapability / totalWeight;
  const tci = 115 + rawCapability * 20;

  return Math.round(tci * 10) / 10;
}

// Key models to label
const labeledModels = new Set([
  'GPT-5',
  'Grok-4-fast',
  'Claude-Sonnet-4.5',
  'Gemini-2.5-pro',
  'Llama-3.3-70B-Instruct',
  'TSLAM-18B',
  'Qwen3-32B',
]);

// Label position offsets for each model (negative x to point left since axis is reversed)
const labelOffsets: Record<string, { x: number; y: number }> = {
  'GPT-5': { x: -70, y: 0 },
  'Grok-4-fast': { x: -95, y: 0 },
  'Claude-Sonnet-4.5': { x: -130, y: 0 },
  'Gemini-2.5-pro': { x: -115, y: 0 },
  'TSLAM-18B': { x: -85, y: 0 },
  'Llama-3.3-70B-Instruct': { x: -155, y: 0 },
  'Qwen3-32B': { x: -90, y: 0 },
};

interface DataPoint {
  rank: number;
  tci: number;
  model: string;
  provider: string;
  color: string;
  isLabeled: boolean;
  teleqna: number | null;
  telelogs: number | null;
  telemath: number | null;
  tsg: number | null;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as DataPoint;
    return (
      <div style={{
        backgroundColor: 'white',
        padding: '12px 16px',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        fontSize: '13px',
        lineHeight: '1.5',
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '8px', color: data.color }}>
          {data.model}
        </div>
        <div style={{ color: '#666', marginBottom: '6px' }}>{data.provider}</div>
        <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '8px' }}>
          TCI Score: {data.tci}
        </div>
        <div style={{ borderTop: '1px solid #eee', paddingTop: '8px', fontSize: '12px' }}>
          <div>TeleQnA: {data.teleqna !== null ? `${data.teleqna}%` : '—'}</div>
          <div>TeleLogs: {data.telelogs !== null ? `${data.telelogs}%` : '—'}</div>
          <div>TeleMath: {data.telemath !== null ? `${data.telemath}%` : '—'}</div>
          <div>3GPP-TSG: {data.tsg !== null ? `${data.tsg}%` : '—'}</div>
        </div>
      </div>
    );
  }
  return null;
};

// Custom label renderer for labeled points
const renderCustomLabel = (props: any) => {
  const { x, y, payload } = props;
  if (!payload?.isLabeled) return null;

  const offset = labelOffsets[payload.model] || { x: -80, y: 0 };

  return (
    <text
      x={x + offset.x}
      y={y + offset.y}
      fill={payload.color}
      fontSize={10}
      fontWeight="500"
      dominantBaseline="middle"
    >
      {payload.model}
    </text>
  );
};

export default function TelcoCapabilityIndex(): JSX.Element {
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch CSV from static data folder
    fetch('/open_telco/data/telecom-llm-leaderboard.csv')
      .then(response => {
        if (!response.ok) throw new Error('Failed to load leaderboard data');
        return response.text();
      })
      .then(csvText => {
        const data = parseCSV(csvText);
        setLeaderboardData(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const chartData = useMemo(() => {
    return leaderboardData
      .map((entry) => {
        const tci = calculateTCI(entry);
        if (tci === null) return null;

        return {
          rank: entry.rank,
          tci,
          model: entry.model,
          provider: entry.provider,
          color: COLORS[entry.provider] || COLORS['Other'],
          isLabeled: labeledModels.has(entry.model),
          teleqna: entry.teleqna,
          telelogs: entry.telelogs,
          telemath: entry.telemath,
          tsg: entry.tsg,
        };
      })
      .filter((d): d is DataPoint => d !== null);
  }, [leaderboardData]);

  // Get unique providers for legend (in order of appearance)
  const providers = useMemo(() => {
    const seen = new Set<string>();
    const result: { name: string; color: string }[] = [];
    leaderboardData.forEach(entry => {
      if (!seen.has(entry.provider)) {
        seen.add(entry.provider);
        result.push({
          name: entry.provider,
          color: COLORS[entry.provider] || COLORS['Other'],
        });
      }
    });
    return result;
  }, [leaderboardData]);

  // Calculate dynamic Y-axis domain based on actual data
  const yAxisDomain = useMemo(() => {
    if (chartData.length === 0) return [90, 140];
    const tciValues = chartData.map(d => d.tci);
    const minTCI = Math.min(...tciValues);
    const maxTCI = Math.max(...tciValues);
    // Add padding and round to nice numbers
    const padding = (maxTCI - minTCI) * 0.1;
    return [
      Math.floor((minTCI - padding) / 5) * 5,
      Math.ceil((maxTCI + padding) / 5) * 5
    ];
  }, [chartData]);

  // Generate Y-axis ticks
  const yAxisTicks = useMemo(() => {
    const [min, max] = yAxisDomain;
    const ticks: number[] = [];
    for (let i = min; i <= max; i += 10) {
      ticks.push(i);
    }
    return ticks;
  }, [yAxisDomain]);

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
        Loading leaderboard data...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#E60000' }}>
        Error loading data: {error}
      </div>
    );
  }

  return (
    <div style={{ width: '100%', padding: '20px 0' }}>
      {/* Title matching Epoch style */}
      <h2 style={{
        fontSize: '20px',
        fontWeight: 'bold',
        marginBottom: '20px',
        color: '#008080',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}>
        Telco Capabilities Index (TCI)
      </h2>

      {/* Chart container */}
      <div style={{ position: 'relative' }}>
        {/* Legend - positioned top right like Epoch */}
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '20px',
          backgroundColor: 'rgba(255,255,255,0.97)',
          border: '1px solid #E0E0E0',
          borderRadius: '6px',
          padding: '10px 14px',
          zIndex: 10,
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        }}>
          <div style={{ fontSize: '9px', color: '#888', marginBottom: '6px' }}>
            {chartData.length} Results
          </div>
          <div style={{ fontSize: '10px', fontWeight: '600', marginBottom: '8px', color: '#333' }}>
            Organization
          </div>
          {providers.map((p) => (
            <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: p.color,
              }} />
              <span style={{ fontSize: '10px', color: '#555' }}>{p.name}</span>
            </div>
          ))}
        </div>

        <ResponsiveContainer width="100%" height={480}>
          <ScatterChart
            margin={{ top: 20, right: 180, bottom: 50, left: 50 }}
          >
            <CartesianGrid
              strokeDasharray="0"
              stroke="#CCCCCC"
              strokeOpacity={0.25}
              vertical={true}
              horizontal={true}
            />
            <XAxis
              type="number"
              dataKey="rank"
              name="Rank"
              domain={[23, 0]}
              reversed={true}
              ticks={[20, 15, 10, 5, 1]}
              tick={{ fontSize: 11, fill: '#666' }}
              axisLine={false}
              tickLine={false}
            >
              <Label
                value="Leaderboard rank"
                offset={-5}
                position="bottom"
                style={{
                  fontSize: '12px',
                  fill: '#666',
                }}
              />
            </XAxis>
            <YAxis
              type="number"
              dataKey="tci"
              name="Score"
              domain={yAxisDomain}
              ticks={yAxisTicks}
              tick={{ fontSize: 11, fill: '#666' }}
              axisLine={false}
              tickLine={false}
            >
              <Label
                value="Score"
                angle={0}
                position="top"
                offset={10}
                style={{
                  fontSize: '12px',
                  fill: '#666',
                }}
              />
            </YAxis>
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter
              data={chartData}
              fill="#8884d8"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  fillOpacity={0.9}
                  r={9}
                />
              ))}
              <LabelList
                dataKey="model"
                content={renderCustomLabel}
              />
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
