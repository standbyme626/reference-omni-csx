"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Summary {
  total_conversations: number;
  active_conversations: number;
  pending_followups: number;
  risk_alerts: number;
}

interface PlatformStat {
  platform: string;
  label: string;
  count: number;
}

const platformLabels: Record<string, string> = {
  taobao: "淘宝",
  douyin_shop: "抖店",
  jd: "京东",
  xhs: "小红书",
  kuaishou: "快手",
  wecom_kf: "企微客服",
};

const menuItems = [
  {
    title: "会话管理",
    description: "查看和处理客户会话",
    href: "/conversations",
    icon: "💬",
    color: "bg-blue-500",
  },
  {
    title: "跟进任务",
    description: "管理待处理的跟进任务",
    href: "/followups",
    icon: "📋",
    color: "bg-green-500",
  },
  {
    title: "风险预警",
    description: "查看和处理风险订单",
    href: "/operations",
    icon: "⚠️",
    color: "bg-red-500",
  },
  {
    title: "数据分析",
    description: "查看运营数据报表",
    href: "/analytics",
    icon: "📊",
    color: "bg-purple-500",
  },
];

export default function HomePage() {
  const [summary, setSummary] = useState<Summary>({
    total_conversations: 0,
    active_conversations: 0,
    pending_followups: 0,
    risk_alerts: 0,
  });
  const [platformStats, setPlatformStats] = useState<PlatformStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch("/api/analytics/summaries");
        const data = await res.json();
        const payload = data?.data ?? data;
        if (payload) {
          setSummary({
            total_conversations: payload.total_conversations || 0,
            active_conversations: payload.active_conversations || 0,
            pending_followups: payload.pending_followups || 0,
            risk_alerts: payload.risk_alerts || 0,
          });
        }

        setPlatformStats([
          { platform: "taobao", label: "淘宝", count: 128 },
          { platform: "douyin_shop", label: "抖店", count: 96 },
          { platform: "jd", label: "京东", count: 64 },
          { platform: "xhs", label: "小红书", count: 32 },
          { platform: "kuaishou", label: "快手", count: 28 },
          { platform: "wecom_kf", label: "企微客服", count: 156 },
        ]);
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">客服工作台</h1>
          <p className="text-gray-600 mt-2">欢迎回来，今天有 {summary.active_conversations} 个活跃会话需要处理</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">总会话数</p>
                <p className="text-2xl font-bold text-gray-900">{summary.total_conversations}</p>
              </div>
              <div className="text-4xl">💬</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">活跃会话</p>
                <p className="text-2xl font-bold text-blue-600">{summary.active_conversations}</p>
              </div>
              <div className="text-4xl">🟢</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">待跟进任务</p>
                <p className="text-2xl font-bold text-orange-600">{summary.pending_followups}</p>
              </div>
              <div className="text-4xl">📋</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">风险预警</p>
                <p className="text-2xl font-bold text-red-600">{summary.risk_alerts}</p>
              </div>
              <div className="text-4xl">⚠️</div>
            </div>
          </div>
        </div>

        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">快捷入口</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {menuItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
              >
                <div className="flex items-center mb-4">
                  <div className={`${item.color} text-white rounded-lg p-3 mr-4`}>
                    <span className="text-2xl">{item.icon}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">{item.title}</h3>
                </div>
                <p className="text-gray-600 text-sm">{item.description}</p>
              </Link>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">各平台会话分布</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {platformStats.map((stat) => (
              <div key={stat.platform} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">
                  {stat.platform === "taobao" && "🛒"}
                  {stat.platform === "douyin_shop" && "🎵"}
                  {stat.platform === "jd" && "🏠"}
                  {stat.platform === "xhs" && "📕"}
                  {stat.platform === "kuaishou" && "📱"}
                  {stat.platform === "wecom_kf" && "💼"}
                </div>
                <p className="text-sm text-gray-600">{stat.label}</p>
                <p className="text-xl font-bold text-gray-900">{stat.count}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow p-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">官方行为仿真系统</h2>
              <p className="text-blue-100">
                基于真实平台行为模拟，支持六平台（淘宝、抖店、京东、小红书、快手、企微客服）
              </p>
            </div>
            <div className="flex space-x-4">
              <a
                href="http://localhost:8001"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-white text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-50 transition-colors"
              >
                Sim Server
              </a>
              <a
                href="http://localhost:8000"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-white text-purple-600 px-4 py-2 rounded-lg font-medium hover:bg-purple-50 transition-colors"
              >
                Domain Service
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
