import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function mapAudit(item: Record<string, any>, index: number) {
  return {
    id: index + 1,
    order_id: item.order_id,
    platform: item.platform || "odoo",
    audit_status: item.audit_status,
    audit_reason: item.audit_notes || null,
    snapshot_at: item.audited_at || null,
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/integration/order-audits${query ? `?${query}` : ""}`, {
      headers: { "Content-Type": "application/json" },
    });
    let data;
    try {
      data = await response.json();
    } catch {
      const text = await response.text();
      return NextResponse.json({ detail: text || `HTTP ${response.status}` }, { status: response.status });
    }
    const items = Array.isArray(data?.data?.audits)
      ? data.data.audits.map(mapAudit)
      : [];
    return NextResponse.json(items, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to connect to order audits service" }, { status: 500 });
  }
}
