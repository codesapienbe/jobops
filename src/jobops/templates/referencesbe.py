"""References.be Job Scraping Template

This template defines the configuration for scraping job listings from references.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class ReferencesBelgiumTemplate:
    """References.be template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.references\.be/jobs/.*",
        r"https://www\.references\.be/nl/jobs/.*",
        r"https://www\.references\.be/fr/jobs/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["references.be", "www.references.be"])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.references\.be/.*/search/.*",
        r"https://www\.references\.be/.*/zoeken/.*",
        r"https://www\.references\.be/.*/recherche/.*",
        r"https://www\.references\.be/.*/cv/.*",
        r"https://www\.references\.be/.*/profile/.*",
        r"https://www\.references\.be/.*/profiel/.*",
        r"https://www\.references\.be/.*/companies/.*",
        r"https://www\.references\.be/.*/bedrijven/.*",
        r"https://www\.references\.be/.*/entreprises/.*",
        r"https://www\.references\.be/.*/career-tips/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.0
    MAX_REQUEST_DELAY: float = 3.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["references.be", "www.references.be"]:
                for pattern in ReferencesBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for References.be"""
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
            user_agent=ReferencesBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=25000,
            min_request_delay=ReferencesBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=ReferencesBelgiumTemplate.MAX_REQUEST_DELAY
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
            "salary_indication": "<salary_indication>",
            "sector": "<sector>",
            "function_level": "<function_level>",
            "experience_required": "<experience_years>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "keywords": "<job_keywords>",
            "company_size": "<company_size>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "job_id": "<references_job_id>",
            "region": "<belgian_region>"
        }
