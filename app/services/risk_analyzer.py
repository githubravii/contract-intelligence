from anthropic import AsyncAnthropic
import json
import re
from typing import Dict, Any, List

from app.config import settings
from app.utils.logger import logger

class RiskAnalyzer:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def analyze_risks(
        self, 
        text: str, 
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """Analyze contract for risks using rules and optionally LLM."""
        
        # Rule-based detection
        rule_findings = self._detect_risks_rules(text)
        
        # LLM-based detection
        llm_findings = []
        if use_llm:
            llm_findings = await self._detect_risks_llm(text)
        
        # Combine findings
        all_findings = rule_findings + llm_findings
        
        # Calculate risk score
        severity_scores = {"low": 1, "medium": 3, "high": 5, "critical": 10}
        risk_score = sum(severity_scores.get(f["severity"], 0) for f in all_findings)
        risk_score = min(risk_score / 10.0, 10.0)  # Normalize to 0-10
        
        # Generate summary
        summary = self._generate_summary(all_findings, risk_score)
        
        return {
            "findings": all_findings,
            "risk_score": round(risk_score, 2),
            "summary": summary
        }
    
    def _detect_risks_rules(self, text: str) -> List[Dict[str, Any]]:
        """Detect risks using pattern matching."""
        findings = []
        
        # Auto-renewal with short notice
        auto_renewal_pattern = r'(?:automatically\s+renew|auto-renew).*?(\d+)\s*days?\s*notice'
        matches = re.finditer(auto_renewal_pattern, text, re.IGNORECASE)
        for match in matches:
            days = int(match.group(1))
            if days < 30:
                findings.append({
                    "risk_type": "auto_renewal_short_notice",
                    "severity": "high",
                    "description": f"Auto-renewal clause with only {days} days notice (< 30 days recommended)",
                    "evidence": match.group(0),
                    "recommendations": "Negotiate for at least 30 days notice period"
                })
        
        # Unlimited liability
        unlimited_pattern = r'unlimited\s+liability|liability\s+without\s+limit'
        if re.search(unlimited_pattern, text, re.IGNORECASE):
            findings.append({
                "risk_type": "unlimited_liability",
                "severity": "critical",
                "description": "Contract contains unlimited liability clause",
                "evidence": re.search(unlimited_pattern, text, re.IGNORECASE).group(0),
                "recommendations": "Cap liability at a reasonable multiple of contract value"
            })
        
        # Broad indemnity
        indemnity_pattern = r'indemnify.*?(?:any|all)\s+(?:claims|losses|damages|liabilities)'
        matches = re.finditer(indemnity_pattern, text, re.IGNORECASE)
        for match in matches:
            findings.append({
                "risk_type": "broad_indemnity",
                "severity": "high",
                "description": "Broad indemnification clause detected",
                "evidence": match.group(0),
                "recommendations": "Limit indemnity to direct damages and reasonable legal fees"
            })
        
        # No limitation of liability
        if not re.search(r'limitation\s+of\s+liability', text, re.IGNORECASE):
            findings.append({
                "risk_type": "missing_liability_cap",
                "severity": "high",
                "description": "No limitation of liability clause found",
                "evidence": None,
                "recommendations": "Add clause capping liability to contract value or reasonable amount"
            })
        
        return findings
    
    async def _detect_risks_llm(self, text: str) -> List[Dict[str, Any]]:
        """Detect risks using LLM analysis."""
        
        # Load risk analysis prompt
        with open("prompts/risk_analysis_prompt.txt", "r") as f:
            prompt_template = f.read()
        
        prompt = prompt_template.format(contract_text=text[:10000])
        
        try:
            message = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Parse JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("findings", [])
        except Exception as e:
            logger.error(f"LLM risk analysis failed: {str(e)}")
        
        return []
    
    def _generate_summary(
        self, 
        findings: List[Dict[str, Any]], 
        risk_score: float
    ) -> str:
        """Generate risk summary."""
        if not findings:
            return "No significant risks detected in this contract."
        
        severity_counts = {}
        for finding in findings:
            sev = finding["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        summary_parts = [f"Risk Score: {risk_score}/10"]
        
        if severity_counts:
            counts_str = ", ".join(
                f"{count} {severity}" 
                for severity, count in sorted(severity_counts.items())
            )
            summary_parts.append(f"Found {len(findings)} issues: {counts_str}")
        
        return ". ".join(summary_parts) + "."