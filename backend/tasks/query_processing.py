from backend.core.celery_app import celery_app
from backend.core.database import AsyncSessionLocal
from backend.core.config import settings
from backend.models.query import Query, QueryStatus
from backend.models.file import File
from backend.services.sql_generation import sql_generation_engine
from backend.services.business_intelligence import business_intelligence_engine
from backend.services.security import security_service
from backend.services.cache import cache_service
import pandas as pd
import asyncio
import logging
from typing import Dict, Any, List
import traceback

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="backend.tasks.query_processing.process_standard_query")
def process_standard_query(self, query_id: str, user_id: str, tenant_id: str) -> Dict[str, Any]:
    """Process a standard SQL query asynchronously"""
    try:
        # Update task progress
        self.update_state(state="PROCESSING", meta={"progress": 10, "status": "Starting query processing"})
        
        return asyncio.run(_process_query_async(self, query_id, user_id, tenant_id, priority="standard"))
        
    except Exception as e:
        logger.error(f"Query processing failed for {query_id}: {e}")
        logger.error(traceback.format_exc())
        
        # Update query status in database
        asyncio.run(_update_query_status(query_id, QueryStatus.FAILED, str(e)))
        
        raise self.retry(exc=e, countdown=60, max_retries=2)


@celery_app.task(bind=True, name="backend.tasks.query_processing.process_urgent_query")  
def process_urgent_query(self, query_id: str, user_id: str, tenant_id: str) -> Dict[str, Any]:
    """Process an urgent SQL query with high priority"""
    try:
        self.update_state(state="PROCESSING", meta={"progress": 10, "status": "Starting urgent query processing"})
        
        return asyncio.run(_process_query_async(self, query_id, user_id, tenant_id, priority="urgent"))
        
    except Exception as e:
        logger.error(f"Urgent query processing failed for {query_id}: {e}")
        asyncio.run(_update_query_status(query_id, QueryStatus.FAILED, str(e)))
        
        raise self.retry(exc=e, countdown=30, max_retries=1)


@celery_app.task(bind=True, name="backend.tasks.query_processing.process_complex_analysis")
def process_complex_analysis(
    self, 
    query_id: str, 
    user_id: str, 
    tenant_id: str,
    analysis_type: str = "full"
) -> Dict[str, Any]:
    """Process complex data analysis with AI insights"""
    try:
        self.update_state(state="PROCESSING", meta={"progress": 5, "status": "Starting complex analysis"})
        
        return asyncio.run(_process_complex_analysis_async(
            self, query_id, user_id, tenant_id, analysis_type
        ))
        
    except Exception as e:
        logger.error(f"Complex analysis failed for {query_id}: {e}")
        asyncio.run(_update_query_status(query_id, QueryStatus.FAILED, str(e)))
        
        raise self.retry(exc=e, countdown=120, max_retries=2)


async def _process_query_async(
    task, 
    query_id: str, 
    user_id: str, 
    tenant_id: str, 
    priority: str = "standard"
) -> Dict[str, Any]:
    """Internal async query processing function"""
    async with AsyncSessionLocal() as db:
        try:
            # Fetch query from database
            query = await db.get(Query, query_id)
            if not query:
                raise Exception(f"Query {query_id} not found")
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 20, "status": "Loading data"})
            
            # Load associated file data
            file_data = None
            schema_info = None
            
            if query.file_id:
                file = await db.get(File, query.file_id)
                if file and file.status.value == "ready":
                    # Load file data (in production, this would be from S3 or similar)
                    file_data = pd.read_csv(file.storage_path)  # Simplified
                    schema_info = await sql_generation_engine.infer_schema_from_csv(file_data)
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 40, "status": "Generating SQL"})
            
            # Generate SQL
            if not query.generated_sql:
                if not schema_info:
                    raise Exception("No schema information available for SQL generation")
                
                generated_sql, metadata = await sql_generation_engine.generate_sql(
                    query.natural_language_query,
                    schema_info,
                    dialect="sqlite",
                    context={"priority": priority, "user_id": user_id}
                )
                
                query.generated_sql = generated_sql
                query.ai_model = metadata.get("model", "claude-3-sonnet")
                query.ai_confidence_score = metadata.get("confidence_score", 0.8)
                query.prompt_tokens = metadata.get("prompt_tokens", 0)
                query.completion_tokens = metadata.get("completion_tokens", 0)
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 60, "status": "Executing SQL"})
            
            # Execute SQL
            if file_data is not None:
                result_data, execution_metadata = await sql_generation_engine.execute_sql(
                    query.generated_sql,
                    file_data
                )
                
                query.execution_time_ms = execution_metadata.get("execution_time_ms", 0)
                query.rows_returned = execution_metadata.get("rows_returned", 0)
                
                if execution_metadata.get("execution_successful", False):
                    # Store results in cache
                    cache_key = cache_service.create_result_cache_key(query_id)
                    await cache_service.set(
                        cache_key, 
                        result_data.to_dict('records'), 
                        ttl=settings.QUERY_RESULT_CACHE_TTL_SECONDS
                    )
                    
                    query.result_cache_key = cache_key
                    query.result_preview = result_data.head(10).to_dict('records')
                    query.status = QueryStatus.COMPLETED
                else:
                    query.error_message = execution_metadata.get("error", "Unknown execution error")
                    query.status = QueryStatus.FAILED
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 80, "status": "Generating insights"})
            
            # Generate basic insights for successful queries
            if query.status == QueryStatus.COMPLETED and file_data is not None:
                try:
                    insights = await business_intelligence_engine.generate_automated_insights(
                        result_data,
                        {"query": query.natural_language_query, "user_id": user_id}
                    )
                    query.insights = insights
                except Exception as e:
                    logger.warning(f"Insight generation failed: {e}")
                    query.insights = {"error": "Insight generation failed"}
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 90, "status": "Saving results"})
            
            # Save query updates
            await db.commit()
            
            # Final progress update
            task.update_state(
                state="SUCCESS", 
                meta={
                    "progress": 100, 
                    "status": "Query processing completed",
                    "query_id": query_id,
                    "rows_returned": query.rows_returned,
                    "execution_time_ms": query.execution_time_ms
                }
            )
            
            return {
                "query_id": query_id,
                "status": query.status.value,
                "rows_returned": query.rows_returned,
                "execution_time_ms": query.execution_time_ms,
                "has_insights": bool(query.insights)
            }
            
        except Exception as e:
            # Update query status to failed
            if 'query' in locals():
                query.status = QueryStatus.FAILED
                query.error_message = str(e)
                await db.commit()
            
            raise e


