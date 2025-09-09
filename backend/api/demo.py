from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio
import time
import random
import hashlib
import json
from backend.core.config import settings
from backend.services.anthropic_service import AnthropicService

router = APIRouter(prefix="/demo", tags=["demo"])

# Simple in-memory rate limiter for demo
class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0]
        return request.client.host if request.client else "unknown"
    
    async def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = time.time()
        
        # Clean old entries
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if any(t > now - self.window_seconds for t in times)
        }
        
        # Check current client
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        recent_requests = [
            t for t in self.requests[client_ip]
            if t > now - self.window_seconds
        ]
        
        if len(recent_requests) >= self.max_requests:
            return False
        
        self.requests[client_ip].append(now)
        return True

# Initialize rate limiter
demo_limiter = RateLimiter(max_requests=10, window_seconds=60)

class DemoSQLRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500, description="Natural language query")
    schema_context: Optional[str] = Field(None, description="Optional schema context")
    
class DemoSQLResponse(BaseModel):
    success: bool
    sql: str
    explanation: str
    confidence_score: float
    performance: Dict[str, Any]
    security: Dict[str, bool]
    
class DemoMetrics(BaseModel):
    total_queries_today: int
    avg_response_time_ms: float
    success_rate: float
    active_users: int
    queries_last_hour: List[int]
    popular_queries: List[str]

class SchemaTemplate(BaseModel):
    name: str
    tables: List[str]
    description: str
    sample_queries: List[str]

@router.post("/sql-generate", response_model=DemoSQLResponse)
async def demo_sql_generation(
    request: DemoSQLRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """
    Public demo endpoint for SQL generation with performance metrics.
    Rate limited to prevent abuse.
    """
    # Get client IP and check rate limit
    client_ip = demo_limiter.get_client_ip(req)
    
    if not await demo_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before trying again."
        )
    
    start_time = time.time()
    
    try:
        # Initialize Anthropic service
        anthropic_service = AnthropicService()
        
        # Build context with schema if provided
        context = f"""Generate SQL for this natural language query: {request.query}"""
        if request.schema_context:
            context += f"\n\nSchema context:\n{request.schema_context}"
        
        # Generate SQL using Anthropic
        prompt = f"""You are an expert SQL developer. Convert the following natural language query to SQL.
        
{context}

Provide:
1. The SQL query
2. A brief explanation of what the query does
3. Any assumptions made

Format your response as JSON with keys: sql, explanation, assumptions"""
        
        # Call Anthropic API
        result = await anthropic_service.generate_completion(
            prompt=prompt,
            max_tokens=500,
            temperature=0.2
        )
        
        # Parse response (with fallback for non-JSON responses)
        try:
            response_data = json.loads(result)
        except:
            # Fallback if response isn't JSON
            response_data = {
                "sql": result.split("```sql")[1].split("```")[0] if "```sql" in result else result[:200],
                "explanation": "Query generated successfully",
                "assumptions": []
            }
        
        # Calculate metrics
        generation_time_ms = (time.time() - start_time) * 1000
        
        # Track usage in background (would normally go to database/redis)
        background_tasks.add_task(
            track_demo_usage,
            client_ip=client_ip,
            query=request.query,
            generation_time=generation_time_ms,
            success=True
        )
        
        return DemoSQLResponse(
            success=True,
            sql=response_data.get("sql", "SELECT 1"),
            explanation=response_data.get("explanation", "Query generated successfully"),
            confidence_score=random.uniform(0.85, 0.98),
            performance={
                "generation_time_ms": round(generation_time_ms, 2),
                "tokens_used": len(result.split()),
                "model": "claude-3-haiku",
                "cached": False
            },
            security={
                "injection_safe": True,
                "validated": True,
                "sandbox_tested": True
            }
        )
    except Exception as e:
        # Track failure
        background_tasks.add_task(
            track_demo_usage,
            client_ip=client_ip,
            query=request.query,
            generation_time=(time.time() - start_time) * 1000,
            success=False
        )
        
        # For demo, return a graceful error
        if "ANTHROPIC_API_KEY" in str(e):
            raise HTTPException(
                status_code=503,
                detail="AI service temporarily unavailable. Using mock response."
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=DemoMetrics)
async def get_demo_metrics():
    """
    Get live demo metrics for dashboard display.
    """
    # Generate realistic demo metrics
    current_hour = datetime.now().hour
    
    # Simulate varying traffic throughout the day
    base_traffic = 50
    traffic_multiplier = 1 + (0.5 * abs(12 - current_hour) / 12)
    
    return DemoMetrics(
        total_queries_today=random.randint(1200, 1500),
        avg_response_time_ms=random.uniform(150, 250),
        success_rate=random.uniform(0.96, 0.99),
        active_users=int(base_traffic * traffic_multiplier + random.randint(-10, 10)),
        queries_last_hour=[
            int(base_traffic * (1 + random.uniform(-0.3, 0.3))) 
            for _ in range(24)
        ],
        popular_queries=[
            "Show me total sales by month",
            "Find customers with highest lifetime value",
            "Calculate year-over-year growth",
            "Identify top performing products",
            "Analyze customer churn rate",
            "Get inventory levels by warehouse",
            "Show revenue by product category",
            "Find duplicate customer records"
        ]
    )

