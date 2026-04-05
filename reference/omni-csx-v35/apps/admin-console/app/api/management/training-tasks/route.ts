import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function mapTrainingTask(item: Record<string, any>) {
  const typeMap: Record<string, string> = {
    quality_review: "review",
    training: "practice",
  };
  const statusMap: Record<string, string> = {
    running: "in_progress",
  };
  return {
    id: item.id,
    task_name: item.task_name,
    task_type: typeMap[item.task_type] || "practice",
    status: statusMap[item.status] || item.status,
    related_case_id: null,
    created_at: item.created_at || null,
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/management/training-tasks${query ? `?${query}` : ""}`, {
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
      ? data.data.items.map(mapTrainingTask)
      : [];
    return NextResponse.json(items, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to connect to management service" }, { status: 500 });
  }
}
