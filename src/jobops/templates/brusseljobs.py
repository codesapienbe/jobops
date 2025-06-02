"""BrusselsJobs Scraping Template

This template defines the configuration for scraping job listings from brusselsjobs.com
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class BrusselsJobsTemplate:
    """BrusselsJobs template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.brusselsjobs\.com/jobs/.*",
        r"https://www\.brusselsjobs\.com/en/jobs/.*",
        r"https://www\.brusselsjobs\.com/fr/jobs/.*",
        r"https://www\.brusselsjobs\.com/nl/jobs/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["brusselsjobs.com", "www.brusselsjobs.com"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.brusselsjobs\.com/.*/search.*",
        r"https://www\.brusselsjobs\.com/.*/recherche.*",
        r"https://www\.brusselsjobs\.com/.*/zoeken.*",
        r"https://www\.brusselsjobs\.com/.*/companies/.*",
        r"https://www\.brusselsjobs\.com/.*/entreprises/.*",
        r"https://www\.brusselsjobs\.com/.*/bedrijven/.*",
        r"https://www\.brusselsjobs\.com/.*/my-account/.*",
        r"https://www\.brusselsjobs\.com/.*/mon-compte/.*",
        r"https://www\.brusselsjobs\.com/.*/mijn-account/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.0
    MAX_REQUEST_DELAY: float = 3.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["brusselsjobs.com", "www.brusselsjobs.com"]:
                for pattern in BrusselsJobsTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for BrusselsJobs"""
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
            user_agent=BrusselsJobsTemplate.USER_AGENT,
            accept_language="en,fr,nl,de;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=BrusselsJobsTemplate.MIN_REQUEST_DELAY,
            max_request_delay=BrusselsJobsTemplate.MAX_REQUEST_DELAY
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
            "salary_range": "<salary_range>",
            "sector": "<sector>",
            "specialization": "<specialization>",
            "experience_level": "<experience_level>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "multilingual_requirement": "<multilingual_position>",
            "international_environment": "<international_company>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "job_reference": "<brusselsjobs_reference>",
            "target_region": "Brussels/Benelux"
        }
