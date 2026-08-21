"""AI query endpoint — stub for the command bar.

This creates the correct architecture for a future LLM integration.
For now it returns deterministic rule-based responses.
"""
from fastapi import APIRouter

from app.schemas.schemas import AIQueryRequest, AIQueryResponse

router = APIRouter(tags=["ai"])

# Simple keyword-based response map for the MVP
_RULES: list[tuple[list[str], str, list[str]]] = [
    (
        ["delayed", "truck", "trucks"],
        "Currently 1 truck (TR-1028) is delayed due to traffic on NH-48. "
        "ETA has been pushed by approximately 3 hours. The affected shipment is SHP-88208.",
        ["Show me the delayed truck", "What shipments are affected?", "Which orders are at risk?"],
    ),
    (
        ["inventory", "risk", "low", "stock", "critical"],
        "There are 3 SKUs at critical inventory levels: SKU-1004 (Enamel Paint 20L) with 2 days coverage, "
        "SKU-2002 (Packaging Film Roll) approaching reorder point, and SKU-2006 (Motor Assembly) at 1.5 days coverage. "
        "Recommend placing emergency orders for SKU-1004 and SKU-2006.",
        ["Show me SKU-1004 bay location", "Which suppliers can fulfil?", "What orders depend on these SKUs?"],
    ),
    (
        ["dock", "congestion", "utilization"],
        "Current dock utilization is at 76%. 7 of 10 docks are active. "
        "D-09 is under maintenance which is contributing to congestion. "
        "Recommend rescheduling D-09 maintenance to off-peak hours.",
        ["Show dock status", "Which trucks are waiting?", "When will D-09 be available?"],
    ),
    (
        ["shipment", "tomorrow", "order", "affect"],
        "3 shipments are at risk of affecting tomorrow's orders: SHP-88202 (delayed +4h), "
        "SHP-88207 (delayed +2.5h), and SHP-88214 (customs hold). "
        "Together they could impact 6 customer orders worth ₹12.4L.",
        ["Show affected orders", "What are the backup options?", "Which suppliers are involved?"],
    ),
    (
        ["supplier", "delay", "risk"],
        "2 suppliers are flagged as high risk: SUP-03 (Hindustan Unilever, reliability 62%) and "
        "SUP-09 (Mahindra Parts, factory shutdown). SUP-09 is critical — affects 5 orders worth ₹7.8L.",
        ["Show SUP-09 impact analysis", "List backup suppliers", "Which SKUs are affected?"],
    ),
    (
        ["SHP-88291", "88291", "why"],
        "Shipment SHP-88202 is delayed by approximately 4 hours. Root cause: late dispatch from "
        "supplier SUP-03 (Hindustan Unilever) due to production scheduling issues at their Mumbai facility. "
        "This impacts SKU-1003 inventory and 2 downstream customer orders.",
        ["Show the affected orders", "Can we source from alternate supplier?", "What is the recovery plan?"],
    ),
]

_DEFAULT = (
    "I can help you understand your supply chain operations. Try asking about "
    "delayed trucks, inventory risks, dock congestion, shipment impacts, or supplier issues.",
    [
        "Which trucks are delayed?",
        "Which bays have inventory risk?",
        "What shipments could affect tomorrow's orders?",
        "Show me dock congestion.",
        "Which suppliers are at risk?",
    ],
)


@router.post("/ai/query", response_model=AIQueryResponse)
def ai_query(req: AIQueryRequest):
    query_lower = req.query.lower()
    for keywords, response, suggestions in _RULES:
        if any(kw in query_lower for kw in keywords):
            return AIQueryResponse(query=req.query, response=response, suggestions=suggestions)
    return AIQueryResponse(query=req.query, response=_DEFAULT[0], suggestions=_DEFAULT[1])
