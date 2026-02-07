"""
AI Complaint Intelligence Layer for SEVAFLOW.

This module processes raw citizen input and extracts structured grievance metadata
using LLM. Supports multiple providers:
- Ollama (for local Qwen2.5-7B-Instruct)
- OpenAI-compatible APIs

RESPONSIBLE AI PRINCIPLES:
- AI assists decision-making; it does not autonomously act
- All outputs are validated and can be overridden
- Transparency in how classifications are made
"""

import json
import re
import os
import httpx
from typing import Optional

from app.config import settings, DEPARTMENTS, PRIORITY_KEYWORDS
from app.models import AIExtractionResult, PriorityLevel


# System prompt for complaint classification
SYSTEM_PROMPT = """You are a government grievance classifier for Delhi, India.

Your role is to analyze citizen complaints and extract structured information.
You must ALWAYS respond with valid JSON only - no explanations, no markdown.

TASK:
Given a citizen's complaint text, extract:
1. issue_type: A brief category (e.g., "Streetlight outage", "Garbage not collected", "Water supply issue")
2. location: The specific location mentioned (street, area, landmark). If unclear, use "Not specified"
3. responsible_department: One of these Delhi departments:
   - MCD Electrical (streetlights, public lighting)
   - Delhi Jal Board (water, sewage, drainage)
   - PWD (roads, potholes, footpaths)
   - MCD Sanitation (garbage, cleaning, waste)
   - Traffic Police (traffic, signals, parking)
   - Delhi Police (crime, safety, law & order)
   - BSES/TPDDL (electricity meters, bills, power supply to homes)
   - DDA (parks, encroachment, development)
   - General Helpdesk (anything else)
4. priority: "low", "medium", or "high" based on:
   - HIGH: Safety hazards, crimes, emergencies, dangerous conditions
   - MEDIUM: Service disruptions, broken infrastructure
   - LOW: Suggestions, minor inconveniences, requests
5. confidence: Your confidence in this classification (0.0 to 1.0)
6. summary: A one-line summary of the complaint in formal language

RESPONSE FORMAT (JSON only):
{
  "issue_type": "string",
  "location": "string", 
  "responsible_department": "string",
  "priority": "low|medium|high",
  "confidence": 0.0-1.0,
  "summary": "string"
}

Be concise. Be accurate. Output ONLY valid JSON."""


class AIProcessor:
    """
    Processes citizen complaints using LLM to extract structured metadata.
    Supports Ollama (local) and OpenAI-compatible APIs.
    """
    
    def __init__(self):
        """Initialize the AI processor."""
        self.provider = os.getenv("LLM_PROVIDER", "ollama")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._log_config()
    
    def _log_config(self):
        """Log the current configuration."""
        if self.provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
            print(f"✅ AI Processor: Ollama ({model}) at {base_url}")
        elif self.provider == "openai":
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            print(f"✅ AI Processor: OpenAI-compatible ({model}) at {base_url}")
        else:
            print("⚠️ AI Processor: Using fallback (rule-based)")
    
    async def process_complaint(self, text: str) -> AIExtractionResult:
        """
        Process a citizen complaint and extract structured metadata.
        
        Args:
            text: Raw complaint text from citizen
            
        Returns:
            AIExtractionResult with extracted metadata
        """
        try:
            if self.provider == "ollama":
                result = await self._process_with_ollama(text)
            elif self.provider == "openai":
                result = await self._process_with_openai(text)
            else:
                result = None
            
            if result:
                return result
        except Exception as e:
            print(f"⚠️ LLM processing failed: {e}, using fallback")
        
        # Fallback to rule-based extraction
        return self._fallback_extraction(text)
    
    async def _process_with_ollama(self, text: str) -> Optional[AIExtractionResult]:
        """Process complaint using Ollama (local LLM)."""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Citizen's complaint:\n\"{text}\""}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 500
            }
        }
        
        response = await self.client.post(
            f"{base_url}/api/chat",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        content = data.get("message", {}).get("content", "")
        
        return self._parse_llm_response(content)
    
    async def _process_with_openai(self, text: str) -> Optional[AIExtractionResult]:
        """Process complaint using OpenAI-compatible API."""
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        api_key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Citizen's complaint:\n\"{text}\""}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        response = await self.client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        return self._parse_llm_response(content)
    
    def _parse_llm_response(self, response_text: str) -> Optional[AIExtractionResult]:
        """Parse LLM response into structured result."""
        # Clean up response (remove markdown code blocks if present)
        response_text = self._clean_json_response(response_text)
        
        try:
            data = json.loads(response_text)
            return AIExtractionResult(
                issue_type=data.get("issue_type", "General Issue"),
                location=data.get("location", "Not specified"),
                responsible_department=data.get("responsible_department", "General Helpdesk"),
                priority=PriorityLevel(data.get("priority", "medium")),
                confidence=float(data.get("confidence", 0.7)),
                summary=data.get("summary", "")
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ JSON parsing failed: {e}")
            return None
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks and clean JSON response."""
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return text.strip()
    
    def _fallback_extraction(self, text: str) -> AIExtractionResult:
        """
        Rule-based fallback extraction when LLM is unavailable.
        Uses keyword matching for department and priority classification.
        """
        text_lower = text.lower()
        
        # Detect department from keywords
        department = "General Helpdesk"
        for dept_name, dept_info in DEPARTMENTS.items():
            keywords = dept_info.get("keywords", [])
            if any(keyword in text_lower for keyword in keywords):
                department = dept_name
                break
        
        # Detect priority from keywords
        priority = PriorityLevel.MEDIUM
        for level, keywords in PRIORITY_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                priority = PriorityLevel(level)
                break
        
        # Extract location (simple heuristic)
        location = self._extract_location_fallback(text)
        
        # Generate simple issue type
        issue_type = self._generate_issue_type_fallback(text, department)
        
        return AIExtractionResult(
            issue_type=issue_type,
            location=location,
            responsible_department=department,
            priority=priority,
            confidence=0.5,  # Lower confidence for fallback
            summary=text[:100] + "..." if len(text) > 100 else text
        )
    
    def _extract_location_fallback(self, text: str) -> str:
        """Extract location using pattern matching."""
        location_patterns = [
            r"(?:near|at|in|around)\s+([A-Z][a-zA-Z\s]+(?:metro|station|gate|market|colony|nagar|vihar|park|road|street|block|sector))",
            r"([A-Z][a-zA-Z\s]+(?:Metro|Station|Gate|Market|Colony|Nagar|Vihar|Park|Road|Street|Block|Sector))",
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Location not specified"
    
    def _generate_issue_type_fallback(self, text: str, department: str) -> str:
        """Generate a simple issue type based on keywords."""
        text_lower = text.lower()
        
        issue_mappings = {
            "streetlight": "Streetlight issue",
            "pothole": "Pothole on road",
            "garbage": "Garbage collection issue",
            "water": "Water supply issue",
            "sewage": "Sewage/drainage issue",
            "traffic": "Traffic issue",
            "parking": "Parking problem",
            "crime": "Law & order issue",
            "road": "Road maintenance issue",
            "electricity": "Electricity issue",
        }
        
        for keyword, issue_type in issue_mappings.items():
            if keyword in text_lower:
                return issue_type
        
        return "General complaint"


# Singleton instance
ai_processor = AIProcessor()


async def process_complaint(text: str) -> AIExtractionResult:
    """
    Convenience function to process a complaint.
    
    Args:
        text: Raw complaint text from citizen
        
    Returns:
        AIExtractionResult with extracted metadata
    """
    return await ai_processor.process_complaint(text)
