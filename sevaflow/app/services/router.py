"""
Routing Engine for SEVAFLOW.

Implements rule-based departmental routing that is:
- Transparent and explainable
- Deterministic (same input = same output)
- Auditable for policy compliance

DESIGN PRINCIPLE: AI identifies the problem → Deterministic rules assign responsibility.
"""

from typing import Tuple
from app.config import DEPARTMENTS
from app.models import AIExtractionResult, PriorityLevel


class Router:
    """
    Rule-based router that assigns complaints to departments.
    Provides transparency and auditability in routing decisions.
    """
    
    def __init__(self):
        """Initialize router with department configuration."""
        self.departments = DEPARTMENTS
    
    def route_complaint(self, ai_result: AIExtractionResult) -> Tuple[str, int]:
        """
        Route a complaint to the appropriate department based on AI extraction.
        
        Args:
            ai_result: Extracted complaint metadata from AI layer
            
        Returns:
            Tuple of (department_name, estimated_resolution_hours)
        """
        department = ai_result.responsible_department
        
        # Validate department exists, fallback to General Helpdesk
        if department not in self.departments:
            department = "General Helpdesk"
        
        # Get SLA hours for the department
        sla_hours = self.departments[department]["sla_hours"]
        
        # Adjust SLA based on priority
        if ai_result.priority == PriorityLevel.HIGH:
            # High priority gets faster handling
            sla_hours = max(sla_hours // 2, 6)  # At least 6 hours
        elif ai_result.priority == PriorityLevel.LOW:
            # Low priority can take longer
            sla_hours = int(sla_hours * 1.5)
        
        return department, sla_hours
    
    def get_department_info(self, department: str) -> dict:
        """Get information about a specific department."""
        return self.departments.get(department, self.departments["General Helpdesk"])
    
    def get_all_departments(self) -> list:
        """Get list of all available departments."""
        return list(self.departments.keys())
    
    def explain_routing(self, ai_result: AIExtractionResult) -> str:
        """
        Generate a human-readable explanation of the routing decision.
        Useful for transparency and debugging.
        """
        department, sla = self.route_complaint(ai_result)
        
        explanation = f"""
ROUTING DECISION EXPLANATION
============================
Issue Type: {ai_result.issue_type}
Location: {ai_result.location}
Priority: {ai_result.priority.value.upper()}
AI Confidence: {ai_result.confidence:.0%}

ASSIGNED TO: {department}
Expected Resolution: {sla} hours

Reasoning:
- AI classified this as: {ai_result.issue_type}
- Department handles: {', '.join(self.departments[department].get('keywords', ['general issues'])[:5])}
- SLA adjusted for {ai_result.priority.value} priority
"""
        return explanation.strip()


# Singleton instance
router = Router()


def route_complaint(ai_result: AIExtractionResult) -> Tuple[str, int]:
    """Convenience function to route a complaint."""
    return router.route_complaint(ai_result)


def get_department_info(department: str) -> dict:
    """Convenience function to get department info."""
    return router.get_department_info(department)


def get_all_departments() -> list:
    """Convenience function to get all departments."""
    return router.get_all_departments()
