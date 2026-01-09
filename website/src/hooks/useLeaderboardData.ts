import { useState, useEffect } from 'react';
import type { LeaderboardEntry } from '../types/leaderboard';
import { transformHuggingFaceData } from '../utils/transformHuggingFaceData';

const HUGGINGFACE_API_URL =
  'https://datasets-server.huggingface.co/rows?dataset=GSMA/leaderboard&config=default&split=train&offset=0&length=100';

interface UseLeaderboardDataResult {
  data: LeaderboardEntry[];
  loading: boolean;
  error: string | null;
}

export function useLeaderboardData(): UseLeaderboardDataResult {
  const [data, setData] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(HUGGINGFACE_API_URL)
      .then(response => {
        if (!response.ok) throw new Error('Failed to load leaderboard data from HuggingFace');
        return response.json();
      })
      .then(jsonData => {
        setData(transformHuggingFaceData(jsonData));
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { data, loading, error };
}
