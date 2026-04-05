import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function toNumericId(value: string): number {
  const digits = value.replace(/\D/g, "");
  return parseInt(digits || "0", 10);
}

function mapTask(task: Record<string, any>) {
  const taskTypeMap: Record<string, string> = {
    return_followup: "after_sale_care",
    shipment_followup: "shipment_exception",
    review_followup: "manual",
  };

  return {
    id: toNumericId(String(task.id || "")),
    conversation_id: task.conversation_id ? toNumericId(String(task.conversation_id)) : null,
    customer_id: 0,
    order_id: null,
    task_type: taskTypeMap[task.type] || task.type || "manual",
    trigger_source: "system",
    title: task.description || task.id,
    description: task.description || null,
    suggested_copy: null,
    status: task.status || "pending",
    priority: task.type === "shipment_followup" ? "high" : "medium",
    due_date: task.due_time || null,
    completed_at: task.status === "completed" ? task.updated_at || task.created_at || null : null,
    completed_by: task.assignee || null,
    extra_json: null,
    created_at: task.created_at || null,
    updated_at: task.updated_at || task.created_at || null,
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/follow-up/tasks${query ? `?${query}` : ""}`, {
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();
    const payload = data?.data ?? data;
    const items = Array.isArray(payload?.items) ? payload.items.map(mapTask) : [];
    return NextResponse.json(
      {
        items,
        total: payload?.total ?? items.length,
        page: payload?.page ?? 1,
        size: payload?.size ?? items.length,
      },
      { status: response.status }
    );
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch follow-up tasks" }, { status: 500 });
  }
}
