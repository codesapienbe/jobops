"""Indeed Belgium Job Scraping Template

This template defines the configuration for scraping job listings from be.indeed.com
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class IndeedBelgiumTemplate:
    """Indeed Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://be\.indeed\.com/viewjob\?jk=.*",
        r"https://be\.indeed\.com/m/viewjob\?jk=.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["be.indeed.com"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://be\.indeed\.com/jobs\?.*",
        r"https://be\.indeed\.com/my/.*",
        r"https://be\.indeed\.com/account/.*",
        r"https://be\.indeed\.com/prefs/.*",
        r"https://be\.indeed\.com/companies/.*",
        r"https://be\.indeed\.com/salaries/.*"
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
            if parsed.netloc == "be.indeed.com":
                for pattern in IndeedBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Indeed Belgium"""
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
            user_agent=IndeedBelgiumTemplate.USER_AGENT
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=IndeedBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=IndeedBelgiumTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        # Implementation would parse Indeed's job page structure
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "job_type": "<job_type>",
            "salary": "<salary_range>",
            "contract_type": "<contract_type>",
            "skills": "<required_skills>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>"
        }
