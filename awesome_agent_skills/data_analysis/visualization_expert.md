---
name: visualization-expert
description: Creates effective data visualizations and dashboards with best practices for clarity.
---

# Visualization Expert Skill

## When to use this skill

Use this skill when you need:
- Chart type recommendations
- Dashboard design
- Visualization code (matplotlib, plotly, etc.)
- Data storytelling
- Accessibility-friendly visuals

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are a data visualization expert who creates clear, impactful charts.

Chart Selection Guide:
- Comparison: Bar chart, grouped bar
- Trend over time: Line chart, area chart
- Part of whole: Pie chart (≤5 categories), stacked bar
- Distribution: Histogram, box plot
- Relationship: Scatter plot, bubble chart
- Geographic: Choropleth map

Design Principles:
- Data-ink ratio: Remove non-essential elements
- Color: Use meaningfully, consider colorblind users
- Labels: Direct label when possible, avoid legends
- Order: Sort by value, not alphabetically
- Context: Include comparisons or benchmarks

Common Mistakes to Avoid:
- 3D charts (distort perception)
- Dual y-axes (confusing)
- Too many categories (>7)
- Truncated y-axes (misleading)
- Pie charts for comparison"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Visualize monthly revenue trends"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| data | string | What data you're visualizing |
| question | string | What insight to highlight |
| tool | string | (Optional) "matplotlib", "plotly", "seaborn" |
| style | string | (Optional) "minimal", "detailed", "presentation" |

### Returns

- Recommended chart type with rationale
- Complete visualization code
- Customization options
- Accessibility considerations
- Alternative approaches

## Example

**Input:**
```
Data: Monthly sales by product category (Jan-Dec)
Question: Show growth trends and compare categories
Tool: matplotlib
```

**Output:**
```markdown
## Recommendation: Multi-line Chart with Annotations

**Why:** Shows trends over time while allowing category comparison. Annotations highlight key insights.

### Code

```python
import matplotlib.pyplot as plt
import pandas as pd

# Sample data
data = {
    'Month': pd.date_range('2024-01', periods=12, freq='M'),
    'Electronics': [45, 52, 48, 61, 58, 72, 78, 85, 82, 95, 110, 125],
    'Clothing': [30, 28, 35, 42, 55, 58, 62, 60, 58, 65, 72, 80],
    'Home': [20, 22, 25, 24, 28, 30, 32, 35, 38, 42, 45, 50]
}
df = pd.DataFrame(data)

# Create figure
fig, ax = plt.subplots(figsize=(12, 6))

# Plot lines
colors = {'Electronics': '#2563eb', 'Clothing': '#059669', 'Home': '#d97706'}
for category in ['Electronics', 'Clothing', 'Home']:
    ax.plot(df['Month'], df[category], 
            label=category, color=colors[category], 
            linewidth=2.5, marker='o', markersize=4)

# Direct labels (better than legend)
for category, color in colors.items():
    y_end = df[category].iloc[-1]
    ax.annotate(f'{category}\n${y_end}K', 
                xy=(df['Month'].iloc[-1], y_end),
                xytext=(10, 0), textcoords='offset points',
                fontsize=10, color=color, fontweight='bold',
                va='center')

# Formatting
ax.set_title('Monthly Sales by Category (2024)', fontsize=16, fontweight='bold', pad=20)
ax.set_ylabel('Sales ($K)', fontsize=12)
ax.set_xlabel('')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.yaxis.grid(True, linestyle='--', alpha=0.3)
ax.set_ylim(0, None)

# Add annotation for key insight
ax.annotate('Electronics +178% YoY', 
            xy=(df['Month'].iloc[6], 78),
            xytext=(df['Month'].iloc[3], 100),
            fontsize=10,
            arrowprops=dict(arrowstyle='->', color='gray'),
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('sales_trends.png', dpi=150, bbox_inches='tight')
plt.show()
```

### Design Choices

| Element | Choice | Rationale |
|---------|--------|-----------|
| Chart type | Line | Best for trends over time |
| Direct labels | Yes | Easier to read than legend |
| Y-axis start | Zero | Honest representation |
| Grid | Horizontal only | Aids value reading |
| Colors | Distinct hues | Colorblind-friendly |

### Alternatives

- **Small multiples:** If comparing shape of trends rather than absolute values
- **Area chart:** If emphasizing total volume
- **Bar chart:** If focusing on specific months, not trend
```
