import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();
  
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/audit-logs${query ? `?${query}` : ""}`, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    const data = await response.json();
    const payload = data?.data ?? data;
    return NextResponse.json(
      { items: payload?.items ?? [], total: payload?.total ?? 0 },
      { status: response.status }
    );
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch audit logs" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const response = await fetch(`${API_GATEWAY_URL}/api/audit-logs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    return NextResponse.json(data?.data ?? data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: "Failed to create audit log" }, { status: 500 });
  }
}
