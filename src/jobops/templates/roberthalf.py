"""Robert Half Belgium Job Scraping Template

This template defines the configuration for scraping job listings from roberthalf.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class RobertHalfBelgiumTemplate:
    """Robert Half Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.roberthalf\.be/nl/vacatures/.*",
        r"https://www\.roberthalf\.be/fr/offres-emploi/.*",
        r"https://www\.roberthalf\.be/en/jobs/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["roberthalf.be", "www.roberthalf.be"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.roberthalf\.be/.*/zoeken/.*",
        r"https://www\.roberthalf\.be/.*/recherche/.*",
        r"https://www\.roberthalf\.be/.*/search/.*",
        r"https://www\.roberthalf\.be/.*/salaires/.*",
        r"https://www\.roberthalf\.be/.*/salary/.*",
        r"https://www\.roberthalf\.be/.*/career-advice/.*",
        r"https://www\.roberthalf\.be/.*/conseils-carriere/.*",
        r"https://www\.roberthalf\.be/.*/about/.*",
        r"https://www\.roberthalf\.be/.*/contact/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.5
    MAX_REQUEST_DELAY: float = 4.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["roberthalf.be", "www.roberthalf.be"]:
                for pattern in RobertHalfBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Robert Half Belgium"""
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
            user_agent=RobertHalfBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=RobertHalfBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=RobertHalfBelgiumTemplate.MAX_REQUEST_DELAY
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
            "specialization": "<specialization_area>",
            "seniority_level": "<seniority_level>",
            "skills": "<required_skills>",
            "certifications": "<required_certifications>",
            "languages": "<required_languages>",
            "experience": "<years_experience>",
            "education": "<education_level>",
            "benefits": "<benefits_package>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "consultant_name": "<recruiter_name>",
            "posted_date": "<posted_date>",
            "job_id": "<robert_half_job_id>"
        }
