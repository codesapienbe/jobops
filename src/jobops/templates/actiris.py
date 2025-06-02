"""Actiris Job Scraping Template

This template defines the configuration for scraping job listings from actiris.brussels
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class ActirisTemplate:
    """Actiris template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.actiris\.brussels/fr/citoyens/trouver-un-emploi/offres-demploi/.*",
        r"https://www\.actiris\.brussels/nl/burgers/werk-zoeken/vacatures/.*",
        r"https://www\.actiris\.brussels/en/citizens/find-job/job-offers/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["actiris.brussels", "www.actiris.brussels"])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.actiris\.brussels/.*/recherche/.*",
        r"https://www\.actiris\.brussels/.*/mon-espace/.*",
        r"https://www\.actiris\.brussels/.*/formations/.*",
        r"https://www\.actiris\.brussels/.*/entreprises/.*",
        r"https://www\.actiris\.brussels/.*/services/.*",
        r"https://www\.actiris\.brussels/.*/actualites/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (compatible; Crawl4AI/1.0; +https://crawl4ai.example.com)"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 3.5
    MAX_REQUEST_DELAY: float = 5.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["actiris.brussels", "www.actiris.brussels"]:
                for pattern in ActirisTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Actiris"""
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
            user_agent=ActirisTemplate.USER_AGENT,
            accept_language="fr-BE,nl-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=ActirisTemplate.MIN_REQUEST_DELAY,
            max_request_delay=ActirisTemplate.MAX_REQUEST_DELAY
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
            "working_hours": "<working_hours>",
            "sector": "<sector>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "experience": "<experience_required>",
            "education": "<education_level>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "reference_number": "<actiris_reference>",
            "posted_date": "<posted_date>",
            "region": "Brussels-Capital"
        }
