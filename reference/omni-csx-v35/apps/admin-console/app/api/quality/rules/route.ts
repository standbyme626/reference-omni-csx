import { NextResponse } from "next/server";

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function mapRule(rule: Record<string, any>, index: number) {
  const severityMap: Record<string, string> = {
    response_time: "high",
    resolution_time: "medium",
    politeness: "low",
  };
  return {
    id: index + 1,
    rule_code: rule.rule_id,
    rule_name: rule.name,
    rule_type: rule.rule_id,
    severity: severityMap[rule.rule_id] || "low",
    description: rule.description || null,
    config_json: rule,
    created_at: null,
    updated_at: null,
  };
}

export async function GET() {
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/quality/rules`, {
      headers: { "Content-Type": "application/json" },
    });
    let data;
    try {
      data = await response.json();
    } catch {
      const text = await response.text();
      return NextResponse.json({ detail: text || `HTTP ${response.status}` }, { status: response.status });
    }
    const items = Array.isArray(data?.data?.rules)
      ? data.data.rules.map(mapRule)
      : [];
    return NextResponse.json(items, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to connect to quality rules service" }, { status: 500 });
  }
}
