import re
import sqlparse
from typing import Dict, List, Optional, Tuple, Any
from anthropic import AsyncAnthropic
import pandas as pd
import hashlib
import json
from backend.core.config import settings
from backend.services.cache import cache_service
import logging

logger = logging.getLogger(__name__)


class SQLGenerationEngine:
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.supported_dialects = ["sqlite", "postgresql", "mysql", "oracle", "mssql"]
        self.max_retry_attempts = 3
        
    async def generate_sql(
        self,
        natural_language_query: str,
        schema_info: Dict[str, Any],
        dialect: str = "sqlite",
        context: Optional[Dict[str, Any]] = None,
        previous_queries: Optional[List[Dict]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        # Create cache key
        cache_key = self._create_cache_key(
            natural_language_query, 
            schema_info, 
            dialect
        )
        
        # Check cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info("SQL generation cache hit")
            return cached_result["sql"], cached_result["metadata"]
        
        # Generate SQL with multi-step reasoning
        sql, metadata = await self._generate_with_chain_of_thought(
            natural_language_query,
            schema_info,
            dialect,
            context,
            previous_queries
        )
        
        # Validate and optimize the generated SQL
        validated_sql, validation_metadata = await self._validate_and_optimize_sql(
            sql, 
            schema_info, 
            dialect
        )
        
        # Merge metadata
        final_metadata = {**metadata, **validation_metadata}
        
        # Cache the result
        result = {"sql": validated_sql, "metadata": final_metadata}
        await cache_service.set(cache_key, result, ttl=settings.QUERY_CACHE_TTL_SECONDS)
        
        return validated_sql, final_metadata
    
    async def _generate_with_chain_of_thought(
        self,
        natural_language_query: str,
        schema_info: Dict[str, Any],
        dialect: str,
        context: Optional[Dict[str, Any]] = None,
        previous_queries: Optional[List[Dict]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        
        # Step 1: Understand the query
        understanding_prompt = self._create_understanding_prompt(
            natural_language_query,
            schema_info,
            context,
            previous_queries
        )
        
        understanding_response = await self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.1,
            messages=[{"role": "user", "content": understanding_prompt}]
        )
        
        understanding = understanding_response.content[0].text
        
        # Step 2: Generate SQL with reasoning
        sql_prompt = self._create_sql_generation_prompt(
            natural_language_query,
            schema_info,
            dialect,
            understanding,
            context
        )
        
        sql_response = await self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.1,
            messages=[{"role": "user", "content": sql_prompt}]
        )
        
        sql_content = sql_response.content[0].text
        
        # Extract SQL and metadata from response
        sql, metadata = self._parse_sql_response(sql_content)
        
        # Add token usage to metadata
        metadata["prompt_tokens"] = understanding_response.usage.input_tokens + sql_response.usage.input_tokens
        metadata["completion_tokens"] = understanding_response.usage.output_tokens + sql_response.usage.output_tokens
        metadata["understanding"] = understanding
        
        return sql, metadata
    
    def _create_understanding_prompt(
        self,
        query: str,
        schema_info: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        previous_queries: Optional[List[Dict]] = None
    ) -> str:
        prompt = f"""
You are an expert data analyst. Analyze this natural language query and break down what the user is asking for.

Query: "{query}"

Available Schema:
{json.dumps(schema_info, indent=2)}
"""
        
        if context:
            prompt += f"\nContext: {json.dumps(context, indent=2)}"
        
        if previous_queries:
            prompt += "\nPrevious queries in this session:\n"
            for pq in previous_queries[-3:]:  # Last 3 queries for context
                prompt += f"- {pq.get('natural_language_query', '')}\n"
        
        prompt += """
Provide a structured analysis:

1. **Intent**: What is the user trying to accomplish?
2. **Data Requirements**: What tables/columns are needed?
3. **Operations**: What SQL operations are required (SELECT, JOIN, GROUP BY, etc.)?
4. **Filters**: What conditions or filters are needed?
5. **Aggregations**: Are any calculations or aggregations required?
6. **Output Format**: What should the result look like?
7. **Complexity Score**: Rate from 1-10 (1=simple SELECT, 10=complex multi-table analysis)
8. **Potential Issues**: Any ambiguities or potential problems?

Be concise but thorough.
"""
        return prompt
    
    def _create_sql_generation_prompt(
        self,
        query: str,
        schema_info: Dict[str, Any],
        dialect: str,
        understanding: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        prompt = f"""
You are an expert SQL developer. Generate an optimized {dialect.upper()} query based on this analysis.

Original Query: "{query}"

Analysis:
{understanding}

Schema Information:
{json.dumps(schema_info, indent=2)}
"""
        
        if context:
            prompt += f"\nContext: {json.dumps(context, indent=2)}"
        
        prompt += f"""
Generate a {dialect.upper()} query following these requirements:

1. **Correctness**: Query must be syntactically correct and logically sound
2. **Performance**: Use appropriate indexes, avoid unnecessary JOINs
3. **Security**: Prevent SQL injection, use safe practices
4. **Readability**: Well-formatted with clear aliases
5. **Completeness**: Include all requested data points

Response Format:
```sql
-- Brief comment explaining the query purpose
[YOUR SQL QUERY HERE]
```

**Explanation**: [Brief explanation of the approach]
**Confidence**: [1-10 scale]
**Optimization Notes**: [Any performance considerations]
**Assumptions**: [Any assumptions made]

Important: Only return valid {dialect.upper()} syntax. No placeholders or pseudo-code.
"""
        return prompt
    
    def _parse_sql_response(self, response: str) -> Tuple[str, Dict[str, Any]]:
        # Extract SQL from code blocks
        sql_pattern = r'```sql\n(.*?)\n```'
        sql_matches = re.findall(sql_pattern, response, re.DOTALL)
        
        if sql_matches:
            sql = sql_matches[0].strip()
            # Remove comments for clean SQL
            sql = re.sub(r'--.*?\n', '\n', sql).strip()
        else:
            # Fallback: try to find SQL-like content
            lines = response.split('\n')
            sql_lines = []
            in_sql = False
            
            for line in lines:
                if any(keyword in line.upper() for keyword in ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE']):
                    in_sql = True
                if in_sql:
                    sql_lines.append(line)
                if line.strip().endswith(';'):
                    break
            
            sql = '\n'.join(sql_lines).strip()
        
        # Extract metadata
        metadata = {}
        
        # Extract confidence score
        confidence_match = re.search(r'\*\*Confidence\*\*:?\s*(\d+)', response)
        if confidence_match:
            metadata["confidence_score"] = int(confidence_match.group(1)) / 10.0
        
        # Extract explanation
        explanation_match = re.search(r'\*\*Explanation\*\*:?\s*(.*?)(?=\*\*|$)', response, re.DOTALL)
        if explanation_match:
            metadata["explanation"] = explanation_match.group(1).strip()
        
        # Extract optimization notes
        optimization_match = re.search(r'\*\*Optimization Notes\*\*:?\s*(.*?)(?=\*\*|$)', response, re.DOTALL)
        if optimization_match:
            metadata["optimization_notes"] = optimization_match.group(1).strip()
        
        # Extract assumptions
        assumptions_match = re.search(r'\*\*Assumptions\*\*:?\s*(.*?)(?=\*\*|$)', response, re.DOTALL)
        if assumptions_match:
            metadata["assumptions"] = assumptions_match.group(1).strip()
        
        return sql, metadata
    
    async def _validate_and_optimize_sql(
        self,
        sql: str,
        schema_info: Dict[str, Any],
        dialect: str
    ) -> Tuple[str, Dict[str, Any]]:
        validation_metadata = {}
        
        try:
            # Parse SQL for syntax validation
            sqlparse.parse(sql)[0]
            validation_metadata["syntax_valid"] = True
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(sql)
            validation_metadata["complexity_score"] = complexity_score
            
            # Check for potential security issues
            security_issues = self._check_security_issues(sql)
            validation_metadata["security_issues"] = security_issues
            
            # Suggest optimizations
            optimizations = self._suggest_optimizations(sql, schema_info)
            validation_metadata["optimization_suggestions"] = optimizations
            
            # Format SQL nicely
            formatted_sql = sqlparse.format(
                sql,
                reindent=True,
                keyword_case='upper',
                identifier_case='lower',
                strip_comments=False
            )
            
            return formatted_sql, validation_metadata
            
        except Exception as e:
            logger.error(f"SQL validation failed: {e}")
            validation_metadata["syntax_valid"] = False
            validation_metadata["validation_error"] = str(e)
            return sql, validation_metadata
    
    def _calculate_complexity_score(self, sql: str) -> float:
        sql_upper = sql.upper()
        score = 1.0
        
        # Count complex operations
        if 'JOIN' in sql_upper:
            score += sql_upper.count('JOIN') * 0.5
        
        if 'SUBQUERY' in sql_upper or '(' in sql and 'SELECT' in sql_upper:
            score += 1.0
        
        if 'GROUP BY' in sql_upper:
            score += 0.5
        
        if 'ORDER BY' in sql_upper:
            score += 0.3
        
        if 'HAVING' in sql_upper:
            score += 0.5
        
        if 'UNION' in sql_upper:
            score += 0.7
        
        if 'WITH' in sql_upper:  # CTE
            score += 1.0
        
        if 'WINDOW' in sql_upper or 'OVER' in sql_upper:
            score += 1.5
        
        return min(score, 10.0)
    
    def _check_security_issues(self, sql: str) -> List[str]:
        issues = []
        sql_upper = sql.upper()
        
        # Check for potentially dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                issues.append(f"Contains {keyword} operation")
        
        # Check for SQL injection patterns
        injection_patterns = [
            r"['\"];.*--",
            r"UNION.*SELECT",
            r"OR.*1=1",
            r"AND.*1=1"
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql_upper):
                issues.append(f"Potential SQL injection pattern: {pattern}")
        
        return issues
    
    def _suggest_optimizations(self, sql: str, schema_info: Dict[str, Any]) -> List[str]:
        suggestions = []
        sql_upper = sql.upper()
        
        # Check for SELECT *
        if 'SELECT *' in sql_upper:
            suggestions.append("Consider selecting only needed columns instead of SELECT *")
        
        # Check for missing WHERE clauses on large tables
        if 'WHERE' not in sql_upper and 'JOIN' in sql_upper:
            suggestions.append("Consider adding WHERE clauses to filter data early")
        
        # Check for potential index usage
        if 'ORDER BY' in sql_upper and 'LIMIT' not in sql_upper:
            suggestions.append("Consider adding LIMIT if you don't need all results")
        
        return suggestions
    
    def _create_cache_key(
        self,
        query: str,
        schema_info: Dict[str, Any],
        dialect: str
    ) -> str:
        content = f"{query}:{json.dumps(schema_info, sort_keys=True)}:{dialect}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def infer_schema_from_csv(self, csv_data: pd.DataFrame) -> Dict[str, Any]:
        """Infer schema information from CSV data"""
        schema = {
            "tables": {
                "data": {
                    "columns": {},
                    "row_count": len(csv_data),
                    "sample_data": csv_data.head(5).to_dict('records')
                }
            }
        }
        
        for column in csv_data.columns:
            col_info = {
                "type": str(csv_data[column].dtype),
                "nullable": csv_data[column].isnull().any(),
                "unique_values": csv_data[column].nunique(),
                "sample_values": csv_data[column].dropna().unique()[:5].tolist()
            }
            
            # Infer semantic type
            if csv_data[column].dtype in ['int64', 'float64']:
                col_info["semantic_type"] = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(csv_data[column]):
                col_info["semantic_type"] = "datetime"
            elif csv_data[column].nunique() < len(csv_data) * 0.1:
                col_info["semantic_type"] = "categorical"
            else:
                col_info["semantic_type"] = "text"
            
            schema["tables"]["data"]["columns"][column] = col_info
        
        return schema
    
    async def execute_sql(
        self,
        sql: str,
        data: pd.DataFrame,
        limit: int = 1000
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Execute SQL query against pandas DataFrame using SQLite"""
        try:
            import sqlite3
            
            # Create in-memory SQLite database
            conn = sqlite3.connect(':memory:')
            
            # Load data into SQLite
            data.to_sql('data', conn, index=False, if_exists='replace')
            
            # Add LIMIT if not present
            sql_with_limit = sql
            if 'LIMIT' not in sql.upper():
                sql_with_limit += f" LIMIT {limit}"
            
            # Execute query
            result = pd.read_sql_query(sql_with_limit, conn)
            
            # Generate execution metadata
            metadata = {
                "rows_returned": len(result),
                "columns_returned": len(result.columns),
                "execution_successful": True,
                "limited_results": len(result) == limit
            }
            
            conn.close()
            return result, metadata
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            metadata = {
                "rows_returned": 0,
                "columns_returned": 0,
                "execution_successful": False,
                "error": str(e)
            }
            return pd.DataFrame(), metadata


sql_generation_engine = SQLGenerationEngine()