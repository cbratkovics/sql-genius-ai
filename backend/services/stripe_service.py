import stripe
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
from backend.models.tenant import Tenant, TenantPlan
from backend.services.tenant import tenant_service
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    def __init__(self):
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.pro_price_id = settings.STRIPE_PRICE_ID_PRO
        self.enterprise_price_id = settings.STRIPE_PRICE_ID_ENTERPRISE
    
    async def create_customer(
        self, 
        email: str, 
        name: str, 
        tenant_id: str
    ) -> str:
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "tenant_id": tenant_id
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise Exception(f"Failed to create customer: {str(e)}")
    
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        tenant_id: str
    ) -> str:
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "tenant_id": tenant_id
                },
                allow_promotion_codes=True,
                automatic_tax={'enabled': True},
                tax_id_collection={'enabled': True},
                subscription_data={
                    'metadata': {
                        'tenant_id': tenant_id
                    }
                }
            )
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout session creation failed: {e}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> str:
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Stripe billing portal creation failed: {e}")
            raise Exception(f"Failed to create billing portal: {str(e)}")
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "price_id": subscription.items.data[0].price.id if subscription.items.data else None,
                "customer_id": subscription.customer
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    def get_usage_record(self, subscription_item_id: str) -> Dict[str, Any]:
        try:
            usage_records = stripe.UsageRecord.list(
                subscription_item=subscription_item_id,
                limit=1
            )
            return usage_records.data[0] if usage_records.data else {}
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get usage record: {e}")
            return {}
    
    def create_usage_record(
        self, 
        subscription_item_id: str, 
        quantity: int, 
        timestamp: Optional[int] = None
    ) -> bool:
        try:
            usage_record_data = {
                "quantity": quantity,
                "action": "increment"
            }
            if timestamp:
                usage_record_data["timestamp"] = timestamp
            
            stripe.UsageRecord.create(
                subscription_item=subscription_item_id,
                **usage_record_data
            )
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create usage record: {e}")
            return False
    
    def construct_webhook_event(self, payload: bytes, sig_header: str):
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                self.webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise Exception("Invalid signature")
    
    async def handle_webhook_event(
        self, 
        event: Dict[str, Any], 
        db: AsyncSession
    ) -> bool:
        try:
            event_type = event['type']
            data = event['data']['object']
            
            if event_type == 'customer.subscription.created':
                return await self._handle_subscription_created(data, db)
            
            elif event_type == 'customer.subscription.updated':
                return await self._handle_subscription_updated(data, db)
            
            elif event_type == 'customer.subscription.deleted':
                return await self._handle_subscription_deleted(data, db)
            
            elif event_type == 'invoice.payment_succeeded':
                return await self._handle_payment_succeeded(data, db)
            
            elif event_type == 'invoice.payment_failed':
                return await self._handle_payment_failed(data, db)
            
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                return True
                
        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return False
    
    async def _handle_subscription_created(
        self, 
        subscription: Dict[str, Any], 
        db: AsyncSession
    ) -> bool:
        tenant_id = subscription.get('metadata', {}).get('tenant_id')
        if not tenant_id:
            logger.error("No tenant_id in subscription metadata")
            return False
        
        plan = self._get_plan_from_price_id(
            subscription['items']['data'][0]['price']['id']
        )
        
        await tenant_service.update(db, tenant_id, {
            "stripe_subscription_id": subscription['id'],
            "plan": plan,
            "status": "active",
            "subscription_ends_at": subscription['current_period_end']
        })
        
        logger.info(f"Subscription created for tenant {tenant_id}")
        return True
    
    async def _handle_subscription_updated(
        self, 
        subscription: Dict[str, Any], 
        db: AsyncSession
    ) -> bool:
        tenant_id = subscription.get('metadata', {}).get('tenant_id')
        if not tenant_id:
            tenant = await tenant_service.get_by_stripe_subscription_id(
                db, subscription['id']
            )
            if not tenant:
                logger.error(f"No tenant found for subscription {subscription['id']}")
                return False
            tenant_id = tenant.id
        
        status_mapping = {
            'active': 'active',
            'past_due': 'active',
            'unpaid': 'suspended',
            'canceled': 'cancelled',
            'incomplete': 'trial',
            'incomplete_expired': 'cancelled',
            'trialing': 'trial'
        }
        
        tenant_status = status_mapping.get(subscription['status'], 'suspended')
        
        await tenant_service.update(db, tenant_id, {
            "status": tenant_status,
            "subscription_ends_at": subscription['current_period_end']
        })
        
        logger.info(f"Subscription updated for tenant {tenant_id}")
        return True
    
    async def _handle_subscription_deleted(
        self, 
        subscription: Dict[str, Any], 
        db: AsyncSession
    ) -> bool:
        tenant = await tenant_service.get_by_stripe_subscription_id(
            db, subscription['id']
        )
        if not tenant:
            logger.error(f"No tenant found for subscription {subscription['id']}")
            return False
        
        await tenant_service.update(db, tenant.id, {
            "status": "cancelled",
            "plan": TenantPlan.FREE,
            "stripe_subscription_id": None
        })
        
        logger.info(f"Subscription deleted for tenant {tenant.id}")
        return True
    
    async def _handle_payment_succeeded(
        self, 
        invoice: Dict[str, Any], 
        db: AsyncSession
    ) -> bool:
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return True
        
        tenant = await tenant_service.get_by_stripe_subscription_id(
            db, subscription_id
        )
        if not tenant:
            logger.error(f"No tenant found for subscription {subscription_id}")
            return False
        
        await tenant_service.update(db, tenant.id, {
            "status": "active"
        })
        
        logger.info(f"Payment succeeded for tenant {tenant.id}")
        return True
    
    async def _handle_payment_failed(
        self, 
        invoice: Dict[str, Any], 
        db: AsyncSession
    ) -> bool:
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return True
        
        tenant = await tenant_service.get_by_stripe_subscription_id(
            db, subscription_id
        )
        if not tenant:
            logger.error(f"No tenant found for subscription {subscription_id}")
            return False
        
        await tenant_service.update(db, tenant.id, {
            "status": "suspended"
        })
        
        logger.info(f"Payment failed for tenant {tenant.id}")
        return True
    
    def _get_plan_from_price_id(self, price_id: str) -> TenantPlan:
        if price_id == self.pro_price_id:
            return TenantPlan.PRO
        elif price_id == self.enterprise_price_id:
            return TenantPlan.ENTERPRISE
        else:
            return TenantPlan.FREE


stripe_service = StripeService()