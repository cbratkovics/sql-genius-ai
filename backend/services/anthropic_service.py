import os
import json
import asyncio
from typing import Optional, Dict, Any
from anthropic import AsyncAnthropic
from backend.core.config import settings

class AnthropicService:
    """Service for interacting with Anthropic's Claude API"""
    
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else os.getenv("ANTHROPIC_API_KEY")
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None
        
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.2,
        model: str = "claude-3-haiku-20240307"
    ) -> str:
        """
        Generate a completion using Claude API.
        Falls back to mock response if API key not configured.
        """
        if not self.client:
            # Return mock response for demo when API key not configured
            return self._get_mock_response(prompt)
        
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic API error: {e}")
            # Fallback to mock response
            return self._get_mock_response(prompt)
    
    def _get_mock_response(self, prompt: str) -> str:
        """
        Generate a mock SQL response for demo purposes.
        """
        # Extract key information from prompt
        prompt_lower = prompt.lower()
        
        if "sales" in prompt_lower and "month" in prompt_lower:
            return json.dumps({
                "sql": """SELECT 
    DATE_TRUNC('month', order_date) as month,
    SUM(total_amount) as total_sales,
    COUNT(*) as order_count
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month DESC""",
                "explanation": "This query aggregates sales data by month, showing total sales amount and order count for each month.",
                "assumptions": ["Assumes an 'orders' table with 'order_date' and 'total_amount' columns"]
            })
        elif "customer" in prompt_lower and ("top" in prompt_lower or "best" in prompt_lower):
            return json.dumps({
                "sql": """SELECT 
    c.customer_id,
    c.customer_name,
    SUM(o.total_amount) as lifetime_value,
    COUNT(o.order_id) as total_orders
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY lifetime_value DESC
LIMIT 10""",
                "explanation": "This query finds the top customers by lifetime value, joining customers and orders tables.",
                "assumptions": ["Assumes 'customers' and 'orders' tables with appropriate foreign key relationships"]
            })
        elif "product" in prompt_lower:
            return json.dumps({
                "sql": """SELECT 
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) as units_sold,
    SUM(oi.quantity * oi.unit_price) as revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC""",
                "explanation": "This query analyzes product performance by calculating units sold and revenue.",
                "assumptions": ["Assumes 'products' and 'order_items' tables exist"]
            })
        else:
            # Generic fallback
            return json.dumps({
                "sql": "SELECT * FROM table_name WHERE condition = 'value' LIMIT 10",
                "explanation": "Generic query structure based on the natural language input.",
                "assumptions": ["Table and column names need to be specified based on your schema"]
            })