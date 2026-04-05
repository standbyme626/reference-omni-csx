"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSummaries();
  }, []);

  const fetchSummaries = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("/api/analytics/summaries");
      if (!response.ok) {
        throw new Error("Failed to fetch analytics");
      }
      const data = await response.json();
      const payload = data?.data ?? data;
      setSummary({
        total_conversations: payload?.total_conversations || 0,
        active_conversations: payload?.active_conversations || 0,
        pending_followups: payload?.pending_followups || 0,
        risk_alerts: payload?.risk_alerts || 0,
      });
    } catch (err) {
      setError("统计数据加载失败");
      console.error("Failed to fetch analytics summaries:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-4 px-4">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-bold">数据概览</h1>
              <Link
                href="/conversations"
                className="text-sm text-blue-600 hover:underline"
              >
                返回会话列表
              </Link>
            </div>
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
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-bold">数据概览</h1>
              <Link
                href="/conversations"
                className="text-sm text-blue-600 hover:underline"
              >
                返回会话列表
              </Link>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto py-6 px-4">
          <p className="text-red-500">{error}</p>
        </main>
      </div>
    );
  }

  const stats = summary
    ? [
        { label: "总会话数", value: summary.total_conversations, color: "text-blue-600" },
        { label: "活跃会话", value: summary.active_conversations, color: "text-green-600" },
        { label: "待跟进任务", value: summary.pending_followups, color: "text-yellow-600" },
        { label: "风险预警", value: summary.risk_alerts, color: "text-red-600" },
      ]
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-4 px-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold">数据概览</h1>
            <Link
              href="/conversations"
              className="text-sm text-blue-600 hover:underline"
            >
              返回会话列表
            </Link>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 px-4">
        {stats.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">暂无统计数据</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {stats.map((item) => (
              <div key={item.label} className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-500">{item.label}</p>
                <p className={`text-3xl font-semibold ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
