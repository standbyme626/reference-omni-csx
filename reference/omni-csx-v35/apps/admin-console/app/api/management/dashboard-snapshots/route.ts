import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function mapDashboardSnapshot(item: Record<string, any>) {
  const metrics = [
    ["conversation_count", item.total_conversations],
    ["avg_response_time", item.pending_followups],
    ["satisfaction_score", item.service_score],
    ["resolved_case_count", item.risk_alerts],
  ];
  return metrics.map(([metricType, metricValue], index) => ({
    id: Number(item.id) * 10 + index,
    snapshot_date: item.snapshot_date,
    metric_type: metricType,
    metric_value: Number(metricValue ?? 0),
    created_at: item.created_at || null,
  }));
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/management/dashboard-snapshots${query ? `?${query}` : ""}`, {
      headers: { "Content-Type": "application/json" },
    });
    let data;
    try {
      data = await response.json();
    } catch {
      const text = await response.text();
      return NextResponse.json({ detail: text || `HTTP ${response.status}` }, { status: response.status });
    }
    const items = Array.isArray(data?.data?.items)
      ? data.data.items.flatMap(mapDashboardSnapshot)
      : [];
    return NextResponse.json(items, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to connect to management service" }, { status: 500 });
  }
}
