import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

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
    if (data && data.data && data.data.items) {
      return NextResponse.json(data.data.items, { status: response.status });
    }
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to connect to operation campaigns service" }, { status: 500 });
  }
}
