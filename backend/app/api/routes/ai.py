"""Agent API — orchestrator queries and the human approval gate.

Route handlers stay thin: they translate HTTP into an orchestrator/tool call
and back. All reasoning lives in ``app.agents``; all data access in
``app.services.tools``.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_goal
from app.agents.specialists import ALL_AGENTS
from app.core.database import get_db
from app.models.models import ActionStatus, AgentAction
from app.schemas.schemas import (
    ActionDecisionResponse,
    ActionOut,
    AgentInfo,
    AgentTraceOut,
    AIQueryRequest,
    AIQueryResponse,
    FindingOut,
    SimulateRequest,
    ToolCallOut,
    ToolInfo,
)
from app.services import tools

router = APIRouter(tags=["ai"])


@router.post("/ai/query", response_model=AIQueryResponse)
def ai_query(req: AIQueryRequest, db: Session = Depends(get_db)):
    """Run a goal through the orchestrator and return findings + proposals."""
    goal = req.query.strip()
    if not goal:
        raise HTTPException(status_code=422, detail="Query must not be empty")

    run = run_goal(db, goal)

    actions = (
        db.query(AgentAction)
        .filter(AgentAction.id.in_(run.action_ids))
        .order_by(AgentAction.projected_savings.desc())
        .all()
        if run.action_ids
        else []
    )

    return AIQueryResponse(
        query=goal,
        response=run.answer,
        suggestions=run.followups,
        agents=[
            AgentTraceOut(
                agent=r.agent,
                relevance=round(r.relevance, 2),
                summary=r.summary,
                findings=[
                    FindingOut(
                        headline=f.headline,
                        detail=f.detail,
                        severity=f.severity,
                        entity_type=f.entity_type,
                        entity_code=f.entity_code,
                        metrics=f.metrics,
                    )
                    for f in r.findings
                ],
                tool_calls=[
                    ToolCallOut(tool=c.tool, args=c.args, result_summary=c.result_summary)
                    for c in r.tool_calls
                ],
            )
            for r in run.agents
        ],
        actions=[ActionOut.model_validate(a) for a in actions],
    )


@router.get("/actions", response_model=list[ActionOut])
def list_actions(status: ActionStatus | None = None, db: Session = Depends(get_db)):
    q = db.query(AgentAction)
    if status is not None:
        q = q.filter(AgentAction.status == status)
    return q.order_by(AgentAction.created_at.desc(), AgentAction.id.desc()).limit(50).all()


@router.post("/actions/{action_id}/approve", response_model=ActionDecisionResponse)
def approve_action(action_id: int, db: Session = Depends(get_db)):
    """The human approval gate. Re-validates, then executes."""
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status == ActionStatus.EXECUTED:
        raise HTTPException(status_code=409, detail="Action already executed")
    if action.status == ActionStatus.REJECTED:
        raise HTTPException(status_code=409, detail="Action was rejected")

    # Conditions may have changed since the proposal was made.
    validation = tools.validate_action(db, action_id)
    if not validation["ok"]:
        db.commit()
        return ActionDecisionResponse(
            ok=False,
            message=f"Validation failed: {validation['notes']}",
            action=ActionOut.model_validate(action),
        )

    result = tools.execute_action(db, action_id)
    db.commit()
    db.refresh(action)
    return ActionDecisionResponse(
        ok=result["ok"],
        message=result["message"],
        action=ActionOut.model_validate(action),
    )


@router.post("/actions/{action_id}/reject", response_model=ActionDecisionResponse)
def reject_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status == ActionStatus.EXECUTED:
        raise HTTPException(status_code=409, detail="Action already executed")

    action.status = ActionStatus.REJECTED
    action.result_message = "Rejected by operator"
    db.commit()
    db.refresh(action)
    return ActionDecisionResponse(
        ok=True,
        message="Action rejected",
        action=ActionOut.model_validate(action),
    )


@router.post("/simulate")
def simulate(req: SimulateRequest, db: Session = Depends(get_db)):
    result = tools.simulate_delay(db, shipment_code=req.shipment_code, extra_hours=req.extra_hours)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/agents", response_model=list[AgentInfo])
def list_agents():
    return [AgentInfo(name=a.name, domain=a.domain) for a in ALL_AGENTS]


@router.get("/tools", response_model=list[ToolInfo])
def list_tools():
    return [ToolInfo(**t) for t in tools.tool_catalog()]
