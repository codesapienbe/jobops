"""EURES European Job Mobility Portal Scraping Template

This template defines the configuration for scraping job listings from eures.europa.eu
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class EURESTemplate:
    """EURES template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://eures\.europa\.eu/job-search-engine/jv-details/.*",
        r"https://eures\.europa\.eu/portal/jv-se/job-details/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["eures.europa.eu"])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://eures\.europa\.eu/portal/jv-se/search.*",
        r"https://eures\.europa\.eu/job-search-engine.*\?.*",
        r"https://eures\.europa\.eu/portal/page/portal/eures/.*",
        r"https://eures\.europa\.eu/living-and-working/.*",
        r"https://eures\.europa\.eu/your-first-eures-job/.*",
        r"https://eures\.europa\.eu/success-stories/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds) - EU site, be respectful
    MIN_REQUEST_DELAY: float = 4.0
    MAX_REQUEST_DELAY: float = 6.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc == "eures.europa.eu":
                for pattern in EURESTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for EURES"""
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
            user_agent=EURESTemplate.USER_AGENT,
            accept_language="en,nl,fr,de;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=35000,
            min_request_delay=EURESTemplate.MIN_REQUEST_DELAY,
            max_request_delay=EURESTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "country": "<eu_country>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "sector": "<sector>",
            "occupation_code": "<isco_code>",
            "experience_level": "<experience_level>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "work_permit_required": "<work_permit_info>",
            "mobility_scheme": "<eures_mobility_program>",
            "living_conditions": "<living_working_conditions>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "contact_details": "<employer_contact>",
            "posted_date": "<posted_date>",
            "application_deadline": "<deadline>",
            "eures_job_id": "<eures_reference>",
            "cross_border_opportunity": "<cross_border_position>"
        }
