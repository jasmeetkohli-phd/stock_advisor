# app_complete.py - Stock Risk Advisor with enhanced UX
import os
import json
import csv
import io
from datetime import datetime
from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Import for PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# -------------------------
# CONFIG / TUNABLE CONSTANTS
# -------------------------
MINIMUM_INVESTMENT_THRESHOLD = 500          # rupees
LOW_INVESTMENT_CONFIDENCE_THRESH = 1000    # rupees threshold used in confidence
DEFAULT_PAGE_TITLE = "Stock Risk Advisor"
ALLOCATION_TO_DB = {
    "Large_Cap": "Large Cap Blue Chip",
    "Mid_Cap": "Mid Cap",
    "Small_Cap": "Small Cap",
    "Growth": "Growth Stocks"
}
# Scoring / weights
WEIGHTS = {
    "emergency": 0.35,
    "debt": 0.25,
    "savings": 0.20,
    "income_stability": 0.20
}

# CSV file for storing assessment data
CSV_FILE = "assessments_data.csv"

# Create directories if they don't exist
os.makedirs("exports", exist_ok=True)

# -------------------------
# PDF GENERATOR CLASS
# -------------------------
class AssessmentPDF:
    def __init__(self, assessment_data):
        self.assessment_data = assessment_data
        self.buffer = io.BytesIO()
        self.pdf = canvas.Canvas(self.buffer, pagesize=letter)
        self.width, self.height = letter
        
    def draw_header(self):
        self.pdf.setFont("Helvetica-Bold", 16)
        self.pdf.drawCentredString(self.width/2, self.height - 50, "Stock Risk Advisor - Assessment Report")
        self.pdf.setFont("Helvetica", 10)
        self.pdf.drawCentredString(self.width/2, self.height - 70, 
                                  f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.pdf.line(50, self.height - 80, self.width - 50, self.height - 80)
        
    def draw_section_title(self, title, y_position):
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.setFillColorRGB(0.2, 0.4, 0.8)
        self.pdf.drawString(50, y_position, title)
        self.pdf.setFillColorRGB(0, 0, 0)
        return y_position - 20
    
    def draw_key_value(self, key, value, y_position, indent=0):
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawString(50 + indent, y_position, f"{key}:")
        self.pdf.setFont("Helvetica", 12)
        self.pdf.drawString(150 + indent, y_position, str(value))
        return y_position - 20
    
    def draw_bullet_point(self, text, y_position, indent=20):
        self.pdf.setFont("Helvetica", 12)
        self.pdf.drawString(50 + indent, y_position, f"• {text}")
        return y_position - 15
    
    def draw_checklist_item(self, text, y_position, indent=20):
        self.pdf.setFont("Helvetica", 12)
        self.pdf.drawString(50 + indent, y_position, f"✓ {text}")
        return y_position - 15
    
    def generate_pdf(self):
        y_position = self.height - 100
        
        # Header
        self.draw_header()
        y_position -= 30
        
        # Personal Information
        y_position = self.draw_section_title("Personal Information", y_position)
        
        answers = self.assessment_data['answers']
        y_position = self.draw_key_value("Assessment Date", datetime.now().strftime('%Y-%m-%d %H:%M'), y_position)
        y_position = self.draw_key_value("Monthly Income", f"₹ {answers.get('monthly_income', 0):,.2f}", y_position)
        y_position = self.draw_key_value("Monthly Expenses", f"₹ {answers.get('monthly_expenses', 0):,.2f}", y_position)
        y_position = self.draw_key_value("Age Group", self.get_age_group(answers.get('age', 3)), y_position)
        
        # Financial Health
        y_position -= 10
        y_position = self.draw_section_title("Financial Health Score", y_position)
        
        financial_data = self.assessment_data.get('financial_data', {})
        y_position = self.draw_key_value("Overall Score", f"{financial_data.get('financial_health_score', 0)}/100", y_position)
        y_position = self.draw_key_value("Monthly Disposable", f"₹ {financial_data.get('disposable_income', 0):,.2f}", y_position)
        y_position = self.draw_key_value("Debt Ratio", f"{financial_data.get('debt_ratio', 0):.2%}", y_position)
        
        # Risk Profile
        y_position -= 10
        y_position = self.draw_section_title("Risk Profile", y_position)
        
        risk_scores = self.assessment_data.get('risk_scores', {})
        y_position = self.draw_key_value("Risk Category", self.assessment_data.get('risk_category', 'N/A'), y_position)
        y_position = self.draw_key_value("Total Risk Score", f"{risk_scores.get('total_score', 0)}/90", y_position)
        
        # Investment Recommendations
        y_position -= 10
        y_position = self.draw_section_title("Investment Recommendations", y_position)
        
        investment_data = self.assessment_data.get('investment_data', {})
        y_position = self.draw_key_value("Monthly Investment", f"₹ {investment_data.get('safe_monthly_investment', 0):,.2f}", y_position)
        y_position = self.draw_key_value("Annual Investment", f"₹ {investment_data.get('annual_investment', 0):,.2f}", y_position)
        
        # Portfolio Allocation
        y_position -= 10
        y_position = self.draw_section_title("Portfolio Allocation", y_position)
        
        allocation = self.assessment_data.get('allocation', {})
        for category, percentage in allocation.items():
            amount = (percentage / 100.0) * investment_data.get('safe_monthly_investment', 0)
            y_position = self.draw_key_value(f"{category}", f"{percentage}% (₹ {amount:,.2f}/month)", y_position, indent=10)
        
        # Action Plan
        y_position -= 10
        y_position = self.draw_section_title("Action Plan", y_position)
        
        if investment_data.get('ef_gap_amount', 0) > 0:
            y_position = self.draw_bullet_point(f"Build Emergency Fund: Save ₹ {investment_data.get('monthly_ef_saving', 0):,.2f}/month for {investment_data.get('ef_build_timeline', 0)} months", y_position)
        
        if answers.get('high_interest_debt', 0) > 0:
            y_position = self.draw_bullet_point(f"Pay High-Interest Debt: Minimum ₹ {investment_data.get('monthly_debt_payment', 0):,.2f}/month", y_position)
        
        if investment_data.get('safe_monthly_investment', 0) > 0:
            y_position = self.draw_bullet_point(f"Start Investing: ₹ {investment_data.get('safe_monthly_investment', 0):,.2f}/month as per allocation", y_position)
        
        # Monthly Checklist
        y_position -= 10
        y_position = self.draw_section_title("Monthly Checklist", y_position)
        
        if investment_data.get('monthly_ef_saving', 0) > 0:
            y_position = self.draw_checklist_item(f"Save ₹ {investment_data.get('monthly_ef_saving', 0):,.2f} for emergency fund", y_position)
        
        if investment_data.get('monthly_debt_payment', 0) > 0:
            y_position = self.draw_checklist_item(f"Pay ₹ {investment_data.get('monthly_debt_payment', 0):,.2f} towards high-interest debt", y_position)
        
        if investment_data.get('safe_monthly_investment', 0) > 0:
            y_position = self.draw_checklist_item(f"Invest ₹ {investment_data.get('safe_monthly_investment', 0):,.2f} as per allocation", y_position)
        
        # Disclaimer
        y_position -= 20
        self.pdf.setFont("Helvetica-Oblique", 10)
        self.pdf.drawString(50, y_position, "Disclaimer: This report is for educational purposes only.")
        y_position -= 15
        self.pdf.drawString(50, y_position, "We are not SEBI-registered investment advisors. This is not financial advice.")
        
        # Save the PDF
        self.pdf.save()
        
        # Get the PDF bytes
        self.buffer.seek(0)
        return self.buffer
    
    @staticmethod
    def get_age_group(age_score):
        age_map = {
            1: "56-65+ years",
            2: "46-55 years",
            3: "36-45 years",
            4: "25-35 years",
            5: "Under 25 years"
        }
        return age_map.get(age_score, "Unknown")

# -------------------------
# CSV DATA HANDLER
# -------------------------
class CSVDataHandler:
    @staticmethod
    def save_assessment_to_csv(assessment_data):
        """Save assessment data to CSV file"""
        try:
            # Prepare data row
            row_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'monthly_income': assessment_data['answers'].get('monthly_income', 0),
                'monthly_expenses': assessment_data['answers'].get('monthly_expenses', 0),
                'emergency_fund': assessment_data['answers'].get('emergency', 3),
                'high_interest_debt': assessment_data['answers'].get('high_interest_debt', 0),
                'age_group': assessment_data['answers'].get('age', 3),
                'investment_purpose': assessment_data['answers'].get('purpose', 3),
                'time_horizon': assessment_data['answers'].get('horizon', 3),
                'risk_behavior': assessment_data['answers'].get('risk_behavior', 3),
                'experience': assessment_data['answers'].get('experience', 2),
                'goal_priority': assessment_data['answers'].get('goal_priority', 2),
                'loss_capacity': assessment_data['answers'].get('loss_capacity', 2),
                'liquidity_need': assessment_data['answers'].get('liquidity_need', 2),
                'financial_health_score': assessment_data.get('financial_data', {}).get('financial_health_score', 0),
                'risk_category': assessment_data.get('risk_category', 'Unknown'),
                'total_risk_score': assessment_data.get('risk_scores', {}).get('total_score', 0),
                'monthly_investment': assessment_data.get('investment_data', {}).get('safe_monthly_investment', 0),
                'annual_investment': assessment_data.get('investment_data', {}).get('annual_investment', 0),
                'confidence_score': assessment_data.get('confidence_score', {}).get('score', 0),
                'contradictions': assessment_data.get('contradictions', 0),
                'portfolio_large_cap': assessment_data.get('allocation', {}).get('Large_Cap', 0),
                'portfolio_mid_cap': assessment_data.get('allocation', {}).get('Mid_Cap', 0),
                'portfolio_small_cap': assessment_data.get('allocation', {}).get('Small_Cap', 0),
                'portfolio_growth': assessment_data.get('allocation', {}).get('Growth', 0)
            }
            
            # Check if file exists to write header
            file_exists = os.path.isfile(CSV_FILE)
            
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(row_data.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row_data)
                
            return True
        except Exception as e:
            st.error(f"Error saving to CSV: {str(e)}")
            return False
    
    @staticmethod
    def load_assessments_from_csv():
        """Load all assessments from CSV file"""
        try:
            if not os.path.exists(CSV_FILE):
                return pd.DataFrame()
            
            df = pd.read_csv(CSV_FILE)
            return df
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            return pd.DataFrame()
    
    @staticmethod
    def get_statistics():
        """Get statistics from stored assessments"""
        df = CSVDataHandler.load_assessments_from_csv()
        if df.empty:
            return None
        
        stats = {
            'total_assessments': len(df),
            'avg_financial_health': df['financial_health_score'].mean(),
            'most_common_risk_category': df['risk_category'].mode().iloc[0] if not df['risk_category'].mode().empty else 'N/A',
            'avg_monthly_investment': df['monthly_investment'].mean(),
            'recent_assessments': df.tail(5).to_dict('records')
        }
        return stats

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title=DEFAULT_PAGE_TITLE,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# CUSTOM CSS
# -------------------------
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 1rem; }
    .section-header { font-size: 1.6rem; color: #374151; font-weight: 600; margin-top: 1.5rem; margin-bottom: 1rem; }
    .card { background-color: #F9FAFB; padding: 1rem; border-radius: 10px; border-left: 5px solid #3B82F6; margin-bottom: 1rem; }
    .metric-card { background: linear-gradient(135deg,#667eea 0%,#764ba2 100%); color: white; padding: 1.25rem; border-radius: 10px; text-align: center; }
    .risk-low { color: #10B981; } .risk-medium { color: #F59E0B; } .risk-high { color: #EF4444; }
    .tab-content { padding: 1.5rem 0; }
    .progress-bar { height: 10px; background-color: #E5E7EB; border-radius: 5px; margin: 10px 0; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 5px; transition: width 0.5s ease; }
    /* Scope button styling to forms only */
    div[data-testid="stForm"] .stButton button { background-color: #3B82F6; color: white; font-weight: 600; border-radius: 8px; padding: 0.4rem 1rem; }
    div[data-testid="stForm"] .stButton button:hover { background-color: #2563EB; }
    /* Wizard navigation */
    .wizard-step { padding: 0.75rem 1rem; border-radius: 8px; margin: 0.25rem 0; }
    .wizard-step-active { background-color: #3B82F6; color: white; }
    .wizard-step-completed { background-color: #10B981; color: white; }
    .wizard-step-pending { background-color: #F3F4F6; color: #6B7280; }
    /* Info boxes */
    .info-box { background-color: #E0F2FE; border-left: 4px solid #0EA5E9; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .warning-box { background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# SESSION STATE INIT
# -------------------------
def init_session_state():
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "Welcome"
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'risk_scores' not in st.session_state:
        st.session_state.risk_scores = None
    if 'risk_category' not in st.session_state:
        st.session_state.risk_category = None
    if 'financial_health_score' not in st.session_state:
        st.session_state.financial_health_score = None
    if 'safe_investment' not in st.session_state:
        st.session_state.safe_investment = None
    if 'override_log' not in st.session_state:
        st.session_state.override_log = []
    if 'confidence_score' not in st.session_state:
        st.session_state.confidence_score = None
    if 'assessment_complete' not in st.session_state:
        st.session_state.assessment_complete = False
    if 'contradictions' not in st.session_state:
        st.session_state.contradictions = 0
    if 'allocation' not in st.session_state:
        st.session_state.allocation = None
    if 'pdf_generated' not in st.session_state:
        st.session_state.pdf_generated = False
    if 'assessment_id' not in st.session_state:
        st.session_state.assessment_id = None
    if 'assessment_step' not in st.session_state:
        st.session_state.assessment_step = 0
    if 'debt_details' not in st.session_state:
        st.session_state.debt_details = {}
init_session_state()

# -------------------------
# STOCK DATABASE
# -------------------------
STOCKS_DB = {
    "Large Cap Blue Chip": [
        {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy", "market_cap": "Large"},
        {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT", "market_cap": "Large"},
        {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking", "market_cap": "Large"},
        {"symbol": "INFY", "name": "Infosys", "sector": "IT", "market_cap": "Large"},
        {"symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "Banking", "market_cap": "Large"},
        {"symbol": "HINDUNILVR", "name": "Hindustan Unilever", "sector": "FMCG", "market_cap": "Large"}
    ],
    "Mid Cap": [
        {"symbol": "TITAN", "name": "Titan Company", "sector": "Consumer", "market_cap": "Mid"},
        {"symbol": "MARUTI", "name": "Maruti Suzuki", "sector": "Auto", "market_cap": "Mid"},
        {"symbol": "ASIANPAINT", "name": "Asian Paints", "sector": "Paints", "market_cap": "Mid"},
        {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "sector": "Financial", "market_cap": "Mid"},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom", "market_cap": "Mid"}
    ],
    "Small Cap": [
        {"symbol": "TATAELXSI", "name": "Tata Elxsi", "sector": "IT", "market_cap": "Small"},
        {"symbol": "COFORGE", "name": "Coforge", "sector": "IT", "market_cap": "Small"},
        {"symbol": "LAURUSLABS", "name": "Laurus Labs", "sector": "Pharma", "market_cap": "Small"},
        {"symbol": "PERSISTENT", "name": "Persistent Systems", "sector": "IT", "market_cap": "Small"}
    ],
    "Growth Stocks": [
        {"symbol": "DMART", "name": "Avenue Supermarts", "sector": "Retail", "market_cap": "Large"},
        {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv", "sector": "Financial", "market_cap": "Large"},
        {"symbol": "TECHM", "name": "Tech Mahindra", "sector": "IT", "market_cap": "Large"},
        {"symbol": "NAUKRI", "name": "Info Edge", "sector": "Internet", "market_cap": "Large"}
    ]
}

# -------------------------
# RISK CALCULATOR
# -------------------------
class RiskCalculator:
    @staticmethod
    def calculate_financial_health_score(answers):
        """Calculate Financial Health Score (0-100)"""
        monthly_income = float(answers.get('monthly_income', 0))
        monthly_expenses = float(answers.get('monthly_expenses', 0))
        emergency_score = int(answers.get('emergency', 3))
        high_interest_debt = float(answers.get('high_interest_debt', 0))

        # Basic metrics
        disposable_income = max(0.0, monthly_income - monthly_expenses)
        annual_income = monthly_income * 12.0

        # Savings Rate Score (1-5)
        savings_rate = (disposable_income / monthly_income) if monthly_income > 0 else 0.0
        if savings_rate < 0.10:
            savings_rate_score = 1
        elif savings_rate < 0.20:
            savings_rate_score = 2
        elif savings_rate < 0.30:
            savings_rate_score = 3
        elif savings_rate < 0.40:
            savings_rate_score = 4
        else:
            savings_rate_score = 5

        # Debt Score (0-1)
        if annual_income > 0:
            debt_ratio = min(1.0, high_interest_debt / annual_income)
        else:
            debt_ratio = 1.0
        debt_score = max(0.0, 1.0 - debt_ratio)

        # Emergency component: map 1-5 → percentage
        emergency_component = (emergency_score / 5.0) * 100.0
        debt_component = debt_score * 100.0
        savings_component = (savings_rate_score / 5.0) * 100.0

        # Income stability: optional - currently assumed good; can be replaced with a user input later
        income_stability_component = 100.0

        financial_health_score = (
            WEIGHTS['emergency'] * emergency_component +
            WEIGHTS['debt'] * debt_component +
            WEIGHTS['savings'] * savings_component +
            WEIGHTS['income_stability'] * income_stability_component
        )

        return {
            'financial_health_score': round(financial_health_score, 2),
            'savings_rate_score': savings_rate_score,
            'debt_score': round(debt_score, 2),
            'disposable_income': round(disposable_income, 2),
            'debt_ratio': round(debt_ratio, 2)
        }

    @staticmethod
    def norm(score):
        """Normalize 1-5 to 0.2-1.0"""
        try:
            return float(score) / 5.0
        except Exception:
            return 0.0

    @staticmethod
    def calculate_risk_scores(answers, financial_data):
        """Calculate Risk Scores (90-point system)"""
        # Inputs (with safe defaults)
        age_score = int(answers.get('age', 3))
        purpose_score = int(answers.get('purpose', 3))
        horizon_score = int(answers.get('horizon', 3))
        risk_behavior_score = int(answers.get('risk_behavior', 3))
        experience_score = int(answers.get('experience', 3))
        emergency_score = int(answers.get('emergency', 3))
        goal_priority = int(answers.get('goal_priority', 2))
        loss_capacity = int(answers.get('loss_capacity', 2))

        # From financial_data
        savings_rate_score = financial_data.get('savings_rate_score', 3)
        debt_score = financial_data.get('debt_score', 0.5)

        # Convert scales
        goal_priority_normalized = ((goal_priority - 1) * 2) + 1  # 1-3 → 1-5
        loss_capacity_normalized = ((loss_capacity - 1) * (4.0/3.0)) + 1  # 1-4 → 1-5

        # RISK CAPACITY (40 points)
        risk_capacity = (
            8.0 * RiskCalculator.norm(age_score) +
            6.0 * RiskCalculator.norm(savings_rate_score) +
            6.0 * debt_score +
            10.0 * RiskCalculator.norm(emergency_score) +
            10.0 * RiskCalculator.norm(horizon_score)
        )

        # RISK TOLERANCE (30 points)
        risk_tolerance = (
            15.0 * RiskCalculator.norm(risk_behavior_score) +
            10.0 * RiskCalculator.norm(experience_score) +
            5.0 * RiskCalculator.norm(loss_capacity_normalized)
        )

        # RISK REQUIREMENT (20 points)
        risk_requirement = (
            15.0 * RiskCalculator.norm(purpose_score) +
            5.0 * RiskCalculator.norm(goal_priority_normalized)
        )

        total_score = risk_capacity + risk_tolerance + risk_requirement

        return {
            'risk_capacity': round(risk_capacity, 2),
            'risk_tolerance': round(risk_tolerance, 2),
            'risk_requirement': round(risk_requirement, 2),
            'total_score': round(total_score, 2)
        }

    @staticmethod
    def get_risk_category(total_score):
        """Determine initial risk category"""
        if total_score <= 30:
            return "VERY LOW RISK"
        elif total_score <= 45:
            return "LOW RISK"
        elif total_score <= 60:
            return "MEDIUM RISK"
        elif total_score <= 75:
            return "HIGH RISK"
        else:
            return "VERY HIGH RISK"

    @staticmethod
    def apply_safety_overrides(initial_category, answers, financial_data):
        """Apply safety overrides and return category, log, allocation, contradictions"""
        risk_index_map = {
            "VERY LOW RISK": 1,
            "LOW RISK": 2,
            "MEDIUM RISK": 3,
            "HIGH RISK": 4,
            "VERY HIGH RISK": 5
        }
        current_index = risk_index_map.get(initial_category, 3)
        override_log = []
        contradictions = 0

        # Get inputs (with safe defaults)
        emergency_score = int(answers.get('emergency', 3))
        high_interest_debt = float(answers.get('high_interest_debt', 0))
        monthly_income = float(answers.get('monthly_income', 0))
        goal_priority = int(answers.get('goal_priority', 2))
        liquidity_need = int(answers.get('liquidity_need', 2))
        age_score = int(answers.get('age', 3))
        risk_behavior = int(answers.get('risk_behavior', 3))
        horizon_score = int(answers.get('horizon', 3))
        experience_score = int(answers.get('experience', 3))
        purpose_score = int(answers.get('purpose', 3))

        # Override: Financial Health (emergency or debt)
        if emergency_score < 3 or high_interest_debt > 0:
            current_index = max(1, current_index - 1)
            override_log.append("Financial health: Emergency fund < 3 months OR high-interest debt present")

        # Override: Goal Priority
        if goal_priority == 1:  # Critical
            current_index = max(1, current_index - 2)
            override_log.append("Goal priority: Critical goal → Downgrade 2 levels")
        elif goal_priority == 2:  # Important
            current_index = max(1, current_index - 1)
            override_log.append("Goal priority: Important goal → Downgrade 1 level")

        # Override: Liquidity Need (High liquidity need caps at MEDIUM)
        if liquidity_need == 1:
            current_index = min(current_index, 3)
            override_log.append("Liquidity: High need → Cap at MEDIUM RISK")

        # Consistency contradictions
        if risk_behavior >= 4 and emergency_score <= 2:
            contradictions += 1
        if risk_behavior >= 4 and horizon_score <= 2:
            contradictions += 1
        if risk_behavior >= 4 and experience_score <= 2:
            contradictions += 1
        if purpose_score == 5 and monthly_income < 50000:
            contradictions += 1

        if contradictions >= 2:
            current_index = max(1, current_index - 1)
            override_log.append(f"Consistency: {contradictions} contradictions found")

        # Age-Equity check
        age_map = {1: 60, 2: 50, 3: 40, 4: 30, 5: 22}
        user_age = age_map.get(age_score, 40)
        reference_equity = 100 - user_age
        equity_map = {1: 20, 2: 40, 3: 60, 4: 80, 5: 90}
        current_equity = equity_map.get(current_index, 60)
        if current_equity > (reference_equity + 15):
            current_index = max(1, current_index - 1)
            override_log.append(f"Age-Equity: Too aggressive for age {user_age}")

        # Portfolio concentration (based on index)
        allocation_table = {
            1: {"Large_Cap": 85, "Mid_Cap": 15, "Small_Cap": 0, "Growth": 0},
            2: {"Large_Cap": 70, "Mid_Cap": 25, "Small_Cap": 0, "Growth": 5},
            3: {"Large_Cap": 50, "Mid_Cap": 30, "Small_Cap": 10, "Growth": 10},
            4: {"Large_Cap": 35, "Mid_Cap": 30, "Small_Cap": 15, "Growth": 20},
            5: {"Large_Cap": 20, "Mid_Cap": 25, "Small_Cap": 25, "Growth": 30}
        }
        allocation = allocation_table.get(current_index, allocation_table[3])

        aggressive_exposure = allocation.get("Small_Cap", 0) + allocation.get("Growth", 0)
        if aggressive_exposure > 45:
            current_index = max(1, current_index - 1)
            override_log.append(f"Concentration: Aggressive exposure {aggressive_exposure}% > 45%")

        # Low income cap
        if monthly_income < 25000:
            current_index = min(current_index, 3)
            override_log.append("Income: Monthly income < ₹25,000 → Cap at MEDIUM RISK")

        # Final bounds
        current_index = max(1, min(5, current_index))
        reverse_map = {1: "VERY LOW RISK", 2: "LOW RISK", 3: "MEDIUM RISK", 4: "HIGH RISK", 5: "VERY HIGH RISK"}
        final_category = reverse_map.get(current_index, "MEDIUM RISK")

        return final_category, override_log, allocation, contradictions

    @staticmethod
    def calculate_safe_investment(answers, financial_data):
        """Calculate safe monthly investment amount"""
        monthly_income = float(answers.get('monthly_income', 0))
        monthly_expenses = float(answers.get('monthly_expenses', 0))
        emergency_score = int(answers.get('emergency', 3))
        high_interest_debt = float(answers.get('high_interest_debt', 0))
        financial_health_score = float(financial_data.get('financial_health_score', 0))

        # Map emergency to months
        emergency_months_map = {1: 0, 2: 1, 3: 2, 4: 4.5, 5: 8}
        current_ef_months = emergency_months_map.get(emergency_score, 0)
        required_ef_months = 6
        ef_gap_months = max(0.0, required_ef_months - current_ef_months)
        ef_gap_amount = ef_gap_months * monthly_expenses

        disposable_income = financial_data.get('disposable_income', 0.0)

        if ef_gap_amount > 0 and disposable_income > 0:
            build_timeline = 12
            if (ef_gap_amount / build_timeline) > (disposable_income * 0.4):
                build_timeline = max(3, int(np.ceil(ef_gap_amount / (disposable_income * 0.4))))
            build_timeline = min(24, build_timeline)
            monthly_ef_saving = ef_gap_amount / build_timeline
        else:
            monthly_ef_saving = 0.0
            build_timeline = 0

        # Debt payment (minimum)
        if high_interest_debt > 0:
            monthly_debt_payment = high_interest_debt * 0.03
        else:
            monthly_debt_payment = 0.0

        # Investment bracket based on financial health
        if financial_health_score < 50:
            max_investment_rate = 0.10
        elif financial_health_score < 70:
            max_investment_rate = 0.20
        elif financial_health_score < 85:
            max_investment_rate = 0.30
        else:
            max_investment_rate = 0.40

        available_after_priorities = max(0.0, disposable_income - monthly_ef_saving - monthly_debt_payment)
        investment_limit = disposable_income * max_investment_rate
        safe_monthly_investment = min(available_after_priorities, investment_limit)

        if safe_monthly_investment < MINIMUM_INVESTMENT_THRESHOLD:
            safe_monthly_investment = 0.0

        return {
            'safe_monthly_investment': round(safe_monthly_investment, 2),
            'annual_investment': round(safe_monthly_investment * 12.0, 2),
            'monthly_ef_saving': round(monthly_ef_saving, 2),
            'monthly_debt_payment': round(monthly_debt_payment, 2),
            'ef_build_timeline': build_timeline,
            'ef_gap_amount': round(ef_gap_amount, 2),
            'investment_tier': max_investment_rate * 100.0
        }

    @staticmethod
    def calculate_confidence_score(financial_health_score, override_log, safe_investment, contradictions):
        """Calculate confidence score 40-90 (normalized to 0-100 for display consistency)"""
        penalties = []
        if financial_health_score < 50:
            penalties.append("Low financial health")
        if len(override_log) >= 3:
            penalties.append("Multiple overrides")
        if contradictions >= 2:
            penalties.append("Contradictory answers")
        if safe_investment < LOW_INVESTMENT_CONFIDENCE_THRESH:
            penalties.append("Low investment capacity")

        base_confidence = 90
        penalty_per_item = 10
        confidence_score = max(40, base_confidence - (len(penalties) * penalty_per_item))

        # Normalize to 0-100 for UI (scale up so 90->90, floor 40->40)
        normalized_score = confidence_score

        if normalized_score >= 80:
            level = "HIGH"
        elif normalized_score >= 60:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {'score': int(normalized_score), 'level': level, 'penalties': penalties}

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def create_navigation_buttons():
    """Create Next/Previous buttons for navigation"""
    tabs = ["Welcome", "Assessment", "Financial Health", "Risk Profile", "Recommendations", "Action Plan", "Data & Export"]
    current_tab = st.session_state.current_tab
    current_index = tabs.index(current_tab) if current_tab in tabs else 0
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Previous button
        if current_index > 0 and current_tab != "Welcome":
            prev_tab = tabs[current_index - 1]
            if st.button("◀️ Previous", use_container_width=True):
                st.session_state.current_tab = prev_tab
                st.rerun()
    
    with col3:
        # Next button
        if current_index < len(tabs) - 1 and current_tab != "Data & Export":
            if current_tab == "Assessment" and not st.session_state.assessment_complete:
                if st.button("Calculate Results ▶️", type="primary", use_container_width=True):
                    calculate_results()
            else:
                next_tab = tabs[current_index + 1]
                if st.button("Next ▶️", type="primary", use_container_width=True):
                    st.session_state.current_tab = next_tab
                    st.rerun()

def create_progress_bar():
    """Create progress bar at top of page"""
    tabs = ["Welcome", "Assessment", "Financial Health", "Risk Profile", "Recommendations", "Action Plan", "Data & Export"]
    current_tab = st.session_state.current_tab
    current_index = tabs.index(current_tab) if current_tab in tabs else 0
    
    progress_html = f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.9rem;">
            {"".join([f'<span style="font-weight: {"bold" if i == current_index else "normal"}; color: {"#3B82F6" if i == current_index else "#6B7280"};">{tab}</span>' for i, tab in enumerate(tabs)])}
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {(current_index + 1)/len(tabs)*100}%; background-color: #3B82F6;"></div>
        </div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)

def calculate_results():
    """Calculate all results from assessment"""
    calculator = RiskCalculator()
    
    # Financial Health Score
    financial_data = calculator.calculate_financial_health_score(st.session_state.answers)
    st.session_state.financial_health_score = financial_data

    # Risk Scores
    risk_scores = calculator.calculate_risk_scores(st.session_state.answers, financial_data)
    st.session_state.risk_scores = risk_scores

    # Risk Category with overrides
    initial_category = calculator.get_risk_category(risk_scores['total_score'])
    final_category, override_log, allocation, contradictions = calculator.apply_safety_overrides(
        initial_category, st.session_state.answers, financial_data
    )
    st.session_state.risk_category = final_category
    st.session_state.override_log = override_log
    st.session_state.allocation = allocation
    st.session_state.contradictions = contradictions

    # Investment Data
    investment_data = calculator.calculate_safe_investment(st.session_state.answers, financial_data)
    st.session_state.safe_investment = investment_data

    # Confidence Score
    confidence_data = calculator.calculate_confidence_score(
        financial_data['financial_health_score'],
        override_log,
        investment_data['safe_monthly_investment'],
        contradictions
    )
    st.session_state.confidence_score = confidence_data

    st.session_state.assessment_complete = True
    st.session_state.assessment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save to CSV
    assessment_data = {
        'answers': st.session_state.answers,
        'financial_data': financial_data,
        'risk_scores': risk_scores,
        'risk_category': final_category,
        'override_log': override_log,
        'allocation': allocation,
        'contradictions': contradictions,
        'investment_data': investment_data,
        'confidence_score': confidence_data
    }
    
    if CSVDataHandler.save_assessment_to_csv(assessment_data):
        st.success("✅ Assessment saved successfully!")
    
    # Navigate to next tab
    st.session_state.current_tab = "Financial Health"
    st.rerun()

# -------------------------
# Welcome Tab
# -------------------------
def create_welcome_tab():
    st.markdown('<h1 class="main-header">📈 Welcome to Stock Risk Advisor!</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ## Your Personalized Stock Investment Guide
        
        This tool helps you:
        
        ✅ **Assess** your financial readiness for stock investing  
        ✅ **Understand** your risk tolerance for different stock types  
        ✅ **Get personalized** stock recommendations  
        ✅ **Create a safe** investment plan with proper allocations  
        ✅ **Track** your financial progress over time  
        
        **What you'll get after completing the assessment:**
        
        1. **Financial Health Score** - How ready you are to invest  
        2. **Risk Profile** - Your investment risk category  
        3. **Stock Allocation** - Large/Mid/Small cap percentages  
        4. **Specific Stock Suggestions** - Examples matching your profile  
        5. **Action Plan** - Step-by-step implementation guide  
        
        **Time required:** ~5-7 minutes
        """)
    
    with col2:
        st.image("https://img.icons8.com/color/300/000000/stock-exchange.png", width=250)
    
    st.markdown("---")
    st.markdown("### 🚀 Ready to Start?")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Begin Assessment", type="primary", use_container_width=True):
            st.session_state.current_tab = "Assessment"
            st.rerun()
    
    st.markdown("---")
    st.markdown("""
    ### 📋 What to Expect
    
    **Step 1: Financial Assessment**  
    Basic questions about your income, expenses, and debt
    
    **Step 2: Risk Assessment**  
    Understanding your comfort with market volatility
    
    **Step 3: Investment Goals**  
    What you want to achieve with your investments
    
    **Step 4: Personalized Recommendations**  
    Stock suggestions and allocation percentages
    
    **Step 5: Action Plan**  
    Implementation timeline and monthly checklist
    """)

# -------------------------
# Assessment Tab (UPDATED)
# -------------------------
def create_assessment_tab():
    st.markdown('<h1 class="main-header">📋 Stock Investment Readiness Assessment</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>📊 What you'll receive:</strong> Financial Health Score + Risk Profile + Stock Recommendations + Action Plan
    </div>
    """, unsafe_allow_html=True)
    
    # Progress indicator
    answered = len([k for k in st.session_state.answers.keys() if st.session_state.answers[k] not in [None, '']])
    progress_pct = min(100, int((answered / 12) * 100)) if answered > 0 else 0
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
            <span>Assessment Progress</span>
            <span>{answered}/12 questions answered</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress_pct}%; background-color: #3B82F6;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("assessment_form"):
        st.markdown("### 💰 Basic Financial Information")
        
        col1, col2 = st.columns(2)
        with col1:
            monthly_income = st.number_input(
                "1. What is your monthly take-home income? (₹)",
                min_value=0.0, max_value=10_000_000.0, value=float(st.session_state.answers.get('monthly_income', 50000.0)),
                step=500.0, 
                help="Your monthly income after taxes and deductions"
            )
            monthly_expenses = st.number_input(
                "2. What are your monthly essential expenses? (₹)",
                min_value=0.0, max_value=10_000_000.0, value=float(st.session_state.answers.get('monthly_expenses', 30000.0)),
                step=500.0,
                help="Rent, food, bills, insurance, minimum debt payments"
            )
        
        with col2:
            emergency = st.selectbox(
                "3. Emergency fund status?",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "❌ No emergency fund",
                    2: "⚠️ 1 month of expenses saved",
                    3: "🟡 1-3 months of expenses saved",
                    4: "🟢 3-6 months of expenses saved",
                    5: "✅ 6+ months of expenses saved"
                }[x],
                index=int(st.session_state.answers.get('emergency', 3)) - 1,
                help="Recommended: 3-6 months of expenses"
            )
            
            age = st.selectbox(
                "4. What is your age group?",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "56-65+ years",
                    2: "46-55 years",
                    3: "36-45 years",
                    4: "25-35 years",
                    5: "Under 25 years"
                }[x],
                index=int(st.session_state.answers.get('age', 3)) - 1
            )
        
        st.markdown("---")
        st.markdown("### 💳 Debt Information")
        
        st.markdown("""
        <div class="warning-box">
            <strong>💡 Debt Management Tip:</strong> High-interest debt (credit cards > 12%) should be paid before aggressive stock investing.
        </div>
        """, unsafe_allow_html=True)
        
        high_interest_debt = st.number_input(
            "5. Total high-interest debt amount (₹)",
            min_value=0.0, max_value=100_000_000.0, 
            value=float(st.session_state.answers.get('high_interest_debt', 0.0)),
            step=1000.0,
            help="Credit cards, personal loans >12% interest"
        )
        
        # Debt type breakdown (optional)
        with st.expander("📝 Break down your debt (optional)"):
            col1, col2 = st.columns(2)
            with col1:
                credit_card_debt = st.number_input("Credit Card Debt (₹)", min_value=0.0, step=1000.0)
                personal_loan = st.number_input("Personal Loan (₹)", min_value=0.0, step=1000.0)
            with col2:
                car_loan = st.number_input("Car Loan (₹)", min_value=0.0, step=1000.0)
                other_debt = st.number_input("Other High-Interest Debt (₹)", min_value=0.0, step=1000.0)
        
        st.markdown("---")
        st.markdown("### 🎯 Investment Goals & Risk Assessment")
        
        col1, col2 = st.columns(2)
        with col1:
            purpose = st.selectbox(
                "6. Primary investment purpose?",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "💰 Capital preservation",
                    2: "📈 Regular income generation",
                    3: "🎓 Education/Tax saving",
                    4: "🏠 Retirement planning",
                    5: "🚀 Wealth creation/Growth"
                }[x],
                index=int(st.session_state.answers.get('purpose', 4)) - 1
            )
            
            horizon = st.selectbox(
                "7. Investment time horizon?",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "Less than 2 years",
                    2: "2-4 years",
                    3: "5-7 years",
                    4: "8-12 years",
                    5: "13+ years"
                }[x],
                index=int(st.session_state.answers.get('horizon', 3)) - 1
            )
        
        with col2:
            experience = st.selectbox(
                "8. Investment experience level?",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "👶 No experience (first time investor)",
                    2: "👶 Beginner (FDs, basic mutual funds)",
                    3: "👤 Intermediate (stocks, some diversification)",
                    4: "👨‍💼 Advanced (multiple asset classes)",
                    5: "👨‍🎓 Expert (professional/sophisticated)"
                }[x],
                index=int(st.session_state.answers.get('experience', 2)) - 1
            )
            
            goal_priority = st.selectbox(
                "9. How critical is your investment goal?",
                options=[1, 2, 3],
                format_func=lambda x: {
                    1: "🔴 Critical (health/education - cannot fail)",
                    2: "🟡 Important (wedding/house - should not fail)",
                    3: "🟢 Flexible (wealth building - can adjust)"
                }[x],
                index=int(st.session_state.answers.get('goal_priority', 2)) - 1
            )
        
        st.markdown("---")
        st.markdown("### 📊 Risk Tolerance Assessment")
        
        with st.expander("ℹ️ Why we ask about risk in different ways", expanded=False):
            st.markdown("""
            **We measure risk in two dimensions:**
            
            1. **Psychological Tolerance**: How market volatility makes you *feel*
            - Measured by: "How would you react if your portfolio dropped 20%?"
            
            2. **Financial Capacity**: How much loss you can *afford*
            - Measured by: "Maximum % you could afford to lose?"
            
            ⚠️ **Example:** Someone might be emotionally comfortable with risk but have limited financial capacity.
            We'll balance both factors for your personalized plan.
            """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**10. Emotional Response to Market Drops**")
            risk_behavior = st.select_slider(
                "If your stocks dropped 20% tomorrow, you would:",
                options=[1, 2, 3, 4, 5],
                value=int(st.session_state.answers.get('risk_behavior', 3)),
                format_func=lambda x: {
                    1: "🚨 Panic & Sell",
                    2: "😟 Worry but Hold",
                    3: "😐 Stay Calm",
                    4: "😊 See Opportunity",
                    5: "🚀 Buy More!"
                }[x]
            )
        
        with col2:
            st.markdown("**11. Financial Capacity for Loss**")
            loss_capacity = st.select_slider(
                "Maximum % you could afford to lose in a bad year:",
                options=[1, 2, 3, 4],
                value=int(st.session_state.answers.get('loss_capacity', 2)),
                format_func=lambda x: {
                    1: "0-10% (Conservative)",
                    2: "11-20% (Moderate)",
                    3: "21-30% (Aggressive)",
                    4: "31%+ (Very Aggressive)"
                }[x]
            )
        
        liquidity_need = st.selectbox(
            "12. Do you expect to need this money suddenly?",
            options=[1, 2, 3],
            format_func=lambda x: {
                1: "⚠️ High (may need within 1 year)",
                2: "🟡 Medium (2-3 years)",
                3: "🟢 Low (>3 years)"
            }[x],
            index=int(st.session_state.answers.get('liquidity_need', 2)) - 1,
            help="Affects liquidity of recommended investments"
        )
        
        st.markdown("---")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Calculate My Stock Investment Plan", 
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            # Basic validation
            if monthly_expenses > monthly_income:
                st.warning("⚠️ Your expenses exceed your income. Please review your inputs.")
                return
            
            # Save answers
            st.session_state.answers.update({
                'monthly_income': float(monthly_income),
                'monthly_expenses': float(monthly_expenses),
                'emergency': int(emergency),
                'high_interest_debt': float(high_interest_debt),
                'age': int(age),
                'purpose': int(purpose),
                'horizon': int(horizon),
                'risk_behavior': int(risk_behavior),
                'experience': int(experience),
                'goal_priority': int(goal_priority),
                'loss_capacity': int(loss_capacity),
                'liquidity_need': int(liquidity_need)
            })
            
            # Calculate results and navigate
            calculate_results()
    
    # Navigation help at bottom
    st.markdown("---")
    st.markdown("""
    **📋 What's next after submitting?**
    
    1. **Financial Health Score** → 2. **Risk Profile** → 3. **Stock Recommendations** → 4. **Action Plan**
    """)

# -------------------------
# Financial Health Tab (UPDATED with navigation)
# -------------------------
def create_financial_health_tab():
    st.markdown('<h1 class="main-header">💰 Financial Health Assessment</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete or st.session_state.financial_health_score is None:
        st.warning("Please complete the assessment first!")
        st.button("Go to Assessment", on_click=lambda: setattr(st.session_state, 'current_tab', 'Assessment'))
        return
    
    financial_data = st.session_state.financial_health_score
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        score = financial_data['financial_health_score']
        color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 1.1rem;">Financial Health Score</h3>
            <h1 style="margin: 0.35rem 0; font-size: 2.5rem; color: {color};">{score}/100</h1>
            <p style="margin: 0;">{'🟢 Strong' if score >= 70 else '🟡 Needs Work' if score >= 50 else '🔴 Critical'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        disposable = financial_data['disposable_income']
        st.markdown(f"""
        <div class="card" style="border-left-color: #3B82F6;">
            <h4 style="margin: 0;">Monthly Disposable Income</h4>
            <h2 style="margin: 0.4rem 0; color: #3B82F6;">₹{disposable:,.0f}</h2>
            <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">Income - Expenses</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        debt_ratio = financial_data['debt_ratio']
        debt_color = "#10B981" if debt_ratio <= 0.1 else "#F59E0B" if debt_ratio <= 0.3 else "#EF4444"
        st.markdown(f"""
        <div class="card" style="border-left-color: {debt_color};">
            <h4 style="margin: 0;">Debt to Income Ratio</h4>
            <h2 style="margin: 0.4rem 0; color: {debt_color};">{debt_ratio:.1%}</h2>
            <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">{'🟢 Low' if debt_ratio <= 0.1 else '🟡 Moderate' if debt_ratio <= 0.3 else '🔴 High'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        savings_score = financial_data['savings_rate_score']
        savings_rate = (financial_data['disposable_income'] / st.session_state.answers.get('monthly_income', 1)) * 100
        savings_color = "#10B981" if savings_rate >= 20 else "#F59E0B" if savings_rate >= 10 else "#EF4444"
        st.markdown(f"""
        <div class="card" style="border-left-color: {savings_color};">
            <h4 style="margin: 0;">Savings Rate</h4>
            <h2 style="margin: 0.4rem 0; color: {savings_color};">{savings_rate:.1f}%</h2>
            <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">{'🟢 Good' if savings_rate >= 20 else '🟡 Okay' if savings_rate >= 10 else '🔴 Low'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed Breakdown
    st.markdown('<h3 class="section-header">📊 Financial Health Breakdown</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        # Emergency Fund Status
        emergency_score = int(st.session_state.answers.get('emergency', 3))
        emergency_labels = ["No fund", "1 month", "1-3 months", "3-6 months", "6+ months"]
        emergency_status = emergency_labels[emergency_score - 1]
        
        st.markdown("<div class='card'><h4 style='margin:0 0 1rem 0;'>🛡️ Emergency Fund Status</h4>", unsafe_allow_html=True)
        progress = emergency_score / 5.0
        st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress*100}%; background-color: #3B82F6;"></div>
        </div>
        <p style="margin: 0.5rem 0; font-weight: 600;">{emergency_status}</p>
        <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">
            {'✅ Recommended level reached' if emergency_score >= 4 else 
             '⚠️ Consider building to 3-6 months' if emergency_score >= 2 else 
             '🚨 Build emergency fund first'}
        </p>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Debt Analysis
        high_interest_debt = st.session_state.answers.get('high_interest_debt', 0)
        if high_interest_debt > 0:
            st.markdown("<div class='card' style='border-left-color: #EF4444;'><h4 style='margin:0 0 1rem 0;'>💳 High-Interest Debt</h4>", unsafe_allow_html=True)
            st.markdown(f"""
            <p style="margin: 0; font-weight: 600; color: #EF4444;">₹{high_interest_debt:,.0f}</p>
            <p style="margin: 0.5rem 0; color: #6B7280; font-size: 0.9rem;">
            Minimum monthly payment: ₹{high_interest_debt * 0.03:,.0f}
            </p>
            <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">
            {'🚨 Priority: Pay this before aggressive investing' if debt_ratio > 0.3 else 
             '⚠️ Consider paying down before increasing investments'}
            </p>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Income vs Expenses
        income = st.session_state.answers.get('monthly_income', 0)
        expenses = st.session_state.answers.get('monthly_expenses', 0)
        
        st.markdown("<div class='card'><h4 style='margin:0 0 1rem 0;'>📈 Income vs Expenses</h4>", unsafe_allow_html=True)
        
        # Create a simple bar chart using HTML
        max_val = max(income, expenses)
        income_width = (income / max_val) * 100 if max_val > 0 else 0
        expenses_width = (expenses / max_val) * 100 if max_val > 0 else 0
        
        st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                <span>Income</span>
                <span>₹{income:,.0f}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {income_width}%; background-color: #10B981;"></div>
            </div>
        </div>
        
        <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                <span>Expenses</span>
                <span>₹{expenses:,.0f}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {expenses_width}%; background-color: #EF4444;"></div>
            </div>
        </div>
        
        <div style="margin-top: 1rem; padding: 0.75rem; background-color: #F3F4F6; border-radius: 6px;">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: 600;">Disposable Income</span>
                <span style="font-weight: 600; color: #3B82F6;">₹{income-expenses:,.0f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Priority Actions
    st.markdown('<h3 class="section-header">🎯 Priority Actions</h3>', unsafe_allow_html=True)
    
    investment_data = st.session_state.safe_investment or {}
    if not investment_data:
        st.warning("Investment recommendations not ready.")
    else:
        # Create action cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if investment_data.get('ef_gap_amount', 0) > 0:
                st.markdown(f"""
                <div class="card" style="border-left-color: #EF4444;">
                    <h4 style="margin:0 0 0.5rem 0; color: #EF4444;">🔴 Build Emergency Fund</h4>
                    <p style="margin: 0 0 0.5rem 0; font-weight: 600;">₹{investment_data['ef_gap_amount']:,.0f} needed</p>
                    <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">
                    Save ₹{investment_data['monthly_ef_saving']:,.0f}/month
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: #6B7280; font-size: 0.9rem;">
                    Target: 6 months of expenses
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if st.session_state.answers.get('high_interest_debt', 0) > 0:
                st.markdown(f"""
                <div class="card" style="border-left-color: #F59E0B;">
                    <h4 style="margin:0 0 0.5rem 0; color: #F59E0B;">🟡 Pay High-Interest Debt</h4>
                    <p style="margin: 0 0 0.5rem 0; font-weight: 600;">₹{st.session_state.answers.get('high_interest_debt', 0):,.0f} total</p>
                    <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">
                    Minimum payment: ₹{investment_data['monthly_debt_payment']:,.0f}/month
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: #6B7280; font-size: 0.9rem;">
                    Priority before aggressive investing
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if investment_data.get('safe_monthly_investment', 0) > 0:
                st.markdown(f"""
                <div class="card" style="border-left-color: #10B981;">
                    <h4 style="margin:0 0 0.5rem 0; color: #10B981;">🟢 Start Investing</h4>
                    <p style="margin: 0 0 0.5rem 0; font-weight: 600;">₹{investment_data['safe_monthly_investment']:,.0f}/month</p>
                    <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">
                    Safe amount after priorities
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: #6B7280; font-size: 0.9rem;">
                    {investment_data['investment_tier']:.0f}% of disposable income
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card" style="border-left-color: #F59E0B;">
                    <h4 style="margin:0 0 0.5rem 0; color: #F59E0B;">🟡 Increase Savings</h4>
                    <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">
                    Your disposable income is insufficient for investing
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: #6B7280; font-size: 0.9rem;">
                    Focus on reducing expenses or increasing income first
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    # Navigation buttons
    st.markdown("---")
    create_navigation_buttons()

# -------------------------
# Risk Profile Tab (UPDATED with navigation)
# -------------------------
def create_risk_profile_tab():
    st.markdown('<h1 class="main-header">🎯 Risk Profile Analysis</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        st.button("Go to Assessment", on_click=lambda: setattr(st.session_state, 'current_tab', 'Assessment'))
        return
    
    risk_scores = st.session_state.risk_scores or {}
    risk_category = st.session_state.risk_category or "Unknown"
    confidence_score = st.session_state.confidence_score or {'score': 0, 'level': 'LOW', 'penalties': []}
    override_log = st.session_state.override_log or []
    
    # Risk Category Display
    category_colors = {
        "VERY LOW RISK": "#10B981",
        "LOW RISK": "#34D399",
        "MEDIUM RISK": "#F59E0B",
        "HIGH RISK": "#F97316",
        "VERY HIGH RISK": "#EF4444"
    }
    category_icons = {
        "VERY LOW RISK": "🟢",
        "LOW RISK": "🟢",
        "MEDIUM RISK": "🟡",
        "HIGH RISK": "🟠",
        "VERY HIGH RISK": "🔴"
    }
    color = category_colors.get(risk_category, "#6B7280")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div style="background-color: {color}20; padding: 1.25rem; border-radius: 10px; border-left: 5px solid {color};">
            <h2 style="margin: 0; color: {color};">{category_icons.get(risk_category, '⚫')} {risk_category}</h2>
            <p style="margin: 0.5rem 0 0 0; color: #6B7280;">Based on your 90-point risk assessment</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        conf_color = "#10B981" if confidence_score['score'] >= 80 else "#F59E0B" if confidence_score['score'] >= 60 else "#EF4444"
        st.markdown(f"""
        <div class="card">
            <h4 style="margin: 0;">Confidence Score</h4>
            <h2 style="margin: 0.4rem 0; color: {conf_color};">{confidence_score['score']}/100</h2>
            <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">{confidence_score['level']} Confidence</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Risk Score Breakdown
    st.markdown('<h3 class="section-header">📊 Risk Score Breakdown (90-point system)</h3>', unsafe_allow_html=True)
    
    scores = [
        ("Risk Capacity", risk_scores.get('risk_capacity', 0), 40, "#3B82F6", "Financial ability to take risk"),
        ("Risk Tolerance", risk_scores.get('risk_tolerance', 0), 30, "#10B981", "Psychological comfort with risk"),
        ("Risk Requirement", risk_scores.get('risk_requirement', 0), 20, "#8B5CF6", "Risk needed for your goals"),
        ("Total Score", risk_scores.get('total_score', 0), 90, color, "Overall risk profile")
    ]
    
    for label, score, max_score, bar_color, description in scores:
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.35rem;">
                    <span style="font-weight: 600;">{label}</span>
                    <span style="font-weight: 600; color: {bar_color};">{score}/{max_score}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {percentage}%; background-color: {bar_color};"></div>
                </div>
                <p style="margin: 0.25rem 0 0 0; color: #6B7280; font-size: 0.9rem;">{description}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Safety Overrides
    st.markdown('<h3 class="section-header">🛡️ Safety Overrides Applied</h3>', unsafe_allow_html=True)
    if override_log:
        for override in override_log:
            st.info(f"✅ {override}")
    else:
        st.success("✅ No safety overrides were needed for your profile")
    
    # Confidence Score Details
    if confidence_score.get('penalties'):
        st.markdown('<h3 class="section-header">📉 Confidence Score Factors</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div class="warning-box">
            <strong>Factors affecting your confidence score:</strong>
        </div>
        """, unsafe_allow_html=True)
        for penalty in confidence_score['penalties']:
            st.markdown(f"⚠️ {penalty}")
    
    # Navigation buttons
    st.markdown("---")
    create_navigation_buttons()

# -------------------------
# Recommendations Tab (UPDATED with navigation)
# -------------------------
def create_recommendations_tab():
    st.markdown('<h1 class="main-header">💼 Stock Investment Recommendations</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        st.button("Go to Assessment", on_click=lambda: setattr(st.session_state, 'current_tab', 'Assessment'))
        return
    
    allocation = st.session_state.allocation or {}
    investment_data = st.session_state.safe_investment or {}
    risk_category = st.session_state.risk_category or "Unknown"
    
    # Investment Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        monthly_inv = investment_data.get('safe_monthly_investment', 0.0)
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 1.1rem;">Monthly Investment</h3>
            <h1 style="margin: 0.35rem 0; font-size: 2rem; color: white;">₹{monthly_inv:,.0f}</h1>
            <p style="margin: 0;">Safe amount after priorities</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        annual_inv = investment_data.get('annual_investment', 0.0)
        st.markdown(f"""
        <div class="card" style="border-left-color: #10B981;">
            <h4 style="margin: 0;">Annual Investment</h4>
            <h2 style="margin: 0.4rem 0; color: #10B981;">₹{annual_inv:,.0f}</h2>
            <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">12 × Monthly</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        tier = investment_data.get('investment_tier', 0.0)
        st.markdown(f"""
        <div class="card" style="border-left-color: #8B5CF6;">
            <h4 style="margin: 0;">Investment Tier</h4>
            <h2 style="margin: 0.4rem 0; color: #8B5CF6;">{tier:.0f}% of Disposable</h2>
            <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">Based on financial health</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Portfolio Allocation
    st.markdown('<h3 class="section-header">📊 Stock Allocation for Your Risk Profile</h3>', unsafe_allow_html=True)
    
    if not allocation:
        st.info("No allocation available. Please complete assessment.")
        return
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Pie chart for allocation
        labels = list(allocation.keys())
        values = list(allocation.values())
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][:len(labels)]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4, marker_colors=colors, textinfo='label+percent')])
        fig.update_layout(height=360, showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("<div style='background-color:#F9FAFB; padding:1rem; border-radius:10px;'>", unsafe_allow_html=True)
        monthly_inv = investment_data.get('safe_monthly_investment', 0.0)
        for category, percentage in allocation.items():
            amount = (percentage / 100.0) * monthly_inv
            st.markdown(f"""
            <div style="margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid #E5E7EB;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:600;">{category}</span>
                    <span style="font-weight:600; color:#1F2937;">{percentage}%</span>
                </div>
                <div style="color:#6B7280; font-size:0.9rem;">₹{amount:,.0f}/month</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recommended Stocks
    st.markdown('<h3 class="section-header">💎 Recommended Stocks (Examples)</h3>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>💡 Note:</strong> These are example stocks for educational purposes. 
        Always do your own research or consult a financial advisor before investing.
    </div>
    """, unsafe_allow_html=True)
    
    mapped_categories = []
    for alloc_key, perc in allocation.items():
        db_key = ALLOCATION_TO_DB.get(alloc_key, alloc_key)
        if perc > 0 and db_key in STOCKS_DB:
            mapped_categories.append((db_key, perc))
    
    if not mapped_categories:
        st.info("No matching stocks in the database for your allocation.")
    else:
        for category, perc in mapped_categories:
            st.markdown(f"### **{category}** ({perc}% allocation)")
            stocks = STOCKS_DB.get(category, [])
            num_to_show = min(4, len(stocks))
            
            cols = st.columns(num_to_show)
            for idx, stock in enumerate(stocks[:num_to_show]):
                with cols[idx]:
                    st.markdown(f"""
                    <div style="background-color:white; padding:1rem; border-radius:8px; border:1px solid #E5E7EB; margin-bottom:0.5rem; height: 180px;">
                        <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:0.4rem;">
                            <span style="font-weight:700; font-size:1.05rem;">{stock['symbol']}</span>
                            <span style="background-color:#F3F4F6; padding:0.25rem 0.5rem; border-radius:4px; font-size:0.8rem;">{stock['market_cap']}</span>
                        </div>
                        <p style="margin:0 0 0.4rem 0; color:#1F2937; font-size:0.95rem;">{stock['name']}</p>
                        <div style="background-color:#E0F2FE; padding:0.25rem 0.5rem; border-radius:4px; display:inline-block;">
                            <span style="color:#0EA5E9; font-size:0.85rem;">{stock['sector']}</span>
                        </div>
                        <div style="margin-top:1rem; padding-top:0.5rem; border-top:1px solid #E5E7EB;">
                            <p style="margin:0; color:#6B7280; font-size:0.8rem;">Example allocation: ₹{(perc/100 * monthly_inv * (1/num_to_show)):,.0f}/month</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("---")
    
    # Navigation buttons
    st.markdown("---")
    create_navigation_buttons()

# -------------------------
# Action Plan Tab (UPDATED with navigation)
# -------------------------
def create_action_plan_tab():
    st.markdown('<h1 class="main-header">🚀 Your Personalized Action Plan</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        st.button("Go to Assessment", on_click=lambda: setattr(st.session_state, 'current_tab', 'Assessment'))
        return
    
    investment_data = st.session_state.safe_investment or {}
    
    # Implementation Timeline
    st.markdown('<h3 class="section-header">📅 Implementation Timeline</h3>', unsafe_allow_html=True)
    
    timeline_steps = []
    if investment_data.get('ef_gap_amount', 0) > 0:
        timeline_steps.append({
            "title": "Build Emergency Fund", 
            "duration": f"{investment_data['ef_build_timeline']} months", 
            "action": f"Save ₹{investment_data['monthly_ef_saving']:,.0f}/month", 
            "priority": "🔴 HIGH",
            "icon": "🛡️"
        })
    
    if st.session_state.answers.get('high_interest_debt', 0) > 0:
        timeline_steps.append({
            "title": "Pay High-Interest Debt", 
            "duration": "Ongoing", 
            "action": f"Pay ₹{investment_data['monthly_debt_payment']:,.0f}/month minimum", 
            "priority": "🟡 MEDIUM",
            "icon": "💳"
        })
    
    if investment_data.get('safe_monthly_investment', 0) > 0:
        timeline_steps.append({
            "title": "Start Investing", 
            "duration": "Immediate", 
            "action": f"Invest ₹{investment_data['safe_monthly_investment']:,.0f}/month", 
            "priority": "🟢 LOW",
            "icon": "📈"
        })
    
    for i, step in enumerate(timeline_steps):
        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
        with col1:
            st.markdown(f"<h1 style='margin: 0;'>{step['icon']}</h1>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="padding:0.75rem;">
                <h4 style="margin:0 0 0.5rem 0;">{i+1}. {step['title']}</h4>
                <p style="margin:0; color:#4B5563;">{step['action']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="padding:0.75rem; background-color:#F3F4F6; border-radius:8px;">
                <p style="margin:0; color:#6B7280; font-weight:600;">Duration</p>
                <p style="margin:0.25rem 0 0 0; color:#1F2937; font-weight:600;">{step['duration']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            priority_color = "#EF4444" if "HIGH" in step['priority'] else "#F59E0B" if "MEDIUM" in step['priority'] else "#10B981"
            st.markdown(f"""
            <div style="padding:0.75rem; background-color:{priority_color}10; border-radius:8px;">
                <p style="margin:0; color:{priority_color}; font-weight:600;">{step['priority']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Monthly Checklist
    st.markdown('<h3 class="section-header">✅ Monthly Checklist</h3>', unsafe_allow_html=True)
    
    checklist_items = []
    if investment_data.get('monthly_ef_saving', 0) > 0:
        checklist_items.append(f"Save ₹{investment_data['monthly_ef_saving']:,.0f} for emergency fund")
    if investment_data.get('monthly_debt_payment', 0) > 0:
        checklist_items.append(f"Pay ₹{investment_data['monthly_debt_payment']:,.0f} towards high-interest debt")
    if investment_data.get('safe_monthly_investment', 0) > 0:
        checklist_items.append(f"Invest ₹{investment_data['safe_monthly_investment']:,.0f} as per allocation")
    checklist_items.append("Review monthly expenses and budget")
    checklist_items.append("Track net worth growth")
    
    for i, item in enumerate(checklist_items):
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            st.markdown(f"<div style='margin-top: 0.5rem;'>✅</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='margin-top: 0.5rem;'>{item}</div>", unsafe_allow_html=True)
    
    # Quarterly Review
    st.markdown('<h3 class="section-header">📋 Quarterly Review (Every 3 Months)</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card">
            <h4 style="margin:0 0 1rem 0;">📊 Portfolio Check</h4>
            <ul style="margin:0; padding-left:1.5rem; color:#4B5563;">
                <li>Review allocation percentages</li>
                <li>Check if rebalancing needed (±5%)</li>
                <li>Review stock performance</li>
                <li>Update financial health score</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
            <h4 style="margin:0 0 1rem 0;">💰 Financial Check</h4>
            <ul style="margin:0; padding-left:1.5rem; color:#4B5563;">
                <li>Update income & expenses</li>
                <li>Check emergency fund status</li>
                <li>Review debt reduction progress</li>
                <li>Adjust SIP if income changes</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Export Options
    st.markdown('<h3 class="section-header">📄 Export Your Plan</h3>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    # PDF Export
    with col1:
        if st.session_state.assessment_complete:
            assessment_data = {
                'answers': st.session_state.answers,
                'financial_data': st.session_state.financial_health_score,
                'risk_scores': st.session_state.risk_scores,
                'risk_category': st.session_state.risk_category,
                'override_log': st.session_state.override_log,
                'allocation': st.session_state.allocation,
                'contradictions': st.session_state.contradictions,
                'investment_data': st.session_state.safe_investment,
                'confidence_score': st.session_state.confidence_score
            }
            
            pdf_generator = AssessmentPDF(assessment_data)
            pdf_buffer = pdf_generator.generate_pdf()
            pdf_bytes = pdf_buffer.getvalue()
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Stock_Risk_Advisor_Plan_{st.session_state.assessment_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    # CSV Export
    with col2:
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r') as file:
                csv_data = file.read()
            
            st.download_button(
                label="📊 Download All Data CSV",
                data=csv_data,
                file_name="all_assessments.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # JSON Export
    with col3:
        if st.session_state.assessment_complete:
            assessment_json = json.dumps({
                'assessment_id': st.session_state.assessment_id,
                'timestamp': datetime.now().isoformat(),
                'answers': st.session_state.answers,
                'financial_health_score': st.session_state.financial_health_score,
                'risk_scores': st.session_state.risk_scores,
                'risk_category': st.session_state.risk_category,
                'safe_investment': st.session_state.safe_investment,
                'allocation': st.session_state.allocation
            }, indent=2)
            
            st.download_button(
                label="📁 Download JSON Report",
                data=assessment_json,
                file_name=f"assessment_{st.session_state.assessment_id}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Navigation and Reset
    st.markdown("---")
    create_navigation_buttons()
    
    st.markdown("### Want to start over?")
    if st.button("🔄 Start New Assessment", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.rerun()

# -------------------------
# Data & Export Tab
# -------------------------
def create_data_export_tab():
    st.markdown('<h1 class="main-header">📊 Data Management & Export</h1>', unsafe_allow_html=True)
    
    df = CSVDataHandler.load_assessments_from_csv()
    
    if df.empty:
        st.info("No assessment data available yet. Complete an assessment to see data here.")
        st.button("Go to Assessment", on_click=lambda: setattr(st.session_state, 'current_tab', 'Assessment'))
        return
    
    # Statistics
    st.markdown('<h3 class="section-header">📈 Assessment Statistics</h3>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Assessments", len(df))
    with col2:
        st.metric("Avg Financial Health", f"{df['financial_health_score'].mean():.1f}")
    with col3:
        st.metric("Avg Monthly Investment", f"₹{df['monthly_investment'].mean():,.0f}")
    with col4:
        most_common_risk = df['risk_category'].mode().iloc[0] if not df['risk_category'].mode().empty else 'N/A'
        st.metric("Most Common Risk", most_common_risk)
    
    # Recent Assessments
    st.markdown('<h3 class="section-header">📋 Recent Assessments</h3>', unsafe_allow_html=True)
    
    recent_df = df.tail(10).copy()
    recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp'])
    recent_df = recent_df.sort_values('timestamp', ascending=False)
    
    display_df = recent_df[['timestamp', 'monthly_income', 'monthly_expenses', 
                           'financial_health_score', 'risk_category', 'monthly_investment']].copy()
    display_df['monthly_income'] = display_df['monthly_income'].apply(lambda x: f"₹{x:,.0f}")
    display_df['monthly_expenses'] = display_df['monthly_expenses'].apply(lambda x: f"₹{x:,.0f}")
    display_df['monthly_investment'] = display_df['monthly_investment'].apply(lambda x: f"₹{x:,.0f}")
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(display_df, use_container_width=True)
    
    # Visualizations
    st.markdown('<h3 class="section-header">📊 Data Visualizations</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        risk_counts = df['risk_category'].value_counts()
        fig1 = px.pie(values=risk_counts.values, names=risk_counts.index, 
                     title="Risk Category Distribution")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.histogram(df, x='financial_health_score', nbins=20,
                           title="Financial Health Score Distribution")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Export Options
    st.markdown('<h3 class="section-header">📁 Export Options</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📊 Download Full CSV",
            data=csv,
            file_name="all_assessments_full.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        summary_stats = df.describe().to_string()
        st.download_button(
            label="📈 Download Summary Stats",
            data=summary_stats,
            file_name="assessment_summary.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
            st.warning("This will delete all assessment data. Are you sure?")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("Yes, Delete All Data"):
                    try:
                        os.remove(CSV_FILE)
                        st.success("All assessment data has been cleared!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {str(e)}")
            with col_cancel:
                if st.button("Cancel"):
                    st.rerun()
    
    # Navigation
    st.markdown("---")
    create_navigation_buttons()

# -------------------------
# MAIN FUNCTION
# -------------------------
def main():
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/stock-exchange.png", width=80)
        st.title("Stock Risk Advisor")
        st.markdown("---")
        
        st.subheader("📊 Navigation")
        tabs = ["Welcome", "Assessment", "Financial Health", "Risk Profile", "Recommendations", "Action Plan", "Data & Export"]
        for tab in tabs:
            if st.button(f"📝 {tab}", key=f"nav_{tab}", use_container_width=True):
                st.session_state.current_tab = tab
                st.rerun()
        
        st.markdown("---")
        
        if st.session_state.assessment_complete:
            st.success("✅ Assessment Complete")
            if st.button("🔄 Start New Assessment", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                init_session_state()
                st.rerun()
        else:
            st.info("📋 Complete assessment to see results")
        
        st.markdown("---")
        
        # Statistics
        stats = CSVDataHandler.get_statistics()
        if stats and stats['total_assessments'] > 0:
            with st.expander("📈 Overall Statistics"):
                st.metric("Total Assessments", stats['total_assessments'])
                st.metric("Avg Financial Health", f"{stats['avg_financial_health']:.1f}")
                st.metric("Most Common Risk", stats['most_common_risk_category'])
                st.metric("Avg Monthly Investment", f"₹{stats['avg_monthly_investment']:,.0f}")
        
        with st.expander("ℹ️ About This Tool"):
            st.markdown("""
            **How it works:**
            1. Answer 12 questions about your finances
            2. Get your Financial Health Score
            3. Receive personalized risk assessment
            4. Get stock recommendations matching your profile
            5. Create an actionable investment plan

            **Features:**
            ✅ Financial Health Assessment
            ✅ Risk Profiling (90-point system)
            ✅ Safe Investment Calculator
            ✅ Personalized Stock Allocation
            ✅ Safety Overrides for Protection
            ✅ PDF Export & CSV Data Storage

            ⚠️ **Educational purpose only.** Not financial advice.
            """)
    
    # Main content with progress bar
    create_progress_bar()
    
    # Show current tab
    current_tab = st.session_state.current_tab
    if current_tab == "Welcome":
        create_welcome_tab()
    elif current_tab == "Assessment":
        create_assessment_tab()
    elif current_tab == "Financial Health":
        create_financial_health_tab()
    elif current_tab == "Risk Profile":
        create_risk_profile_tab()
    elif current_tab == "Recommendations":
        create_recommendations_tab()
    elif current_tab == "Action Plan":
        create_action_plan_tab()
    elif current_tab == "Data & Export":
        create_data_export_tab()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align:center; color:#6B7280; font-size:0.9rem; padding:1rem 0;'>
        <p>⚠️ <strong>Educational Purpose Only</strong> - This tool helps understand stock investing based on risk profiles.</p>
        <p>We are not SEBI-registered investment advisors. This is not financial advice.</p>
        <p>Data is stored locally in CSV format for analysis and export.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