async def _process_complex_analysis_async(
    task,
    query_id: str,
    user_id: str, 
    tenant_id: str,
    analysis_type: str
) -> Dict[str, Any]:
    """Internal async complex analysis processing function"""
    async with AsyncSessionLocal() as db:
        try:
            # Fetch query and associated data
            query = await db.get(Query, query_id)
            if not query:
                raise Exception(f"Query {query_id} not found")
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 10, "status": "Loading data for analysis"})
            
            # Get cached result data
            if query.result_cache_key:
                cached_data = await cache_service.get(query.result_cache_key)
                if cached_data:
                    result_data = pd.DataFrame(cached_data)
                else:
                    raise Exception("Result data not found in cache")
            else:
                raise Exception("No result data available for analysis")
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 30, "status": "Performing trend analysis"})
            
            # Generate comprehensive insights
            insights = await business_intelligence_engine.generate_automated_insights(
                result_data,
                {
                    "query": query.natural_language_query,
                    "user_id": user_id,
                    "analysis_type": analysis_type
                }
            )
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 60, "status": "Security and PII scanning"})
            
            # Perform security analysis
            pii_findings = security_service.scan_for_pii(result_data)
            data_classification = security_service.classify_data_sensitivity(result_data, pii_findings)
            
            # Update progress  
            task.update_state(state="PROCESSING", meta={"progress": 80, "status": "Generating visualizations"})
            
            # Generate advanced visualizations metadata
            visualization_suggestions = _generate_visualization_suggestions(result_data)
            
            # Update progress
            task.update_state(state="PROCESSING", meta={"progress": 90, "status": "Saving analysis results"})
            
            # Combine all analysis results
            comprehensive_insights = {
                **insights,
                "security_analysis": {
                    "pii_findings": pii_findings,
                    "data_classification": data_classification.value,
                    "contains_sensitive_data": len(pii_findings) > 0
                },
                "visualization_suggestions": visualization_suggestions,
                "analysis_metadata": {
                    "analysis_type": analysis_type,
                    "processing_time": task.request.id,
                    "data_points_analyzed": len(result_data)
                }
            }
            
            # Update query with comprehensive insights
            query.insights = comprehensive_insights
            await db.commit()
            
            # Final progress update
            task.update_state(
                state="SUCCESS",
                meta={
                    "progress": 100,
                    "status": "Complex analysis completed",
                    "query_id": query_id,
                    "insights_generated": len(comprehensive_insights),
                    "security_classification": data_classification.value
                }
            )
            
            return {
                "query_id": query_id,
                "analysis_completed": True,
                "insights_count": len(comprehensive_insights),
                "security_classification": data_classification.value,
                "has_pii": len(pii_findings) > 0
            }
            
        except Exception as e:
            logger.error(f"Complex analysis failed: {e}")
            raise e


def _generate_visualization_suggestions(data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate visualization suggestions based on data characteristics"""
    suggestions = []
    
    numeric_cols = data.select_dtypes(include=['number']).columns
    categorical_cols = data.select_dtypes(include=['object']).columns
    
    # Bar chart for categorical data
    if len(categorical_cols) > 0 and len(data) < 1000:
        suggestions.append({
            "type": "bar",
            "title": "Distribution Analysis",
            "x_axis": categorical_cols[0],
            "y_axis": "count",
            "description": "Shows distribution of categorical values"
        })
    
    # Line chart for time series
    date_cols = []
    for col in data.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            date_cols.append(col)
    
    if date_cols and len(numeric_cols) > 0:
        suggestions.append({
            "type": "line",
            "title": "Trend Analysis",
            "x_axis": date_cols[0],
            "y_axis": numeric_cols[0],
            "description": "Shows trends over time"
        })
    
    # Scatter plot for correlation
    if len(numeric_cols) >= 2:
        suggestions.append({
            "type": "scatter",
            "title": "Correlation Analysis", 
            "x_axis": numeric_cols[0],
            "y_axis": numeric_cols[1],
            "description": "Shows relationship between numeric variables"
        })
    
    return suggestions


async def _update_query_status(query_id: str, status: QueryStatus, error_message: str = None):
    """Update query status in database"""
    async with AsyncSessionLocal() as db:
        try:
            query = await db.get(Query, query_id)
            if query:
                query.status = status
                if error_message:
                    query.error_message = error_message
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update query status: {e}")