import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();

  try {
    const url = `${API_GATEWAY_URL}/api/conversations${query ? `?${query}` : ""}`;
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();
    const payload = data?.data ?? data;
    const items = Array.isArray(payload?.items) ? payload.items : Array.isArray(payload) ? payload : [];
    return NextResponse.json(
      { items, total: payload?.total ?? items.length },
      { status: response.status }
    );
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch conversations" }, { status: 500 });
  }
}
