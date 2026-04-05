import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function mapCampaign(item: Record<string, any>) {
  const typeMap: Record<string, string> = {
    promotion: "push",
    launch: "wecom",
  };
  const statusMap: Record<string, string> = {
    active: "ready",
    preparing: "draft",
  };

  return {
    id: parseInt(String(item.id || "").replace(/\D/g, "") || "0", 10),
    name: item.name,
    campaign_type: typeMap[item.type] || item.type || "push",
    target_description: item.description || null,
    audience_json: null,
    preview_text: item.description || null,
    status: statusMap[item.status] || item.status || "draft",
    extra_json: { target_platforms: item.target_platforms || [] },
    created_at: item.start_time || null,
    updated_at: item.end_time || item.start_time || null,
  };
}

export async function GET() {
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/operation-campaigns`, {
      headers: { "Content-Type": "application/json" },
    });
    let data;
    try {
      data = await response.json();
    } catch {
      const text = await response.text();
      return NextResponse.json({ detail: text || `HTTP ${response.status}` }, { status: response.status });
    }
    const items = Array.isArray(data?.data?.items) ? data.data.items.map(mapCampaign) : [];
    return NextResponse.json(items, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to connect to operation campaigns service" }, { status: 500 });
  }
}
