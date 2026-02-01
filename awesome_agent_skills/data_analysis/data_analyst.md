---
name: data-analyst
description: Analyzes data, writes SQL queries, and generates insights from datasets.
---

# Data Analyst Skill

## When to use this skill

Use this skill when you need:
- SQL query writing and optimization
- Data exploration with pandas
- Statistical analysis
- Insight generation from datasets
- Data cleaning and transformation

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an expert data analyst skilled in SQL, Python, and statistical analysis.

Analysis Process:
1. Understand the business question
2. Explore the data structure
3. Clean and prepare data
4. Perform analysis
5. Generate actionable insights

SQL Best Practices:
- Use CTEs for readability
- Always include comments
- Handle NULLs explicitly
- Use appropriate JOINs
- Consider query performance

Pandas Best Practices:
- Use vectorized operations
- Chain methods for readability
- Handle missing values early
- Document transformations

Insight Guidelines:
- Lead with the "so what"
- Quantify findings
- Note limitations
- Suggest next steps"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Analyze our customer churn data"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| question | string | Business question to answer |
| data | string | Dataset description or schema |
| tool | string | (Optional) "sql", "pandas", "both" |
| depth | string | (Optional) "quick", "detailed" |

### Returns

- SQL queries or Python code
- Analysis results interpretation
- Visualizations recommendations
- Key insights and patterns
- Recommended actions

## Example

**Input:**
```
Question: Which customers are at risk of churning?
Tables: customers (id, signup_date, plan), events (customer_id, event_type, timestamp)
```

**Output:**
```markdown
## Churn Risk Analysis

### Approach
Identify customers with declining engagement patterns over the last 30 days.

### SQL Query

```sql
-- Calculate engagement metrics per customer
WITH customer_activity AS (
    SELECT 
        c.id,
        c.plan,
        c.signup_date,
        COUNT(e.event_type) as total_events,
        COUNT(CASE WHEN e.timestamp > NOW() - INTERVAL '7 days' 
              THEN 1 END) as events_last_7d,
        COUNT(CASE WHEN e.timestamp > NOW() - INTERVAL '30 days' 
              THEN 1 END) as events_last_30d,
        MAX(e.timestamp) as last_active
    FROM customers c
    LEFT JOIN events e ON c.id = e.customer_id
    WHERE e.timestamp > NOW() - INTERVAL '90 days'
    GROUP BY c.id, c.plan, c.signup_date
),

-- Calculate engagement trend
engagement_trend AS (
    SELECT 
        *,
        events_last_7d::float / NULLIF(events_last_30d, 0) * 4 as weekly_trend,
        NOW() - last_active as days_since_active
    FROM customer_activity
)

-- Flag at-risk customers
SELECT 
    id,
    plan,
    total_events,
    events_last_7d,
    days_since_active,
    CASE 
        WHEN days_since_active > INTERVAL '14 days' THEN 'High Risk'
        WHEN weekly_trend < 0.5 THEN 'Medium Risk'
        WHEN events_last_7d < 3 THEN 'Low Risk'
        ELSE 'Active'
    END as churn_risk
FROM engagement_trend
WHERE days_since_active > INTERVAL '7 days'
   OR weekly_trend < 0.75
ORDER BY 
    CASE churn_risk
        WHEN 'High Risk' THEN 1
        WHEN 'Medium Risk' THEN 2
        ELSE 3
    END;
```

### Key Insights

1. **High Risk Indicators:**
   - No activity in 14+ days
   - Declining weekly engagement (>50% drop)
   - Low event count on paid plans

2. **Recommended Actions:**
   - Trigger re-engagement email for 14+ day inactive
   - Offer support call to declining premium users
   - Implement in-app prompts after 7 days inactive

### Next Analysis
- Correlation between plan type and churn rate
- Feature usage patterns before churn
- Cohort analysis by signup month
```
