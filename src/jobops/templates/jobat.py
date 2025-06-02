"""Jobat Job Scraping Template

This template defines the configuration for scraping job listings from jobat.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class JobatTemplate:
    """Jobat template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.jobat\.be/nl/jobs/.*",
        r"https://www\.jobat\.be/fr/jobs/.*",
        r"https://www\.jobat\.be/en/jobs/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["jobat.be", "www.jobat.be"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.jobat\.be/.*/zoeken/.*",
        r"https://www\.jobat\.be/.*/profiel/.*",
        r"https://www\.jobat\.be/.*/bedrijven/.*",
        r"https://www\.jobat\.be/.*/salary-tool/.*",
        r"https://www\.jobat\.be/.*/career-advice/.*",
        r"https://www\.jobat\.be/.*/mijn-jobat/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.5
    MAX_REQUEST_DELAY: float = 4.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["jobat.be", "www.jobat.be"]:
                for pattern in JobatTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Jobat"""
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
            user_agent=JobatTemplate.USER_AGENT,
            accept_language="nl-BE,nl;q=0.9,fr;q=0.8,en;q=0.7"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=JobatTemplate.MIN_REQUEST_DELAY,
            max_request_delay=JobatTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        # Implementation would parse Jobat's multilingual job page structure
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "working_regime": "<full_time_part_time>",
            "sector": "<industry_sector>",
            "experience_level": "<experience_required>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "deadline": "<application_deadline>"
        }
