import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import json
import logging
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent, SequentialAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for session management
APP_NAME = "finance_advisor"
USER_ID = "default_user"

# Define Pydantic models for output schemas
class SpendingCategory(BaseModel):
    category: str = Field(..., description="Expense category name")
    amount: float = Field(..., description="Amount spent in this category")
    percentage: Optional[float] = Field(None, description="Percentage of total spending")

class SpendingRecommendation(BaseModel):
    category: str = Field(..., description="Category for recommendation")
    recommendation: str = Field(..., description="Recommendation details")
    potential_savings: Optional[float] = Field(None, description="Estimated monthly savings")

class BudgetAnalysis(BaseModel):
    total_expenses: float = Field(..., description="Total monthly expenses")
    monthly_income: Optional[float] = Field(None, description="Monthly income")
    spending_categories: List[SpendingCategory] = Field(..., description="Breakdown of spending by category")
    recommendations: List[SpendingRecommendation] = Field(..., description="Spending recommendations")

class EmergencyFund(BaseModel):
    recommended_amount: float = Field(..., description="Recommended emergency fund size")
    current_amount: Optional[float] = Field(None, description="Current emergency fund (if any)")
    current_status: str = Field(..., description="Status assessment of emergency fund")

class SavingsRecommendation(BaseModel):
    category: str = Field(..., description="Savings category")
    amount: float = Field(..., description="Recommended monthly amount")
    rationale: Optional[str] = Field(None, description="Explanation for this recommendation")

class AutomationTechnique(BaseModel):
    name: str = Field(..., description="Name of automation technique")
    description: str = Field(..., description="Details of how to implement")

class SavingsStrategy(BaseModel):
    emergency_fund: EmergencyFund = Field(..., description="Emergency fund recommendation")
    recommendations: List[SavingsRecommendation] = Field(..., description="Savings allocation recommendations")
    automation_techniques: Optional[List[AutomationTechnique]] = Field(None, description="Automation techniques to help save")

class Debt(BaseModel):
    name: str = Field(..., description="Name of debt")
    amount: float = Field(..., description="Current balance")
    interest_rate: float = Field(..., description="Annual interest rate (%)")
    min_payment: Optional[float] = Field(None, description="Minimum monthly payment")

class PayoffPlan(BaseModel):
    total_interest: float = Field(..., description="Total interest paid")
    months_to_payoff: int = Field(..., description="Months until debt-free")
    monthly_payment: Optional[float] = Field(None, description="Recommended monthly payment")

class PayoffPlans(BaseModel):
    avalanche: PayoffPlan = Field(..., description="Highest interest first method")
    snowball: PayoffPlan = Field(..., description="Smallest balance first method")

class DebtRecommendation(BaseModel):
    title: str = Field(..., description="Title of recommendation")
    description: str = Field(..., description="Details of recommendation")
    impact: Optional[str] = Field(None, description="Expected impact of this action")

class DebtReduction(BaseModel):
    total_debt: float = Field(..., description="Total debt amount")
    debts: List[Debt] = Field(..., description="List of all debts")
    payoff_plans: PayoffPlans = Field(..., description="Debt payoff strategies")
    recommendations: Optional[List[DebtRecommendation]] = Field(None, description="Recommendations for debt reduction")

# Load environment variables
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

