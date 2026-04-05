"use client";

import { useState, useEffect } from "react";

interface AnalyticsData {
  total_conversations: number;
  active_conversations: number;
  pending_followups: number;
  risk_alerts: number;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("/api/analytics/summaries");
      if (!response.ok) {
        throw new Error("Failed to fetch analytics");
      }
      const result = await response.json();
      if ((result.code === 0 || result.code === "0") && result.data) {
        setData(result.data);
      } else {
        throw new Error(result.message || "Invalid response");
      }
    } catch (err) {
      setError("统计数据加载失败");
      console.error("Failed to fetch analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-4 px-4">
            <h1 className="text-xl font-bold">数据概览</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto py-6 px-4">
          <p className="text-gray-500">加载中...</p>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-4 px-4">
            <h1 className="text-xl font-bold">数据概览</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto py-6 px-4">
          <p className="text-red-500">{error}</p>
        </main>
      </div>
    );
  }

  const stats = data
    ? [
        { label: "总会话数", value: data.total_conversations, color: "blue" },
        { label: "活跃会话", value: data.active_conversations, color: "green" },
        { label: "待跟进", value: data.pending_followups, color: "yellow" },
        { label: "风险告警", value: data.risk_alerts, color: "red" },
      ]
    : [];

  const colorMap: Record<string, string> = {
    blue: "text-blue-600",
    green: "text-green-600",
    yellow: "text-yellow-600",
    red: "text-red-600",
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-4 px-4">
          <h1 className="text-xl font-bold">数据概览</h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 px-4">
        {!data ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">暂无统计数据</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="bg-white rounded-lg shadow p-6"
              >
                <p className="text-sm text-gray-500 truncate">{stat.label}</p>
                <p className={`text-3xl font-semibold ${colorMap[stat.color]}`}>
                  {stat.value}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
