import asyncio
import boto3
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from collections import defaultdict
import redis.asyncio as redis
from backend.core.config import settings
from backend.observability.metrics import metrics_collector

logger = logging.getLogger(__name__)


class CostCategory(str, Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    AI_API = "ai_api"
    DATABASE = "database"
    MONITORING = "monitoring"
    SECURITY = "security"
    BACKUP = "backup"


class CostAllocationType(str, Enum):
    TENANT = "tenant"
    SERVICE = "service"
    ENVIRONMENT = "environment"
    TEAM = "team"
    PROJECT = "project"


@dataclass
class CostItem:
    service: str
    category: CostCategory
    amount: float
    currency: str
    timestamp: datetime
    resource_id: str = None
    tenant_id: str = None
    tags: Dict[str, str] = field(default_factory=dict)
    usage_quantity: float = 0.0
    usage_unit: str = ""
    region: str = "us-east-1"


@dataclass
class CostBudget:
    budget_id: str
    name: str
    amount: float
    currency: str
    period: str  # "monthly", "quarterly", "yearly"
    allocation_type: CostAllocationType
    allocation_value: str  # tenant_id, service_name, etc.
    alert_thresholds: List[float] = field(default_factory=lambda: [50.0, 80.0, 100.0])
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class CostAnomaly:
    anomaly_id: str
    service: str
    category: CostCategory
    expected_cost: float
    actual_cost: float
    deviation_percent: float
    detected_at: datetime
    severity: str  # "low", "medium", "high", "critical"
    root_cause: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class SavingsRecommendation:
    recommendation_id: str
    title: str
    description: str
    service: str
    category: CostCategory
    estimated_monthly_savings: float
    implementation_effort: str  # "low", "medium", "high"
    confidence: float  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # "pending", "implemented", "dismissed"


class FinOpsManager:
    """Enterprise Financial Operations and Cost Management"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
        # AWS clients for cost data
        try:
            self.ce_client = boto3.client(
                'ce',  # Cost Explorer
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                region_name='us-east-1'  # Cost Explorer only available in us-east-1
            )
            self.pricing_client = boto3.client(
                'pricing',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                region_name='us-east-1'
            )
        except Exception as e:
            logger.warning(f"AWS clients not configured: {e}")
            self.ce_client = None
            self.pricing_client = None
        
        # AI API cost tracking
        self.ai_pricing = {
            "anthropic": {
                "claude-3-5-sonnet-20241022": {
                    "input_tokens": 0.003 / 1000,   # $0.003 per 1K input tokens
                    "output_tokens": 0.015 / 1000   # $0.015 per 1K output tokens
                },
                "claude-3-haiku-20240307": {
                    "input_tokens": 0.00025 / 1000,
                    "output_tokens": 0.00125 / 1000
                }
            },
            "openai": {
                "gpt-4": {
                    "input_tokens": 0.03 / 1000,
                    "output_tokens": 0.06 / 1000
                },
                "gpt-3.5-turbo": {
                    "input_tokens": 0.0015 / 1000,
                    "output_tokens": 0.002 / 1000
                }
            }
        }
        
        # Cost allocation rules
        self.allocation_rules = {}
        
        # Budget monitoring
        self.budgets = {}
        
        # Anomaly detection parameters
        self.anomaly_threshold = 0.3  # 30% deviation
        self.anomaly_window_days = 7
    
    async def initialize(self):
        """Initialize FinOps system"""
        await self._load_budgets()
        await self._load_allocation_rules()
        asyncio.create_task(self._cost_collection_scheduler())
        asyncio.create_task(self._anomaly_detection_scheduler())
        asyncio.create_task(self._budget_monitoring_scheduler())
        logger.info("FinOps manager initialized")
    
    async def track_ai_api_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        tenant_id: str = None,
        request_id: str = None
    ) -> float:
        """Track AI API usage and cost"""
        try:
            if provider not in self.ai_pricing or model not in self.ai_pricing[provider]:
                logger.warning(f"Unknown AI model pricing: {provider}/{model}")
                return 0.0
            
            pricing = self.ai_pricing[provider][model]
            
            input_cost = input_tokens * pricing["input_tokens"]
            output_cost = output_tokens * pricing["output_tokens"]
            total_cost = input_cost + output_cost
            
            # Create cost item
            cost_item = CostItem(
                service=f"{provider}-{model}",
                category=CostCategory.AI_API,
                amount=total_cost,
                currency="USD",
                timestamp=datetime.utcnow(),
                resource_id=request_id,
                tenant_id=tenant_id,
                usage_quantity=input_tokens + output_tokens,
                usage_unit="tokens",
                tags={
                    "provider": provider,
                    "model": model,
                    "input_tokens": str(input_tokens),
                    "output_tokens": str(output_tokens)
                }
            )
            
            # Store cost data
            await self._store_cost_item(cost_item)
            
            # Update metrics
            metrics_collector.ai_api_cost.labels(
                provider=provider,
                model=model
            ).inc(total_cost)
            
            logger.debug(f"AI API cost tracked: ${total_cost:.6f} for {provider}/{model}")
            return total_cost
            
        except Exception as e:
            logger.error(f"Failed to track AI API cost: {e}")
            return 0.0
    
    async def track_infrastructure_cost(
        self,
        service: str,
        category: CostCategory,
        amount: float,
        resource_id: str = None,
        tenant_id: str = None,
        tags: Dict[str, str] = None
    ):
        """Track infrastructure cost"""
        try:
            cost_item = CostItem(
                service=service,
                category=category,
                amount=amount,
                currency="USD",
                timestamp=datetime.utcnow(),
                resource_id=resource_id,
                tenant_id=tenant_id,
                tags=tags or {}
            )
            
            await self._store_cost_item(cost_item)
            
        except Exception as e:
            logger.error(f"Failed to track infrastructure cost: {e}")
    
    async def _store_cost_item(self, cost_item: CostItem):
        """Store cost item in Redis"""
        try:
            # Create cost item key with timestamp for time-series data
            timestamp_key = cost_item.timestamp.strftime("%Y%m%d%H")
            cost_key = f"cost:{timestamp_key}:{cost_item.service}:{cost_item.tenant_id or 'system'}"
            
            # Store individual cost item
            item_data = {
                "service": cost_item.service,
                "category": cost_item.category.value,
                "amount": cost_item.amount,
                "currency": cost_item.currency,
                "timestamp": cost_item.timestamp.isoformat(),
                "resource_id": cost_item.resource_id,
                "tenant_id": cost_item.tenant_id,
                "usage_quantity": cost_item.usage_quantity,
                "usage_unit": cost_item.usage_unit,
                "region": cost_item.region,
                "tags": cost_item.tags
            }
            
            await self.redis_client.lpush(cost_key, json.dumps(item_data))
            await self.redis_client.expire(cost_key, 86400 * 90)  # 90 days retention
            
            # Update aggregated cost totals
            await self._update_cost_aggregates(cost_item)
            
        except Exception as e:
            logger.error(f"Failed to store cost item: {e}")
    
    async def _update_cost_aggregates(self, cost_item: CostItem):
        """Update aggregated cost totals for reporting"""
        try:
            today = datetime.utcnow().date()
            month_key = today.strftime("%Y%m")
            
            # Aggregate by service
            service_key = f"cost:agg:service:{cost_item.service}:{month_key}"
            await self.redis_client.incrbyfloat(service_key, cost_item.amount)
            await self.redis_client.expire(service_key, 86400 * 90)
            
            # Aggregate by category
            category_key = f"cost:agg:category:{cost_item.category.value}:{month_key}"
            await self.redis_client.incrbyfloat(category_key, cost_item.amount)
            await self.redis_client.expire(category_key, 86400 * 90)
            
            # Aggregate by tenant
            if cost_item.tenant_id:
                tenant_key = f"cost:agg:tenant:{cost_item.tenant_id}:{month_key}"
                await self.redis_client.incrbyfloat(tenant_key, cost_item.amount)
                await self.redis_client.expire(tenant_key, 86400 * 90)
            
            # Update daily total
            daily_key = f"cost:agg:daily:{today.strftime('%Y%m%d')}"
            await self.redis_client.incrbyfloat(daily_key, cost_item.amount)
            await self.redis_client.expire(daily_key, 86400 * 90)
            
        except Exception as e:
            logger.error(f"Failed to update cost aggregates: {e}")
    
    async def get_cost_report(
        self,
        start_date: date,
        end_date: date,
        allocation_type: CostAllocationType = None,
        allocation_value: str = None
    ) -> Dict[str, Any]:
        """Generate cost report for specified period"""
        try:
            report = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_cost": 0.0,
                "currency": "USD",
                "breakdown": {
                    "by_service": {},
                    "by_category": {},
                    "by_tenant": {},
                    "by_day": {}
                },
                "top_costs": [],
                "trends": {},
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Get cost data for the period
            current_date = start_date
            while current_date <= end_date:
                daily_costs = await self._get_daily_costs(current_date)
                report["breakdown"]["by_day"][current_date.isoformat()] = daily_costs["total"]
                report["total_cost"] += daily_costs["total"]
                
                # Aggregate by service
                for service, cost in daily_costs["by_service"].items():
                    report["breakdown"]["by_service"][service] = (
                        report["breakdown"]["by_service"].get(service, 0) + cost
                    )
                
                # Aggregate by category
                for category, cost in daily_costs["by_category"].items():
                    report["breakdown"]["by_category"][category] = (
                        report["breakdown"]["by_category"].get(category, 0) + cost
                    )
                
                # Aggregate by tenant
                for tenant, cost in daily_costs["by_tenant"].items():
                    report["breakdown"]["by_tenant"][tenant] = (
                        report["breakdown"]["by_tenant"].get(tenant, 0) + cost
                    )
                
                current_date += timedelta(days=1)
            
            # Calculate top costs
            all_services = list(report["breakdown"]["by_service"].items())
            report["top_costs"] = sorted(all_services, key=lambda x: x[1], reverse=True)[:10]
            
            # Calculate trends (compare with previous period)
            period_days = (end_date - start_date).days + 1
            prev_start = start_date - timedelta(days=period_days)
            prev_end = start_date - timedelta(days=1)
            
            prev_report = await self.get_cost_report(prev_start, prev_end)
            if prev_report["total_cost"] > 0:
                trend_percent = ((report["total_cost"] - prev_report["total_cost"]) / 
                               prev_report["total_cost"]) * 100
                report["trends"]["total_cost_change"] = {
                    "amount": report["total_cost"] - prev_report["total_cost"],
                    "percent": trend_percent
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate cost report: {e}")
            return {"error": str(e)}
    
    async def _get_daily_costs(self, target_date: date) -> Dict[str, Any]:
        """Get cost breakdown for a specific day"""
        try:
            daily_key = f"cost:agg:daily:{target_date.strftime('%Y%m%d')}"
            total_cost = await self.redis_client.get(daily_key)
            total_cost = float(total_cost) if total_cost else 0.0
            
            # Get breakdown by service, category, tenant
            month_key = target_date.strftime("%Y%m")
            
            breakdown = {
                "total": total_cost,
                "by_service": {},
                "by_category": {},
                "by_tenant": {}
            }
            
            # Get service costs
            service_pattern = f"cost:agg:service:*:{month_key}"
            async for key in self.redis_client.scan_iter(match=service_pattern):
                service_name = key.split(':')[3]
                cost = await self.redis_client.get(key)
                breakdown["by_service"][service_name] = float(cost) if cost else 0.0
            
            # Get category costs  
            category_pattern = f"cost:agg:category:*:{month_key}"
            async for key in self.redis_client.scan_iter(match=category_pattern):
                category_name = key.split(':')[3]
                cost = await self.redis_client.get(key)
                breakdown["by_category"][category_name] = float(cost) if cost else 0.0
            
            # Get tenant costs
            tenant_pattern = f"cost:agg:tenant:*:{month_key}"
            async for key in self.redis_client.scan_iter(match=tenant_pattern):
                tenant_id = key.split(':')[3]
                cost = await self.redis_client.get(key)
                breakdown["by_tenant"][tenant_id] = float(cost) if cost else 0.0
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Failed to get daily costs: {e}")
            return {"total": 0.0, "by_service": {}, "by_category": {}, "by_tenant": {}}
    
    async def detect_cost_anomalies(self) -> List[CostAnomaly]:
        """Detect cost anomalies using statistical analysis"""
        try:
            anomalies = []
            
            # Get recent cost data for analysis
            end_date = date.today()
            start_date = end_date - timedelta(days=30)  # 30 days of data
            
            # Analyze costs by service
            services = await self._get_services_with_costs(start_date, end_date)
            
            for service in services:
                daily_costs = await self._get_service_daily_costs(service, start_date, end_date)
                
                if len(daily_costs) < 7:  # Need at least 7 days of data
                    continue
                
                # Calculate statistical metrics
                costs_array = np.array(list(daily_costs.values()))
                mean_cost = np.mean(costs_array[:-1])  # Exclude today
                std_cost = np.std(costs_array[:-1])
                today_cost = costs_array[-1]
                
                if std_cost == 0:  # No variation in costs
                    continue
                
                # Calculate Z-score for today's cost
                z_score = abs(today_cost - mean_cost) / std_cost
                
                if z_score > 2.0:  # Significant deviation (2 standard deviations)
                    deviation_percent = ((today_cost - mean_cost) / mean_cost) * 100
                    
                    # Determine severity
                    if z_score > 3.0:
                        severity = "critical"
                    elif z_score > 2.5:
                        severity = "high" 
                    else:
                        severity = "medium"
                    
                    anomaly = CostAnomaly(
                        anomaly_id=f"anomaly-{service}-{end_date.strftime('%Y%m%d')}",
                        service=service,
                        category=CostCategory.AI_API,  # Would determine from service
                        expected_cost=mean_cost,
                        actual_cost=today_cost,
                        deviation_percent=deviation_percent,
                        detected_at=datetime.utcnow(),
                        severity=severity,
                        root_cause=await self._analyze_anomaly_root_cause(service, daily_costs),
                        recommendation=await self._generate_anomaly_recommendation(service, deviation_percent)
                    )
                    
                    anomalies.append(anomaly)
                    
                    # Store anomaly
                    await self._store_anomaly(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Cost anomaly detection failed: {e}")
            return []
    
    async def _get_services_with_costs(self, start_date: date, end_date: date) -> List[str]:
        """Get list of services that have costs in the period"""
        try:
            services = set()
            
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime("%Y%m")
                pattern = f"cost:agg:service:*:{month_key}"
                
                async for key in self.redis_client.scan_iter(match=pattern):
                    service_name = key.split(':')[3]
                    services.add(service_name)
                
                current_date += timedelta(days=1)
            
            return list(services)
            
        except Exception as e:
            logger.error(f"Failed to get services with costs: {e}")
            return []
    
    async def _get_service_daily_costs(
        self, 
        service: str, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, float]:
        """Get daily costs for a specific service"""
        try:
            daily_costs = {}
            
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime("%Y%m")
                service_key = f"cost:agg:service:{service}:{month_key}"
                
                cost = await self.redis_client.get(service_key)
                daily_costs[current_date.isoformat()] = float(cost) if cost else 0.0
                
                current_date += timedelta(days=1)
            
            return daily_costs
            
        except Exception as e:
            logger.error(f"Failed to get service daily costs: {e}")
            return {}
    
    async def _analyze_anomaly_root_cause(
        self, 
        service: str, 
        daily_costs: Dict[str, float]
    ) -> Optional[str]:
        """Analyze potential root cause of cost anomaly"""
        
        # Simple heuristics for root cause analysis
        costs = list(daily_costs.values())
        
        if len(costs) < 2:
            return None
        
        # Check for sudden spike
        if costs[-1] > costs[-2] * 2:
            return "Sudden usage spike detected"
        
        # Check for gradual increase
        if len(costs) >= 7:
            recent_avg = np.mean(costs[-3:])
            previous_avg = np.mean(costs[-7:-3])
            
            if recent_avg > previous_avg * 1.5:
                return "Gradual cost increase trend"
        
        # Check for AI API specific issues
        if "anthropic" in service or "openai" in service:
            return "Possible increase in AI API usage or rate changes"
        
        return "Unknown cause - manual investigation required"
    
    async def _generate_anomaly_recommendation(
        self, 
        service: str, 
        deviation_percent: float
    ) -> Optional[str]:
        """Generate recommendation for cost anomaly"""
        
        if abs(deviation_percent) > 100:
            return "Investigate immediately - cost doubled or more"
        elif abs(deviation_percent) > 50:
            return "Review usage patterns and optimize if possible"
        elif abs(deviation_percent) > 25:
            return "Monitor closely and consider usage optimization"
        else:
            return "Continue monitoring"
    
    async def _store_anomaly(self, anomaly: CostAnomaly):
        """Store cost anomaly"""
        try:
            anomaly_data = {
                "anomaly_id": anomaly.anomaly_id,
                "service": anomaly.service,
                "category": anomaly.category.value,
                "expected_cost": anomaly.expected_cost,
                "actual_cost": anomaly.actual_cost,
                "deviation_percent": anomaly.deviation_percent,
                "detected_at": anomaly.detected_at.isoformat(),
                "severity": anomaly.severity,
                "root_cause": anomaly.root_cause,
                "recommendation": anomaly.recommendation
            }
            
            await self.redis_client.setex(
                f"cost:anomaly:{anomaly.anomaly_id}",
                86400 * 30,  # 30 days
                json.dumps(anomaly_data)
            )
            
            # Add to anomaly index
            await self.redis_client.zadd(
                "cost:anomaly:index",
                {anomaly.anomaly_id: anomaly.detected_at.timestamp()}
            )
            
        except Exception as e:
            logger.error(f"Failed to store anomaly: {e}")
    
    async def generate_savings_recommendations(self) -> List[SavingsRecommendation]:
        """Generate cost savings recommendations"""
        try:
            recommendations = []
            
            # Analyze AI API usage patterns
            ai_recommendations = await self._analyze_ai_api_optimization()
            recommendations.extend(ai_recommendations)
            
            # Analyze infrastructure utilization
            infra_recommendations = await self._analyze_infrastructure_optimization()
            recommendations.extend(infra_recommendations)
            
            # Analyze data storage patterns
            storage_recommendations = await self._analyze_storage_optimization()
            recommendations.extend(storage_recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate savings recommendations: {e}")
            return []
    
    async def _analyze_ai_api_optimization(self) -> List[SavingsRecommendation]:
        """Analyze AI API usage for optimization opportunities"""
        recommendations = []
        
        try:
            # Get AI API usage patterns from last 30 days
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            # Analyze usage by model
            ai_services = [s for s in await self._get_services_with_costs(start_date, end_date) 
                          if 'anthropic' in s or 'openai' in s]
            
            total_ai_cost = 0.0
            expensive_models = []
            
            for service in ai_services:
                daily_costs = await self._get_service_daily_costs(service, start_date, end_date)
                service_cost = sum(daily_costs.values())
                total_ai_cost += service_cost
                
                if service_cost > 100:  # $100+ in 30 days
                    expensive_models.append((service, service_cost))
            
            # Recommendation: Switch to cheaper models for non-critical tasks
            if expensive_models:
                expensive_models.sort(key=lambda x: x[1], reverse=True)
                top_expensive = expensive_models[0]
                
                # Estimate savings by switching 30% of usage to cheaper model
                if "claude-3-5-sonnet" in top_expensive[0]:
                    estimated_savings = top_expensive[1] * 0.3 * 0.7  # 70% cost reduction
                    
                    recommendations.append(SavingsRecommendation(
                        recommendation_id=f"ai-model-optimization-{datetime.utcnow().strftime('%Y%m%d')}",
                        title="Optimize AI Model Usage",
                        description=f"Consider using Claude Haiku for simpler queries. Current high usage: {top_expensive[0]} (${top_expensive[1]:.2f}/month)",
                        service=top_expensive[0],
                        category=CostCategory.AI_API,
                        estimated_monthly_savings=estimated_savings,
                        implementation_effort="medium",
                        confidence=0.8
                    ))
            
            # Recommendation: Implement request caching
            if total_ai_cost > 200:  # $200+ monthly
                cache_savings = total_ai_cost * 0.15  # 15% savings from caching
                
                recommendations.append(SavingsRecommendation(
                    recommendation_id=f"ai-caching-{datetime.utcnow().strftime('%Y%m%d')}",
                    title="Implement AI Response Caching",
                    description="Cache similar queries to reduce API calls. Analyze duplicate/similar requests pattern.",
                    service="ai-apis",
                    category=CostCategory.AI_API,
                    estimated_monthly_savings=cache_savings,
                    implementation_effort="medium",
                    confidence=0.7
                ))
            
        except Exception as e:
            logger.error(f"AI API optimization analysis failed: {e}")
        
        return recommendations
    
    async def _analyze_infrastructure_optimization(self) -> List[SavingsRecommendation]:
        """Analyze infrastructure for optimization opportunities"""
        recommendations = []
        
        # Placeholder for infrastructure analysis
        # In production, this would analyze EC2, RDS, etc. usage
        
        return recommendations
    
    async def _analyze_storage_optimization(self) -> List[SavingsRecommendation]:
        """Analyze storage for optimization opportunities"""
        recommendations = []
        
        # Placeholder for storage analysis
        # In production, this would analyze S3, EBS usage patterns
        
        return recommendations
    
    async def create_budget(
        self,
        name: str,
        amount: float,
        period: str,
        allocation_type: CostAllocationType,
        allocation_value: str,
        alert_thresholds: List[float] = None
    ) -> CostBudget:
        """Create cost budget"""
        try:
            budget_id = f"budget-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            budget = CostBudget(
                budget_id=budget_id,
                name=name,
                amount=amount,
                currency="USD",
                period=period,
                allocation_type=allocation_type,
                allocation_value=allocation_value,
                alert_thresholds=alert_thresholds or [50.0, 80.0, 100.0]
            )
            
            # Store budget
            await self._store_budget(budget)
            
            self.budgets[budget_id] = budget
            logger.info(f"Created budget: {budget_id}")
            
            return budget
            
        except Exception as e:
            logger.error(f"Failed to create budget: {e}")
            raise
    
    async def _store_budget(self, budget: CostBudget):
        """Store budget in Redis"""
        try:
            budget_data = {
                "budget_id": budget.budget_id,
                "name": budget.name,
                "amount": budget.amount,
                "currency": budget.currency,
                "period": budget.period,
                "allocation_type": budget.allocation_type.value,
                "allocation_value": budget.allocation_value,
                "alert_thresholds": budget.alert_thresholds,
                "created_at": budget.created_at.isoformat(),
                "is_active": budget.is_active
            }
            
            await self.redis_client.set(
                f"cost:budget:{budget.budget_id}",
                json.dumps(budget_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to store budget: {e}")
    
    async def _load_budgets(self):
        """Load budgets from Redis"""
        try:
            pattern = "cost:budget:*"
            async for key in self.redis_client.scan_iter(match=pattern):
                budget_data = await self.redis_client.get(key)
                if budget_data:
                    data = json.loads(budget_data)
                    budget = CostBudget(
                        budget_id=data["budget_id"],
                        name=data["name"],
                        amount=data["amount"],
                        currency=data["currency"],
                        period=data["period"],
                        allocation_type=CostAllocationType(data["allocation_type"]),
                        allocation_value=data["allocation_value"],
                        alert_thresholds=data["alert_thresholds"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        is_active=data["is_active"]
                    )
                    self.budgets[budget.budget_id] = budget
                    
        except Exception as e:
            logger.error(f"Failed to load budgets: {e}")
    
    async def _load_allocation_rules(self):
        """Load cost allocation rules"""
        # Placeholder for allocation rules loading
        pass
    
    async def _cost_collection_scheduler(self):
        """Schedule regular cost data collection"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self._collect_aws_costs()
                
            except Exception as e:
                logger.error(f"Cost collection scheduler error: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _anomaly_detection_scheduler(self):
        """Schedule regular anomaly detection"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self.detect_cost_anomalies()
                
            except Exception as e:
                logger.error(f"Anomaly detection scheduler error: {e}")
                await asyncio.sleep(1800)
    
    async def _budget_monitoring_scheduler(self):
        """Schedule budget monitoring"""
        while True:
            try:
                await asyncio.sleep(1800)  # Every 30 minutes
                await self._monitor_budgets()
                
            except Exception as e:
                logger.error(f"Budget monitoring scheduler error: {e}")
                await asyncio.sleep(900)
    
    async def _collect_aws_costs(self):
        """Collect AWS cost data"""
        if not self.ce_client:
            return
        
        try:
            # Get yesterday's costs (AWS Cost Explorer has 1-day delay)
            end_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = end_date
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ]
            )
            
            # Process and store AWS costs
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    usage_type = group['Keys'][1]
                    amount = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if amount > 0:
                        await self.track_infrastructure_cost(
                            service=service,
                            category=self._map_aws_service_to_category(service),
                            amount=amount,
                            tags={"usage_type": usage_type, "source": "aws"}
                        )
            
        except Exception as e:
            logger.error(f"AWS cost collection failed: {e}")
    
    def _map_aws_service_to_category(self, service: str) -> CostCategory:
        """Map AWS service to cost category"""
        service_lower = service.lower()
        
        if 'ec2' in service_lower or 'lambda' in service_lower:
            return CostCategory.COMPUTE
        elif 'rds' in service_lower or 'dynamodb' in service_lower:
            return CostCategory.DATABASE
        elif 's3' in service_lower or 'ebs' in service_lower:
            return CostCategory.STORAGE
        elif 'cloudfront' in service_lower or 'route53' in service_lower:
            return CostCategory.NETWORK
        elif 'cloudwatch' in service_lower or 'cloudtrail' in service_lower:
            return CostCategory.MONITORING
        else:
            return CostCategory.COMPUTE  # Default fallback
    
    async def _monitor_budgets(self):
        """Monitor budget utilization and send alerts"""
        try:
            for budget in self.budgets.values():
                if not budget.is_active:
                    continue
                
                # Calculate current period spend
                current_spend = await self._calculate_budget_spend(budget)
                utilization_percent = (current_spend / budget.amount) * 100
                
                # Check alert thresholds
                for threshold in budget.alert_thresholds:
                    if utilization_percent >= threshold:
                        await self._send_budget_alert(budget, current_spend, utilization_percent, threshold)
                
        except Exception as e:
            logger.error(f"Budget monitoring failed: {e}")
    
    async def _calculate_budget_spend(self, budget: CostBudget) -> float:
        """Calculate current spend for budget period"""
        # Simplified calculation - would be more sophisticated in production
        today = date.today()
        
        if budget.period == "monthly":
            start_date = today.replace(day=1)
        elif budget.period == "quarterly":
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = today.replace(month=quarter_start_month, day=1)
        else:  # yearly
            start_date = today.replace(month=1, day=1)
        
        # Get costs for the period based on allocation
        if budget.allocation_type == CostAllocationType.TENANT:
            return await self._get_tenant_costs(budget.allocation_value, start_date, today)
        elif budget.allocation_type == CostAllocationType.SERVICE:
            return await self._get_service_costs(budget.allocation_value, start_date, today)
        else:
            # Get total costs
            report = await self.get_cost_report(start_date, today)
            return report["total_cost"]
    
    async def _get_tenant_costs(self, tenant_id: str, start_date: date, end_date: date) -> float:
        """Get costs for specific tenant"""
        total_cost = 0.0
        
        current_date = start_date
        while current_date <= end_date:
            month_key = current_date.strftime("%Y%m")
            tenant_key = f"cost:agg:tenant:{tenant_id}:{month_key}"
            
            cost = await self.redis_client.get(tenant_key)
            total_cost += float(cost) if cost else 0.0
            
            current_date += timedelta(days=1)
        
        return total_cost
    
    async def _get_service_costs(self, service: str, start_date: date, end_date: date) -> float:
        """Get costs for specific service"""
        total_cost = 0.0
        
        current_date = start_date
        while current_date <= end_date:
            month_key = current_date.strftime("%Y%m")
            service_key = f"cost:agg:service:{service}:{month_key}"
            
            cost = await self.redis_client.get(service_key)
            total_cost += float(cost) if cost else 0.0
            
            current_date += timedelta(days=1)
        
        return total_cost
    
    async def _send_budget_alert(
        self, 
        budget: CostBudget, 
        current_spend: float, 
        utilization_percent: float, 
        threshold: float
    ):
        """Send budget alert notification"""
        logger.warning(
            f"Budget alert: {budget.name} is {utilization_percent:.1f}% utilized "
            f"(${current_spend:.2f} of ${budget.amount:.2f}) - Threshold: {threshold}%"
        )
        
        # In production, this would send notifications via email, Slack, etc.


# Global instance
finops_manager = FinOpsManager()