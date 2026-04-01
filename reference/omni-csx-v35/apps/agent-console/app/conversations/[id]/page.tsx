"use client";

import { useState, useEffect, use } from "react";
import { useParams } from "next/navigation";
import FollowupPanel from "./components/FollowupPanel";
import RecommendationPanel from "./components/RecommendationPanel";
import RiskFlagPanel from "./components/RiskFlagPanel";
import CustomerProfilePanel from "./components/CustomerProfilePanel";

interface Message {
  id: string;
  direction: string;
  content: string;
  sender: string;
  create_time: string;
}

interface Conversation {
  id: string;
  conversation_pk?: number;
  platform: string;
  customer_id?: string;
  customer_pk?: number;
  customer_nick: string;
  status: string;
  assigned_agent: string | null;
}

interface Order {
  order_id: string;
  status: string;
  status_name: string;
  create_time: string;
  payment_amount: number;
  receiver_name: string;
  receiver_phone: string;
  items: { sku_name: string; quantity: number }[];
}

interface Shipment {
  shipments: {
    express_company: string;
    express_no: string;
    status: string;
    status_name: string;
  }[];
}

interface AfterSale {
  after_sale_id: string;
  type: string;
  type_name: string;
  status: string;
  status_name: string;
  apply_amount: number;
}

interface AISuggestion {
  intent: string;
  confidence: number;
  suggested_reply: string;
  used_tools: string[];
  risk_level: string;
  needs_human_review: boolean;
}

interface InventorySnapshot {
  product_id: string;
  sku_id?: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  warehouse?: string;
  location?: string;
}

interface OrderAuditSnapshot {
  order_id: string;
  audit_status: string;
  audit_notes?: string;
  audited_by?: string;
}

interface OrderExceptionSnapshot {
  exception_id: string;
  order_id: string;
  exception_type: string;
  severity: string;
  description: string;
  status: string;
}

interface FulfillmentSnapshot {
  order_id: string;
  status: string;
  warehouse?: string;
  picking_id?: string;
}

interface BusinessContext {
  context_id: string;
  platform: string;
  biz_id: string;
  biz_type: string;
  order_snapshot?: {
    order_id: string;
    status: string;
    total_amount: string;
    created_at: string;
  };
  shipment_snapshot?: {
    shipment_id: string;
    status: string;
    company?: string;
    tracking_no?: string;
  };
  after_sale_snapshot?: {
    after_sale_id: string;
    status: string;
    reason?: string;
  };
  inventory_snapshot?: InventorySnapshot;
  order_audit_snapshot?: OrderAuditSnapshot;
  order_exception_snapshots: OrderExceptionSnapshot[];
  fulfillment_snapshot?: FulfillmentSnapshot;
  risk_flags?: {
    level: string;
    tags: string[];
    score: number;
  };
  action_candidates: Array<{
    action_type: string;
    priority: number;
    description: string;
  }>;
  reply_candidates: Array<{
    reply_type: string;
    content: string;
    confidence: number;
  }>;
}

const platformLabels: Record<string, string> = {
  jd: "京东",
  douyin_shop: "抖音",
  wecom_kf: "企微",
  taobao: "淘宝",
  xhs: "小红书",
  kuaishou: "快手",
};

function ConversationHeader({ conversation }: { conversation: Conversation }) {
  return (
    <div className="bg-white border-b px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">会话 {conversation.id}</h2>
          <p className="text-sm text-gray-500">
            客户: {conversation.customer_nick} | 平台: {platformLabels[conversation.platform] || conversation.platform}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span
            className={`px-3 py-1 rounded-full text-sm ${
              conversation.status === "active"
                ? "bg-green-100 text-green-800"
                : "bg-yellow-100 text-yellow-800"
            }`}
          >
            {conversation.status === "active" ? "进行中" : "等待中"}
          </span>
        </div>
      </div>
    </div>
  );
}

