import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function mapTrainingCase(item: Record<string, any>) {
  const typeMap: Record<string, string> = {
    after_sale: "typical",
    shipment: "edge_case",
  };
  return {
    id: item.id,
    conversation_id: null,
    customer_id: null,
    case_title: item.title,
    case_summary: `难度: ${item.difficulty} / 状态: ${item.status}`,
    case_type: typeMap[item.scenario] || "typical",
    created_at: item.created_at || null,
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/management/training-cases${query ? `?${query}` : ""}`, {
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
      ? data.data.items.map(mapTrainingCase)
      : [];
    return NextResponse.json(items, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to connect to management service" }, { status: 500 });
  }
}
