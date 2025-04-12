import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from google.adk.agents import LlmAgent, SequentialAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.sessions import InMemorySessionService, Session

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

class FinanceAdvisorSystem:
    def __init__(self):
        """Initialize the finance advisor system with specialized agents"""
        # Budget Analysis Agent
        self.budget_analysis_agent = LlmAgent(
            name="BudgetAnalysisAgent",
            model="gemini-2.0-flash-exp",
            description="Analyzes financial data to categorize spending patterns and recommend budget improvements",
            instruction="""You are a Budget Analysis Agent specialized in reviewing financial transactions and expenses.

Your tasks:
1. Analyze income, transactions, and expenses
2. Categorize spending into logical groups
3. Identify spending patterns and trends
4. Suggest specific areas where spending could be reduced
5. Provide actionable recommendations with potential savings amounts

Consider:
- Number of dependants when evaluating household expenses
- Typical spending ratios for the income level
- Essential vs discretionary spending
- Seasonal spending patterns if data spans multiple months""",
            output_key="budget_analysis"
        )
        
        # Savings Strategy Agent
        self.savings_strategy_agent = LlmAgent(
            name="SavingsStrategyAgent",
            model="gemini-2.0-flash-exp",
            description="Recommends optimal savings strategies based on income, expenses, and financial goals",
            instruction="""You are a Savings Strategy Agent specialized in creating personalized savings plans.

Your tasks:
1. Recommend savings strategies based on income and expenses
2. Calculate optimal emergency fund size based on expenses and dependants
3. Suggest appropriate savings allocation across different purposes
4. Recommend practical automation techniques for saving consistently

Consider:
- Risk factors based on job stability and dependants
- Balancing immediate needs with long-term financial health
- Progressive savings rates as discretionary income increases
- Multiple savings goals (emergency, retirement, specific purchases)""",
            output_key="savings_strategy"
        )
        
        # Debt Reduction Agent
        self.debt_reduction_agent = LlmAgent(
            name="DebtReductionAgent",
    model="gemini-2.0-flash-exp",
            description="Creates optimized debt payoff plans to minimize interest paid and time to debt freedom",
            instruction="""You are a Debt Reduction Agent specialized in creating debt payoff strategies.

Your tasks:
1. Analyze debts by interest rate, balance, and minimum payments
2. Create prioritized debt payoff plans (avalanche and snowball methods)
3. Calculate total interest paid and time to debt freedom for each approach
4. Suggest debt consolidation or refinancing opportunities when beneficial
5. Provide specific recommendations to accelerate debt payoff

Consider:
- Cash flow and budget constraints from the budget analysis
- Psychological factors (quick wins vs mathematical optimization)
- Interest savings potential
- Credit utilization and credit score impact""",
            output_key="debt_reduction"
        )
        
        # Coordinator Agent - Orchestrates the specialized agents
        self.coordinator_agent = SequentialAgent(
            name="FinanceCoordinatorAgent",
            description="Coordinates specialized finance agents to provide comprehensive financial advice",
            sub_agents=[
                self.budget_analysis_agent,
                self.savings_strategy_agent,
                self.debt_reduction_agent
            ]
        )
    
    async def analyze_finances(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process financial data through the agent system and return comprehensive analysis"""
        # Prepare the session context
        session = Session()
        
        # Store financial data in session state for agents to access
        session.state.update({
            "monthly_income": financial_data.get("monthly_income", 0),
            "dependants": financial_data.get("dependants", 0),
            "transactions": financial_data.get("transactions", []),
            "manual_expenses": financial_data.get("manual_expenses", {}),
            "debts": financial_data.get("debts", [])
        })
        
        # Preprocess transaction data if available
        if financial_data.get("transactions"):
            self._preprocess_transactions(session)
        
        # Initialize preprocessing for manual expenses if provided
        if financial_data.get("manual_expenses"):
            self._preprocess_manual_expenses(session)
        
        # Set up the invocation context
        context = InvocationContext(session=session, user_input="Analyze financial data")
        
        # Run the coordinator agent which will execute all sub-agents in sequence
        async for event in self.coordinator_agent.run(context):
            # We could process events here if needed
            pass
        
        # Collect results from session state
        results = {
            "budget_analysis": session.state.get("budget_analysis", {}),
            "savings_strategy": session.state.get("savings_strategy", {}),
            "debt_reduction": session.state.get("debt_reduction", {})
        }
        
        return results
    
    def _preprocess_transactions(self, session):
        """Preprocess transaction data for easier analysis by the agents"""
        transactions = session.state.get("transactions", [])
        
        if not transactions:
            return
        
        # Convert list of transactions to DataFrame for analysis
        df = pd.DataFrame(transactions)
        
        # Basic preprocessing
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month'] = df['Date'].dt.month
            df['Year'] = df['Date'].dt.year
        
        # Calculate spending by category
        if 'Category' in df.columns and 'Amount' in df.columns:
            category_spending = df.groupby('Category')['Amount'].sum().to_dict()
            session.state["category_spending"] = category_spending
            
            # Total spending
            total_spending = df['Amount'].sum()
            session.state["total_spending"] = total_spending
    
    def _preprocess_manual_expenses(self, session):
        """Process manually entered expenses"""
        manual_expenses = session.state.get("manual_expenses", {})
        
        if not manual_expenses:
            return
        
        # Calculate total spending from manual entries
        total_manual_spending = sum(manual_expenses.values())
        session.state["total_manual_spending"] = total_manual_spending
        
        # Store categorized spending directly
        session.state["manual_category_spending"] = manual_expenses

def display_budget_analysis(analysis: Dict[str, Any]):
    """Display budget analysis results"""
    # Display spending breakdown
    if "spending_categories" in analysis:
        st.subheader("Spending by Category")
        fig = px.pie(
            values=[cat["amount"] for cat in analysis["spending_categories"]],
            names=[cat["category"] for cat in analysis["spending_categories"]],
            title="Your Spending Breakdown"
        )
        st.plotly_chart(fig)
    
    # Display income vs expenses
    if "total_expenses" in analysis:
        st.subheader("Income vs. Expenses")
        income = analysis["monthly_income"]
        expenses = analysis["total_expenses"]
        surplus_deficit = income - expenses
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["Income", "Expenses"], 
                            y=[income, expenses],
                            marker_color=["green", "red"]))
        fig.update_layout(title="Monthly Income vs. Expenses")
        st.plotly_chart(fig)
        
        st.metric("Monthly Surplus/Deficit", 
                  f"${surplus_deficit:.2f}", 
                  delta=f"{surplus_deficit:.2f}")
    
    # Display spending reduction recommendations
    if "recommendations" in analysis:
        st.subheader("Spending Reduction Recommendations")
        for rec in analysis["recommendations"]:
            st.markdown(f"**{rec['category']}**: {rec['recommendation']}")
            if "potential_savings" in rec:
                st.metric(f"Potential Monthly Savings", f"${rec['potential_savings']:.2f}")

def display_savings_strategy(strategy: Dict[str, Any]):
    """Display savings strategy results"""
    st.subheader("Savings Recommendations")
    
    # Emergency Fund
    if "emergency_fund" in strategy:
        ef = strategy["emergency_fund"]
        st.markdown(f"### Emergency Fund")
        st.markdown(f"**Recommended Size**: ${ef['recommended_amount']:.2f}")
        st.markdown(f"**Current Status**: {ef['current_status']}")
        
        # Progress bar
        if "current_amount" in ef and "recommended_amount" in ef:
            progress = ef["current_amount"] / ef["recommended_amount"]
            st.progress(min(progress, 1.0))
            st.markdown(f"${ef['current_amount']:.2f} of ${ef['recommended_amount']:.2f}")
    
    # Savings Recommendations
    if "recommendations" in strategy:
        st.markdown("### Recommended Savings Allocations")
        for rec in strategy["recommendations"]:
            st.markdown(f"**{rec['category']}**: ${rec['amount']:.2f}/month")
            st.markdown(f"_{rec['rationale']}_")
    
    # Automation Techniques
    if "automation_techniques" in strategy:
        st.markdown("### Automation Techniques")
        for technique in strategy["automation_techniques"]:
            st.markdown(f"**{technique['name']}**: {technique['description']}")

def display_debt_reduction(plan: Dict[str, Any]):
    """Display debt reduction plan results"""
    # Total Debt Overview
    if "total_debt" in plan:
        st.metric("Total Debt", f"${plan['total_debt']:.2f}")
    
    # Debt Breakdown
    if "debts" in plan:
        st.subheader("Your Debts")
        debt_df = pd.DataFrame(plan["debts"])
        st.dataframe(debt_df)
        
        # Debt visualization
        fig = px.bar(debt_df, x="name", y="amount", color="interest_rate",
                    labels={"name": "Debt", "amount": "Amount ($)", "interest_rate": "Interest Rate (%)"},
                    title="Debt Breakdown")
        st.plotly_chart(fig)
    
    # Payoff Plans
    if "payoff_plans" in plan:
        st.subheader("Debt Payoff Plans")
        tabs = st.tabs(["Avalanche Method", "Snowball Method", "Comparison"])
        
        with tabs[0]:
            st.markdown("### Avalanche Method (Highest Interest First)")
            if "avalanche" in plan["payoff_plans"]:
                avalanche = plan["payoff_plans"]["avalanche"]
                st.markdown(f"**Total Interest Paid**: ${avalanche['total_interest']:.2f}")
                st.markdown(f"**Time to Debt Freedom**: {avalanche['months_to_payoff']} months")
                
                if "monthly_payment" in avalanche:
                    st.markdown(f"**Recommended Monthly Payment**: ${avalanche['monthly_payment']:.2f}")
                
                if "schedule" in avalanche:
                    st.markdown("#### Payoff Schedule")
                    schedule_df = pd.DataFrame(avalanche["schedule"])
                    st.dataframe(schedule_df)
        
        with tabs[1]:
            st.markdown("### Snowball Method (Smallest Balance First)")
            if "snowball" in plan["payoff_plans"]:
                snowball = plan["payoff_plans"]["snowball"]
                st.markdown(f"**Total Interest Paid**: ${snowball['total_interest']:.2f}")
                st.markdown(f"**Time to Debt Freedom**: {snowball['months_to_payoff']} months")
                
                if "monthly_payment" in snowball:
                    st.markdown(f"**Recommended Monthly Payment**: ${snowball['monthly_payment']:.2f}")
                
                if "schedule" in snowball:
                    st.markdown("#### Payoff Schedule")
                    schedule_df = pd.DataFrame(snowball["schedule"])
                    st.dataframe(schedule_df)
        
        with tabs[2]:
            st.markdown("### Method Comparison")
            if "avalanche" in plan["payoff_plans"] and "snowball" in plan["payoff_plans"]:
                avalanche = plan["payoff_plans"]["avalanche"]
                snowball = plan["payoff_plans"]["snowball"]
                
                comparison_data = {
                    "Method": ["Avalanche", "Snowball"],
                    "Total Interest": [avalanche["total_interest"], snowball["total_interest"]],
                    "Months to Payoff": [avalanche["months_to_payoff"], snowball["months_to_payoff"]]
                }
                comparison_df = pd.DataFrame(comparison_data)
                
                st.dataframe(comparison_df)
                
                fig = go.Figure(data=[
                    go.Bar(name="Total Interest", x=comparison_df["Method"], y=comparison_df["Total Interest"]),
                    go.Bar(name="Months to Payoff", x=comparison_df["Method"], y=comparison_df["Months to Payoff"])
                ])
                fig.update_layout(barmode='group', title="Debt Payoff Method Comparison")
                st.plotly_chart(fig)
    
    # Recommendations
    if "recommendations" in plan:
        st.subheader("Debt Reduction Recommendations")
        for rec in plan["recommendations"]:
            st.markdown(f"**{rec['title']}**: {rec['description']}")
            if "impact" in rec:
                st.markdown(f"_Impact: {rec['impact']}_")

def main():
    st.set_page_config(page_title="AI Personal Finance Coach", layout="wide")
    
    # Check if we have the API key
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("""
        GOOGLE_API_KEY not found in environment variables.
        Please create a .env file with your Google API key:
        ```
        GOOGLE_API_KEY=your_api_key_here
        ```
        """)
        return
    
    st.title("AI Personal Finance Coach")
    st.subheader("Get personalized financial advice from AI agents")
    
    # Sidebar for user inputs
    with st.sidebar:
        st.header("Your Financial Information")
        
        # Monthly Income
        monthly_income = st.number_input("Monthly Income ($)", min_value=0.0, step=100.0, value=3000.0)
        
        # Number of Dependants
        dependants = st.number_input("Number of Dependants", min_value=0, step=1, value=0)
        
        # Transaction data upload
        st.subheader("Upload Transaction Data")
        st.write("Upload a CSV with columns: Date, Category, Amount")
        transaction_file = st.file_uploader("Upload CSV of transactions", type=["csv"])
        
        # Manual expense entry option
        st.subheader("Or Enter Expenses Manually")
        use_manual_expenses = st.checkbox("Enter expenses manually")
        
        manual_expenses = {}
        if use_manual_expenses:
            categories = ["Housing", "Utilities", "Food", "Transportation", "Healthcare", 
                          "Entertainment", "Personal", "Savings", "Other"]
            for category in categories:
                manual_expenses[category] = st.number_input(f"{category} ($)", min_value=0.0, step=50.0, value=0.0)
        
        # Debt Information
        st.subheader("Debt Information")
        num_debts = st.number_input("Number of Debts", min_value=0, max_value=10, step=1, value=0)
        
        debts = []
        for i in range(num_debts):
            st.markdown(f"**Debt #{i+1}**")
            debt_name = st.text_input(f"Debt Name #{i+1}", value=f"Debt {i+1}")
            debt_amount = st.number_input(f"Amount ${i+1}", min_value=0.0, step=100.0, value=1000.0)
            interest_rate = st.number_input(f"Interest Rate (%) #{i+1}", min_value=0.0, max_value=100.0, step=0.1, value=5.0)
            min_payment = st.number_input(f"Minimum Monthly Payment #{i+1}", min_value=0.0, step=10.0, value=50.0)
            
            debts.append({
                "name": debt_name,
                "amount": debt_amount,
                "interest_rate": interest_rate,
                "min_payment": min_payment
            })
        
        analyze_button = st.button("Analyze My Finances")
    
    # Main content area
    transactions_df = None
    if transaction_file is not None:
        transactions_df = pd.read_csv(transaction_file)
        st.subheader("Your Transaction Data")
        st.dataframe(transactions_df)
    
    if use_manual_expenses and manual_expenses:
        st.subheader("Your Manual Expenses")
        manual_df = pd.DataFrame({
            'Category': list(manual_expenses.keys()),
            'Amount': list(manual_expenses.values())
        })
        st.dataframe(manual_df)
    
    # Prepare data for agent analysis
    financial_data = {
        "monthly_income": monthly_income,
        "dependants": dependants,
        "transactions": transactions_df.to_dict('records') if transactions_df is not None else None,
        "manual_expenses": manual_expenses if use_manual_expenses else None,
        "debts": debts
    }
    
    # When analyze button is clicked, run agent analysis
    if analyze_button:
        with st.spinner("AI agents are analyzing your financial data..."):
            # Create finance advisor system
            finance_system = FinanceAdvisorSystem()
            
            # Run analysis
            results = asyncio.run(finance_system.analyze_finances(financial_data))
        
        # Display results in tabs
        tabs = st.tabs(["Budget Analysis", "Savings Strategy", "Debt Reduction"])
        
        with tabs[0]:
            st.subheader("Budget Analysis")
            if "budget_analysis" in results:
                display_budget_analysis(results["budget_analysis"])
            else:
                st.write("No budget analysis available.")
        
        with tabs[1]:
            st.subheader("Savings Strategy")
            if "savings_strategy" in results:
                display_savings_strategy(results["savings_strategy"])
            else:
                st.write("No savings strategy available.")
        
        with tabs[2]:
            st.subheader("Debt Reduction Plan")
            if "debt_reduction" in results:
                display_debt_reduction(results["debt_reduction"])
            else:
                st.write("No debt reduction plan available.")

if __name__ == "__main__":
    main()