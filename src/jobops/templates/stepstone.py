"""StepStone Belgium Job Scraping Template

This template defines the configuration for scraping job listings from stepstone.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class StepStoneBelgiumTemplate:
    """StepStone Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.stepstone\.be/jobs/.*",
        r"https://www\.stepstone\.be/en/jobs/.*",
        r"https://www\.stepstone\.be/fr/jobs/.*",
        r"https://www\.stepstone\.be/nl/jobs/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["stepstone.be", "www.stepstone.be"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.stepstone\.be/.*/search.*",
        r"https://www\.stepstone\.be/.*/profile/.*",
        r"https://www\.stepstone\.be/.*/companies/.*",
        r"https://www\.stepstone\.be/.*/career-advice/.*",
        r"https://www\.stepstone\.be/.*/salary/.*",
        r"https://www\.stepstone\.be/.*/login.*",
        r"https://www\.stepstone\.be/.*/register.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.0
    MAX_REQUEST_DELAY: float = 4.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["stepstone.be", "www.stepstone.be"]:
                for pattern in StepStoneBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for StepStone Belgium"""
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
            user_agent=StepStoneBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=StepStoneBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=StepStoneBelgiumTemplate.MAX_REQUEST_DELAY
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
            "experience_level": "<experience_level>",
            "sector": "<industry_sector>",
            "skills": "<required_skills>",
            "education": "<education_requirements>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "company_size": "<company_size>"
        }
