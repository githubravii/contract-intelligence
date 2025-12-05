from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.schemas import WebhookCreate, WebhookResponse
from app.models import WebhookSubscription
from app.utils.security import verify_api_key
import secrets

router = APIRouter()

@router.post("/webhook/events", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Register a webhook for event notifications."""
    
    # Generate secret if not provided
    if not webhook.secret:
        webhook.secret = secrets.token_hex(32)
    
    subscription = WebhookSubscription(
        url=webhook.url,
        event_types=webhook.event_types,
        secret=webhook.secret,
        active=1
    )
    
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    
    return WebhookResponse(
        id=subscription.id,
        url=subscription.url,
        event_types=subscription.event_types,
        active=bool(subscription.active),
        created_at=subscription.created_at
    )

@router.get("/webhook/events", response_model=List[WebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """List all webhook subscriptions."""
    
    result = await db.execute(select(WebhookSubscription))
    webhooks = result.scalars().all()
    
    return [
        WebhookResponse(
            id=w.id,
            url=w.url,
            event_types=w.event_types,
            active=bool(w.active),
            created_at=w.created_at
        )
        for w in webhooks
    ]

@router.delete("/webhook/events/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Delete a webhook subscription."""
    
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(404, "Webhook not found")
    
    await db.delete(webhook)
    await db.commit()
    
    return {"message": "Webhook deleted"}
