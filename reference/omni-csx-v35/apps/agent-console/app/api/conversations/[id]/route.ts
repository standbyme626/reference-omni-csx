import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const response = await fetch(`${API_GATEWAY_URL}/api/conversations/${id}`, {
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();
    const payload = data?.data?.conversation ?? data?.data ?? data;
    return NextResponse.json(
      {
        ...payload,
        id: payload?.id ?? payload?.conversation_id ?? id,
        customer_nick: payload?.customer_nick ?? "未知客户",
        assigned_agent: payload?.assigned_agent ?? null,
      },
      { status: response.status }
    );
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch conversation" }, { status: 500 });
  }
}
