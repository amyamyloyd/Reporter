"""
Report Builder Utility for AutoGen Excel Intelligence System

This module handles report generation using pandas + duckdb for data logic
and supports HTML, XLSX, JSON, and chart formats as specified.

Key Functions:
- build_report() - Main function to build reports in various formats
- generate_html_report() - Generate HTML output with charts
- generate_xlsx_report() - Generate Excel output
- generate_json_report() - Generate JSON output
- create_chart() - Create charts using plotly/matplotlib
"""

import pandas as pd
import duckdb
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Configure logging for report operations
logger = logging.getLogger(__name__)

async def build_report(conn: duckdb.DuckDBPyConnection, table_name: str, 
                      report_config: Dict[str, Any], output_type: str) -> Dict[str, Any]:
    """
    Build report using filters + schema + data → return output in desired format
    
    This is the main function called by ReportAgent to assemble reports using
    pandas + duckdb for data logic and various libraries for rendering.
    
    Args:
        conn: DuckDB connection
        table_name: Name of the DuckDB table
        report_config: Report configuration from LLM interpretation
        output_type: Output format (html, xlsx, json)
        
    Returns:
        Dict[str, Any]: Report result with content and metadata
        
    Example:
        result = await build_report(
            conn, "hospital_ledger_fy2024_001", 
            {"sql": "SELECT * FROM table", "chart": "bar"},
            "html"
        )
    """
    try:
        # Extract SQL query from report configuration
        sql_query = report_config.get("sql", f"SELECT * FROM {table_name} LIMIT 1000")
        chart_type = report_config.get("chart", "")
        description = report_config.get("description", "Generated report")
        
        logger.info(f"Building report with SQL: {sql_query}")
        logger.info(f"Output type: {output_type}")
        
        # Execute SQL query to get data
        try:
            result = conn.execute(sql_query).fetchall()
            columns_result = conn.execute(sql_query).description
            
            # Extract column names
            columns = [col[0] for col in columns_result] if columns_result else []
            
            # Convert to pandas DataFrame for processing
            df = pd.DataFrame(result, columns=columns)
            
            logger.info(f"Query executed successfully: {len(df)} rows, {len(df.columns)} columns")
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise Exception(f"Failed to execute report query: {str(e)}")
        
        # Generate output based on type
        if output_type == "html":
            return await generate_html_report(df, report_config, description)
        elif output_type == "xlsx":
            return await generate_xlsx_report(df, report_config, description)
        elif output_type == "json":
            return await generate_json_report(df, report_config, description)
        else:
            # Default to HTML
            return await generate_html_report(df, report_config, description)
            
    except Exception as e:
        logger.error(f"Failed to build report: {e}")
        return None

