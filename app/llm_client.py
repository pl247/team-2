"""
LLM client for calling the on-prem NVIDIA Nemotron model via vLLM.
Includes graceful fallback for when the LLM is unreachable or returns malformed output.
"""
import json
import logging
import time
from typing import Dict, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Valid values for LLM output validation
VALID_REASON_CATEGORIES = {
    "Mechanical Failure", "Operator Error", "Material Shortage", 
    "Maintenance", "Power Loss", "Unknown"
}
VALID_SEVERITIES = {"Low", "Medium", "High", "Critical"}


class LLMClient:
    """Client for interacting with the on-prem LLM service."""
    
    def __init__(self, base_url: str, model: str, api_key: str, timeout_seconds: int = 15):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.session = self._create_session()
        self._last_health_check = 0
        self._is_healthy = False
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Define retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for LLM API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def health_check(self) -> bool:
        """
        Check if the LLM service is reachable and healthy.
        Cached for performance - only checks every 30 seconds.
        """
        current_time = time.time()
        if current_time - self._last_health_check < 30:
            return self._is_healthy
            
        try:
            # Try to access the models endpoint to check service availability
            url = f"{self.base_url}/models"
            response = self.session.get(
                url, 
                headers=self._get_headers(),
                timeout=min(5, self.timeout_seconds)  # Quick timeout for health check
            )
            
            self._is_healthy = response.status_code == 200
            self._last_health_check = current_time
            
            if self._is_healthy:
                logger.info("LLM service health check: OK")
            else:
                logger.warning(f"LLM service health check failed: {response.status_code}")
                
        except Exception as e:
            self._is_healthy = False
            self._last_health_check = current_time
            logger.warning(f"LLM service health check exception: {e}")
            
        return self._is_healthy
    
    def classify_event(self, description: str) -> Tuple[str, str]:
        """
        Classify a machine event using the LLM.
        
        Args:
            description: Free-text description of the machine event
            
        Returns:
            Tuple of (reason_category, severity)
            
        On failure, returns ("Unclassified", "Medium") as fallback.
        """
        if not description or not description.strip():
            logger.warning("Empty description provided for LLM classification")
            return "Unclassified", "Medium"
        
        # Check if LLM is healthy first
        if not self.health_check():
            logger.warning("LLM service unhealthy, using fallback classification")
            return "Unclassified", "Medium"
        
        try:
            # Prepare the request payload
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are an industrial equipment expert. Classify machine downtime events into:
                        reason_category: Mechanical Failure, Operator Error, Material Shortage, Maintenance, Power Loss, or Unknown
                        severity: Low, Medium, High, or Critical
                        
                        Respond ONLY with valid JSON in this exact format:
                        {"reason_category": "<category>", "severity": "<severity>"}
                        
                        Do not include any other text, explanation, or formatting."""
                    },
                    {
                        "role": "user",
                        "content": f"Classify this machine event: {description}"
                    }
                ],
                "temperature": 0.1,  # Low temperature for consistent outputs
                "max_tokens": 50,
                "response_format": {"type": "json_object"}  # Request JSON output
            }
            
            # Make the API call
            url = f"{self.base_url}/chat/completions"
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout_seconds
            )
            
            if response.status_code != 200:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                return "Unclassified", "Medium"
            
            # Parse the response
            result = response.json()
            
            # Extract the content from the response
            if "choices" not in result or len(result["choices"]) == 0:
                logger.error("LLM response missing choices")
                return "Unclassified", "Medium"
                
            message_content = result["choices"][0].get("message", {}).get("content", "")
            if not message_content:
                logger.error("LLM response missing message content")
                return "Unclassified", "Medium"
            
            # Parse JSON from the response
            try:
                classification = json.loads(message_content.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.debug(f"LLM raw response: {message_content}")
                return "Unclassified", "Medium"
            
            # Validate the response format
            reason_category = classification.get("reason_category", "").strip()
            severity = classification.get("severity", "").strip()
            
            # Validate against allowed values
            if reason_category not in VALID_REASON_CATEGORIES:
                logger.warning(f"Invalid reason_category from LLM: {reason_category}")
                reason_category = "Unclassified"
                
            if severity not in VALID_SEVERITIES:
                logger.warning(f"Invalid severity from LLM: {severity}")
                severity = "Medium"
            
            logger.info(f"LLM classification successful: {reason_category}, {severity}")
            return reason_category, severity
            
        except requests.exceptions.Timeout:
            logger.error("LLM request timed out")
            return "Unclassified", "Medium"
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to LLM service")
            return "Unclassified", "Medium"
        except Exception as e:
            logger.error(f"Unexpected error in LLM classification: {e}")
            return "Unclassified", "Medium"


# Factory function for easy instantiation
def create_llm_client() -> Optional[LLMClient]:
    """
    Create an LLM client from environment variables.
    Returns None if required configuration is missing.
    """
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    api_key = os.getenv("LLM_API_KEY")
    timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "15"))
    
    if not all([base_url, model, api_key]):
        logger.warning("LLM configuration incomplete, LLM features disabled")
        return None
    
    return LLMClient(base_url, model, api_key, timeout_seconds)