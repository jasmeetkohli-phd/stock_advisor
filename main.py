# stock_risk_advisor_enhanced_v3_with_inflation.py
# Complete working version with all tabs and inflation features

import os
import json
import csv
import io
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Try to import ReportLab for PDF generation
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

APP_TITLE = "📈 Stock Risk Advisor"
APP_ICON = "📊"
MODEL_VERSION = "3.3"
MINIMUM_INVESTMENT_THRESHOLD = 500
CSV_FILE = "assessments_data_v3.csv"

# Age-equity mapping
AGE_EQUITY_MAP = {
    1: 85, 2: 75, 3: 65, 4: 55, 5: 40, 6: 30
}

# Timeframe mapping
TIMEFRAME_MAP = {
    1: 1, 2: 3, 3: 6, 4: 10, 5: 15, 6: 10
}

# Scoring weights
WEIGHTS = {
    "financial_stability": 0.25,
    "debt_situation": 0.15,
    "risk_tolerance": 0.25,
    "investment_horizon": 0.20,
    "knowledge_experience": 0.15
}

# Enhanced stock database
STOCKS_DB = {
    "Large_Cap": [
        {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy", 
         "risk": "Low", "note": "Market leader", "inflation_performance": "Good",
         "esg_rating": "Medium", "growth_focus": "High", "inflation_protection": "Medium"},
        {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT", 
         "risk": "Low", "note": "IT services giant", "inflation_performance": "Medium",
         "esg_rating": "High", "growth_focus": "Medium", "inflation_protection": "Medium"},
        {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking", 
         "risk": "Low", "note": "Premier private bank", "inflation_performance": "Good",
         "esg_rating": "Medium", "growth_focus": "High", "inflation_protection": "Low"},
        {"symbol": "INFY", "name": "Infosys", "sector": "IT", 
         "risk": "Low", "note": "Global IT consulting", "inflation_performance": "Medium",
         "esg_rating": "High", "growth_focus": "Medium", "inflation_protection": "Medium"},
        {"symbol": "ITC", "name": "ITC Limited", "sector": "FMCG", 
         "risk": "Low", "note": "Diversified conglomerate", "inflation_performance": "Excellent",
         "esg_rating": "High", "growth_focus": "Medium", "inflation_protection": "High"},
    ],
    "Mid_Cap": [
        {"symbol": "TITAN", "name": "Titan Company", "sector": "Consumer", 
         "risk": "Medium", "note": "Lifestyle brand leader", "inflation_performance": "Good",
         "esg_rating": "Medium", "growth_focus": "High", "inflation_protection": "Medium"},
        {"symbol": "ASIANPAINT", "name": "Asian Paints", "sector": "Paints", 
         "risk": "Medium", "note": "Paint industry leader", "inflation_performance": "Good",
         "esg_rating": "Medium", "growth_focus": "High", "inflation_protection": "Medium"},
        {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "sector": "Financial", 
         "risk": "Medium-High", "note": "Consumer financing leader", "inflation_performance": "Medium",
         "esg_rating": "Low", "growth_focus": "High", "inflation_protection": "Low"},
        {"symbol": "DABUR", "name": "Dabur India", "sector": "FMCG", 
         "risk": "Medium", "note": "Ayurvedic products", "inflation_performance": "Excellent",
         "esg_rating": "High", "growth_focus": "Medium", "inflation_protection": "High"},
    ],
    "Small_Cap": [
        {"symbol": "TATAELXSI", "name": "Tata Elxsi", "sector": "IT", 
         "risk": "High", "note": "Design services", "inflation_performance": "Medium",
         "esg_rating": "High", "growth_focus": "High", "inflation_protection": "Medium"},
        {"symbol": "LAURUSLABS", "name": "Laurus Labs", "sector": "Pharma", 
         "risk": "High", "note": "Pharmaceuticals", "inflation_performance": "Good",
         "esg_rating": "Medium", "growth_focus": "High", "inflation_protection": "Medium"},
    ],
    "Growth": [
        {"symbol": "DMART", "name": "Avenue Supermarts", "sector": "Retail", 
         "risk": "Medium-High", "note": "Value retail chain", "inflation_performance": "Excellent",
         "esg_rating": "Medium", "growth_focus": "High", "inflation_protection": "High"},
        {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv", "sector": "Financial", 
         "risk": "Medium-High", "note": "Financial services", "inflation_performance": "Medium",
         "esg_rating": "Medium", "growth_focus": "High", "inflation_protection": "Low"},
        {"symbol": "TECHM", "name": "Tech Mahindra", "sector": "IT", 
         "risk": "Medium", "note": "Digital transformation", "inflation_performance": "Medium",
         "esg_rating": "High", "growth_focus": "Medium", "inflation_protection": "Medium"},
    ],
    "Inflation_Protection": [
        {"symbol": "NESTLEIND", "name": "Nestle India", "sector": "FMCG", 
         "risk": "Low", "note": "Food & beverage", "inflation_performance": "Excellent",
         "esg_rating": "High", "growth_focus": "Medium", "inflation_protection": "Excellent"},
        {"symbol": "HINDUNILVR", "name": "Hindustan Unilever", "sector": "FMCG", 
         "risk": "Low", "note": "Consumer goods", "inflation_performance": "Excellent",
         "esg_rating": "High", "growth_focus": "Medium", "inflation_protection": "Excellent"},
        {"symbol": "BRITANNIA", "name": "Britannia Industries", "sector": "FMCG", 
         "risk": "Medium", "note": "Food products", "inflation_performance": "Excellent",
         "esg_rating": "High", "growth_focus": "Medium", "inflation_protection": "High"},
    ]
}

