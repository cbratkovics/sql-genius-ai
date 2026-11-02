import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.deps import get_current_active_user, get_current_tenant
from backend.models.tenant import Tenant, TenantPlan
from backend.models.user import User
from backend.services.stripe_service import stripe_service
from backend.services.tenant import tenant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


class CheckoutRequest(BaseModel):
    plan: TenantPlan
    success_url: str
    cancel_url: str


class BillingPortalRequest(BaseModel):
    return_url: str


class SubscriptionResponse(BaseModel):
    id: str | None
    status: str | None
    plan: TenantPlan
    current_period_start: int | None
    current_period_end: int | None
    cancel_at_period_end: bool | None


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        # Ensure tenant has a Stripe customer ID
        if not current_tenant.stripe_customer_id:
            customer_id = await stripe_service.create_customer(
                email=current_tenant.contact_email,
                name=current_tenant.company_name or current_tenant.name,
                tenant_id=current_tenant.id
            )

            await tenant_service.update_stripe_info(
                db,
                current_tenant.id,
                customer_id
            )
        else:
            customer_id = current_tenant.stripe_customer_id

        # Get price ID based on plan
        price_id = None
        if request.plan == TenantPlan.PRO:
            price_id = stripe_service.pro_price_id
        elif request.plan == TenantPlan.ENTERPRISE:
            price_id = stripe_service.enterprise_price_id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan selected"
            )

        if not price_id:
            raise HTTPException(status_code=503, detail="Selected plan is not configured")

        # Create checkout session
        checkout_url = stripe_service.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            tenant_id=current_tenant.id
        )

        return {"checkout_url": checkout_url}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Checkout session creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/create-portal-session")
async def create_billing_portal_session(
    request: BillingPortalRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        if not current_tenant.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No billing account found"
            )

        portal_url = stripe_service.create_billing_portal_session(
            customer_id=current_tenant.stripe_customer_id,
            return_url=request.return_url
        )

        return {"portal_url": portal_url}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Billing portal creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: Annotated[User, Depends(get_current_active_user)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)]
):
    try:
        if not current_tenant.stripe_subscription_id:
            return SubscriptionResponse(
                id=None,
                status=None,
                plan=current_tenant.plan,
                current_period_start=None,
                current_period_end=None,
                cancel_at_period_end=None
            )

        subscription = stripe_service.get_subscription(
            current_tenant.stripe_subscription_id
        )

        if not subscription:
            return SubscriptionResponse(
                id=None,
                status=None,
                plan=current_tenant.plan,
                current_period_start=None,
                current_period_end=None,
                cancel_at_period_end=None
            )

        return SubscriptionResponse(
            id=subscription["id"],
            status=subscription["status"],
            plan=current_tenant.plan,
            current_period_start=subscription["current_period_start"],
            current_period_end=subscription["current_period_end"],
            cancel_at_period_end=subscription.get("cancel_at_period_end", False)
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get subscription")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription"
        )


@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: Annotated[User, Depends(get_current_active_user)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)]
):
    try:
        if not current_tenant.stripe_subscription_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )

        success = stripe_service.cancel_subscription(
            current_tenant.stripe_subscription_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )

        return {"message": "Subscription will be cancelled at the end of the current period"}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Subscription cancellation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')

        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )

        event = stripe_service.construct_webhook_event(payload, sig_header)

        success = await stripe_service.handle_webhook_event(event, db)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook processing failed"
            )

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Webhook processing failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed"
        )
