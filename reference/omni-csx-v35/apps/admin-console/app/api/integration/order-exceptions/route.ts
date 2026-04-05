import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/integration/order-exceptions${query ? `?${query}` : ""}`, {
      headers: { "Content-Type": "application/json" },
    });
    let data;
    try {
      data = await response.json();
    } catch {
      const text = await response.text();
      return NextResponse.json({ detail: text || `HTTP ${response.status}` }, { status: response.status });
    }
    const items = Array.isArray(data?.data?.exceptions) ? data.data.exceptions : [];
    return NextResponse.json(items, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to connect to order exceptions service" }, { status: 500 });
  }
}