class FinanceAdvisorSystem:
    """Main class to manage finance advisor agents"""
    
    def __init__(self):
        """Initialize the finance advisor system with specialized agents"""
        # Initialize session service
        self.session_service = InMemorySessionService()
        
        # Budget Analysis Agent
        self.budget_analysis_agent = LlmAgent(
            name="BudgetAnalysisAgent",
            model="gemini-2.0-flash-exp",
            description="Analyzes financial data to categorize spending patterns and recommend budget improvements",
            instruction="""You are a Budget Analysis Agent specialized in reviewing financial transactions and expenses.
You are the first agent in a sequence of three financial advisor agents.

Your tasks:
1. Analyze income, transactions, and expenses in detail
2. Categorize spending into logical groups with clear breakdown
3. Identify spending patterns and trends across categories
4. Suggest specific areas where spending could be reduced with concrete suggestions
5. Provide actionable recommendations with specific, quantified potential savings amounts

Consider:
- Number of dependants when evaluating household expenses
- Typical spending ratios for the income level (housing 30%, food 15%, etc.)
- Essential vs discretionary spending with clear separation
- Seasonal spending patterns if data spans multiple months

For spending categories, include ALL expenses from the user's data, ensure percentages add up to 100%,
and make sure every expense is categorized.

For recommendations:
- Provide at least 3-5 specific, actionable recommendations with estimated savings
- Explain the reasoning behind each recommendation
- Consider the impact on quality of life and long-term financial health
- Suggest specific implementation steps for each recommendation

IMPORTANT: Store your analysis in state['budget_analysis'] for use by subsequent agents.""",
            output_schema=BudgetAnalysis,
            output_key="budget_analysis"
        )
        
        # Savings Strategy Agent
        self.savings_strategy_agent = LlmAgent(
            name="SavingsStrategyAgent",
            model="gemini-2.0-flash-exp",
            description="Recommends optimal savings strategies based on income, expenses, and financial goals",
            instruction="""You are a Savings Strategy Agent specialized in creating personalized savings plans.
You are the second agent in the sequence. READ the budget analysis from state['budget_analysis'] first.

Your tasks:
1. Review the budget analysis results from state['budget_analysis']
2. Recommend comprehensive savings strategies based on the analysis
3. Calculate optimal emergency fund size based on expenses and dependants
4. Suggest appropriate savings allocation across different purposes
5. Recommend practical automation techniques for saving consistently

Consider:
- Risk factors based on job stability and dependants
- Balancing immediate needs with long-term financial health
- Progressive savings rates as discretionary income increases
- Multiple savings goals (emergency, retirement, specific purchases)
- Areas of potential savings identified in the budget analysis

IMPORTANT: Store your strategy in state['savings_strategy'] for use by the Debt Reduction Agent.""",
            output_schema=SavingsStrategy,
            output_key="savings_strategy"
        )
        
        # Debt Reduction Agent
        self.debt_reduction_agent = LlmAgent(
            name="DebtReductionAgent",
            model="gemini-2.0-flash-exp",
            description="Creates optimized debt payoff plans to minimize interest paid and time to debt freedom",
            instruction="""You are a Debt Reduction Agent specialized in creating debt payoff strategies.
You are the final agent in the sequence. READ both state['budget_analysis'] and state['savings_strategy'] first.

Your tasks:
1. Review both budget analysis and savings strategy from the state
2. Analyze debts by interest rate, balance, and minimum payments
3. Create prioritized debt payoff plans (avalanche and snowball methods)
4. Calculate total interest paid and time to debt freedom
5. Suggest debt consolidation or refinancing opportunities
6. Provide specific recommendations to accelerate debt payoff

Consider:
- Cash flow constraints from the budget analysis
- Emergency fund and savings goals from the savings strategy
- Psychological factors (quick wins vs mathematical optimization)
- Credit score impact and improvement opportunities

IMPORTANT: Store your final plan in state['debt_reduction'] and ensure it aligns with the previous analyses.""",
            output_schema=DebtReduction,
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
        
        # Add debug callbacks to monitor agent behavior and state flow
        self._add_debug_callbacks()
        
        # Create a runner for the coordinator agent
        self.runner = Runner(
            agent=self.coordinator_agent,
            app_name=APP_NAME,
            session_service=self.session_service
        )
    
    def _add_debug_callbacks(self):
        """Add debug callbacks to agents to track execution and state flow"""
        logger.info("=== Registering Callbacks ===")
        for agent in [self.budget_analysis_agent, self.savings_strategy_agent, self.debt_reduction_agent]:
            logger.info(f"Adding callbacks to agent: {agent.name}")
            agent.before_model_callback = self._simple_before_model_callback
            agent.after_model_callback = self._simple_after_model_callback
            # Verify callback registration
            logger.info(f"Callbacks registered - Before: {agent.before_model_callback.__name__}, After: {agent.after_model_callback.__name__}")
    
    def _simple_before_model_callback(self, callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
        """Simple debug callback before model call"""
        agent_name = callback_context.agent_name
        logger.info(f"=== Before Model Callback ({agent_name}) ===")
        # Log arguments excluding 'self'
        args_log = {k: v for k, v in locals().items() if k != 'self'}
        logger.info(f"({agent_name}) Callback args: {args_log}")
        logger.info(f"({agent_name}) Callback context type: {type(callback_context)}")
        logger.info(f"({agent_name}) LLM request type: {type(llm_request)}")
        if hasattr(callback_context, 'state'):
            logger.info(f"({agent_name}) Current state available")
        return None
    
    def _simple_after_model_callback(self, callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
        """Simple debug callback after model call"""
        agent_name = callback_context.agent_name
        logger.info(f"=== After Model Callback ({agent_name}) ===")
        # Log arguments excluding 'self'
        args_log = {k: v for k, v in locals().items() if k != 'self'}
        logger.info(f"({agent_name}) Callback args: {args_log}") 
        logger.info(f"({agent_name}) Callback context type: {type(callback_context)}")
        logger.info(f"({agent_name}) LLM response type: {type(llm_response)}")
        # llm_request is not expected here based on the error
        if hasattr(callback_context, 'state'):
            logger.info(f"({agent_name}) Updated state available")
        return None
    
    async def analyze_finances(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process financial data through the agent system and return comprehensive analysis"""
        session_id = f"finance_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting finance analysis with session_id: {session_id}")
        
        try:
            # Create a new session with required parameters
            initial_state = {
                "monthly_income": financial_data.get("monthly_income", 0),
                "dependants": financial_data.get("dependants", 0),
                "transactions": financial_data.get("transactions", []),
                "manual_expenses": financial_data.get("manual_expenses", {}),
                "debts": financial_data.get("debts", [])
            }
            
            session = self.session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
                state=initial_state
            )
            
            # Log initial state
            logger.info(f"Created session with initial state items: {list(initial_state.keys())}")
            
            # Preprocess transaction data if available
            transactions = session.state.get("transactions")
            if transactions:
                self._preprocess_transactions(session)
            
            # Initialize preprocessing for manual expenses if provided
            manual_expenses = session.state.get("manual_expenses")
            if manual_expenses:
                self._preprocess_manual_expenses(session)
            
            # Create default results
            default_results = self._create_default_results(financial_data)
            
            # Create user message content
            user_content = types.Content(
                role='user',
                parts=[types.Part(text=json.dumps(financial_data))]
            )
            
            logger.info("Running coordinator agent")
            
            # Run the analysis through the coordinator agent
            event_count = 0
            current_agent = None
            async for event in self.runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=user_content
            ):
                event_count += 1
                # --- DETAILED EVENT LOGGING --- 
                logger.info(f"-- RAW EVENT {event_count} START --")
                logger.info(f"Event Author: {event.author}")
                logger.info(f"Event ID: {event.id}")
                logger.info(f"Invocation ID: {event.invocation_id}")
                logger.info(f"Is Final Response Flag: {event.is_final_response()}")
                if event.content:
                     logger.info(f"Event Content: {str(event.content)[:500]}...") # Log content snippet
                if hasattr(event, 'actions') and event.actions:
                    logger.info(f"Event Actions: {event.actions}")
                logger.info(f"-- RAW EVENT {event_count} END --")
                # --- END DETAILED EVENT LOGGING ---
                
                # Original logging logic below
                logger.info(f"Event {event_count}: author={event.author}")
                
                if event.author != current_agent:
                    current_agent = event.author
                    logger.info(f"Agent execution changed to: {current_agent}")
                
                if event.content and event.content.parts:
                    part = event.content.parts[0]
                    if hasattr(part, 'text') and part.text:
                        logger.info(f"Text content: {part.text[:100]}...")
                
                if hasattr(event, 'actions') and event.actions:
                    if hasattr(event.actions, 'state_delta') and event.actions.state_delta:
                        state_delta = event.actions.state_delta
                        logger.info(f"State delta received: {state_delta}")
                
                # Check for final response *only* from the coordinator agent
                if event.is_final_response() and event.author == self.coordinator_agent.name:
                    logger.warning(f"Event {event_count} from COORDINATOR ({event.author}) flagged as FINAL. Breaking loop.")
                    if event.content and event.content.parts:
                        part = event.content.parts[0]
                        if hasattr(part, 'text') and part.text:
                            logger.info(f"Final response text: {part.text[:100]}...")
                    break
                elif event.is_final_response():
                    # Log but don't break if a sub-agent marks as final
                    logger.info(f"Event {event_count} from sub-agent {event.author} flagged as FINAL, but continuing sequence.")
            
            # Get the updated session
            logger.info("Retrieving updated session")
            updated_session = self.session_service.get_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id
            )
            
            # Process agent outputs from state
            results = {}
            
            # Process each agent output
            for key in ["budget_analysis", "savings_strategy", "debt_reduction"]:
                value = updated_session.state.get(key)
                if value is not None:
                    logger.info(f"Found {key} in state: type={type(value)}")
                    
                    if value == "":
                        logger.warning(f"{key} is empty in state, using default")
                        results[key] = default_results[key]
                        continue
                    
                    if isinstance(value, str):
                        try:
                            parsed_value = json.loads(value)
                            results[key] = parsed_value
                            logger.info(f"Successfully parsed {key} as JSON")
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse {key} as JSON, using as is: {value[:100]}...")
                            if key in default_results:
                                results[key] = default_results[key]
                            else:
                                results[key] = value
                    else:
                        results[key] = value
                else:
                    logger.warning(f"{key} not found in session state, using default")
                    results[key] = default_results[key]
            
            return results
            
        except Exception as e:
            logger.exception(f"Error during finance analysis: {str(e)}")
            raise
        finally:
            # Clean up the session
            try:
                self.session_service.delete_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=session_id
                )
                logger.info(f"Cleaned up session: {session_id}")
            except Exception as e:
                logger.warning(f"Failed to clean up session: {e}")
    
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

    def _create_default_results(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create default results in case agent execution fails"""
        monthly_income = financial_data.get("monthly_income", 0)
        expenses = {}
        
        # Extract expenses from manual entries or transactions
        if financial_data.get("manual_expenses"):
            expenses = financial_data.get("manual_expenses")
        elif financial_data.get("transactions"):
            # Simplified aggregation of transactions
            for transaction in financial_data.get("transactions", []):
                category = transaction.get("Category", "Uncategorized")
                amount = transaction.get("Amount", 0)
                if category in expenses:
                    expenses[category] += amount
                else:
                    expenses[category] = amount
        
        total_expenses = sum(expenses.values())
        
        # Create default budget analysis
        default_budget = {
            "total_expenses": total_expenses,
            "monthly_income": monthly_income,
            "spending_categories": [
                {"category": cat, "amount": amt, "percentage": (amt / total_expenses * 100) if total_expenses > 0 else 0}
                for cat, amt in expenses.items()
            ],
            "recommendations": [
                {"category": "General", "recommendation": "Consider reviewing your expenses carefully", "potential_savings": total_expenses * 0.1}
            ]
        }
        
        # Create default savings strategy
        default_savings = {
            "emergency_fund": {
                "recommended_amount": total_expenses * 6,
                "current_amount": 0,
                "current_status": "Not started"
            },
            "recommendations": [
                {"category": "Emergency Fund", "amount": total_expenses * 0.1, "rationale": "Build emergency fund first"},
                {"category": "Retirement", "amount": monthly_income * 0.15, "rationale": "Long-term savings"}
            ],
            "automation_techniques": [
                {"name": "Automatic Transfer", "description": "Set up automatic transfers on payday"}
            ]
        }
        
        # Create default debt reduction
        default_debts = financial_data.get("debts", [])
        total_debt = sum(debt.get("amount", 0) for debt in default_debts)
        
        default_debt = {
            "total_debt": total_debt,
            "debts": default_debts,
            "payoff_plans": {
                "avalanche": {
                    "total_interest": total_debt * 0.2,
                    "months_to_payoff": 24,
                    "monthly_payment": total_debt / 24
                },
                "snowball": {
                    "total_interest": total_debt * 0.25,
                    "months_to_payoff": 24,
                    "monthly_payment": total_debt / 24
                }
            },
            "recommendations": [
                {"title": "Increase Payments", "description": "Increase your monthly payments", "impact": "Reduces total interest paid"}
            ]
        }
        
        return {
            "budget_analysis": default_budget,
            "savings_strategy": default_savings,
            "debt_reduction": default_debt
        }

def display_budget_analysis(analysis: Dict[str, Any]):
    """Display budget analysis results"""
    logger.info(f"Displaying budget analysis, type: {type(analysis)}")
    
    # Ensure we have a dictionary
    if isinstance(analysis, str):
        logger.info(f"Budget analysis is a string, attempting to parse as JSON")
        try:
            analysis = json.loads(analysis)
            logger.info("Successfully parsed budget analysis from JSON string")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse budget analysis results: {e}")
            logger.error(f"First 200 chars of analysis: {analysis[:200]}")
            st.error("Failed to parse budget analysis results")
            return
    
    if not isinstance(analysis, dict):
        logger.error(f"Invalid budget analysis format: {type(analysis)}")
        st.error("Invalid budget analysis format")
        return
    
    logger.info(f"Budget analysis keys: {list(analysis.keys())}")
    
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
        income = analysis.get("monthly_income", 0)
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
    # Ensure we have a dictionary
    if isinstance(strategy, str):
        try:
            strategy = json.loads(strategy)
        except json.JSONDecodeError:
            st.error("Failed to parse savings strategy results")
            return
    
    if not isinstance(strategy, dict):
        st.error("Invalid savings strategy format")
        return
    
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
    # Ensure we have a dictionary
    if isinstance(plan, str):
        try:
            plan = json.loads(plan)
        except json.JSONDecodeError:
            st.error("Failed to parse debt reduction results")
            return
    
    if not isinstance(plan, dict):
        st.error("Invalid debt reduction format")
        return
    
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
        logger.error("GOOGLE_API_KEY environment variable not set")
        st.error("""
        GOOGLE_API_KEY not found in environment variables.
        Please create a .env file with your Google API key:
        ```
        GOOGLE_API_KEY=your_api_key_here
        ```
        """)
        return
    
    st.title("📊 AI Personal Finance Coach")
    st.subheader("Get personalized financial advice from AI agents")
    st.markdown("---")
    
    # --- Input Section --- 
    st.header("Step 1: Enter Your Financial Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Income & Dependants")
        monthly_income = st.number_input("Monthly Income ($)", min_value=0.0, step=100.0, value=3000.0, key="income")
        dependants = st.number_input("Number of Dependants", min_value=0, step=1, value=0, key="dependants")

    with col2:
        st.subheader("Expense Data")
        expense_option = st.radio(
            "How do you want to enter expenses?",
            ("Upload CSV Transactions", "Enter Manually"),
            key="expense_option"
        )
        
        transaction_file = None
        manual_expenses = {}
        use_manual_expenses = False
        transactions_df = None

        if expense_option == "Upload CSV Transactions":
            st.write("Upload a CSV with columns: Date, Category, Amount")
            transaction_file = st.file_uploader("Upload CSV of transactions", type=["csv"], key="transaction_file")
            if transaction_file is not None:
                try:
                    transactions_df = pd.read_csv(transaction_file)
                    st.success("Transaction file uploaded successfully!")
                    # Optional: Display small preview
                    # st.dataframe(transactions_df.head(3))
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
                    transactions_df = None # Ensure df is None if error
        else:
            use_manual_expenses = True
            st.write("Enter monthly expenses by category:")
            categories = ["Housing", "Utilities", "Food", "Transportation", "Healthcare", 
                          "Entertainment", "Personal", "Savings", "Other"]
            # Use columns for better manual entry layout
            exp_col1, exp_col2 = st.columns(2)
            for i, category in enumerate(categories):
                col = exp_col1 if i < (len(categories) + 1) // 2 else exp_col2
                manual_expenses[category] = col.number_input(f"{category} ($)", min_value=0.0, step=50.0, value=0.0, key=f"manual_{category}")
            # Display manual entries for confirmation
            if any(manual_expenses.values()):
                st.write("Entered Manual Expenses:")
                manual_df_disp = pd.DataFrame({
                    'Category': list(manual_expenses.keys()),
                    'Amount': list(manual_expenses.values())
                })
                st.dataframe(manual_df_disp[manual_df_disp['Amount'] > 0])


    st.subheader("Debt Information")
    num_debts = st.number_input("Number of Debts", min_value=0, max_value=10, step=1, value=0, key="num_debts")
    
    debts = []
    if num_debts > 0:
        debt_cols = st.columns(num_debts)
        for i in range(num_debts):
            with debt_cols[i]:
                st.markdown(f"**Debt #{i+1}**")
                debt_name = st.text_input(f"Name", value=f"Debt {i+1}", key=f"debt_name_{i}")
                debt_amount = st.number_input(f"Amount $", min_value=0.01, step=100.0, value=1000.0, key=f"debt_amount_{i}")
                interest_rate = st.number_input(f"Interest Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=5.0, key=f"debt_rate_{i}")
                min_payment = st.number_input(f"Min. Payment $", min_value=0.0, step=10.0, value=50.0, key=f"debt_min_payment_{i}")
                
                debts.append({
                    "name": debt_name,
                    "amount": debt_amount,
                    "interest_rate": interest_rate,
                    "min_payment": min_payment
                })
        
    st.markdown("---")
    analyze_button = st.button("Analyze My Finances", key="analyze_button")
    st.markdown("---")
    
    # --- Results Section --- 
    if analyze_button:
        # Validate inputs before proceeding
        if expense_option == "Upload CSV Transactions" and transactions_df is None:
            st.error("Please upload a valid transaction CSV file or choose manual entry.")
            return
        if use_manual_expenses and not any(manual_expenses.values()):
             st.warning("No manual expenses entered. Analysis might be limited.")
             # Optionally proceed or return, depending on desired behavior

        st.header("Step 2: Financial Analysis Results")
        with st.spinner("AI agents are analyzing your financial data..."): 
            # Prepare data for agent analysis
            financial_data = {
                "monthly_income": monthly_income,
                "dependants": dependants,
                "transactions": transactions_df.to_dict('records') if transactions_df is not None else None,
                "manual_expenses": manual_expenses if use_manual_expenses else None,
                "debts": debts
            }
            
            # Create finance advisor system
            finance_system = FinanceAdvisorSystem()
            
            # Run analysis
            logger.info("Starting financial analysis")
            results = None
            try:
                results = asyncio.run(finance_system.analyze_finances(financial_data))
                logger.info(f"Analysis complete, results keys: {list(results.keys())}")
                
                # Log the types of each result
                for key, value in results.items():
                    logger.info(f"Result '{key}' is type: {type(value)}")
                    # if value: # Avoid logging large outputs unless needed
                    #     preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    #     logger.info(f"Preview of {key}: {preview}")
            except Exception as e:
                logger.exception(f"Error in financial analysis: {e}")
                st.error(f"An error occurred during analysis: {str(e)}")
                # results remains None
        
        # Display results if analysis was successful
        if results:
            tabs = st.tabs(["💰 Budget Analysis", "📈 Savings Strategy", "💳 Debt Reduction"])
            
            with tabs[0]:
                st.subheader("Budget Analysis")
                if "budget_analysis" in results and results["budget_analysis"]:
                    display_budget_analysis(results["budget_analysis"])
                else:
                    st.write("No budget analysis available or analysis failed.")
            
            with tabs[1]:
                st.subheader("Savings Strategy")
                if "savings_strategy" in results and results["savings_strategy"]:
                    display_savings_strategy(results["savings_strategy"])
                else:
                    st.write("No savings strategy available or analysis failed.")
            
            with tabs[2]:
                st.subheader("Debt Reduction Plan")
                if "debt_reduction" in results and results["debt_reduction"]:
                    display_debt_reduction(results["debt_reduction"])
                else:
                    st.write("No debt reduction plan available or analysis failed.")
        else:
            st.error("Financial analysis could not be completed.")

if __name__ == "__main__":
    main()