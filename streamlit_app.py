def create_visualizations(df, query_type="auto"):
    """Create comprehensive business intelligence visualizations with improved layout"""
    charts = []
    
    if df.empty:
        return charts
    
    # Detect numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Remove any ID-like columns from numeric analysis
    numeric_cols = [col for col in numeric_cols if not any(x in col.lower() for x in ['id', 'index', 'rank'])]
    
    if len(numeric_cols) == 0:
        return charts
    
    # STANDARDIZED TITLE FORMATTING FUNCTION
    def apply_standard_formatting(fig, title, height=550):
        """Apply consistent formatting to all charts"""
        fig.update_layout(
            title={
                'text': f"<b>{title}</b>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial', 'color': '#2c3e50'}
            },
            height=height,
            paper_bgcolor='rgba(248,249,250,0.95)',
            plot_bgcolor='rgba(255,255,255,0.95)',
            font=dict(family="Arial", size=12),
            margin=dict(l=60, r=60, t=80, b=60),
            showlegend=True
        )
        return fig
    
    # 1. EXECUTIVE KPI DASHBOARD - CARD STYLE
    if len(numeric_cols) >= 1:
        # Create card-style KPI dashboard using bar chart with custom styling
        kpi_data = []
        kpi_labels = []
        kpi_values = []
        kpi_colors = []
        
        # Prepare data for up to 5 key metrics
        colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']
        
        for i, col in enumerate(numeric_cols[:5]):
            total_val = df[col].sum()
            avg_val = df[col].mean()
            
            # Format metric name
            metric_name = col.replace('_', ' ').title()
            
            # Create formatted label with value and average
            if 'spend' in col.lower() or 'cost' in col.lower() or 'revenue' in col.lower():
                label = f"{metric_name}<br>${total_val:,.0f}<br><span style='font-size:10px'>Avg: ${avg_val:,.0f}</span>"
            else:
                label = f"{metric_name}<br>{total_val:,.0f}<br><span style='font-size:10px'>Avg: {avg_val:,.0f}</span>"
            
            kpi_labels.append(label)
            kpi_values.append(total_val)
            kpi_colors.append(colors[i % len(colors)])
        
        # Create horizontal bar chart that looks like cards
        fig_kpi = go.Figure()
        
        fig_kpi.add_trace(go.Bar(
            y=kpi_labels,
            x=kpi_values,
            orientation='h',
            marker=dict(
                color=kpi_colors,
                line=dict(color='white', width=2)
            ),
            text=[f"${val:,.0f}" if any(term in numeric_cols[i].lower() for term in ['spend', 'cost', 'revenue']) 
                  else f"{val:,.0f}" for i, val in enumerate(kpi_values)],
            textposition='auto',
            textfont=dict(size=14, color='white', family='Arial'),
            hovertemplate='<b>%{y}</b><br>Value: %{x:,.0f}<extra></extra>'
        ))
        
        fig_kpi.update_layout(
            title={
                'text': "<b>🎯 Executive KPI Dashboard</b>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'family': 'Arial', 'color': '#2c3e50'}
            },
            height=400,
            paper_bgcolor='rgba(248,249,250,0.95)',
            plot_bgcolor='rgba(255,255,255,0.95)',
            font=dict(family="Arial", size=12),
            margin=dict(l=200, r=60, t=80, b=60),
            xaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.3)'),
            yaxis=dict(showgrid=False),
            showlegend=False
        )
        
        charts.append(("🎯 Executive KPI Dashboard", fig_kpi))
    
    # 2. PERFORMANCE CORRELATION ANALYSIS - IMPROVED
    if len(numeric_cols) >= 2:
        correlation_data = df[numeric_cols].corr()
        
        fig_corr = px.imshow(
            correlation_data,
            text_auto='.2f',
            aspect="auto",
            title="📊 Performance Correlation Matrix",
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1
        )
        
        fig_corr = apply_standard_formatting(fig_corr, "📊 Performance Correlation Matrix", 500)
        fig_corr.update_traces(textfont_size=12, textfont_color="white")
        
        charts.append(("📊 Correlation Analysis", fig_corr))
        
        # ENHANCED EFFICIENCY ANALYSIS - More Business Focused
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            # Calculate efficiency ratio
            efficiency_ratio = df[y_col] / df[x_col].replace(0, 1) if x_col != y_col else df[y_col]
            df_plot = df.copy()
            df_plot['efficiency_ratio'] = efficiency_ratio
            
            fig_scatter = px.scatter(
                df_plot, 
                x=x_col, 
                y=y_col,
                size='efficiency_ratio',
                color=categorical_cols[0] if len(categorical_cols) > 0 else 'efficiency_ratio',
                title=f"💎 Performance Efficiency: {y_col.replace('_', ' ').title()} vs {x_col.replace('_', ' ').title()}",
                hover_data=['efficiency_ratio'] + numeric_cols[:3],
                color_continuous_scale='Viridis' if len(categorical_cols) == 0 else None
            )
            
            # Add quadrant lines for better interpretation
            x_median = df[x_col].median()
            y_median = df[y_col].median()
            
            fig_scatter.add_hline(y=y_median, line_dash="dash", line_color="red", 
                                annotation_text="Performance Median", annotation_position="top left")
            fig_scatter.add_vline(x=x_median, line_dash="dash", line_color="red", 
                                annotation_text="Investment Median", annotation_position="top right")
            
            fig_scatter = apply_standard_formatting(fig_scatter, "💎 Performance Efficiency Analysis")
            fig_scatter.update_traces(marker=dict(line=dict(width=1, color='white')), opacity=0.8)
            
            charts.append(("💎 Efficiency Analysis", fig_scatter))
    
    # 3. MARKET SEGMENTATION & PERFORMANCE - IMPROVED
    if len(categorical_cols) > 0 and len(numeric_cols) > 0:
        cat_col = categorical_cols[0]
        
        # Enhanced market share analysis
        if len(df[cat_col].unique()) <= 10:
            market_data = df.groupby(cat_col)[numeric_cols[0]].sum().reset_index()
            
            fig_pie = px.pie(
                market_data,
                values=numeric_cols[0],
                names=cat_col,
                title="🏆 Market Share Analysis",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.3
            )
            
            fig_pie.update_traces(
                textposition='auto',
                textinfo='percent+label',
                textfont_size=12,
                marker=dict(line=dict(color='white', width=2))
            )
            
            fig_pie = apply_standard_formatting(fig_pie, f"🏆 Market Share by {cat_col.replace('_', ' ').title()}")
            
            charts.append(("🏆 Market Share Analysis", fig_pie))
        
        # Performance comparison with better formatting
        comparison_data = df.groupby(cat_col)[numeric_cols[0]].agg(['mean', 'sum', 'count']).reset_index()
        comparison_data.columns = [cat_col, 'average', 'total', 'count']
        
        fig_comparison = px.bar(
            comparison_data,
            x=cat_col,
            y='average',
            title="📈 Performance Comparison",
            color='average',
            color_continuous_scale='Viridis',
            text='average'
        )
        
        # Add overall average line
        overall_avg = df[numeric_cols[0]].mean()
        fig_comparison.add_hline(
            y=overall_avg,
            line_dash="dash",
            line_color="#e74c3c",
            line_width=2,
            annotation_text=f"Overall Average: {overall_avg:,.0f}",
            annotation_position="top right"
        )
        
        fig_comparison.update_traces(
            texttemplate='%{text:,.0f}',
            textposition='outside',
            textfont_size=11,
            marker_line_color='white',
            marker_line_width=1
        )
        
        fig_comparison = apply_standard_formatting(fig_comparison, f"📈 Performance by {cat_col.replace('_', ' ').title()}")
        fig_comparison.update_xaxis(tickangle=45)
        fig_comparison.update_layout(showlegend=False)
        
        charts.append(("📈 Performance Benchmarking", fig_comparison))
    
    # 4. IMPROVED ROI ANALYSIS
    if len(numeric_cols) >= 2:
        # Calculate actual ROI metrics
        primary_metric = numeric_cols[0]
        secondary_metric = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
        
        # Create ROI calculation
        df_roi = df.copy()
        df_roi['roi_ratio'] = df_roi[primary_metric] / df_roi[secondary_metric].replace(0, 1)
        
        # ROI distribution analysis
        fig_roi = px.histogram(
            df_roi,
            x='roi_ratio',
            nbins=15,
            title="💰 ROI Distribution Analysis",
            color_discrete_sequence=['#667eea'],
            marginal="box"
        )
        
        # Add ROI benchmarks
        roi_median = df_roi['roi_ratio'].median()
        roi_75th = df_roi['roi_ratio'].quantile(0.75)
        roi_25th = df_roi['roi_ratio'].quantile(0.25)
        
        fig_roi.add_vline(x=roi_median, line_dash="solid", line_color="#e74c3c", 
                         annotation_text=f"Median ROI: {roi_median:.2f}")
        fig_roi.add_vline(x=roi_75th, line_dash="dot", line_color="#27ae60", 
                         annotation_text=f"Top 25%: {roi_75th:.2f}")
        fig_roi.add_vline(x=roi_25th, line_dash="dot", line_color="#f39c12", 
                         annotation_text=f"Bottom 25%: {roi_25th:.2f}")
        
        fig_roi = apply_standard_formatting(fig_roi, f"💰 ROI Analysis: {primary_metric.replace('_', ' ').title()}/{secondary_metric.replace('_', ' ').title()}")
        
        charts.append(("💰 ROI Analysis", fig_roi))
    
    # 5. TOP PERFORMERS RANKING
    if len(numeric_cols) > 0:
        primary_metric = numeric_cols[0]
        top_performers = df.nlargest(min(10, len(df)), primary_metric)
        
        if len(categorical_cols) > 0:
            label_col = categorical_cols[0]
        else:
            # Create index-based labels if no categorical columns
            top_performers = top_performers.reset_index()
            label_col = 'index'
            top_performers[label_col] = top_performers[label_col].astype(str)
            
        fig_ranking = px.bar(
            top_performers,
            x=label_col,
            y=primary_metric,
            title="🚀 Top Performers Ranking",
            color=primary_metric,
            color_continuous_scale='Plasma',
            text=primary_metric
        )
        
        # Add performance tiers
        if len(top_performers) > 3:
            top_tier = top_performers[primary_metric].quantile(0.75)
            fig_ranking.add_hline(y=top_tier, line_dash="dot", line_color="#FFD700", 
                                 annotation_text="🥇 Top Tier")
        
        fig_ranking.update_traces(
            texttemplate='%{text:,.0f}',
            textposition='outside',
            textfont_size=11,
            marker_line_color='white',
            marker_line_width=1
        )
        
        fig_ranking = apply_standard_formatting(fig_ranking, f"🚀 Top Performers: {primary_metric.replace('_', ' ').title()}")
        fig_ranking.update_xaxis(tickangle=45)
        fig_ranking.update_layout(showlegend=False)
        
        charts.append(("🚀 Performance Ranking", fig_ranking))
    
    # 6. DISTRIBUTION INSIGHTS
    if len(numeric_cols) > 0:
        primary_col = numeric_cols[0]
        
        fig_dist = px.box(
            df,
            y=primary_col,
            title="📊 Distribution Analytics",
            color_discrete_sequence=['#667eea'],
            points="all"
        )
        
        # Add statistical annotations
        mean_val = df[primary_col].mean()
        median_val = df[primary_col].median()
        
        fig_dist.add_hline(y=mean_val, line_dash="dash", line_color="#e74c3c", 
                          annotation_text=f"Mean: {mean_val:,.0f}")
        fig_dist.add_hline(y=median_val, line_dash="solid", line_color="#27ae60", 
                          annotation_text=f"Median: {median_val:,.0f}")
        
        fig_dist.update_traces(
            marker=dict(size=6, opacity=0.6),
            boxpoints='outliers',
            fillcolor='rgba(102, 126, 234, 0.3)',
            line_color='#667eea'
        )
        
        fig_dist = apply_standard_formatting(fig_dist, f"📊 Distribution: {primary_col.replace('_', ' ').title()}", 450)
        
        charts.append(("📊 Distribution Analytics", fig_dist))
    
    return charts
