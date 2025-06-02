"""Forem Job Scraping Template

This template defines the configuration for scraping job listings from leforem.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class ForemTemplate:
    """Forem template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.leforem\.be/particuliers/offres-emploi-formation/consulter-offres-emploi/.*",
        r"https://www\.leforem\.be/Citoyens/Offres-emploi-et-formation/Consulter-les-offres-d-emploi/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["leforem.be", "www.leforem.be"])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.leforem\.be/particuliers/recherche/.*",
        r"https://www\.leforem\.be/particuliers/mon-espace/.*",
        r"https://www\.leforem\.be/particuliers/formation/.*",
        r"https://www\.leforem\.be/entreprises/.*",
        r"https://www\.leforem\.be/apropos/.*",
        r"https://www\.leforem\.be/citoyens/mes-services/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 3.0
    MAX_REQUEST_DELAY: float = 5.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["leforem.be", "www.leforem.be"]:
                for pattern in ForemTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Forem"""
        content_filter = PruningContentFilter(
            threshold=0.3,
            threshold_type="fixed",
            min_word_threshold=10
        )
        
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=content_filter
        )
        
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True,
            verbose=False,
            user_agent=ForemTemplate.USER_AGENT,
            accept_language="fr-BE,fr;q=0.9,en;q=0.7"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=ForemTemplate.MIN_REQUEST_DELAY,
            max_request_delay=ForemTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "working_regime": "<working_regime>",
            "sector": "<sector>",
            "function_group": "<function_group>",
            "skills": "<required_skills>",
            "experience": "<experience_required>",
            "education": "<education_level>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "reference_number": "<forem_reference>",
            "posted_date": "<posted_date>",
            "region": "Wallonia"
        }
