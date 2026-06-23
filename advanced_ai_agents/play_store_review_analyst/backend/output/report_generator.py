import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates trend analysis reports in various formats"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_markdown_report(self, trend_analysis: Dict[str, Any], 
                                app_name: str, target_date: str = None) -> str:
        """
        Generate markdown report with frequency table.
        
        Args:
            trend_analysis: Dict with frequency_table and insights
            app_name: Name of the app
            target_date: Target date (YYYY-MM-DD)
            
        Returns:
            Path to generated report
        """
        try:
            if not target_date:
                target_date = datetime.now().strftime("%Y-%m-%d")
            
            filename = self.output_dir / f"{app_name}_report_{target_date}.md"
            
            with open(filename, "w", encoding="utf-8") as f:
                # Header
                f.write(f"# Trend Analysis Report\n\n")
                f.write(f"**App:** {app_name}\n\n")
                f.write(f"**Analysis Date:** {target_date}\n\n")
                f.write(f"**Window:** {trend_analysis.get('window_days', 30)} days\n\n")
                
                # Frequency table
                freq_table = trend_analysis.get("frequency_table", {})
                if freq_table:
                    f.write("## Frequency Table\n\n")
                    f.write(self._generate_markdown_table(freq_table))
                    f.write("\n")
                
                # Metadata
                f.write("---\n\n")
                f.write(f"*Report generated: {datetime.now().isoformat()}*\n")
            
            logger.info(f"Generated markdown report: {filename}")
            return filename.name  # Return just the filename, not the full path
            
        except Exception as e:
            logger.error(f"Error generating markdown report: {str(e)}")
            raise
    
    def _generate_markdown_table(self, freq_table: Dict[str, Dict[str, int]]) -> str:
        """Generate markdown table from frequency table"""
        try:
            if not freq_table:
                return ""
            
            # Get dates
            all_dates = []
            for category_dates in freq_table.values():
                all_dates.extend(category_dates.keys())
            
            dates = sorted(list(set(all_dates)))
            
            if not dates:
                return ""
            
            # Header
            table = "| Topic | " + " | ".join(dates) + " |\n"
            table += "|" + "|".join([":---:"] * (len(dates) + 1)) + "|\n"
            
            # Rows
            for topic, date_freq in sorted(freq_table.items()):
                row = f"| {topic} |"
                for date in dates:
                    count = date_freq.get(date, 0)
                    row += f" {count} |"
                table += row + "\n"
            
            return table
            
        except Exception as e:
            logger.error(f"Error generating table: {str(e)}")
            return ""
    
    def generate_html_report(self, trend_analysis: Dict[str, Any],
                        app_name: str, target_date: str = None) -> str:
        """Generate enhanced HTML report with charts and insights"""
        try:
            if not target_date:
                target_date = datetime.now().strftime("%Y-%m-%d")
            
            filename = self.output_dir / f"{app_name}_report_{target_date}.html"
            
            freq_table = trend_analysis.get("frequency_table", {})
            insights = trend_analysis.get("insights", {})
            severity_scores = trend_analysis.get("severity_scores", {})
            recommendations = trend_analysis.get("actionable_recommendations", [])
            
            # Get dates for chart
            all_dates = []
            for category_dates in freq_table.values():
                all_dates.extend(category_dates.keys())
            dates = sorted(list(set(all_dates)))
            
            # Prepare chart data (top 5 topics only)
            top_topics = insights.get("top_topics", [])[:5]
            chart_data = {
                "dates": dates,
                "datasets": []
            }
            
            colors = [
                "rgb(255, 99, 132)",
                "rgb(54, 162, 235)",
                "rgb(255, 206, 86)",
                "rgb(75, 192, 192)",
                "rgb(153, 102, 255)"
            ]
            
            for idx, topic in enumerate(top_topics):
                if topic in freq_table:
                    data = [freq_table[topic].get(d, 0) for d in dates]
                    chart_data["datasets"].append({
                        "label": topic,
                        "data": data,
                        "borderColor": colors[idx % len(colors)],
                        "backgroundColor": colors[idx % len(colors)].replace("rgb", "rgba").replace(")", ", 0.1)"),
                        "tension": 0.4
                    })
            
            html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trend Analysis Report - {app_name}</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
            }}
            
            .header p {{
                font-size: 1.1rem;
                opacity: 0.95;
            }}
            
            .content {{
                padding: 40px;
            }}
            
            .section {{
                margin-bottom: 40px;
            }}
            
            .section-title {{
                font-size: 1.8rem;
                color: #333;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #667eea;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .stat-card {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }}
            
            .stat-card h3 {{
                font-size: 0.9rem;
                color: #666;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .stat-card .value {{
                font-size: 2.2rem;
                font-weight: bold;
                color: #667eea;
            }}
            
            .recommendations {{
                background: #fff9e6;
                border-left: 5px solid #ffc107;
                padding: 25px;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
            
            .recommendation-item {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                border-left: 4px solid #ddd;
            }}
            
            .recommendation-item.critical {{
                border-left-color: #dc3545;
            }}
            
            .recommendation-item.high {{
                border-left-color: #ff6b6b;
            }}
            
            .recommendation-item.medium {{
                border-left-color: #ffc107;
            }}
            
            .recommendation-item.low {{
                border-left-color: #28a745;
            }}
            
            .rec-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }}
            
            .rec-title {{
                font-size: 1.2rem;
                font-weight: 600;
                color: #333;
            }}
            
            .rec-badge {{
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
            }}
            
            .rec-badge.critical {{
                background: #dc3545;
                color: white;
            }}
            
            .rec-badge.high {{
                background: #ff6b6b;
                color: white;
            }}
            
            .rec-badge.medium {{
                background: #ffc107;
                color: #333;
            }}
            
            .rec-badge.low {{
                background: #28a745;
                color: white;
            }}
            
            .rec-details {{
                color: #666;
                margin-top: 10px;
                line-height: 1.6;
            }}
            
            .chart-container {{
                position: relative;
                height: 400px;
                margin: 30px 0;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }}
            
            .table-container {{
                overflow-x: auto;
                margin-top: 30px;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                border-radius: 10px;
                overflow: hidden;
            }}
            
            thead {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            
            th {{
                padding: 15px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 0.85rem;
                letter-spacing: 0.5px;
            }}
            
            td {{
                padding: 12px 15px;
                border-bottom: 1px solid #f0f0f0;
            }}
            
            tbody tr:hover {{
                background: #f8f9fa;
            }}
            
            .severity-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
            }}
            
            .severity-critical {{
                background: #dc3545;
                color: white;
            }}
            
            .severity-high {{
                background: #ff6b6b;
                color: white;
            }}
            
            .severity-medium {{
                background: #ffc107;
                color: #333;
            }}
            
            .severity-low {{
                background: #28a745;
                color: white;
            }}
            
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 0.9rem;
            }}
            
            @media print {{
                body {{
                    background: white;
                }}
                .container {{
                    box-shadow: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Trend Analysis Report</h1>
                <p><strong>{app_name}</strong> | Analysis Date: {target_date}</p>
            </div>
            
            <div class="content">
                <!-- Executive Summary -->
                <div class="section">
                    <h2 class="section-title">Executive Summary</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Total Topics</h3>
                            <div class="value">{len(freq_table)}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Analysis Window</h3>
                            <div class="value">{trend_analysis.get('window_days', 30)} Days</div>
                        </div>
                        <div class="stat-card">
                            <h3>Top Issue</h3>
                            <div class="value" style="font-size: 1.2rem;">{insights.get('top_topics', ['N/A'])[0] if insights.get('top_topics') else 'N/A'}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Trending Up</h3>
                            <div class="value">{len(insights.get('trending_up', []))}</div>
                        </div>
                    </div>
                </div>
                
                <!-- Actionable Recommendations -->
                <div class="section">
                    <h2 class="section-title">🎯 Actionable Recommendations</h2>
                    <div class="recommendations">
    """
            
            # Add recommendations
            if recommendations:
                for rec in recommendations:
                    classification = rec['classification'].lower()
                    html += f"""
                        <div class="recommendation-item {classification}">
                            <div class="rec-header">
                                <div class="rec-title">{rec['topic']}</div>
                                <span class="rec-badge {classification}">{rec['classification']}</span>
                            </div>
                            <div class="rec-details">
                                <strong>{rec['action']}</strong><br>
                                {rec['details']}<br>
                                Severity Score: {rec['severity_score']}/100
                            </div>
                        </div>
    """
            else:
                html += "<p>No recommendations available.</p>"
            
            html += """
                    </div>
                </div>
                
                <!-- Trend Chart -->
                <div class="section">
                    <h2 class="section-title">📈 Trend Visualization (Top 5 Topics)</h2>
                    <div class="chart-container">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>
                
                <!-- Detailed Table -->
                <div class="section">
                    <h2 class="section-title">📋 Detailed Breakdown</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Topic</th>
                                    <th>Severity</th>
                                    <th>Total Reviews</th>
                                    <th>Avg Rating</th>
                                    <th>Classification</th>
                                </tr>
                            </thead>
                            <tbody>
    """
            
            # Add severity table rows
            sorted_severity = sorted(
                severity_scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )
            
            for topic, severity_data in sorted_severity:
                classification = severity_data['classification'].lower()
                html += f"""
                                <tr>
                                    <td><strong>{topic}</strong></td>
                                    <td>{severity_data['score']}/100</td>
                                    <td>{severity_data['total_reviews']}</td>
                                    <td>{severity_data['avg_rating']}★</td>
                                    <td><span class="severity-badge severity-{classification}">{severity_data['classification']}</span></td>
                                </tr>
    """
            
            html += f"""
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Analysis window: {trend_analysis.get('window_days', 30)} days</p>
            </div>
        </div>
        
        <script>
            const chartData = {json.dumps(chart_data)};
            
            const ctx = document.getElementById('trendChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: chartData.dates,
                    datasets: chartData.datasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'bottom'
                        }},
                        title: {{
                            display: true,
                            text: 'Review Frequency Over Time'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Number of Reviews'
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Date'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.info(f"Generated enhanced HTML report: {filename}")
            return filename.name
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            raise