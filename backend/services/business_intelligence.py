import pandas as pd
import numpy as np
from typing import Dict, List, Any
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from anthropic import AsyncAnthropic
import json
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)


class BusinessIntelligenceEngine:
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.insight_types = [
            "trend_analysis",
            "anomaly_detection", 
            "correlation_analysis",
            "forecasting",
            "segmentation",
            "performance_metrics",
            "roi_analysis"
        ]
    
    async def generate_automated_insights(
        self,
        data: pd.DataFrame,
        query_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive business insights from data"""
        insights = {
            "summary": await self._generate_executive_summary(data, query_context),
            "trends": self._analyze_trends(data),
            "anomalies": self._detect_anomalies(data),
            "correlations": self._analyze_correlations(data),
            "segments": await self._perform_segmentation(data),
            "forecasts": self._generate_forecasts(data),
            "kpis": self._calculate_kpis(data),
            "recommendations": await self._generate_recommendations(data, query_context)
        }
        
        return insights
    
    async def _generate_executive_summary(
        self,
        data: pd.DataFrame,
        query_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered executive summary"""
        self._create_data_profile(data)
        
        prompt = f"""
You are a senior business analyst. Analyze this dataset and provide an executive summary.

Dataset Profile:
- Rows: {len(data)}
- Columns: {len(data.columns)}
- Data types: {dict(data.dtypes)}
- Missing values: {data.isnull().sum().to_dict()}

Sample data (first 3 rows):
{data.head(3).to_dict('records')}

Query context: {json.dumps(query_context, default=str)}

Provide an executive summary with:
1. Key findings (3-5 bullet points)
2. Business impact assessment
3. Data quality assessment
4. Recommended actions
5. ROI implications

Keep it concise and business-focused.
"""
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            summary_text = response.content[0].text
            
            return {
                "summary_text": summary_text,
                "data_quality_score": self._calculate_data_quality_score(data),
                "business_impact_score": self._assess_business_impact(data),
                "confidence_level": 0.85
            }
            
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            return {
                "summary_text": "Unable to generate executive summary",
                "data_quality_score": self._calculate_data_quality_score(data),
                "business_impact_score": 0.5,
                "confidence_level": 0.0
            }
    
    def _analyze_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in numeric columns"""
        trends = {}
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if len(data[column].dropna()) < 3:
                continue
            
            values = data[column].dropna()
            
            # Calculate trend metrics
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Determine trend direction
            if abs(slope) < std_err:
                direction = "stable"
            elif slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
            
            # Calculate trend strength
            strength = min(abs(r_value), 1.0)
            
            trends[column] = {
                "direction": direction,
                "strength": strength,
                "slope": slope,
                "r_squared": r_value ** 2,
                "p_value": p_value,
                "significance": "significant" if p_value < 0.05 else "not_significant",
                "growth_rate": (values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100 if values.iloc[0] != 0 else 0
            }
        
        return trends
    
    def _detect_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in numeric data using statistical methods"""
        anomalies = {}
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            values = data[column].dropna()
            
            if len(values) < 10:
                continue
            
            # Calculate Z-scores
            z_scores = np.abs(stats.zscore(values))
            
            # IQR method
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Identify anomalies
            z_score_anomalies = values[z_scores > 3]
            iqr_anomalies = values[(values < lower_bound) | (values > upper_bound)]
            
            if len(z_score_anomalies) > 0 or len(iqr_anomalies) > 0:
                anomalies[column] = {
                    "z_score_anomalies": {
                        "count": len(z_score_anomalies),
                        "values": z_score_anomalies.tolist()[:5],  # Top 5
                        "percentage": len(z_score_anomalies) / len(values) * 100
                    },
                    "iqr_anomalies": {
                        "count": len(iqr_anomalies),
                        "values": iqr_anomalies.tolist()[:5],  # Top 5
                        "percentage": len(iqr_anomalies) / len(values) * 100
                    },
                    "bounds": {
                        "lower": float(lower_bound),
                        "upper": float(upper_bound)
                    }
                }
        
        return anomalies
    
    def _analyze_correlations(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between numeric variables"""
        numeric_data = data.select_dtypes(include=[np.number])
        
        if len(numeric_data.columns) < 2:
            return {"message": "Insufficient numeric columns for correlation analysis"}
        
        # Calculate correlation matrix
        correlation_matrix = numeric_data.corr()
        
        # Find strong correlations (exclude self-correlations)
        strong_correlations = []
        
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                
                if abs(corr_value) > 0.5:  # Strong correlation threshold
                    strong_correlations.append({
                        "variable_1": correlation_matrix.columns[i],
                        "variable_2": correlation_matrix.columns[j],
                        "correlation": float(corr_value),
                        "strength": self._classify_correlation_strength(abs(corr_value)),
                        "direction": "positive" if corr_value > 0 else "negative"
                    })
        
        # Sort by absolute correlation value
        strong_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return {
            "correlation_matrix": correlation_matrix.to_dict(),
            "strong_correlations": strong_correlations[:10],  # Top 10
            "total_correlations": len(strong_correlations)
        }
    
    def _classify_correlation_strength(self, correlation: float) -> str:
        """Classify correlation strength"""
        if correlation >= 0.8:
            return "very_strong"
        elif correlation >= 0.6:
            return "strong"
        elif correlation >= 0.4:
            return "moderate"
        elif correlation >= 0.2:
            return "weak"
        else:
            return "very_weak"
    
    async def _perform_segmentation(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform customer/data segmentation using clustering"""
        numeric_data = data.select_dtypes(include=[np.number]).dropna()
        
        if len(numeric_data) < 10 or len(numeric_data.columns) < 2:
            return {"message": "Insufficient data for segmentation"}
        
        try:
            # Standardize the data
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(numeric_data)
            
            # Determine optimal number of clusters (between 2 and 6)
            max_clusters = min(6, len(numeric_data) // 5)
            
            if max_clusters < 2:
                return {"message": "Insufficient data points for clustering"}
            
            inertias = []
            for k in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(scaled_data)
                inertias.append(kmeans.inertia_)
            
            # Use elbow method to find optimal k
            optimal_k = self._find_elbow_point(inertias) + 2
            
            # Final clustering
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(scaled_data)
            
            # Analyze segments
            segments = []
            for i in range(optimal_k):
                segment_data = numeric_data[clusters == i]
                segment_profile = {
                    "segment_id": i,
                    "size": len(segment_data),
                    "percentage": len(segment_data) / len(numeric_data) * 100,
                    "characteristics": {}
                }
                
                # Calculate segment characteristics
                for column in numeric_data.columns:
                    segment_profile["characteristics"][column] = {
                        "mean": float(segment_data[column].mean()),
                        "median": float(segment_data[column].median()),
                        "std": float(segment_data[column].std())
                    }
                
                segments.append(segment_profile)
            
            return {
                "optimal_clusters": optimal_k,
                "segments": segments,
                "silhouette_score": self._calculate_silhouette_score(scaled_data, clusters)
            }
            
        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            return {"message": f"Segmentation failed: {str(e)}"}
    
    def _find_elbow_point(self, inertias: List[float]) -> int:
        """Find elbow point in inertia curve"""
        if len(inertias) < 3:
            return 0
        
        # Simple elbow detection using second derivative
        second_derivatives = []
        for i in range(1, len(inertias) - 1):
            second_derivatives.append(inertias[i-1] - 2*inertias[i] + inertias[i+1])
        
        return np.argmax(second_derivatives)
    
    def _calculate_silhouette_score(self, data: np.ndarray, labels: np.ndarray) -> float:
        """Calculate silhouette score for clustering quality"""
        try:
            from sklearn.metrics import silhouette_score
            return float(silhouette_score(data, labels))
        except Exception:
            return 0.0
    
    def _generate_forecasts(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate simple forecasts for time series data"""
        forecasts = {}
        
        # Look for date columns
        date_columns = []
        for column in data.columns:
            if data[column].dtype in ['datetime64[ns]', 'object']:
                try:
                    pd.to_datetime(data[column])
                    date_columns.append(column)
                except (ValueError, TypeError):
                    continue
        
        if not date_columns:
            return {"message": "No date columns found for forecasting"}
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for date_col in date_columns[:1]:  # Use first date column
            for numeric_col in numeric_columns[:3]:  # Forecast top 3 numeric columns
                try:
                    # Prepare time series data
                    ts_data = data[[date_col, numeric_col]].copy()
                    ts_data[date_col] = pd.to_datetime(ts_data[date_col])
                    ts_data = ts_data.sort_values(date_col).dropna()
                    
                    if len(ts_data) < 5:
                        continue
                    
                    # Simple linear trend forecast
                    x = np.arange(len(ts_data))
                    y = ts_data[numeric_col].values
                    
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    
                    # Forecast next 3 periods
                    future_periods = 3
                    future_x = np.arange(len(ts_data), len(ts_data) + future_periods)
                    future_y = slope * future_x + intercept
                    
                    forecasts[f"{numeric_col}_forecast"] = {
                        "current_value": float(y[-1]),
                        "forecasted_values": future_y.tolist(),
                        "trend_strength": float(abs(r_value)),
                        "confidence": float(max(0, 1 - p_value)) if p_value else 0.5,
                        "growth_trend": "increasing" if slope > 0 else "decreasing"
                    }
                    
                except Exception as e:
                    logger.warning(f"Forecast failed for {numeric_col}: {e}")
                    continue
        
        return forecasts
    
    def _calculate_kpis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate common business KPIs"""
        kpis = {}
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            values = data[column].dropna()
            
            if len(values) == 0:
                continue
            
            kpis[column] = {
                "total": float(values.sum()),
                "average": float(values.mean()),
                "median": float(values.median()),
                "min": float(values.min()),
                "max": float(values.max()),
                "std_dev": float(values.std()),
                "coefficient_of_variation": float(values.std() / values.mean()) if values.mean() != 0 else 0,
                "percentiles": {
                    "25th": float(values.quantile(0.25)),
                    "75th": float(values.quantile(0.75)),
                    "90th": float(values.quantile(0.90)),
                    "95th": float(values.quantile(0.95))
                }
            }
        
        # Calculate data distribution metrics
        kpis["data_overview"] = {
            "total_records": len(data),
            "total_columns": len(data.columns),
            "numeric_columns": len(numeric_columns),
            "missing_data_percentage": float(data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100),
            "duplicate_rows": int(data.duplicated().sum())
        }
        
        return kpis
    
    async def _generate_recommendations(
        self,
        data: pd.DataFrame,
        query_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered business recommendations"""
        data_insights = {
            "shape": data.shape,
            "dtypes": dict(data.dtypes),
            "missing_values": data.isnull().sum().to_dict(),
            "numeric_summary": data.describe().to_dict() if len(data.select_dtypes(include=[np.number]).columns) > 0 else {}
        }
        
        prompt = f"""
You are a business consultant. Based on this data analysis, provide actionable business recommendations.

Data Insights:
{json.dumps(data_insights, default=str, indent=2)}

Query Context:
{json.dumps(query_context, default=str)}

Provide 3-5 specific, actionable recommendations in this format:
1. **Recommendation Title**: Brief description
   - Impact: High/Medium/Low
   - Effort: High/Medium/Low
   - Timeline: Days/Weeks/Months
   - Expected ROI: Quantify if possible

Focus on practical business actions that can be taken based on the data.
"""
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )
            
            recommendations_text = response.content[0].text
            
            # Parse recommendations (simplified)
            recommendations = []
            lines = recommendations_text.split('\n')
            current_rec = None
            
            for line in lines:
                if line.strip() and line[0].isdigit():
                    if current_rec:
                        recommendations.append(current_rec)
                    
                    current_rec = {
                        "title": line.split('**')[1] if '**' in line else line.strip(),
                        "description": line.split('**')[2].strip() if '**' in line else "",
                        "impact": "Medium",
                        "effort": "Medium", 
                        "timeline": "Weeks",
                        "roi_estimate": "TBD"
                    }
                
                elif current_rec and line.strip():
                    if "Impact:" in line:
                        current_rec["impact"] = line.split("Impact:")[1].strip().split()[0]
                    elif "Effort:" in line:
                        current_rec["effort"] = line.split("Effort:")[1].strip().split()[0]
                    elif "Timeline:" in line:
                        current_rec["timeline"] = line.split("Timeline:")[1].strip()
                    elif "ROI:" in line:
                        current_rec["roi_estimate"] = line.split("ROI:")[1].strip()
            
            if current_rec:
                recommendations.append(current_rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendations generation failed: {e}")
            return [{
                "title": "Data Analysis Complete",
                "description": "Review the generated insights and trends",
                "impact": "Medium",
                "effort": "Low",
                "timeline": "Days",
                "roi_estimate": "Variable"
            }]
    
    def _create_data_profile(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Create comprehensive data profile"""
        profile = {
            "shape": data.shape,
            "columns": list(data.columns),
            "data_types": dict(data.dtypes.astype(str)),
            "missing_values": data.isnull().sum().to_dict(),
            "memory_usage": data.memory_usage(deep=True).sum(),
            "duplicate_rows": int(data.duplicated().sum())
        }
        
        # Add numeric column statistics
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            profile["numeric_summary"] = data[numeric_cols].describe().to_dict()
        
        return profile
    
    def _calculate_data_quality_score(self, data: pd.DataFrame) -> float:
        """Calculate data quality score (0-1)"""
        score = 1.0
        
        # Penalize missing values
        missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
        score -= missing_ratio * 0.3
        
        # Penalize duplicate rows
        duplicate_ratio = data.duplicated().sum() / len(data)
        score -= duplicate_ratio * 0.2
        
        # Check data consistency
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if data[col].std() == 0:  # No variance
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _assess_business_impact(self, data: pd.DataFrame) -> float:
        """Assess potential business impact of the data (0-1)"""
        impact_score = 0.5  # Base score
        
        # Higher impact for larger datasets
        if len(data) > 1000:
            impact_score += 0.2
        
        # Higher impact for more columns (more dimensions)
        if len(data.columns) > 10:
            impact_score += 0.1
        
        # Higher impact for financial/business keywords in columns
        business_keywords = ['revenue', 'profit', 'cost', 'sales', 'customer', 'price', 'roi']
        for col in data.columns:
            if any(keyword in col.lower() for keyword in business_keywords):
                impact_score += 0.05
        
        return min(1.0, impact_score)


business_intelligence_engine = BusinessIntelligenceEngine()