function MessageStream({ messages }: { messages: Message[] }) {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.direction === "inbound" ? "justify-start" : "justify-end"}`}
        >
          <div
            className={`max-w-md px-4 py-2 rounded-lg ${
              msg.direction === "inbound"
                ? "bg-gray-100 text-gray-800"
                : "bg-blue-500 text-white"
            }`}
          >
            <p className="text-sm">{msg.content}</p>
            <p className="text-xs mt-1 opacity-70">
              {new Date(msg.create_time).toLocaleString("zh-CN")}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function ReplyComposer({
  onSend,
  initialText,
}: {
  onSend: (text: string) => void;
  initialText?: string;
}) {
  const [text, setText] = useState(initialText || "");

  useEffect(() => {
    setText(initialText || "");
  }, [initialText]);

  return (
    <div className="border-t p-4 bg-white">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="输入回复内容..."
        className="w-full border rounded-lg p-3 min-h-[100px]"
      />
      <div className="mt-2 flex justify-end">
        <button
          onClick={() => {
            if (text.trim()) {
              onSend(text);
              setText("");
            }
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          发送
        </button>
      </div>
    </div>
  );
}

function OrderPanel({ order, platform }: { order: Order | null; platform?: string }) {
  if (!order) return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium text-lg mb-3">订单信息</h3>
      <p className="text-sm text-gray-500">
        {platform === "wecom_kf" ? "当前平台暂不支持订单上下文" : "暂无订单信息"}
      </p>
    </div>
  );
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium text-lg mb-3">订单信息</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">订单号:</span>
          <span>{order.order_id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">状态:</span>
          <span>{order.status_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">金额:</span>
          <span>¥{order.payment_amount}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">收货人:</span>
          <span>{order.receiver_name}</span>
        </div>
        <div className="mt-3 pt-3 border-t">
          <p className="text-gray-500 mb-1">商品:</p>
          {(order.items || []).map((item, idx) => (
            <p key={idx} className="text-sm">
              {item.sku_name} x{item.quantity}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}

function ShipmentPanel({ shipment, platform }: { shipment: Shipment | null; platform?: string }) {
  if (!shipment || !shipment.shipments?.length) return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium text-lg mb-3">物流信息</h3>
      <p className="text-sm text-gray-500">
        {platform === "wecom_kf" ? "当前平台暂不支持物流信息" : platform === "douyin_shop" ? "当前平台暂不支持物流查询" : "暂无物流信息"}
      </p>
    </div>
  );
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium text-lg mb-3">物流信息</h3>
      {shipment.shipments.map((ship, idx) => (
        <div key={idx} className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">快递:</span>
            <span>{ship.express_company}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">单号:</span>
            <span>{ship.express_no}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">状态:</span>
            <span>{ship.status_name}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function AfterSalePanel({ afterSale, platform }: { afterSale: AfterSale | null; platform?: string }) {
  if (!afterSale) return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium text-lg mb-3">售后信息</h3>
      <p className="text-sm text-gray-500">
        {platform === "wecom_kf" ? "当前平台暂不支持售后信息" : "暂无售后信息"}
      </p>
    </div>
  );
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium text-lg mb-3">售后信息</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">售后单号:</span>
          <span>{afterSale.after_sale_id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">类型:</span>
          <span>{afterSale.type_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">状态:</span>
          <span>{afterSale.status_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">金额:</span>
          <span>¥{afterSale.apply_amount}</span>
        </div>
      </div>
    </div>
  );
}

function SuggestionPanel({
  suggestion,
  onApply,
  onGenerate,
}: {
  suggestion: AISuggestion | null;
  onApply: (text: string) => void;
  onGenerate: () => void;
}) {
  if (!suggestion) return (
    <div className="bg-white rounded-lg shadow p-4 border-l-4 border-gray-300">
      <h3 className="font-medium text-lg mb-3">AI 建议回复</h3>
      <button
        onClick={onGenerate}
        className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
      >
        生成建议
      </button>
    </div>
  );
  
  return (
    <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
      <h3 className="font-medium text-lg mb-3">AI 建议回复</h3>
      <div className="space-y-2 text-sm mb-4">
        <div className="flex justify-between">
          <span className="text-gray-500">意图:</span>
          <span>{suggestion.intent || "-"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">置信度:</span>
          <span>
            {typeof suggestion.confidence === "number"
              ? `${(suggestion.confidence * 100).toFixed(0)}%`
              : "-"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">风险:</span>
          <span
            className={`${
              suggestion.risk_level === "low"
                ? "text-green-600"
                : suggestion.risk_level === "high"
                ? "text-red-600"
                : "text-yellow-600"
            }`}
          >
            {suggestion.risk_level || "-"}
          </span>
        </div>
      </div>
      <div className="bg-gray-50 p-3 rounded mb-4">
        <p className="text-sm">{suggestion.suggested_reply || "暂无建议内容"}</p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onApply(suggestion.suggested_reply)}
          className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
        >
          使用建议回复
        </button>
        <button
          onClick={onGenerate}
          className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600"
        >
          重新生成
        </button>
        <span className="text-xs text-gray-500 self-center">
          需人工确认后发送
        </span>
      </div>
    </div>
  );
}

function InventoryPanel({ inventory }: { inventory?: InventorySnapshot }) {
  if (!inventory) return null;
  
  return (
    <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
      <h3 className="font-medium text-lg mb-3">库存信息</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">商品ID:</span>
          <span>{inventory.product_id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">SKU:</span>
          <span>{inventory.sku_id || "-"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">库存数量:</span>
          <span className="font-medium">{inventory.quantity}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">预留数量:</span>
          <span className="text-orange-600">{inventory.reserved_quantity}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">可用数量:</span>
          <span className="text-green-600 font-medium">{inventory.available_quantity}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">仓库:</span>
          <span>{inventory.warehouse || "-"}</span>
        </div>
      </div>
    </div>
  );
}

function OrderAuditPanel({ audit }: { audit?: OrderAuditSnapshot }) {
  if (!audit) return null;
  
  const statusColor = audit.audit_status === "approved" 
    ? "text-green-600" 
    : audit.audit_status === "rejected" 
    ? "text-red-600" 
    : "text-yellow-600";
  
  return (
    <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
      <h3 className="font-medium text-lg mb-3">订单审核</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">订单号:</span>
          <span>{audit.order_id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">审核状态:</span>
          <span className={`font-medium ${statusColor}`}>
            {audit.audit_status === "approved" ? "已通过" : audit.audit_status === "rejected" ? "已拒绝" : "待审核"}
          </span>
        </div>
        {audit.audit_notes && (
          <div className="mt-2 pt-2 border-t">
            <span className="text-gray-500">备注:</span>
            <p className="mt-1">{audit.audit_notes}</p>
          </div>
        )}
        {audit.audited_by && (
          <div className="flex justify-between">
            <span className="text-gray-500">审核人:</span>
            <span>{audit.audited_by}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function OrderExceptionPanel({ exceptions }: { exceptions: OrderExceptionSnapshot[] }) {
  if (!exceptions || exceptions.length === 0) return null;
  
  return (
    <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
      <h3 className="font-medium text-lg mb-3 text-red-600">
        订单异常 ({exceptions.length})
      </h3>
      <div className="space-y-3">
        {exceptions.map((exc, idx) => (
          <div key={idx} className="p-2 bg-red-50 rounded text-sm">
            <div className="flex justify-between mb-1">
              <span className="font-medium text-red-700">{exc.exception_type}</span>
              <span className={`px-2 py-0.5 rounded text-xs ${
                exc.status === "open" ? "bg-red-200 text-red-800" : "bg-green-200 text-green-800"
              }`}>
                {exc.status === "open" ? "待处理" : "已解决"}
              </span>
            </div>
            <p className="text-gray-600">{exc.description}</p>
            <div className="flex justify-between mt-1 text-xs text-gray-500">
              <span>严重程度: {exc.severity}</span>
              <span>{exc.exception_id}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FulfillmentPanel({ fulfillment }: { fulfillment?: FulfillmentSnapshot }) {
  if (!fulfillment) return null;
  
  const statusText: Record<string, string> = {
    pending: "待处理",
    assigned: "已分配",
    picking: "拣货中",
    done: "已完成",
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
      <h3 className="font-medium text-lg mb-3">履约信息</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">订单号:</span>
          <span>{fulfillment.order_id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">状态:</span>
          <span className="font-medium">{statusText[fulfillment.status] || fulfillment.status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">仓库:</span>
          <span>{fulfillment.warehouse || "-"}</span>
        </div>
        {fulfillment.picking_id && (
          <div className="flex justify-between">
            <span className="text-gray-500">拣货单:</span>
            <span>{fulfillment.picking_id}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function ActionCandidatesPanel({ candidates }: { candidates: Array<{ action_type: string; priority: number; description: string }> }) {
  if (!candidates || candidates.length === 0) return null;
  
  return (
    <div className="bg-white rounded-lg shadow p-4 border-l-4 border-indigo-500">
      <h3 className="font-medium text-lg mb-3">建议操作</h3>
      <div className="space-y-2">
        {candidates.map((action, idx) => (
          <div key={idx} className="p-2 bg-indigo-50 rounded text-sm">
            <div className="flex justify-between mb-1">
              <span className="font-medium text-indigo-700">{action.action_type}</span>
              <span className="text-xs text-gray-500">优先级: {action.priority}</span>
            </div>
            <p className="text-gray-600">{action.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export default function ConversationDetailPage() {
  const params = useParams();
  const convId = params.id as string;
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [order, setOrder] = useState<Order | null>(null);
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [afterSale, setAfterSale] = useState<AfterSale | null>(null);
  const [suggestion, setSuggestion] = useState<AISuggestion | null>(null);
  const [replyText, setReplyText] = useState("");
  const [loading, setLoading] = useState(true);
  const [businessContext, setBusinessContext] = useState<BusinessContext | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [convRes, msgRes] = await Promise.all([
          fetch(`/api/conversations/${convId}`),
          fetch(`/api/conversations/${convId}/messages`),
        ]);
        
        const convData = await convRes.json();
        const msgData = await msgRes.json();
        
        setConversation(convData);
        setMessages(msgData.items || []);
        
        const contextMap: Record<string, { platform: string; orderId?: string; bizType?: string }> = {
          "conv_001": { platform: "taobao", orderId: "ORDER_001", bizType: "order" },
          "conv_002": { platform: "douyin_shop", orderId: "ORDER_002", bizType: "order" },
          "conv_003": { platform: "wecom_kf", orderId: "conv_003", bizType: "conversation" },
        };
        const ctx = contextMap[convId];
        
        if (ctx && ctx.orderId) {
          try {
            const contextRes = await fetch(`/api/context/build`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                platform: ctx.platform,
                biz_id: ctx.orderId,
                biz_type: ctx.bizType || "order",
                include_inventory: true,
                include_risk: true,
                include_quality: true,
                include_recommendations: true,
              }),
            });
            const contextData = await contextRes.json();
            if (contextData && contextData.context_id) {
              setBusinessContext(contextData);
              
              if (contextData.order_snapshot) {
                setOrder({
                  order_id: contextData.order_snapshot.order_id,
                  status: contextData.order_snapshot.status,
                  status_name: contextData.order_snapshot.status,
                  create_time: contextData.order_snapshot.created_at,
                  payment_amount: parseFloat(contextData.order_snapshot.total_amount) || 0,
                  receiver_name: "",
                  receiver_phone: "",
                  items: [],
                });
              }
              
              if (contextData.shipment_snapshot) {
                setShipment({
                  shipments: [{
                    express_company: contextData.shipment_snapshot.company || "",
                    express_no: contextData.shipment_snapshot.tracking_no || "",
                    status: contextData.shipment_snapshot.status,
                    status_name: contextData.shipment_snapshot.status,
                  }],
                });
              }
              
              if (contextData.after_sale_snapshot) {
                setAfterSale({
                  after_sale_id: contextData.after_sale_snapshot.after_sale_id,
                  type: "refund",
                  type_name: "退款",
                  status: contextData.after_sale_snapshot.status,
                  status_name: contextData.after_sale_snapshot.status,
                  apply_amount: 0,
                });
              }
              
              if (contextData.reply_candidates && contextData.reply_candidates.length > 0) {
                setSuggestion({
                  intent: contextData.action_candidates?.[0]?.action_type || "unknown",
                  confidence: contextData.reply_candidates[0].confidence,
                  suggested_reply: contextData.reply_candidates[0].content,
                  used_tools: [],
                  risk_level: contextData.risk_flags?.level || "low",
                  needs_human_review: false,
                });
              }
            }
          } catch (contextError) {
            console.error("Failed to fetch business context:", contextError);
          }
        }
      } catch (error) {
        console.error("Failed to fetch conversation data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [convId]);

  const handleSend = async (text: string) => {
    const newMsg: Message = {
      id: `msg_${Date.now()}`,
      direction: "outbound",
      content: text,
      sender: "agent",
      create_time: new Date().toISOString(),
    };
    setMessages([...messages, newMsg]);

    try {
      await fetch(`/api/audit-logs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "message_sent",
          actor_type: "agent",
          actor_id: "agent_001",
          target_type: "message",
          target_id: newMsg.id,
          detail: `Sent message in conversation: ${convId}`,
          detail_json: { conversation_id: convId, content: text },
        }),
      });
    } catch (error) {
      console.error("Failed to create audit log:", error);
    }
  };

  const handleApplySuggestion = (text: string) => {
    setReplyText(text);
  };

  const handleGenerateSuggestion = async () => {
    try {
      const lastMsg = messages.filter(m => m.direction === "inbound").pop();
      if (!lastMsg) return;
      
      const res = await fetch(`/api/ai/suggest-reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: convId,
          message: lastMsg.content,
          platform: conversation?.platform || "jd",
        }),
      });
      const data = await res.json();
      setSuggestion(data);
    } catch (error) {
      console.error("Failed to generate suggestion:", error);
    }
  };

  if (loading) return <div className="p-8 text-center">加载中...</div>;
  if (!conversation) return <div className="p-8 text-center">会话不存在</div>;

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <ConversationHeader conversation={conversation} />
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col">
          <MessageStream messages={messages} />
          <ReplyComposer onSend={handleSend} initialText={replyText} />
        </div>
        <div className="w-80 border-l bg-gray-100 p-4 space-y-4 overflow-y-auto">
          <OrderPanel order={order} platform={conversation?.platform} />
          <ShipmentPanel shipment={shipment} platform={conversation?.platform} />
          <AfterSalePanel afterSale={afterSale} platform={conversation?.platform} />
          
          {businessContext && (
            <>
              <InventoryPanel inventory={businessContext.inventory_snapshot} />
              <OrderAuditPanel audit={businessContext.order_audit_snapshot} />
              <OrderExceptionPanel exceptions={businessContext.order_exception_snapshots} />
              <FulfillmentPanel fulfillment={businessContext.fulfillment_snapshot} />
              <ActionCandidatesPanel candidates={businessContext.action_candidates} />
            </>
          )}
          
          <SuggestionPanel
            suggestion={suggestion}
            onApply={handleApplySuggestion}
            onGenerate={handleGenerateSuggestion}
          />
          {conversation?.conversation_pk && (
            <FollowupPanel conversationPk={conversation.conversation_pk} />
          )}
          {conversation?.conversation_pk && (
            <RecommendationPanel conversationPk={conversation.conversation_pk} />
          )}
          {conversation?.customer_pk && (
            <RiskFlagPanel customerPk={conversation.customer_pk} conversationPk={conversation.conversation_pk} />
          )}
          {conversation?.customer_pk && (
            <CustomerProfilePanel customerPk={conversation.customer_pk} />
          )}
        </div>
      </div>
    </div>
  );
}