# ETF database
ETFS_DB = {
    "VERY LOW RISK": ["NIFTYBEES", "GOLDBEES"],
    "LOW RISK": ["NIFTYBEES", "MIDCAPBEES"],
    "MEDIUM RISK": ["NIFTYBEES", "MIDCAPBEES"],
    "HIGH RISK": ["MIDCAPBEES", "SMLCAPBEES"],
    "VERY HIGH RISK": ["SMLCAPBEES"]
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency(value: float) -> str:
    """Format currency with Indian numbering system"""
    if value >= 10000000:
        return f"₹{value/10000000:.2f} crore"
    elif value >= 100000:
        return f"₹{value/100000:.2f} lakh"
    else:
        return f"₹{value:,.0f}"

# ============================================================================
# CORE CLASSES
# ============================================================================

class RiskCalculator:
    """Enhanced calculator with inflation and ESG features"""
    
    @staticmethod
    def map_to_score(value: int, min_val: int = 1, max_val: int = 6, reverse: bool = False) -> float:
        """Map 1-6 scale to 0-100 score"""
        if reverse:
            value = max_val - value + min_val
        return ((value - min_val) / (max_val - min_val)) * 100
    
    @staticmethod
    def validate_answers(answers: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate answers for consistency"""
        warnings = []
        
        required_questions = [
            'income', 'expenses', 'emergency_fund', 'loan_types',
            'emi_percentage', 'income_stability', 'dependents',
            'primary_goal', 'timeframe', 'loss_avoidance', 'market_drop_reaction',
            'experience', 'knowledge', 'liquidity_needs', 'age_group'
        ]
        
        for q in required_questions:
            if q not in answers or answers[q] is None:
                return False, [f"Required question '{q}' not answered"]
        
        # Basic validations
        income = answers.get('income', 0)
        expenses = answers.get('expenses', 0)
        
        if expenses > income * 0.95:
            warnings.append("Your expenses seem very high relative to income.")
        
        if expenses > income:
            warnings.append("⚠️ **Critical Issue:** Expenses exceed income.")
        
        return True, warnings
    
    @staticmethod
    def calculate_financial_score(answers: Dict[str, Any]) -> Dict[str, float]:
        """Calculate Financial Health Score"""
        monthly_income = answers.get('income', 0)
        monthly_expenses = answers.get('expenses', 0)
        emergency_score = answers.get('emergency_fund', 3)
        income_stability_score = answers.get('income_stability', 3)
        dependents_count = answers.get('dependents', 0)
        
        # Emergency fund to months
        emergency_months_map = {1: 0, 2: 0.5, 3: 2, 4: 5, 5: 9.5, 6: 15}
        emergency_months = emergency_months_map.get(emergency_score, 2)
        
        # Components
        emergency_component = RiskCalculator.map_to_score(emergency_score)
        income_stability_component = RiskCalculator.map_to_score(income_stability_score, reverse=True)
        dependents_adjustment = max(0, 100 - (dependents_count * 15))
        
        # Savings rate
        if monthly_income > 0:
            savings_rate = (monthly_income - monthly_expenses) / monthly_income
            if savings_rate <= 0:
                savings_rate_component = 0
            elif savings_rate >= 0.3:
                savings_rate_component = 100
            else:
                savings_rate_component = (savings_rate / 0.3) * 100
        else:
            savings_rate_component = 0
        
        # Final score
        financial_score = (
            0.35 * emergency_component +
            0.25 * income_stability_component +
            0.20 * dependents_adjustment +
            0.20 * savings_rate_component
        )
        
        disposable_income = max(0, monthly_income - monthly_expenses)
        savings_rate_pct = (disposable_income / monthly_income * 100) if monthly_income > 0 else 0
        
        return {
            'financial_score': round(financial_score, 2),
            'emergency_component': round(emergency_component, 2),
            'income_stability_component': round(income_stability_component, 2),
            'dependents_adjustment': round(dependents_adjustment, 2),
            'savings_component': round(savings_rate_component, 2),
            'disposable_income': round(disposable_income, 2),
            'savings_rate': round(savings_rate_pct, 2),
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'emergency_months': emergency_months,
            'income_stability': income_stability_score,
            'dependents_count': dependents_count
        }
    
    @staticmethod
    def calculate_debt_score(answers: Dict[str, Any]) -> Dict[str, float]:
        """Calculate Debt Score"""
        loan_types = answers.get('loan_types', [])
        emi_percentage_score = answers.get('emi_percentage', 1)
        
        # Debt classification
        good_debt_types = {'home_loan', 'education_loan', 'business_loan'}
        bad_debt_types = {'personal_loan', 'credit_card', 'consumer_loan', 'payday_loan'}
        neutral_debt_types = {'gold_loan', 'property_loan'}
        
        good_debt_count = len([lt for lt in loan_types if lt in good_debt_types])
        bad_debt_count = len([lt for lt in loan_types if lt in bad_debt_types])
        neutral_debt_count = len([lt for lt in loan_types if lt in neutral_debt_types])
        
        # Loan type score
        if not loan_types:
            loan_type_score = 100
        else:
            base_score = 50
            loan_type_score = base_score + (good_debt_count * 20) - (bad_debt_count * 30) + (neutral_debt_count * 5)
            loan_type_score = max(0, min(100, loan_type_score))
        
        # EMI score
        emi_percentage_map = {1: 100, 2: 75, 3: 50, 4: 25}
        emi_score = emi_percentage_map.get(emi_percentage_score, 50)
        
        # Overall debt score
        if loan_types:
            debt_score = (0.60 * loan_type_score) + (0.40 * emi_score)
        else:
            debt_score = 100
        
        return {
            'debt_score': round(debt_score, 2),
            'loan_type_score': round(loan_type_score, 2),
            'emi_score': round(emi_score, 2),
            'good_debt_count': good_debt_count,
            'bad_debt_count': bad_debt_count,
            'neutral_debt_count': neutral_debt_count,
            'has_debt': len(loan_types) > 0,
            'emi_percentage_category': emi_percentage_score
        }
    
    @staticmethod
    def calculate_risk_tolerance(answers: Dict[str, Any]) -> Dict[str, float]:
        """Calculate Risk Tolerance Score"""
        loss_avoidance_score = answers.get('loss_avoidance', 3)
        market_drop_reaction_score = answers.get('market_drop_reaction', 3)
        
        loss_avoidance = RiskCalculator.map_to_score(loss_avoidance_score, reverse=True)
        emotional_reaction = RiskCalculator.map_to_score(market_drop_reaction_score)
        
        # ESG adjustment
        esg_importance = answers.get('esg_importance', 1)
        esg_adjustment = 0
        if esg_importance == 4:
            esg_adjustment = -20
        elif esg_importance == 3:
            esg_adjustment = -10
        elif esg_importance == 2:
            esg_adjustment = -5
        
        risk_tolerance_score = (
            0.60 * loss_avoidance +
            0.40 * emotional_reaction
        ) + esg_adjustment
        
        risk_tolerance_score = max(0, min(100, risk_tolerance_score))
        
        # Max tolerable loss
        if loss_avoidance >= 80:
            max_loss = 10
        elif loss_avoidance >= 60:
            max_loss = 20
        elif loss_avoidance >= 40:
            max_loss = 30
        else:
            max_loss = 40
        
        return {
            'risk_tolerance_score': round(risk_tolerance_score, 2),
            'loss_avoidance': round(loss_avoidance, 2),
            'emotional_reaction': round(emotional_reaction, 2),
            'esg_adjustment': esg_adjustment,
            'max_tolerable_loss_pct': max_loss,
            'esg_importance': esg_importance
        }
    
    @staticmethod
    def calculate_horizon_score(answers: Dict[str, Any], dependent_answers: Dict[str, Any]) -> Dict[str, float]:
        """Calculate Investment Horizon Score"""
        primary_goal = answers.get('primary_goal')
        timeframe_score = answers.get('timeframe', 3)
        liquidity_score = answers.get('liquidity_needs', 4)
        
        timeframe_years = TIMEFRAME_MAP.get(timeframe_score, 6)
        
        # Goal adjustments
        goal_adjustment = 0
        goal_details = ""
        
        if primary_goal == 'capital_preservation':
            safety_importance = dependent_answers.get('capital_safety_importance', 2)
            if safety_importance == 1:
                goal_adjustment = -20
                goal_details = "Capital preservation focus"
            elif safety_importance == 2:
                goal_adjustment = 0
                goal_details = "Balanced capital preservation"
            else:
                goal_adjustment = 10
                goal_details = "Risk-tolerant capital preservation"
        
        elif primary_goal == 'regular_income':
            income_start = dependent_answers.get('income_start_timing', 2)
            if income_start == 1:
                goal_adjustment = -30
                goal_details = "Immediate income need"
            elif income_start == 2:
                goal_adjustment = -10
                goal_details = "Near-term income need"
            else:
                goal_adjustment = 10
                goal_details = "Long-term income planning"
        
        elif primary_goal == 'major_life_goal':
            goal_timeframe = dependent_answers.get('goal_timeframe', 3)
            if goal_timeframe == 1:
                goal_adjustment = -30
                goal_details = "Short-term major goal"
            elif goal_timeframe == 2:
                goal_adjustment = -10
                goal_details = "Medium-term major goal"
            elif goal_timeframe == 3:
                goal_adjustment = 10
                goal_details = "Long-term major goal"
            else:
                goal_adjustment = 20
                goal_details = "Very long-term major goal"
        
        elif primary_goal == 'retirement':
            years_to_retirement = dependent_answers.get('years_to_retirement', 2)
            if years_to_retirement == 1:
                goal_adjustment = -20
                goal_details = "Near retirement"
            elif years_to_retirement == 2:
                goal_adjustment = 10
                goal_details = "Mid-career retirement planning"
            else:
                goal_adjustment = 30
                goal_details = "Early career retirement planning"
        
        elif primary_goal == 'wealth_creation':
            investment_horizon = dependent_answers.get('wealth_horizon', 2)
            if investment_horizon == 1:
                goal_adjustment = -20
                goal_details = "Short-term wealth creation"
            elif investment_horizon == 2:
                goal_adjustment = 10
                goal_details = "Medium-term wealth creation"
            else:
                goal_adjustment = 30
                goal_details = "Long-term wealth creation"
        
        else:  # not_sure
            priority = dependent_answers.get('not_sure_priority', 4)
            if priority == 1:
                goal_adjustment = -20
                goal_details = "Safety priority"
            elif priority == 2:
                goal_adjustment = -10
                goal_details = "Income priority"
            elif priority == 3:
                goal_adjustment = 20
                goal_details = "Growth priority"
            else:
                goal_adjustment = 0
                goal_details = "Undecided"
        
        # Base components
        timeframe_component = RiskCalculator.map_to_score(timeframe_score)
        liquidity_component = RiskCalculator.map_to_score(liquidity_score, reverse=True)
        
        adjusted_timeframe = timeframe_component + goal_adjustment
        adjusted_timeframe = max(0, min(100, adjusted_timeframe))
        
        horizon_score = (
            0.60 * adjusted_timeframe +
            0.40 * liquidity_component
        )
        
        return {
            'horizon_score': round(horizon_score, 2),
            'timeframe_component': round(timeframe_component, 2),
            'liquidity_component': round(liquidity_component, 2),
            'goal_adjustment': goal_adjustment,
            'goal_details': goal_details,
            'timeframe_years': timeframe_years,
            'primary_goal': primary_goal
        }
    
    @staticmethod
    def calculate_knowledge_score(answers: Dict[str, Any]) -> Dict[str, float]:
        """Calculate Knowledge & Experience Score"""
        experience_score = answers.get('experience', 2)
        knowledge_score = answers.get('knowledge', 2)
        
        experience_component = RiskCalculator.map_to_score(experience_score)
        knowledge_component = RiskCalculator.map_to_score(knowledge_score)
        
        knowledge_score_value = (
            0.60 * experience_component +
            0.40 * knowledge_component
        )
        
        return {
            'knowledge_score': round(knowledge_score_value, 2),
            'experience_component': round(experience_component, 2),
            'knowledge_component': round(knowledge_component, 2)
        }
    
    @staticmethod
    def calculate_overall_risk_score(answers: Dict[str, Any], dependent_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Overall Risk Score"""
        financial_data = RiskCalculator.calculate_financial_score(answers)
        debt_data = RiskCalculator.calculate_debt_score(answers)
        risk_tolerance_data = RiskCalculator.calculate_risk_tolerance(answers)
        horizon_data = RiskCalculator.calculate_horizon_score(answers, dependent_answers)
        knowledge_data = RiskCalculator.calculate_knowledge_score(answers)
        
        overall_score = (
            WEIGHTS['financial_stability'] * financial_data['financial_score'] +
            WEIGHTS['debt_situation'] * debt_data['debt_score'] +
            WEIGHTS['risk_tolerance'] * risk_tolerance_data['risk_tolerance_score'] +
            WEIGHTS['investment_horizon'] * horizon_data['horizon_score'] +
            WEIGHTS['knowledge_experience'] * knowledge_data['knowledge_score']
        )
        
        return {
            'overall_risk_score': round(overall_score, 2),
            'financial_data': financial_data,
            'debt_data': debt_data,
            'risk_tolerance_data': risk_tolerance_data,
            'horizon_data': horizon_data,
            'knowledge_data': knowledge_data,
            'weights_used': WEIGHTS,
            'model_version': MODEL_VERSION
        }
    
    @staticmethod
    def get_risk_category(overall_risk_score: float) -> str:
        """Determine risk category based on score"""
        if overall_risk_score <= 20:
            return "VERY LOW RISK"
        elif overall_risk_score <= 40:
            return "LOW RISK"
        elif overall_risk_score <= 60:
            return "MEDIUM RISK"
        elif overall_risk_score <= 80:
            return "HIGH RISK"
        else:
            return "VERY HIGH RISK"
    
    @staticmethod
    def check_investment_suitability(answers: Dict[str, Any], financial_data: Dict[str, float]) -> Dict[str, Any]:
        """Check if user should invest in stocks at all"""
        emergency_months = financial_data.get('emergency_months', 0)
        income_stability = answers.get('income_stability', 3)
        debt_data = RiskCalculator.calculate_debt_score(answers)
        liquidity_score = answers.get('liquidity_needs', 4)
        
        warnings = []
        blocking_issues = []
        
        # CRITICAL ISSUES
        if emergency_months == 0:
            blocking_issues.append("No emergency savings")
        
        if income_stability == 4:
            blocking_issues.append("No current income")
        
        if debt_data['emi_percentage_category'] == 4:
            blocking_issues.append("Debt EMI exceeds 60% of income")
        
        if liquidity_score <= 1:
            blocking_issues.append("Very likely to need money within 1 year")
        
        # WARNINGS
        if emergency_months < 3:
            warnings.append(f"Emergency fund only {emergency_months:.1f} months (recommended: 3-6 months)")
        
        if income_stability >= 3:
            warnings.append("Income stability concerns")
        
        if debt_data['bad_debt_count'] > 0:
            warnings.append(f"Has {debt_data['bad_debt_count']} type(s) of bad debt")
        
        if liquidity_score <= 2:
            warnings.append("May need money within 1-2 years")
        
        # Determine suitability
        if blocking_issues:
            suitability = "NOT SUITABLE"
            recommendation = "Focus on building emergency fund, stabilizing income, and reducing high debt before investing"
        elif warnings:
            suitability = "CAUTION ADVISED"
            recommendation = "Consider addressing warnings before significant stock investment"
        else:
            suitability = "SUITABLE"
            recommendation = "Proceed with recommended investment plan"
        
        return {
            'suitability': suitability,
            'blocking_issues': blocking_issues,
            'warnings': warnings,
            'recommendation': recommendation
        }
    
    @staticmethod
    def determine_portfolio_allocation(overall_risk_score: float, answers: Dict[str, Any], 
                                     inflation_preference: str = "balanced") -> Dict[str, float]:
        """Determine portfolio allocation with inflation preference"""
        age_score = answers.get('age_group', 4)
        base_equity_pct = AGE_EQUITY_MAP.get(age_score, 65)
        
        risk_multiplier = overall_risk_score / 100
        adjusted_equity_pct = base_equity_pct * (0.6 + 0.4 * risk_multiplier)
        
        # Inflation preference adjustment
        inflation_adjustment = {
            "growth": 1.0,
            "balanced": 0.8,
            "protection": 0.6
        }.get(inflation_preference, 0.8)
        
        inflation_adjusted_equity = adjusted_equity_pct * inflation_adjustment
        
        # Inflation protection allocation
        inflation_protection_pct = 0
        if inflation_preference == "protection":
            inflation_protection_pct = 20
            inflation_adjusted_equity = max(0, inflation_adjusted_equity - inflation_protection_pct)
        elif inflation_preference == "balanced":
            inflation_protection_pct = 10
            inflation_adjusted_equity = max(0, inflation_adjusted_equity - inflation_protection_pct)
        
        # Distribute equity based on risk
        if overall_risk_score <= 20:
            allocation = {
                "Large_Cap": inflation_adjusted_equity * 0.9,
                "Mid_Cap": inflation_adjusted_equity * 0.1,
                "Small_Cap": 0,
                "Growth": 0,
                "Inflation_Protection": inflation_protection_pct,
                "Fixed_Income": 100 - inflation_adjusted_equity - inflation_protection_pct
            }
        elif overall_risk_score <= 40:
            allocation = {
                "Large_Cap": inflation_adjusted_equity * 0.7,
                "Mid_Cap": inflation_adjusted_equity * 0.3,
                "Small_Cap": 0,
                "Growth": 0,
                "Inflation_Protection": inflation_protection_pct,
                "Fixed_Income": 100 - inflation_adjusted_equity - inflation_protection_pct
            }
        elif overall_risk_score <= 60:
            allocation = {
                "Large_Cap": inflation_adjusted_equity * 0.5,
                "Mid_Cap": inflation_adjusted_equity * 0.3,
                "Small_Cap": inflation_adjusted_equity * 0.1,
                "Growth": inflation_adjusted_equity * 0.1,
                "Inflation_Protection": inflation_protection_pct,
                "Fixed_Income": 100 - inflation_adjusted_equity - inflation_protection_pct
            }
        elif overall_risk_score <= 80:
            allocation = {
                "Large_Cap": inflation_adjusted_equity * 0.3,
                "Mid_Cap": inflation_adjusted_equity * 0.3,
                "Small_Cap": inflation_adjusted_equity * 0.2,
                "Growth": inflation_adjusted_equity * 0.2,
                "Inflation_Protection": inflation_protection_pct,
                "Fixed_Income": 100 - inflation_adjusted_equity - inflation_protection_pct
            }
        else:
            allocation = {
                "Large_Cap": inflation_adjusted_equity * 0.1,
                "Mid_Cap": inflation_adjusted_equity * 0.25,
                "Small_Cap": inflation_adjusted_equity * 0.3,
                "Growth": inflation_adjusted_equity * 0.35,
                "Inflation_Protection": inflation_protection_pct,
                "Fixed_Income": 100 - inflation_adjusted_equity - inflation_protection_pct
            }
        
        # Normalize
        total = sum(allocation.values())
        if abs(total - 100) > 0.01:
            allocation = {k: (v / total) * 100 for k, v in allocation.items()}
        
        allocation = {k: round(v, 1) for k, v in allocation.items()}
        
        # Ensure exact 100%
        rounded_sum = sum(allocation.values())
        if abs(rounded_sum - 100) > 0:
            largest_key = max(allocation, key=allocation.get)
            allocation[largest_key] = round(allocation[largest_key] + (100 - rounded_sum), 1)
        
        return allocation
    
    @staticmethod
    def calculate_safe_investment(answers: Dict[str, Any], financial_data: Dict[str, float], 
                                 risk_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate safe monthly investment amount"""
        monthly_income = financial_data.get('monthly_income', 0)
        monthly_expenses = financial_data.get('monthly_expenses', 0)
        disposable_income = financial_data.get('disposable_income', 0)
        financial_score = financial_data.get('financial_score', 0)
        emergency_months = financial_data.get('emergency_months', 0)
        income_stability = answers.get('income_stability', 3)
        dependents_count = financial_data.get('dependents_count', 0)
        
        suitability = RiskCalculator.check_investment_suitability(answers, financial_data)
        
        if suitability['suitability'] == "NOT SUITABLE":
            return {
                'safe_monthly_investment': 0,
                'annual_investment': 0,
                'monthly_ef_saving': disposable_income * 0.5,
                'monthly_debt_payment': disposable_income * 0.3,
                'ef_gap_amount': max(0, 6 - emergency_months) * monthly_expenses,
                'investment_percentage': 0,
                'investment_confidence': "Very Low",
                'suitability': suitability,
                'recommendation_priority': "EMERGENCY_FUND_DEBT"
            }
        
        # Emergency fund gap
        target_emergency_months = 6 if income_stability <= 2 else 9
        ef_gap_months = max(0, target_emergency_months - emergency_months)
        ef_gap_amount = ef_gap_months * monthly_expenses
        
        # Debt priority
        debt_data = RiskCalculator.calculate_debt_score(answers)
        debt_priority_amount = 0
        if debt_data['has_debt']:
            if debt_data['emi_percentage_category'] >= 3:
                debt_priority_percentage = 0.20
            elif debt_data['bad_debt_count'] > 0:
                debt_priority_percentage = 0.15
            else:
                debt_priority_percentage = 0.10
            
            debt_priority_amount = disposable_income * debt_priority_percentage
        
        # Multipliers
        dependents_multiplier = 1.0 - (dependents_count * 0.1)
        dependents_multiplier = max(0.5, dependents_multiplier)
        
        if income_stability == 1:
            stability_multiplier = 1.0
        elif income_stability == 2:
            stability_multiplier = 0.8
        elif income_stability == 3:
            stability_multiplier = 0.6
        else:
            stability_multiplier = 0.0
        
        if financial_score < 40:
            fh_multiplier = 0.0
        elif financial_score < 60:
            fh_multiplier = 0.15
        elif financial_score < 80:
            fh_multiplier = 0.25
        else:
            fh_multiplier = 0.35
        
        risk_tolerance = risk_data.get('risk_tolerance_data', {}).get('risk_tolerance_score', 50)
        risk_multiplier = risk_tolerance / 100
        
        # Investment percentage
        base_percentage = fh_multiplier * (0.5 + 0.5 * risk_multiplier)
        investment_percentage = base_percentage * stability_multiplier * dependents_multiplier
        
        # Available after priorities
        available_after_priorities = max(0, disposable_income - debt_priority_amount)
        
        # Emergency fund building
        monthly_ef_saving = 0
        if ef_gap_amount > 0 and disposable_income > 0:
            build_timeline = min(18, max(6, int(ef_gap_months * 3)))
            monthly_ef_saving = min(available_after_priorities * 0.5, ef_gap_amount / build_timeline)
            available_for_investment = max(0, available_after_priorities - monthly_ef_saving)
        else:
            available_for_investment = available_after_priorities
        
        # Safe investment
        safe_monthly_investment = min(
            available_for_investment * investment_percentage,
            available_for_investment * 0.3
        )
        
        if safe_monthly_investment < MINIMUM_INVESTMENT_THRESHOLD:
            safe_monthly_investment = 0
        
        # Confidence level
        if safe_monthly_investment == 0:
            confidence = "Very Low"
        elif safe_monthly_investment < disposable_income * 0.05:
            confidence = "Low"
        elif safe_monthly_investment < disposable_income * 0.10:
            confidence = "Medium"
        elif safe_monthly_investment < disposable_income * 0.20:
            confidence = "High"
        else:
            confidence = "Very High"
        
        # Priority
        if ef_gap_amount > 0 and emergency_months < 3:
            priority = "EMERGENCY_FUND"
        elif debt_priority_amount > 0:
            priority = "DEBT_REDUCTION"
        else:
            priority = "INVESTMENT"
        
        return {
            'safe_monthly_investment': round(safe_monthly_investment, 2),
            'annual_investment': round(safe_monthly_investment * 12, 2),
            'monthly_ef_saving': round(monthly_ef_saving, 2),
            'monthly_debt_payment': round(debt_priority_amount, 2),
            'ef_gap_amount': round(ef_gap_amount, 2),
            'ef_build_timeline': 12 if ef_gap_amount > 0 else 0,
            'investment_percentage': round(investment_percentage * 100, 2),
            'investment_confidence': confidence,
            'available_for_investment': round(available_for_investment, 2),
            'suitability': suitability,
            'recommendation_priority': priority,
            'dependents_multiplier': round(dependents_multiplier, 2),
            'stability_multiplier': round(stability_multiplier, 2)
        }
    
    @staticmethod
    def get_stock_recommendations(risk_category: str, allocation: Dict[str, float], 
                                 esg_importance: int = 1, inflation_preference: str = "balanced") -> Dict[str, Any]:
        """Get stock recommendations based on risk, ESG, and inflation preferences"""
        
        base_recommendations = {
            "VERY LOW RISK": {
                "strategy": "Conservative Income",
                "description": "Focus on stability and regular income",
                "allocation_notes": "Primarily large-cap stocks for stability"
            },
            "LOW RISK": {
                "strategy": "Balanced Growth",
                "description": "Mix of stability and moderate growth",
                "allocation_notes": "Mostly large-cap with some mid-cap exposure"
            },
            "MEDIUM RISK": {
                "strategy": "Growth Oriented",
                "description": "Balance of growth and reasonable risk",
                "allocation_notes": "Diversified across market caps"
            },
            "HIGH RISK": {
                "strategy": "Aggressive Growth",
                "description": "Focus on growth with higher risk tolerance",
                "allocation_notes": "Significant mid/small cap and growth exposure"
            },
            "VERY HIGH RISK": {
                "strategy": "Speculative Growth",
                "description": "High-risk, high-potential investments",
                "allocation_notes": "Heavy emphasis on growth and small caps"
            }
        }
        
        base_rec = base_recommendations.get(risk_category, base_recommendations["MEDIUM RISK"])
        
        # Adjust strategy based on inflation preference
        if inflation_preference == "growth":
            base_rec["strategy"] = base_rec["strategy"] + " (Growth Focused)"
            base_rec["description"] = base_rec["description"] + " with maximum growth focus"
        elif inflation_preference == "protection":
            base_rec["strategy"] = base_rec["strategy"] + " (Inflation Protected)"
            base_rec["description"] = base_rec["description"] + " with focus on inflation-resistant assets"
        else:
            base_rec["strategy"] = base_rec["strategy"] + " (Balanced)"
            base_rec["description"] = base_rec["description"] + " with balance between growth and inflation protection"
        
        # Select stocks
        selected_stocks = []
        
        def filter_stocks_by_preferences(stock_list, category_allocation, esg_pref, inflation_pref):
            if category_allocation <= 0:
                return []
            
            filtered = []
            for stock in stock_list:
                # ESG filter
                esg_ok = True
                if esg_pref >= 3:
                    if stock.get('esg_rating', 'Low') == 'Low':
                        continue
                    if esg_pref == 4 and stock.get('esg_rating', 'Medium') != 'High':
                        continue
                
                filtered.append(stock)
            
            # Sort based on inflation preference
            if inflation_pref == "protection":
                filtered.sort(key=lambda x: {'Excellent': 3, 'Good': 2, 'Medium': 1, 'Low': 0}.get(x.get('inflation_protection', 'Low'), 0), reverse=True)
            elif inflation_pref == "growth":
                filtered.sort(key=lambda x: {'High': 3, 'Medium': 2, 'Low': 1}.get(x.get('growth_focus', 'Medium'), 0), reverse=True)
            
            max_stocks = max(1, int(category_allocation / 10))
            return filtered[:max_stocks]
        
        # Filter stocks for each category
        for category, percentage in allocation.items():
            if percentage > 0 and category in STOCKS_DB:
                category_stocks = filter_stocks_by_preferences(
                    STOCKS_DB[category], 
                    percentage, 
                    esg_importance, 
                    inflation_preference
                )
                selected_stocks.extend(category_stocks[:2])
        
        selected_stocks = selected_stocks[:6]
        
        # Get ETFs
        etfs = ETFS_DB.get(risk_category, [])
        if inflation_preference == "protection":
            etfs = etfs + ["GOLDBEES"]
        
        # Inflation note
        inflation_note = ""
        if inflation_preference == "growth":
            inflation_note = "⚠️ Growth-focused portfolios may be more volatile during high inflation."
        elif inflation_preference == "protection":
            inflation_note = "✅ Includes inflation-resistant stocks that tend to perform better during price rises."
        else:
            inflation_note = "⚖️ Balanced approach for growth potential with some inflation protection."
        
        return {
            **base_rec,
            "stocks": selected_stocks,
            "etfs": etfs,
            "esg_filter_applied": esg_importance >= 2,
            "inflation_preference": inflation_preference,
            "inflation_note": inflation_note
        }

# ============================================================================
# CSV DATA HANDLER
# ============================================================================

class CSVDataHandler:
    """Handles CSV data operations"""
    
    @staticmethod
    def save_assessment_to_csv(assessment_data: Dict[str, Any]) -> bool:
        """Save assessment data to CSV"""
        try:
            answers = assessment_data.get('answers', {})
            dependent_answers = assessment_data.get('dependent_answers', {})
            financial_data = assessment_data.get('financial_data', {})
            risk_data = assessment_data.get('risk_data', {})
            debt_data = assessment_data.get('debt_data', {})
            investment_data = assessment_data.get('investment_data', {})
            allocation = assessment_data.get('allocation', {})
            risk_category = assessment_data.get('risk_category', 'Unknown')
            inflation_preference = assessment_data.get('inflation_preference', 'balanced')
            
            row = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'model_version': MODEL_VERSION,
                'income': float(answers.get('income', 0)),
                'expenses': float(answers.get('expenses', 0)),
                'emergency_fund': int(answers.get('emergency_fund', 3)),
                'income_stability': int(answers.get('income_stability', 3)),
                'dependents': int(answers.get('dependents', 0)),
                'loan_types': json.dumps(answers.get('loan_types', [])),
                'emi_percentage': int(answers.get('emi_percentage', 1)),
                'primary_goal': str(answers.get('primary_goal', 'not_sure')),
                'goal_dependent_data': json.dumps(dependent_answers),
                'timeframe': int(answers.get('timeframe', 3)),
                'loss_avoidance': int(answers.get('loss_avoidance', 3)),
                'market_drop_reaction': int(answers.get('market_drop_reaction', 3)),
                'experience': int(answers.get('experience', 2)),
                'knowledge': int(answers.get('knowledge', 2)),
                'liquidity_needs': int(answers.get('liquidity_needs', 4)),
                'age_group': int(answers.get('age_group', 4)),
                'esg_importance': int(answers.get('esg_importance', 1)),
                'esg_areas': json.dumps(answers.get('esg_areas', [])),
                'inflation_preference': str(inflation_preference),
                'financial_health_score': float(financial_data.get('financial_score', 0)),
                'debt_score': float(debt_data.get('debt_score', 0)),
                'risk_tolerance_score': float(risk_data.get('risk_tolerance_data', {}).get('risk_tolerance_score', 0)),
                'horizon_score': float(risk_data.get('horizon_data', {}).get('horizon_score', 0)),
                'knowledge_score': float(risk_data.get('knowledge_data', {}).get('knowledge_score', 0)),
                'overall_risk_score': float(risk_data.get('overall_risk_score', 0)),
                'risk_category': str(risk_category),
                'monthly_investment': float(investment_data.get('safe_monthly_investment', 0)),
                'annual_investment': float(investment_data.get('annual_investment', 0)),
                'investment_confidence': str(investment_data.get('investment_confidence', 'Low')),
                'suitability': str(investment_data.get('suitability', {}).get('suitability', 'Unknown')),
                'portfolio_large_cap': float(allocation.get('Large_Cap', 0)),
                'portfolio_mid_cap': float(allocation.get('Mid_Cap', 0)),
                'portfolio_small_cap': float(allocation.get('Small_Cap', 0)),
                'portfolio_growth': float(allocation.get('Growth', 0)),
                'portfolio_inflation_protection': float(allocation.get('Inflation_Protection', 0)),
                'portfolio_fixed_income': float(allocation.get('Fixed_Income', 0))
            }
            
            file_exists = os.path.isfile(CSV_FILE)
            
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
            return False
    
    @staticmethod
    def load_assessments_from_csv() -> pd.DataFrame:
        """Load assessments from CSV"""
        try:
            if not os.path.exists(CSV_FILE):
                return pd.DataFrame()
            
            df = pd.read_csv(CSV_FILE, encoding='utf-8')
            
            if df.empty:
                return df
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            json_cols = ['loan_types', 'goal_dependent_data', 'esg_areas']
            for col in json_cols:
                if col in df.columns:
                    try:
                        df[col] = df[col].apply(lambda x: json.loads(x) if pd.notna(x) and x != '' else [])
                    except:
                        df[col] = df[col].apply(lambda x: [] if pd.notna(x) else [])
            
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp', ascending=False)
            
            return df
        except Exception as e:
            return pd.DataFrame()
    
    @staticmethod
    def get_statistics() -> Optional[Dict[str, Any]]:
        """Get statistics from stored assessments"""
        try:
            df = CSVDataHandler.load_assessments_from_csv()
            if df.empty:
                return None
            
            if 'model_version' in df.columns:
                df = df[df['model_version'] == MODEL_VERSION]
            
            if df.empty:
                return None
            
            stats = {
                'total_assessments': int(len(df)),
                'model_version': MODEL_VERSION,
                'avg_financial_health': 0.0,
                'avg_debt_score': 0.0,
                'avg_risk_score': 0.0,
                'most_common_risk_category': 'N/A',
                'avg_monthly_investment': 0.0,
                'most_common_inflation_pref': 'N/A'
            }
            
            if 'financial_health_score' in df.columns:
                avg_fh = df['financial_health_score'].mean()
                if not pd.isna(avg_fh):
                    stats['avg_financial_health'] = float(avg_fh)
            
            if 'debt_score' in df.columns:
                avg_debt = df['debt_score'].mean()
                if not pd.isna(avg_debt):
                    stats['avg_debt_score'] = float(avg_debt)
            
            if 'overall_risk_score' in df.columns:
                avg_risk = df['overall_risk_score'].mean()
                if not pd.isna(avg_risk):
                    stats['avg_risk_score'] = float(avg_risk)
            
            if 'risk_category' in df.columns:
                mode_result = df['risk_category'].mode()
                if not mode_result.empty:
                    stats['most_common_risk_category'] = mode_result.iloc[0]
            
            if 'monthly_investment' in df.columns:
                avg_inv = df['monthly_investment'].mean()
                if not pd.isna(avg_inv):
                    stats['avg_monthly_investment'] = float(avg_inv)
            
            if 'inflation_preference' in df.columns:
                mode_result = df['inflation_preference'].mode()
                if not mode_result.empty:
                    stats['most_common_inflation_pref'] = mode_result.iloc[0]
            
            return stats
        except Exception as e:
            return None

# ============================================================================
# STREAMLIT APP
# ============================================================================

# Page Configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1E3A8A; font-weight: 700; margin-bottom: 1rem; }
    .section-header { font-size: 1.8rem; color: #374151; font-weight: 600; margin: 1.5rem 0 1rem 0; }
    .card { 
        background-color: white; 
        padding: 1.5rem; 
        border-radius: 10px; 
        border-left: 5px solid #3B82F6; 
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white; 
        padding: 1.5rem; 
        border-radius: 10px; 
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .progress-bar { 
        height: 10px; 
        background-color: #E5E7EB; 
        border-radius: 5px; 
        margin: 10px 0; 
        overflow: hidden; 
    }
    .progress-fill { 
        height: 100%; 
        border-radius: 5px; 
        transition: width 0.5s ease; 
    }
    .stButton > button { 
        background-color: #3B82F6; 
        color: white; 
        font-weight: 600; 
        border-radius: 8px; 
        padding: 0.5rem 1rem; 
        border: none;
        width: 100%;
    }
    .info-box { 
        background-color: #E0F2FE; 
        border-left: 4px solid #0EA5E9; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0;
    }
    .warning-box { 
        background-color: #FEF3C7; 
        border-left: 4px solid #F59E0B; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0;
    }
    .success-box { 
        background-color: #D1FAE5; 
        border-left: 4px solid #10B981; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0;
    }
    .danger-box { 
        background-color: #FEE2E2; 
        border-left: 4px solid #EF4444; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 1rem 0;
    }
    .inflation-education {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
    }
    .part-header {
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 2rem 0 1rem 0;
        font-size: 1.2rem;
        font-weight: 600;
    }
    .inflation-option {
        background-color: #F9FAFB;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px solid #E5E7EB;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .inflation-option:hover {
        border-color: #3B82F6;
        background-color: #EFF6FF;
        transform: translateY(-2px);
    }
    .inflation-option.selected {
        border-color: #10B981;
        background-color: #D1FAE5;
    }
    .stock-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .stock-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    .allocation-breakdown {
        background-color: #F9FAFB;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        margin: 1rem 0;
    }
    .data-table {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
def init_session_state():
    defaults = {
        'current_tab': "Welcome",
        'answers': {
            'income': None,
            'expenses': None,
            'emergency_fund': None,
            'income_stability': None,
            'dependents': None,
            'loan_types': [],
            'emi_percentage': None,
            'primary_goal': None,
            'timeframe': None,
            'loss_avoidance': None,
            'market_drop_reaction': None,
            'experience': None,
            'knowledge': None,
            'liquidity_needs': None,
            'age_group': None,
            'esg_importance': None,
            'esg_areas': []
        },
        'dependent_answers': {},
        'risk_data': None,
        'risk_category': None,
        'financial_data': None,
        'debt_data': None,
        'safe_investment': None,
        'assessment_complete': False,
        'allocation': None,
        'recommendations': None,
        'assessment_id': None,
        'validation_warnings': [],
        'inflation_preference': None,
        'show_inflation_education': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_results():
    """Calculate all assessment results"""
    calculator = RiskCalculator()
    
    is_valid, warnings = calculator.validate_answers(st.session_state.answers)
    
    if warnings:
        st.session_state.validation_warnings = warnings
    
    if not is_valid:
        st.error("Please complete all required questions.")
        return
    
    # Calculate scores
    risk_data = calculator.calculate_overall_risk_score(st.session_state.answers, st.session_state.dependent_answers)
    financial_data = risk_data['financial_data']
    debt_data = risk_data['debt_data']
    risk_category = calculator.get_risk_category(risk_data['overall_risk_score'])
    
    # Save initial results
    st.session_state.financial_data = financial_data
    st.session_state.debt_data = debt_data
    st.session_state.risk_data = risk_data
    st.session_state.risk_category = risk_category
    st.session_state.assessment_complete = True
    st.session_state.assessment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Go to Financial Health first
    st.session_state.current_tab = "Financial Health"
    
    st.rerun()

def apply_inflation_preference():
    """Apply inflation preference and calculate final recommendations"""
    calculator = RiskCalculator()
    
    if not st.session_state.risk_data:
        st.error("Risk data not available. Please complete assessment first.")
        return
    
    inflation_pref = st.session_state.inflation_preference or "balanced"
    
    # Calculate allocation with inflation preference
    allocation = calculator.determine_portfolio_allocation(
        st.session_state.risk_data['overall_risk_score'], 
        st.session_state.answers,
        inflation_pref
    )
    
    investment_data = calculator.calculate_safe_investment(
        st.session_state.answers, st.session_state.financial_data, st.session_state.risk_data
    )
    
    recommendations = calculator.get_stock_recommendations(
        st.session_state.risk_category, 
        allocation,
        st.session_state.answers.get('esg_importance', 1),
        inflation_pref
    )
    
    # Update session state
    st.session_state.allocation = allocation
    st.session_state.safe_investment = investment_data
    st.session_state.recommendations = recommendations
    st.session_state.show_inflation_education = False
    
    # Save to CSV
    assessment_data = {
        'answers': st.session_state.answers,
        'dependent_answers': st.session_state.dependent_answers,
        'financial_data': st.session_state.financial_data,
        'debt_data': st.session_state.debt_data,
        'risk_data': st.session_state.risk_data,
        'risk_category': st.session_state.risk_category,
        'allocation': allocation,
        'investment_data': investment_data,
        'recommendations': recommendations,
        'inflation_preference': inflation_pref
    }
    
    if CSVDataHandler.save_assessment_to_csv(assessment_data):
        st.success("✅ Assessment saved!")
    
    # Go to Recommendations
    st.session_state.current_tab = "Recommendations"
    st.rerun()

def create_navigation_buttons():
    """Create navigation buttons"""
    tabs = ["Welcome", "Assessment", "Financial Health", "Debt Analysis", 
            "Risk Profile", "Inflation Education", "Recommendations", "Action Plan", "Data & Export"]
    current = st.session_state.current_tab
    idx = tabs.index(current) if current in tabs else 0
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if idx > 0 and current != "Welcome":
            if st.button("◀️ Previous", use_container_width=True):
                st.session_state.current_tab = tabs[idx - 1]
                st.rerun()
    
    with col3:
        if idx < len(tabs) - 1 and current != "Data & Export":
            if current == "Assessment" and not st.session_state.assessment_complete:
                if st.button("Calculate Results ▶️", type="primary", use_container_width=True):
                    calculate_results()
            elif current == "Inflation Education" and st.session_state.inflation_preference:
                if st.button("Get Recommendations ▶️", type="primary", use_container_width=True):
                    apply_inflation_preference()
            else:
                if st.button("Next ▶️", type="primary", use_container_width=True):
                    st.session_state.current_tab = tabs[idx + 1]
                    st.rerun()

def create_progress_bar():
    """Create progress bar"""
    tabs = ["Welcome", "Assessment", "Financial Health", "Debt Analysis", 
            "Risk Profile", "Inflation Education", "Recommendations", "Action Plan", "Data & Export"]
    current = st.session_state.current_tab
    idx = tabs.index(current) if current in tabs else 0
    
    tab_labels = []
    for i, tab in enumerate(tabs):
        if i == idx:
            tab_labels.append(f'<span style="font-weight: bold; color: #3B82F6;">{tab}</span>')
        else:
            tab_labels.append(f'<span style="font-weight: normal; color: #6B7280;">{tab}</span>')
    
    progress_html = f"""
    <div style="margin-bottom: 2rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            {"".join(tab_labels)}
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {(idx + 1)/len(tabs)*100}%; 
                 background-color: #3B82F6;"></div>
        </div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)

# ============================================================================
# TAB FUNCTIONS
# ============================================================================

def create_welcome_tab():
    """Create welcome tab"""
    st.markdown('<h1 class="main-header">📈 Welcome to Stock Risk Advisor </h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Your Intelligent Stock Investment Guide
        
        **Stock Risk Advisor helps you make informed, personalized stock investment decisions**
        based on your complete financial profile, risk tolerance, and investment goals.
        
           
        
        
        ### 📋 What You'll Get
        
        1. **Financial Health Score** - How ready you are to invest  
        2. **Debt Health Analysis** - Good vs bad debt assessment  
        3. **Risk Profile** - Your personalized risk category  
        4. **Inflation Strategy** - Choose between growth, protection, or balanced  
        5. **Portfolio Allocation** - Customized for your profile  
        6. **Stock Recommendations** - Filtered by ESG and inflation preferences  
        7. **Safe Investment Amount** - Sustainable monthly investment  
        8. **Step-by-Step Action Plan** - Clear implementation guide  
        9. **Data Export** - Download all your assessment data
        
        ### ⏱️ Time Required
        **10-12 minutes** for comprehensive assessment
        
        ### 🔒 Privacy & Data
        • All data stored locally on your device  
        • No registration or personal information required  
        • Export and delete data anytime  
        • Educational purpose only - not financial advice  
        """)
    
    with col2:
        st.image("https://img.icons8.com/color/300/000000/stock-exchange.png", width=250)
        
        # Quick stats
        try:
            stats = CSVDataHandler.get_statistics()
            if stats and stats['total_assessments'] > 0:
                st.markdown("---")
                st.markdown("### 📊 Community Stats")
                st.metric("Total Assessments", stats['total_assessments'])
                st.metric("Avg Financial Health", f"{stats['avg_financial_health']:.1f}")
                st.metric("Most Common Risk", stats['most_common_risk_category'])
        except:
            pass
    
    st.markdown("---")
    
    # Start button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Begin Comprehensive Assessment", type="primary", use_container_width=True):
            st.session_state.current_tab = "Assessment"
            st.rerun()
    
    st.markdown("---")
    
    # Methodology Preview
    with st.expander("🔬 Preview: How We Calculate Recommendations"):
        st.markdown(f"""
        ### Transparent Assessment Methodology (v{MODEL_VERSION})
        
        **Five Key Dimensions:**
        1. **Financial Stability (25%)** - Emergency fund, income stability, savings rate
        2. **Debt Situation (15%)** - Good vs bad debt, EMI percentage
        3. **Risk Tolerance (25%)** - Psychological comfort with risk
        4. **Investment Horizon (20%)** - Timeframe and liquidity needs
        5. **Knowledge & Experience (15%)** - Investing knowledge and experience
        
        **Plus Inflation Strategy:**
        • **Growth Focus:** Maximum growth potential, may be volatile during inflation
        • **Inflation Protection:** Focus on inflation-resistant assets
        • **Balanced:** Mix of growth and defensive stocks
        
        **ESG Integration:** Stocks filtered based on your sustainability preferences
        """)
    
    # Disclaimer
    st.markdown("""
    ---
    <div style='text-align:center; color:#6B7280; font-size:0.9rem; padding:1rem 0;'>
        <p>⚠️ <strong>Educational Purpose Only</strong> - This tool helps understand stock investing principles.</p>
        <p>We are not SEBI-registered investment advisors. This is not financial advice.</p>
        <p>Investing in stocks involves risk of loss. Past performance doesn't guarantee future results.</p>
        <p>Data is stored locally in CSV format for analysis and export. Model Version: {MODEL_VERSION}</p>
    </div>
    """.format(MODEL_VERSION=MODEL_VERSION), unsafe_allow_html=True)

def create_assessment_tab():
    """Create the assessment tab"""
    st.markdown('<h1 class="main-header">📋 Comprehensive Stock Investment Assessment</h1>', unsafe_allow_html=True)
    
    # Progress indicator
    answered_count = sum(1 for v in st.session_state.answers.values() if v not in [None, [], 0])
    progress = min(100, int((answered_count / len(st.session_state.answers)) * 100))
    
    st.markdown(f"""
    <div style="margin: 1.5rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>Assessment Progress</span>
            <span>{answered_count}/{len(st.session_state.answers)} questions answered</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show validation warnings
    if st.session_state.validation_warnings:
        for warning in st.session_state.validation_warnings:
            st.warning(warning)
    
    with st.form("assessment_form"):
        # Part 1: Financial Foundation
        st.markdown('<div class="part-header">🟦 PART 1: FINANCIAL FOUNDATION</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="info-box"><strong>Financial Foundation Assessment</strong><br>'
                   'This section evaluates your basic financial health before considering stock investments.</div>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Q1: Monthly Take-home Income")
            income = st.number_input(
                "Enter amount in ₹",
                min_value=0.0,
                max_value=10000000.0,
                step=1000.0,
                value=float(st.session_state.answers['income']) if st.session_state.answers['income'] else 50000.0,
                format="%.0f",
                key="income_input"
            )
            st.session_state.answers['income'] = float(income) if income else None
        
        with col2:
            st.markdown("#### Q2: Monthly Essential Expenses")
            expenses = st.number_input(
                "Enter amount in ₹",
                min_value=0.0,
                max_value=10000000.0,
                step=1000.0,
                value=float(st.session_state.answers['expenses']) if st.session_state.answers['expenses'] else 35000.0,
                format="%.0f",
                key="expenses_input"
            )
            st.session_state.answers['expenses'] = float(expenses) if expenses else None
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Q3: Emergency Fund Coverage")
            emergency_fund = st.selectbox(
                "Select coverage",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x: [
                    "No emergency savings",
                    "Less than 1 month",
                    "1–3 months",
                    "4–6 months (Recommended)",
                    "7–12 months",
                    "More than 12 months"
                ][x-1],
                index=st.session_state.answers['emergency_fund'] - 1 if st.session_state.answers['emergency_fund'] else 2,
                key="emergency_fund_input"
            )
            st.session_state.answers['emergency_fund'] = emergency_fund
        
        with col2:
            st.markdown("#### Q4: Income Stability")
            income_stability = st.selectbox(
                "Select stability level",
                options=[1, 2, 3, 4],
                format_func=lambda x: [
                    "Very stable (e.g., salaried job)",
                    "Moderately stable",
                    "Unstable",
                    "No current income"
                ][x-1],
                index=st.session_state.answers['income_stability'] - 1 if st.session_state.answers['income_stability'] else 1,
                key="income_stability_input"
            )
            st.session_state.answers['income_stability'] = income_stability
        
        st.markdown("#### Q5: Financial Dependents")
        dependents = st.selectbox(
            "Select number of dependents",
            options=[0, 1, 2, 3, 4],
            format_func=lambda x: ["None", "1", "2", "3", "4 or more"][x],
            index=st.session_state.answers['dependents'] if st.session_state.answers['dependents'] is not None else 1,
            key="dependents_input"
        )
        st.session_state.answers['dependents'] = dependents
        
        # Part 2: Debt Situation
        st.markdown('<div class="part-header">🟦 PART 2: DEBT SITUATION</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="info-box"><strong>Debt Assessment</strong><br>'
                   'Understanding your debt helps prioritize repayment vs investing.</div>', 
                   unsafe_allow_html=True)
        
        st.markdown("#### Q6: Which type of loans do you currently have?")
        col1, col2, col3 = st.columns(3)
        loan_types = []
        
        with col1:
            st.markdown("**Good Debt**")
            if st.checkbox("Home loan", key="home_loan"):
                loan_types.append('home_loan')
            if st.checkbox("Education loan", key="education_loan"):
                loan_types.append('education_loan')
        
        with col2:
            st.markdown("**Neutral**")
            if st.checkbox("Gold loan", key="gold_loan"):
                loan_types.append('gold_loan')
        
        with col3:
            st.markdown("**Bad Debt**")
            if st.checkbox("Personal loan", key="personal_loan"):
                loan_types.append('personal_loan')
            if st.checkbox("Credit card", key="credit_card"):
                loan_types.append('credit_card')
        
        st.session_state.answers['loan_types'] = loan_types
        
        
        st.markdown("#### Q7: Total Monthly EMI as % of Income")
        emi_percentage = st.selectbox(
            "Select EMI percentage range",
            options=[1, 2, 3, 4],
            format_func=lambda x: [
                "<20% (Comfortable)",
                "20–40% (Manageable)",
                "40–60% (Stressed)",
                ">60% (Overburdened)"
            ][x-1],
            index=st.session_state.answers['emi_percentage'] - 1 if st.session_state.answers['emi_percentage'] else 0,
            key="emi_percentage_input"
        )
        st.session_state.answers['emi_percentage'] = emi_percentage
        
        # Part 3: Investment Goals
        st.markdown('<div class="part-header">🟦 PART 3: INVESTMENT GOALS</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="info-box"><strong>Investment Goals & Timeframe</strong><br>'
                   'Understanding your investment purpose and timeline.</div>', 
                   unsafe_allow_html=True)
        
        st.markdown("#### Q8: Primary Investment Goal")
        primary_goal = st.selectbox(
            "Select your primary goal",
            options=['capital_preservation', 'regular_income', 'major_life_goal', 
                    'retirement', 'wealth_creation', 'not_sure'],
            format_func=lambda x: {
                'capital_preservation': 'Capital Preservation',
                'regular_income': 'Regular Income',
                'major_life_goal': 'Major Life Goal',
                'retirement': 'Retirement Planning',
                'wealth_creation': 'Wealth Creation',
                'not_sure': 'Not Sure'
            }[x],
            index=['capital_preservation', 'regular_income', 'major_life_goal', 
                  'retirement', 'wealth_creation', 'not_sure'].index(
                st.session_state.answers['primary_goal']
            ) if st.session_state.answers['primary_goal'] else 5,
            key="primary_goal_input"
        )
        st.session_state.answers['primary_goal'] = primary_goal
        
        # Goal-dependent questions
        if primary_goal == 'capital_preservation':
            capital_safety = st.selectbox(
                "How important is capital safety?",
                options=[1, 2, 3],
                format_func=lambda x: ["Safety is most important", "Balance", "Can take some risk"][x-1],
                index=st.session_state.dependent_answers.get('capital_safety_importance', 1) - 1,
                key="capital_safety_input"
            )
            st.session_state.dependent_answers['capital_safety_importance'] = capital_safety
        
        st.markdown("#### Q9: Investment Timeframe")
        timeframe = st.selectbox(
            "Select timeframe",
            options=[1, 2, 3, 4, 5, 6],
            format_func=lambda x: [
                "Less than 2 years",
                "2–4 years",
                "5–7 years",
                "8–12 years",
                "13+ years",
                "Multiple timeframes"
            ][x-1],
            index=st.session_state.answers['timeframe'] - 1 if st.session_state.answers['timeframe'] else 2,
            key="timeframe_input"
        )
        st.session_state.answers['timeframe'] = timeframe
        
        # Part 4: Risk Psychology
        st.markdown('<div class="part-header">🟦 PART 4: RISK PSYCHOLOGY</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Q10: Importance of Avoiding Loss")
            loss_avoidance = st.selectbox(
                "Select importance level",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: [
                    "Very Important – Cannot tolerate loss",
                    "Important – Prefer stable returns",
                    "Moderate – Accept small losses",
                    "Flexible – Understand loss is normal",
                    "Not a Priority – Focus on growth"
                ][x-1],
                index=st.session_state.answers['loss_avoidance'] - 1 if st.session_state.answers['loss_avoidance'] else 1,
                key="loss_avoidance_input"
            )
            st.session_state.answers['loss_avoidance'] = loss_avoidance
        
        with col2:
            st.markdown("#### Q11: Reaction to Market Drop")
            market_drop_reaction = st.selectbox(
                "Select your likely reaction",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: [
                    "Sell immediately",
                    "Reduce position",
                    "Hold nervously",
                    "Stay calm",
                    "See as buying opportunity"
                ][x-1],
                index=st.session_state.answers['market_drop_reaction'] - 1 if st.session_state.answers['market_drop_reaction'] else 2,
                key="market_drop_reaction_input"
            )
            st.session_state.answers['market_drop_reaction'] = market_drop_reaction
        
        # Part 5: Experience & Personal
        st.markdown('<div class="part-header">🟦 PART 5: EXPERIENCE & PERSONAL</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Q12: Stock Investing Experience")
            experience = st.selectbox(
                "Select experience level",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x: [
                    "First-time investor",
                    "Beginner (<1 year)",
                    "Intermediate (1-3 years)",
                    "Experienced (3-7 years)",
                    "Advanced (7+ years)",
                    "Professional"
                ][x-1],
                index=st.session_state.answers['experience'] - 1 if st.session_state.answers['experience'] else 1,
                key="experience_input"
            )
            st.session_state.answers['experience'] = experience
        
        with col2:
            st.markdown("#### Q13: Stock Investing Knowledge")
            knowledge = st.selectbox(
                "Select knowledge level",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x: [
                    "Very Limited",
                    "Basic",
                    "Intermediate",
                    "Good",
                    "Advanced",
                    "Expert"
                ][x-1],
                index=st.session_state.answers['knowledge'] - 1 if st.session_state.answers['knowledge'] else 1,
                key="knowledge_input"
            )
            st.session_state.answers['knowledge'] = knowledge
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Q14: Liquidity Needs")
            liquidity_needs = st.selectbox(
                "How likely will you need to withdraw?",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x: [
                    "Very likely (within 1 year)",
                    "Likely (1-2 years)",
                    "Possible (2-3 years)",
                    "Unlikely (3-5 years)",
                    "Very unlikely (5+ years)",
                    "Never – long-term only"
                ][x-1],
                index=st.session_state.answers['liquidity_needs'] - 1 if st.session_state.answers['liquidity_needs'] else 3,
                key="liquidity_needs_input"
            )
            st.session_state.answers['liquidity_needs'] = liquidity_needs
        
        with col2:
            st.markdown("#### Q15: Age Group")
            age_group = st.selectbox(
                "Select age group",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x: [
                    "Under 25 years",
                    "25-34 years",
                    "35-44 years",
                    "45-54 years",
                    "55-64 years",
                    "65+ years"
                ][x-1],
                index=st.session_state.answers['age_group'] - 1 if st.session_state.answers['age_group'] else 2,
                key="age_group_input"
            )
            st.session_state.answers['age_group'] = age_group
        
        # Part 6: ESG Preferences
        st.markdown('<div class="part-header">🟦 PART 6: VALUES & PREFERENCES</div>', unsafe_allow_html=True)
        
        st.markdown("#### Q16: Importance of Sustainable Investing (ESG)")
        esg_importance = st.selectbox(
            "How important is ESG to you?",
            options=[1, 2, 3, 4],
            format_func=lambda x: [
                "Not important – prioritize returns",
                "Somewhat important",
                "Very important – align with values",
                "Essential – only ESG options"
            ][x-1],
            index=st.session_state.answers['esg_importance'] - 1 if st.session_state.answers['esg_importance'] else 0,
            key="esg_importance_input"
        )
        st.session_state.answers['esg_importance'] = esg_importance
        
        if esg_importance >= 2:
            st.markdown("##### Which areas matter most?")
            esg_areas = []
            if st.checkbox("Climate/Environmental", key="esg_climate"):
                esg_areas.append("climate")
            if st.checkbox("Social justice & diversity", key="esg_social"):
                esg_areas.append("social")
            if st.checkbox("Ethical governance", key="esg_governance"):
                esg_areas.append("governance")
            
            if st.checkbox("Not interested in sustainable investing", key="esg_not_interested"):
                esg_areas = ["not_interested"]
            
            st.session_state.answers['esg_areas'] = esg_areas
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Calculate My Financial Health",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            st.session_state.validation_warnings = []
            calculate_results()

def create_financial_health_tab():
    """Create financial health dashboard"""
    st.markdown('<h1 class="main-header">💰 Financial Health Assessment</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        if st.button("Go to Assessment"):
            st.session_state.current_tab = "Assessment"
            st.rerun()
        return
    
    financial_data = st.session_state.financial_data
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = financial_data['financial_score']
        color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 1.1rem;">Financial Health Score</h3>
            <h1 style="margin: 0.5rem 0; font-size: 2.5rem;">{score}/100</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        disposable = financial_data['disposable_income']
        st.markdown(f"""
        <div class="card">
            <h4 style="margin: 0;">Monthly Disposable Income</h4>
            <h2 style="margin: 0.5rem 0; color: #3B82F6;">₹{disposable:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        savings = financial_data['savings_rate']
        st.markdown(f"""
        <div class="card">
            <h4 style="margin: 0;">Savings Rate</h4>
            <h2 style="margin: 0.5rem 0; color: #10B981;">{savings:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        emergency_months = financial_data['emergency_months']
        st.markdown(f"""
        <div class="card">
            <h4 style="margin: 0;">Emergency Fund</h4>
            <h2 style="margin: 0.5rem 0; color: #F59E0B;">{emergency_months:.1f} months</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed breakdown
    st.markdown('<h3 class="section-header">📊 Financial Health Components</h3>', unsafe_allow_html=True)
    
    components = [
        ("Emergency Fund", financial_data['emergency_component']),
        ("Income Stability", financial_data['income_stability_component']),
        ("Dependents Adjustment", financial_data['dependents_adjustment']),
        ("Savings Rate", financial_data['savings_component'])
    ]
    
    for name, score in components:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**{name}**")
        with col2:
            progress_color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="flex-grow: 1;">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {score}%; background-color: {progress_color};"></div>
                    </div>
                </div>
                <div style="font-weight: 600;">{score:.0f}/100</div>
            </div>
            """, unsafe_allow_html=True)
    
    create_navigation_buttons()

def create_debt_analysis_tab():
    """Create debt analysis tab"""
    st.markdown('<h1 class="main-header">💳 Debt Situation Analysis</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        if st.button("Go to Assessment"):
            st.session_state.current_tab = "Assessment"
            st.rerun()
        return
    
    debt_data = st.session_state.debt_data
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        score = debt_data['debt_score']
        color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"
        
        st.markdown(f"""
        <div style="background-color: {color}20; padding: 1.5rem; border-radius: 10px; 
                    border-left: 5px solid {color}; margin-bottom: 1rem;">
            <h2 style="margin: 0; color: {color};">Debt Health Score: {score}/100</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if debt_data['has_debt']:
            emi_category = debt_data['emi_percentage_category']
            emi_text = ["<20%", "20–40%", "40–60%", ">60%"][emi_category-1]
            emi_color = ["#10B981", "#34D399", "#F59E0B", "#EF4444"][emi_category-1]
            st.markdown(f"""
            <div style="background-color: {emi_color}20; padding: 1rem; border-radius: 8px; 
                        border-left: 4px solid {emi_color}; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: {emi_color};">EMI Burden</h4>
                <h3 style="margin: 0.5rem 0; color: {emi_color};">{emi_text}</h3>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-box">
                <h4 style="margin: 0;">No Debt</h4>
                <p style="margin: 0.5rem 0 0 0;">Excellent! You have no debt obligations.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Debt breakdown
    if debt_data['has_debt']:
        st.markdown('<h3 class="section-header">📊 Debt Type Analysis</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            good_debt = debt_data['good_debt_count']
            st.markdown(f"""
            <div class="card">
                <h4 style="margin: 0;">Good Debt</h4>
                <h2 style="margin: 0.5rem 0; color: #10B981;">{good_debt}</h2>
                <p style="margin: 0; font-size: 0.9rem;">Home/Education loans</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            bad_debt = debt_data['bad_debt_count']
            st.markdown(f"""
            <div class="card">
                <h4 style="margin: 0;">Bad Debt</h4>
                <h2 style="margin: 0.5rem 0; color: #EF4444;">{bad_debt}</h2>
                <p style="margin: 0; font-size: 0.9rem;">Personal/Credit card</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            neutral_debt = debt_data['neutral_debt_count']
            st.markdown(f"""
            <div class="card">
                <h4 style="margin: 0;">Neutral Debt</h4>
                <h2 style="margin: 0.5rem 0; color: #F59E0B;">{neutral_debt}</h2>
                <p style="margin: 0; font-size: 0.9rem;">Gold/Property loans</p>
            </div>
            """, unsafe_allow_html=True)
    
    create_navigation_buttons()

def create_risk_profile_tab():
    """Create risk profile analysis"""
    st.markdown('<h1 class="main-header">🎯 Risk Profile Analysis</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        if st.button("Go to Assessment"):
            st.session_state.current_tab = "Assessment"
            st.rerun()
        return
    
    risk_data = st.session_state.risk_data
    risk_category = st.session_state.risk_category
    
    category_colors = {
        "VERY LOW RISK": "#10B981",
        "LOW RISK": "#34D399",
        "MEDIUM RISK": "#F59E0B",
        "HIGH RISK": "#F97316",
        "VERY HIGH RISK": "#EF4444"
    }
    
    color = category_colors.get(risk_category, "#6B7280")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div style="background-color: {color}20; padding: 1.5rem; border-radius: 10px; 
                    border-left: 5px solid {color}; margin-bottom: 1rem;">
            <h2 style="margin: 0; color: {color};">{risk_category}</h2>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">Based on your comprehensive assessment</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        score = risk_data['overall_risk_score']
        st.markdown(f"""
        <div class="card">
            <h4 style="margin: 0;">Overall Risk Score</h4>
            <h2 style="margin: 0.5rem 0; color: {color};">{score:.0f}/100</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Component scores
    st.markdown('<h3 class="section-header">📊 Component Scores</h3>', unsafe_allow_html=True)
    
    components = [
        ("Financial Stability", risk_data['financial_data']['financial_score']),
        ("Debt Situation", risk_data['debt_data']['debt_score']),
        ("Risk Tolerance", risk_data['risk_tolerance_data']['risk_tolerance_score']),
        ("Investment Horizon", risk_data['horizon_data']['horizon_score']),
        ("Knowledge & Experience", risk_data['knowledge_data']['knowledge_score'])
    ]
    
    for name, score in components:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**{name}**")
        with col2:
            progress_color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="flex-grow: 1;">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {score}%; background-color: {progress_color};"></div>
                    </div>
                </div>
                <div style="font-weight: 600;">{score:.0f}/100</div>
            </div>
            """, unsafe_allow_html=True)
    
    create_navigation_buttons()

def create_inflation_education_tab():
    """Show inflation education and preference selection"""
    st.markdown('<h1 class="main-header">💰 Inflation Strategy Selection</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        if st.button("Go to Assessment"):
            st.session_state.current_tab = "Assessment"
            st.rerun()
        return
    
    # Show risk category
    risk_category = st.session_state.risk_category
    category_colors = {
        "VERY LOW RISK": "#10B981",
        "LOW RISK": "#34D399",
        "MEDIUM RISK": "#F59E0B",
        "HIGH RISK": "#F97316",
        "VERY HIGH RISK": "#EF4444"
    }
    color = category_colors.get(risk_category, "#6B7280")
    
    st.markdown(f"""
    <div style="background-color: {color}20; padding: 1.5rem; border-radius: 10px; 
                border-left: 5px solid {color}; margin-bottom: 2rem;">
        <h3 style="margin: 0; color: {color};">Your Risk Profile: {risk_category}</h3>
        <p style="margin: 0.5rem 0 0 0;">Choose an inflation strategy that matches your risk profile</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inflation Education
    st.markdown('<div class="inflation-education">', unsafe_allow_html=True)
    st.markdown("""
    ## 📊 What is Inflation & Why It Matters?
    
    **Inflation** reduces your purchasing power over time. Different investments respond differently:
    
    **📈 Growth Stocks:** May suffer during high inflation but offer high long-term growth
    **🛡️ Inflation-Resistant Stocks:** Tend to perform better during inflation
    **⚖️ Balanced Approach:** Mix of both strategies
    
    Your choice will affect which stocks we recommend for your portfolio.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Risk-specific advice
    risk_advice = {
        "VERY LOW RISK": "Consider inflation protection to preserve purchasing power",
        "LOW RISK": "Balanced approach recommended",
        "MEDIUM RISK": "Flexible approach based on your inflation outlook",
        "HIGH RISK": "Growth focus with some protection",
        "VERY HIGH RISK": "Maximum growth, can handle inflation volatility"
    }
    
    advice = risk_advice.get(risk_category, "Balanced approach recommended")
    st.markdown(f'<div class="info-box"><strong>For your risk profile:</strong> {advice}</div>', unsafe_allow_html=True)
    
    # Inflation Preference Selection
    st.markdown('<h3 class="section-header">🤔 Choose Your Inflation Strategy</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="inflation-option">
            <h3>🚀 Maximum Growth</h3>
            <p><strong>Focus:</strong> High-growth stocks</p>
            <p><strong>Best for:</strong> Long-term investors who want maximum returns</p>
            <p><strong>Risk:</strong> May be volatile during inflation</p>
            <p><strong>Recommended for:</strong> Medium to High risk profiles</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Choose Growth", key="growth_btn", use_container_width=True):
            st.session_state.inflation_preference = "growth"
            st.success("Growth strategy selected! Click 'Get Recommendations' to continue.")
    
    with col2:
        st.markdown("""
        <div class="inflation-option">
            <h3>🛡️ Inflation Protection</h3>
            <p><strong>Focus:</strong> Inflation-resistant stocks</p>
            <p><strong>Best for:</strong> Inflation-concerned investors</p>
            <p><strong>Risk:</strong> Lower volatility, steady returns</p>
            <p><strong>Recommended for:</strong> Low to Medium risk profiles</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Choose Protection", key="protection_btn", use_container_width=True):
            st.session_state.inflation_preference = "protection"
            st.success("Protection strategy selected! Click 'Get Recommendations' to continue.")
    
    with col3:
        st.markdown("""
        <div class="inflation-option">
            <h3>⚖️ Balanced</h3>
            <p><strong>Focus:</strong> Mix of growth and protection</p>
            <p><strong>Best for:</strong> Most investors</p>
            <p><strong>Risk:</strong> Balanced approach</p>
            <p><strong>Recommended for:</strong> All risk profiles</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Choose Balanced", key="balanced_btn", use_container_width=True):
            st.session_state.inflation_preference = "balanced"
            st.success("Balanced strategy selected! Click 'Get Recommendations' to continue.")
    
    create_navigation_buttons()

def create_recommendations_tab():
    """Create detailed investment recommendations"""
    st.markdown('<h1 class="main-header">💼 Personalized Investment Recommendations</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        if st.button("Go to Assessment"):
            st.session_state.current_tab = "Assessment"
            st.rerun()
        return
    
    if not st.session_state.inflation_preference:
        st.warning("Please select an inflation strategy first!")
        if st.button("Go to Inflation Education"):
            st.session_state.current_tab = "Inflation Education"
            st.rerun()
        return
    
    allocation = st.session_state.allocation
    investment_data = st.session_state.safe_investment
    recommendations = st.session_state.recommendations
    financial_data = st.session_state.financial_data
    
    # Investment Summary
    st.markdown('<h3 class="section-header">💰 Investment Summary</h3>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        monthly = investment_data['safe_monthly_investment']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 1rem;">Monthly Investment</h3>
            <h1 style="margin: 0.5rem 0; font-size: 1.8rem;">₹{monthly:,.0f}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        annual = investment_data['annual_investment']
        st.markdown(f"""
        <div class="card">
            <h4 style="margin: 0; font-size: 0.9rem;">Annual Investment</h4>
            <h2 style="margin: 0.5rem 0; color: #10B981; font-size: 1.5rem;">₹{annual:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        confidence = investment_data['investment_confidence']
        confidence_color = {
            "Very High": "#10B981",
            "High": "#34D399",
            "Medium": "#F59E0B",
            "Low": "#F97316",
            "Very Low": "#EF4444"
        }.get(confidence, "#6B7280")
        st.markdown(f"""
        <div class="card">
            <h4 style="margin: 0; font-size: 0.9rem;">Investment Confidence</h4>
            <h2 style="margin: 0.5rem 0; color: {confidence_color}; font-size: 1.5rem;">{confidence}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        inflation_pref = st.session_state.inflation_preference
        inflation_color = {
            "growth": "#EF4444",
            "protection": "#10B981",
            "balanced": "#3B82F6"
        }.get(inflation_pref, "#6B7280")
        st.markdown(f"""
        <div class="card">
            <h4 style="margin: 0; font-size: 0.9rem;">Inflation Strategy</h4>
            <h2 style="margin: 0.5rem 0; color: {inflation_color}; font-size: 1.5rem;">{inflation_pref.title()}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Portfolio Allocation
    st.markdown('<h3 class="section-header">📊 Portfolio Allocation Breakdown</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Prepare data for pie chart
        labels = []
        values = []
        colors_pie = []
        
        category_info = {
            "Large_Cap": ("Large Cap", "#3B82F6"),
            "Mid_Cap": ("Mid Cap", "#10B981"),
            "Small_Cap": ("Small Cap", "#F59E0B"),
            "Growth": ("Growth Stocks", "#8B5CF6"),
            "Inflation_Protection": ("Inflation Protection", "#EC4899"),
            "Fixed_Income": ("Fixed Income", "#6B7280")
        }
        
        for key, value in allocation.items():
            if value > 0:
                label, color = category_info.get(key, (key, "#999999"))
                labels.append(label)
                values.append(value)
                colors_pie.append(color)
        
        if values:
            fig = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=0.4, 
                marker_colors=colors_pie,
                textinfo='label+percent',
                hoverinfo='label+value+percent'
            )])
            
            fig.update_layout(
                height=400, 
                showlegend=True,
                margin=dict(t=0, b=0, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown('<div class="allocation-breakdown">', unsafe_allow_html=True)
        st.markdown("### Allocation Details")
        total_equity = sum([allocation.get(k, 0) for k in ["Large_Cap", "Mid_Cap", "Small_Cap", "Growth", "Inflation_Protection"]])
        
        st.markdown(f"""
        **Equity Allocation:** {total_equity:.1f}%
        
        **Breakdown:**
        - Large Cap: {allocation.get('Large_Cap', 0):.1f}%
        - Mid Cap: {allocation.get('Mid_Cap', 0):.1f}%
        - Small Cap: {allocation.get('Small_Cap', 0):.1f}%
        - Growth: {allocation.get('Growth', 0):.1f}%
        - Inflation Protection: {allocation.get('Inflation_Protection', 0):.1f}%
        - Fixed Income: {allocation.get('Fixed_Income', 0):.1f}%
        
        **Strategy:** {recommendations.get('strategy', 'N/A')}
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Monthly Investment Allocation
    st.markdown('<h3 class="section-header">💵 Monthly Investment Allocation</h3>', unsafe_allow_html=True)
    
    monthly_investment = investment_data['safe_monthly_investment']
    if monthly_investment > 0:
        allocation_table_data = []
        for category, percentage in allocation.items():
            if percentage > 0:
                amount = monthly_investment * (percentage / 100)
                category_name = category_info.get(category, (category, "#999999"))[0]
                allocation_table_data.append({
                    "Category": category_name,
                    "Allocation %": f"{percentage:.1f}%",
                    "Monthly Amount": f"₹{amount:,.0f}",
                    "Annual Amount": f"₹{amount * 12:,.0f}"
                })
        
        df_allocation = pd.DataFrame(allocation_table_data)
        st.dataframe(df_allocation, use_container_width=True, hide_index=True)
    else:
        st.info("No monthly investment recommended at this time. Focus on building your emergency fund and reducing debt.")
    
    # Stock Recommendations
    if recommendations and recommendations.get('stocks'):
        st.markdown('<h3 class="section-header">📈 Stock Recommendations</h3>', unsafe_allow_html=True)
        
        st.markdown(f"""
        **Investment Strategy:** {recommendations.get('strategy', 'N/A')}
        
        **Description:** {recommendations.get('description', '')}
        
        **Inflation Strategy:** {recommendations.get('inflation_note', '')}
        """)
        
        stocks = recommendations['stocks']
        for i in range(0, len(stocks), 3):
            cols = st.columns(3)
            for j in range(3):
                idx = i + j
                if idx < len(stocks):
                    stock = stocks[idx]
                    with cols[j]:
                        inflation_perf = stock.get('inflation_performance', 'Medium')
                        esg_rating = stock.get('esg_rating', 'Medium')
                        growth_focus = stock.get('growth_focus', 'Medium')
                        
                        # Color coding for inflation performance
                        inflation_color = {
                            'Excellent': '#10B981',
                            'Good': '#34D399',
                            'Medium': '#F59E0B',
                            'Low': '#EF4444'
                        }.get(inflation_perf, '#6B7280')
                        
                        # Color coding for ESG rating
                        esg_color = {
                            'High': '#10B981',
                            'Medium': '#F59E0B',
                            'Low': '#EF4444'
                        }.get(esg_rating, '#6B7280')
                        
                        st.markdown(f"""
                        <div class="stock-card">
                            <h4 style="margin: 0 0 0.5rem 0;">{stock.get('symbol', '')}</h4>
                            <p style="margin: 0 0 0.5rem 0; font-size: 0.9rem; font-weight: 600;">
                                {stock.get('name', '')}
                            </p>
                            <p style="margin: 0 0 0.5rem 0; font-size: 0.8rem; color: #6B7280;">
                                {stock.get('sector', '')} • {stock.get('risk', 'Medium')} Risk
                            </p>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="font-size: 0.8rem; color: {inflation_color};">
                                    📊 Inflation: {inflation_perf}
                                </span>
                                <span style="font-size: 0.8rem; color: {esg_color};">
                                    🌱 ESG: {esg_rating}
                                </span>
                            </div>
                            <p style="margin: 0; font-size: 0.8rem; color: #4B5563;">
                                {stock.get('note', '')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # ETF Recommendations
        if recommendations.get('etfs'):
            st.markdown('<h4 class="section-header">🏷️ ETF Recommendations</h4>', unsafe_allow_html=True)
            etfs = recommendations['etfs']
            etf_text = ", ".join(etfs)
            st.markdown(f"""
            <div class="info-box">
                <p style="margin: 0;"><strong>Consider these ETFs:</strong> {etf_text}</p>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    ETFs provide diversified exposure and are good for beginners.
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Why These Recommendations?
    st.markdown('<h3 class="section-header">🤔 Why These Recommendations?</h3>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="info-box">
        <p><strong>Based on your profile:</strong></p>
        <ul>
            <li><strong>Risk Profile:</strong> {st.session_state.risk_category} - This determines your equity allocation</li>
            <li><strong>Inflation Strategy:</strong> {st.session_state.inflation_preference.title()} - This affects stock selection</li>
            <li><strong>Financial Health:</strong> {financial_data['financial_score']:.0f}/100 - This determines how much you can safely invest</li>
            <li><strong>ESG Preference:</strong> {st.session_state.answers.get('esg_importance', 1)}/4 - This filters stocks based on sustainability</li>
        </ul>
        <p><strong>Note:</strong> These are educational recommendations. Always do your own research before investing.</p>
    </div>
    """, unsafe_allow_html=True)
    
    create_navigation_buttons()

def create_action_plan_tab():
    """Create action plan"""
    st.markdown('<h1 class="main-header">🚀 Your Personalized Action Plan</h1>', unsafe_allow_html=True)
    
    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first!")
        if st.button("Go to Assessment"):
            st.session_state.current_tab = "Assessment"
            st.rerun()
        return
    
    investment_data = st.session_state.safe_investment
    financial_data = st.session_state.financial_data
    debt_data = st.session_state.debt_data
    
    st.markdown('<h3 class="section-header">📅 Step-by-Step Implementation</h3>', unsafe_allow_html=True)
    
    steps = []
    priority_order = []
    
    # Emergency Fund step
    emergency_months = financial_data.get('emergency_months', 0)
    if emergency_months < 3:
        steps.append({
            "title": "Step 1: Build Emergency Fund",
            "description": f"Current: {emergency_months:.1f} months | Target: 6 months",
            "action": f"Save ₹{investment_data.get('monthly_ef_saving', 0):,.0f} per month",
            "timeline": f"{investment_data.get('ef_build_timeline', 12)} months",
            "priority": "HIGH",
            "reason": "Essential for financial security before investing"
        })
        priority_order.append("EMERGENCY_FUND")
    
    # Debt reduction step
    if debt_data.get('has_debt', False) and debt_data.get('bad_debt_count', 0) > 0:
        steps.append({
            "title": "Step 2: Reduce High-Interest Debt",
            "description": f"Bad debt types: {debt_data.get('bad_debt_count', 0)}",
            "action": f"Pay ₹{investment_data.get('monthly_debt_payment', 0):,.0f} extra per month",
            "timeline": "Until high-interest debt is cleared",
            "priority": "HIGH",
            "reason": "High-interest debt costs more than stock returns"
        })
        priority_order.append("DEBT_REDUCTION")
    
    # Investing step
    suitability = investment_data.get('suitability', {}).get('suitability', 'UNKNOWN')
    monthly_inv = investment_data.get('safe_monthly_investment', 0)
    if suitability in ["SUITABLE", "CAUTION ADVISED"] and monthly_inv > 0:
        steps.append({
            "title": "Step 3: Start Stock Investing",
            "description": f"Monthly investment capacity: ₹{monthly_inv:,.0f}",
            "action": "Follow the recommended portfolio allocation",
            "timeline": "Start immediately, continue monthly",
            "priority": "MEDIUM" if priority_order else "HIGH",
            "reason": "Begin building long-term wealth through stocks"
        })
        priority_order.append("INVESTMENT")
    
    # Education step (always included)
    steps.append({
        "title": "Step 4: Continue Learning",
        "description": "Stock market knowledge improves decision making",
        "action": "Read about investing basics and market trends",
        "timeline": "Ongoing",
        "priority": "LOW",
        "reason": "Knowledge reduces investment mistakes"
    })
    
    # Display steps
    for i, step in enumerate(steps):
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.markdown(f"<h3>{i+1}</h3>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="padding: 1rem;">
                <h4 style="margin: 0 0 0.5rem 0;">{step['title']}</h4>
                <p style="margin: 0 0 0.5rem 0; color: #4B5563;"><strong>{step['description']}</strong></p>
                <p style="margin: 0 0 0.5rem 0;"><strong>Action:</strong> {step['action']}</p>
                <p style="margin: 0 0 0.5rem 0;"><strong>Timeline:</strong> {step['timeline']}</p>
                <p style="margin: 0; color: #6B7280; font-size: 0.9rem;">{step['reason']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            priority_color = {
                "HIGH": "#EF4444",
                "MEDIUM": "#F59E0B",
                "LOW": "#10B981"
            }.get(step['priority'], "#6B7280")
            
            st.markdown(f"""
            <div style="padding: 1rem; background-color: {priority_color}10; border-radius: 8px; text-align: center;">
                <p style="margin: 0; color: {priority_color}; font-weight: 600; font-size: 0.9rem;">{step['priority']}</p>
                <p style="margin: 0.5rem 0 0 0; color: {priority_color}; font-size: 0.8rem;">PRIORITY</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Next Steps
    st.markdown('<h3 class="section-header">📝 Next Steps</h3>', unsafe_allow_html=True)
    
    if priority_order:
        next_step = priority_order[0]
        if next_step == "EMERGENCY_FUND":
            st.markdown("""
            <div class="warning-box">
                <h4 style="margin: 0 0 0.5rem 0;">🟡 Immediate Priority: Emergency Fund</h4>
                <p style="margin: 0;">Focus on building your emergency fund before starting to invest. 
                This will protect you from unexpected expenses without having to sell investments at a loss.</p>
            </div>
            """, unsafe_allow_html=True)
        elif next_step == "DEBT_REDUCTION":
            st.markdown("""
            <div class="warning-box">
                <h4 style="margin: 0 0 0.5rem 0;">🟡 Immediate Priority: Debt Reduction</h4>
                <p style="margin: 0;">Focus on paying off high-interest debt first. 
                The interest you pay on debt is often higher than stock market returns.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-box">
                <h4 style="margin: 0 0 0.5rem 0;">🟢 Ready to Start Investing!</h4>
                <p style="margin: 0;">You can begin implementing your investment plan immediately. 
                Start with the recommended monthly amount and adjust as your financial situation improves.</p>
            </div>
            """, unsafe_allow_html=True)
    
    create_navigation_buttons()

def create_data_export_tab():
    """Create data export tab with proper data display"""
    st.markdown('<h1 class="main-header">📊 Data Management & Export</h1>', unsafe_allow_html=True)
    
    # Load data
    df = CSVDataHandler.load_assessments_from_csv()
    
    if df.empty:
        st.info("No assessment data available yet. Complete an assessment to see data here.")
        
        # Show current assessment status
        if st.session_state.assessment_complete:
            st.success("✅ You have completed an assessment!")
            st.info("Your assessment data will be saved after you complete the recommendation process.")
        else:
            st.warning("You haven't completed any assessments yet.")
        
        if st.button("Go to Assessment"):
            st.session_state.current_tab = "Assessment"
            st.rerun()
        return
    
    # Show success message
    st.success(f"✅ Loaded {len(df)} assessment(s) from storage")
    
    # Statistics Section
    st.markdown('<h3 class="section-header">📈 Assessment Statistics</h3>', unsafe_allow_html=True)
    
    # Filter for current model version
    if 'model_version' in df.columns:
        current_version_df = df[df['model_version'] == MODEL_VERSION]
        if not current_version_df.empty:
            df = current_version_df
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total = len(df)
        st.metric("Total Assessments", total)
    
    with col2:
        if 'financial_health_score' in df.columns:
            avg_fh = df['financial_health_score'].mean()
            st.metric("Avg Financial Health", f"{avg_fh:.1f}" if not pd.isna(avg_fh) else "N/A")
    
    with col3:
        if 'risk_category' in df.columns:
            mode_result = df['risk_category'].mode()
            if not mode_result.empty:
                st.metric("Most Common Risk", mode_result.iloc[0])
    
    with col4:
        if 'inflation_preference' in df.columns:
            mode_result = df['inflation_preference'].mode()
            if not mode_result.empty:
                st.metric("Most Common Inflation", mode_result.iloc[0].title())
    
    # Data Preview Section
    st.markdown('<h3 class="section-header">📋 Your Assessment Data</h3>', unsafe_allow_html=True)
    
    # Select and format columns for display
    display_columns = [
        'timestamp', 'risk_category', 'inflation_preference', 
        'financial_health_score', 'debt_score', 'overall_risk_score',
        'monthly_investment', 'annual_investment', 'suitability'
    ]
    
    # Filter available columns
    available_columns = [col for col in display_columns if col in df.columns]
    
    if available_columns:
        # Create a copy for display
        display_df = df[available_columns].copy()
        
        # Format columns
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        
        if 'monthly_investment' in display_df.columns:
            display_df['monthly_investment'] = display_df['monthly_investment'].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "N/A")
        
        if 'annual_investment' in display_df.columns:
            display_df['annual_investment'] = display_df['annual_investment'].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "N/A")
        
        if 'inflation_preference' in display_df.columns:
            display_df['inflation_preference'] = display_df['inflation_preference'].str.title()
        
        # Format scores
        score_columns = ['financial_health_score', 'debt_score', 'overall_risk_score']
        for col in score_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
        
        # Show the dataframe
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Show number of records
        st.caption(f"Showing {len(display_df)} assessment(s)")
    else:
        st.info("No data columns available for display.")
    
    # Export Options Section
    st.markdown('<h3 class="section-header">📁 Export Options</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Prepare CSV data
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv_data,
            file_name=f"stock_risk_assessments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            help="Download all assessment data as CSV file"
        )
    
    with col2:
        # Prepare JSON data
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_data,
            file_name=f"stock_risk_assessments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            help="Download all assessment data as JSON file"
        )
    
    with col3:
        # Clear Data Button
        if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
            st.warning("⚠️ **Danger Zone: This will delete ALL assessment data permanently!**")
            
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("Yes, Delete Everything", type="primary"):
                    try:
                        if os.path.exists(CSV_FILE):
                            os.remove(CSV_FILE)
                            st.success("✅ All data cleared successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {e}")
            
            with col_cancel:
                if st.button("Cancel", type="secondary"):
                    st.rerun()
    
    # Current Session Data
    st.markdown('<h3 class="section-header">📝 Current Session Data</h3>', unsafe_allow_html=True)
    
    if st.session_state.assessment_complete:
        current_data = {
            "Assessment ID": st.session_state.assessment_id,
            "Risk Category": st.session_state.risk_category,
            "Financial Health Score": f"{st.session_state.financial_data['financial_score']:.1f}" if st.session_state.financial_data else "N/A",
            "Debt Score": f"{st.session_state.debt_data['debt_score']:.1f}" if st.session_state.debt_data else "N/A",
            "Inflation Preference": st.session_state.inflation_preference or "Not selected",
            "Monthly Investment": f"₹{st.session_state.safe_investment['safe_monthly_investment']:,.0f}" if st.session_state.safe_investment else "N/A"
        }
        
        current_df = pd.DataFrame([current_data])
        st.dataframe(current_df, use_container_width=True, hide_index=True)
    else:
        st.info("No current assessment data. Complete an assessment to see your data here.")
    
    create_navigation_buttons()

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application function"""
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/stock-exchange.png", width=80)
        st.title("Stock Risk Advisor")
        st.caption(f"Model v{MODEL_VERSION}")
        st.markdown("---")
        
        # Navigation
        st.subheader("📊 Navigation")
        tabs = ["Welcome", "Assessment", "Financial Health", "Debt Analysis", 
                "Risk Profile", "Inflation Education", "Recommendations", "Action Plan", "Data & Export"]
        
        for tab in tabs:
            if st.button(f"📝 {tab}", use_container_width=True):
                st.session_state.current_tab = tab
                st.rerun()
        
        st.markdown("---")
        
        # Assessment Status
        if st.session_state.assessment_complete:
            st.success("✅ Assessment Complete")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 New", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        if key not in ['current_tab']:
                            del st.session_state[key]
                    init_session_state()
                    st.rerun()
            
            with col2:
                if st.session_state.inflation_preference:
                    if st.button("📊 Recommendations", use_container_width=True):
                        st.session_state.current_tab = "Recommendations"
                        st.rerun()
                else:
                    if st.button("💰 Inflation", use_container_width=True):
                        st.session_state.current_tab = "Inflation Education"
                        st.rerun()
        else:
            st.info("📋 Complete assessment to see results")
            if st.button("Start Assessment", use_container_width=True):
                st.session_state.current_tab = "Assessment"
                st.rerun()
        
        st.markdown("---")
        
        # Statistics
        try:
            stats = CSVDataHandler.get_statistics()
            if stats and stats['total_assessments'] > 0:
                with st.expander("📈 Statistics", expanded=False):
                    st.metric("Total Assessments", stats['total_assessments'])
                    st.metric("Avg Financial Health", f"{stats['avg_financial_health']:.1f}")
                    st.metric("Most Common Risk", stats.get('most_common_risk_category', 'N/A'))
                    if stats.get('most_common_inflation_pref', 'N/A') != 'N/A':
                        st.metric("Most Common Inflation", stats['most_common_inflation_pref'].title())
        except Exception as e:
            # Silently fail for statistics - not critical
            pass
    
    # Main content
    create_progress_bar()
    
    # Route to correct tab
    tab_functions = {
        "Welcome": create_welcome_tab,
        "Assessment": create_assessment_tab,
        "Financial Health": create_financial_health_tab,
        "Debt Analysis": create_debt_analysis_tab,
        "Risk Profile": create_risk_profile_tab,
        "Inflation Education": create_inflation_education_tab,
        "Recommendations": create_recommendations_tab,
        "Action Plan": create_action_plan_tab,
        "Data & Export": create_data_export_tab
    }
    
    current_tab = st.session_state.current_tab
    if current_tab in tab_functions:
        tab_functions[current_tab]()
    else:
        # Default to welcome tab
        st.session_state.current_tab = "Welcome"
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center; color:#6B7280; font-size:0.9rem; padding:1rem 0;'>
        <p>⚠️ <strong>Educational Purpose Only</strong> - Includes inflation education and ESG preferences.</p>
        <p>We are not SEBI-registered investment advisors. This is not financial advice.</p>
        <p>Model Version: {MODEL_VERSION}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