async def generate_html_report(df: pd.DataFrame, report_config: Dict[str, Any], 
                             description: str) -> Dict[str, Any]:
    """
    Generate HTML report with optional charts
    
    Creates HTML output using jinja2 templates and plotly/matplotlib for charts.
    Supports table format and chart format as specified.
    
    Args:
        df: Pandas DataFrame with report data
        report_config: Report configuration
        description: Report description
        
    Returns:
        Dict[str, Any]: HTML content and metadata
    """
    try:
        chart_type = report_config.get("chart", "")
        
        # Generate basic HTML structure
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Report: {description}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ margin-bottom: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .chart-container {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Report: {description}</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Records: {len(df)}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>This report contains {len(df)} records with {len(df.columns)} columns.</p>
    </div>
"""
        
        # Add chart if specified
        if chart_type and len(df) > 0:
            chart_html = await create_chart(df, chart_type, description)
            if chart_html:
                html_content += f"""
    <div class="chart-container">
        <h2>Chart: {description}</h2>
        {chart_html}
    </div>
"""
        
        # Add data table
        html_content += f"""
    <div class="data-table">
        <h2>Data Table</h2>
        {df.to_html(index=False, classes='data-table', escape=False)}
    </div>
</body>
</html>
"""
        
        logger.info(f"Generated HTML report with {len(df)} rows")
        
        return {
            "html": html_content,
            "summary": f"Generated HTML report with {len(df)} records",
            "row_count": len(df),
            "column_count": len(df.columns)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate HTML report: {e}")
        return None

async def generate_xlsx_report(df: pd.DataFrame, report_config: Dict[str, Any], 
                             description: str) -> Dict[str, Any]:
    """
    Generate Excel report using openpyxl
    
    Creates XLSX output with proper formatting and multiple sheets if needed.
    Uses openpyxl for Excel generation as specified.
    
    Args:
        df: Pandas DataFrame with report data
        report_config: Report configuration
        description: Report description
        
    Returns:
        Dict[str, Any]: Download URL and filename
    """
    try:
        # Ensure reports directory exists
        os.makedirs("stored_queries/reports", exist_ok=True)
        
        # Generate filename using duckdb_table_name + timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Extract table name from the report config or use fallback
        table_name = report_config.get("table_name", "report")
        filename = f"{table_name}_{timestamp}.xlsx"
        filepath = f"stored_queries/reports/{filename}"
        
        # Create Excel file using pandas (which uses openpyxl)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Write main data sheet
            df.to_excel(writer, sheet_name='Report Data', index=False)
            
            # Add summary sheet
            summary_data = {
                'Metric': ['Total Records', 'Total Columns', 'Generated Date', 'Description'],
                'Value': [len(df), len(df.columns), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), description]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"Generated Excel report: {filename}")
        
        # Return download information
        return {
            "download_url": f"/reports/{filename}",
            "filename": filename,
            "filepath": filepath,
            "summary": f"Generated Excel report with {len(df)} records",
            "row_count": len(df),
            "column_count": len(df.columns)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate Excel report: {e}")
        return None

async def generate_json_report(df: pd.DataFrame, report_config: Dict[str, Any], 
                             description: str) -> Dict[str, Any]:
    """
    Generate JSON report output
    
    Creates JSON output with structured data and metadata.
    
    Args:
        df: Pandas DataFrame with report data
        report_config: Report configuration
        description: Report description
        
    Returns:
        Dict[str, Any]: JSON data and metadata
    """
    try:
        # Convert DataFrame to JSON
        data_json = df.to_dict('records')
        
        # Create structured JSON response
        json_data = {
            "report_info": {
                "description": description,
                "generated_date": datetime.now().isoformat(),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns)
            },
            "data": data_json,
            "summary": {
                "total_records": len(df),
                "columns": list(df.columns),
                "data_types": df.dtypes.to_dict()
            }
        }
        
        logger.info(f"Generated JSON report with {len(df)} records")
        
        return {
            "data": json_data,
            "summary": f"Generated JSON report with {len(df)} records",
            "row_count": len(df),
            "column_count": len(df.columns)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate JSON report: {e}")
        return None

async def create_chart(df: pd.DataFrame, chart_type: str, title: str) -> Optional[str]:
    """
    Create chart using plotly or matplotlib
    
    Generates charts based on the specified type (bar, line, pie, etc.)
    using plotly for interactive charts or matplotlib for static charts.
    
    Args:
        df: Pandas DataFrame with data
        chart_type: Type of chart (bar, line, pie, etc.)
        title: Chart title
        
    Returns:
        Optional[str]: HTML content for the chart or None if failed
    """
    try:
        if len(df) == 0:
            logger.warning("Cannot create chart - no data available")
            return None
        
        # Try to use plotly first (preferred for interactive charts)
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            from plotly.utils import PlotlyJSONEncoder
            
            # Determine chart type and create appropriate chart
            if chart_type.lower() == "bar":
                if len(df.columns) >= 2:
                    # Use first two columns for bar chart
                    fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=title)
                else:
                    # Single column - create count chart
                    value_counts = df.iloc[:, 0].value_counts()
                    fig = px.bar(x=value_counts.index, y=value_counts.values, title=title)
                    
            elif chart_type.lower() == "line":
                if len(df.columns) >= 2:
                    fig = px.line(df, x=df.columns[0], y=df.columns[1], title=title)
                else:
                    fig = px.line(y=df.iloc[:, 0], title=title)
                    
            elif chart_type.lower() == "pie":
                if len(df.columns) >= 2:
                    fig = px.pie(df, names=df.columns[0], values=df.columns[1], title=title)
                else:
                    value_counts = df.iloc[:, 0].value_counts()
                    fig = px.pie(values=value_counts.values, names=value_counts.index, title=title)
                    
            else:
                # Default to bar chart
                if len(df.columns) >= 2:
                    fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=title)
                else:
                    value_counts = df.iloc[:, 0].value_counts()
                    fig = px.bar(x=value_counts.index, y=value_counts.values, title=title)
            
            # Convert to HTML
            chart_html = fig.to_html(include_plotlyjs='cdn', div_id="chart")
            
            logger.info(f"Created {chart_type} chart using plotly")
            return chart_html
            
        except ImportError:
            logger.warning("Plotly not available, falling back to matplotlib")
            
        # Fallback to matplotlib
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import base64
            from io import BytesIO
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Determine chart type and create appropriate chart
            if chart_type.lower() == "bar":
                if len(df.columns) >= 2:
                    ax.bar(df.iloc[:, 0], df.iloc[:, 1])
                    ax.set_xlabel(df.columns[0])
                    ax.set_ylabel(df.columns[1])
                else:
                    value_counts = df.iloc[:, 0].value_counts()
                    ax.bar(value_counts.index, value_counts.values)
                    
            elif chart_type.lower() == "line":
                if len(df.columns) >= 2:
                    ax.plot(df.iloc[:, 0], df.iloc[:, 1])
                    ax.set_xlabel(df.columns[0])
                    ax.set_ylabel(df.columns[1])
                else:
                    ax.plot(df.iloc[:, 0])
                    
            elif chart_type.lower() == "pie":
                if len(df.columns) >= 2:
                    ax.pie(df.iloc[:, 1], labels=df.iloc[:, 0], autopct='%1.1f%%')
                else:
                    value_counts = df.iloc[:, 0].value_counts()
                    ax.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
                    
            else:
                # Default to bar chart
                if len(df.columns) >= 2:
                    ax.bar(df.iloc[:, 0], df.iloc[:, 1])
                    ax.set_xlabel(df.columns[0])
                    ax.set_ylabel(df.columns[1])
                else:
                    value_counts = df.iloc[:, 0].value_counts()
                    ax.bar(value_counts.index, value_counts.values)
            
            ax.set_title(title)
            plt.tight_layout()
            
            # Convert to base64 for HTML embedding
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            chart_html = f'<img src="data:image/png;base64,{image_base64}" alt="{title}" style="max-width: 100%; height: auto;">'
            
            logger.info(f"Created {chart_type} chart using matplotlib")
            return chart_html
            
        except ImportError:
            logger.error("Neither plotly nor matplotlib available for chart generation")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create chart: {e}")
        return None

def validate_report_config(report_config: Dict[str, Any]) -> bool:
    """
    Validate report configuration
    
    Ensures the report configuration has all required fields and valid values.
    
    Args:
        report_config: Report configuration to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check required fields
        required_fields = ["sql", "description"]
        for field in required_fields:
            if field not in report_config:
                logger.error(f"Missing required field in report config: {field}")
                return False
        
        # Validate SQL query
        sql_query = report_config.get("sql", "")
        if not sql_query or not sql_query.strip():
            logger.error("SQL query is empty or invalid")
            return False
        
        # Validate chart type if specified
        chart_type = report_config.get("chart", "")
        if chart_type and chart_type not in ["bar", "line", "pie", "scatter", "histogram"]:
            logger.warning(f"Unknown chart type: {chart_type}")
        
        logger.info("Report configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Report configuration validation failed: {e}")
        return False