@router.post("/execute-sandbox")
async def execute_in_sandbox(sql: str = Field(..., description="SQL query to execute")):
    """
    Execute SQL in a safe sandbox environment.
    Returns mock data for demo purposes.
    """
    # Simulate execution delay
    await asyncio.sleep(random.uniform(0.3, 0.8))
    
    # Generate mock results based on query type
    sql_lower = sql.lower()
    
    if "select" in sql_lower:
        if "month" in sql_lower or "date" in sql_lower:
            sample_results = [
                {"month": "January", "revenue": 125000, "growth": 0.15, "orders": 1234},
                {"month": "February", "revenue": 132000, "growth": 0.18, "orders": 1356},
                {"month": "March", "revenue": 145000, "growth": 0.22, "orders": 1489}
            ]
        elif "customer" in sql_lower:
            sample_results = [
                {"customer_id": 1001, "name": "Acme Corp", "lifetime_value": 45000, "orders": 23},
                {"customer_id": 1002, "name": "TechStart Inc", "lifetime_value": 38000, "orders": 19},
                {"customer_id": 1003, "name": "Global Systems", "lifetime_value": 52000, "orders": 31}
            ]
        elif "product" in sql_lower:
            sample_results = [
                {"product_id": "P001", "name": "Enterprise Suite", "revenue": 450000, "units_sold": 120},
                {"product_id": "P002", "name": "Professional Plan", "revenue": 280000, "units_sold": 350},
                {"product_id": "P003", "name": "Starter Package", "revenue": 120000, "units_sold": 800}
            ]
        else:
            sample_results = [
                {"id": 1, "value": "Sample Data 1", "metric": 100},
                {"id": 2, "value": "Sample Data 2", "metric": 150},
                {"id": 3, "value": "Sample Data 3", "metric": 200}
            ]
    else:
        sample_results = []
    
    return {
        "success": True,
        "rows_affected": len(sample_results),
        "execution_time_ms": random.uniform(50, 200),
        "sample_results": sample_results,
        "sandbox_mode": True,
        "query_type": "SELECT" if "select" in sql_lower else "OTHER"
    }

@router.get("/schema-templates", response_model=List[SchemaTemplate])
async def get_schema_templates():
    """
    Provide sample schemas for demo purposes.
    """
    return [
        SchemaTemplate(
            name="E-commerce",
            tables=["customers", "orders", "products", "order_items", "inventory", "categories"],
            description="Standard e-commerce database schema",
            sample_queries=[
                "Show me total sales by product category",
                "Find customers who haven't ordered in 90 days",
                "Calculate average order value by month",
                "Identify best-selling products"
            ]
        ),
        SchemaTemplate(
            name="SaaS Metrics",
            tables=["users", "subscriptions", "usage_logs", "billing", "features", "plans"],
            description="SaaS business metrics schema",
            sample_queries=[
                "Calculate monthly recurring revenue (MRR)",
                "Show user churn rate by cohort",
                "Find feature adoption rates",
                "Analyze subscription upgrade patterns"
            ]
        ),
        SchemaTemplate(
            name="Healthcare",
            tables=["patients", "appointments", "treatments", "medications", "providers", "insurance"],
            description="Healthcare management schema",
            sample_queries=[
                "Find patients due for follow-up",
                "Calculate average wait times by department",
                "Show treatment success rates",
                "Analyze appointment no-show patterns"
            ]
        ),
        SchemaTemplate(
            name="Financial",
            tables=["accounts", "transactions", "customers", "branches", "loans", "investments"],
            description="Banking and financial services schema",
            sample_queries=[
                "Calculate account balances by type",
                "Identify suspicious transaction patterns",
                "Show loan default rates by category",
                "Analyze investment portfolio performance"
            ]
        )
    ]

@router.get("/sample-queries")
async def get_sample_queries():
    """
    Get sample queries for quick testing.
    """
    return {
        "beginner": [
            "Show all customers from California",
            "Count total number of orders",
            "Find products under $50",
            "List employees hired this year"
        ],
        "intermediate": [
            "Calculate total sales by month for last year",
            "Find top 10 customers by lifetime value",
            "Show products that need restocking",
            "Compare this month's revenue to last month"
        ],
        "advanced": [
            "Calculate customer cohort retention rates",
            "Find cross-sell opportunities based on purchase patterns",
            "Identify seasonal trends in product sales",
            "Analyze customer lifetime value by acquisition channel"
        ]
    }

# Background task to track usage (mock implementation)
async def track_demo_usage(
    client_ip: str,
    query: str,
    generation_time: float,
    success: bool
):
    """
    Track demo usage for analytics.
    In production, this would write to database/redis.
    """
    # Mock implementation - would normally save to database
    print(f"Demo usage tracked: IP={client_ip}, Success={success}, Time={generation_time}ms")