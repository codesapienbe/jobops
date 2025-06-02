"""LinkedIn Jobs Belgium Scraping Template

This template defines the configuration for scraping job listings from linkedin.com/jobs
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class LinkedInJobsBelgiumTemplate:
    """LinkedIn Jobs Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.linkedin\.com/jobs/view/\d+",
        r"https://be\.linkedin\.com/jobs/view/\d+"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["linkedin.com", "www.linkedin.com", "be.linkedin.com"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://.*\.linkedin\.com/jobs/search/.*",
        r"https://.*\.linkedin\.com/in/.*",
        r"https://.*\.linkedin\.com/company/.*",
        r"https://.*\.linkedin\.com/feed/.*",
        r"https://.*\.linkedin\.com/messaging/.*",
        r"https://.*\.linkedin\.com/notifications/.*",
        r"https://.*\.linkedin\.com/mynetwork/.*",
        r"https://.*\.linkedin\.com/learning/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds) - LinkedIn requires more careful rate limiting
    MIN_REQUEST_DELAY: float = 4.0
    MAX_REQUEST_DELAY: float = 7.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if any(domain in parsed.netloc for domain in ["linkedin.com"]):
                for pattern in LinkedInJobsBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for LinkedIn Jobs"""
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
            user_agent=LinkedInJobsBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en-US;q=0.8",
            extra_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=40000,
            min_request_delay=LinkedInJobsBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=LinkedInJobsBelgiumTemplate.MAX_REQUEST_DELAY
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
            "seniority_level": "<seniority_level>",
            "industry": "<industry>",
            "company_size": "<company_size>",
            "skills": "<required_skills>",
            "connections": "<mutual_connections>",
            "applicant_count": "<number_of_applicants>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "linkedin_job_id": "<linkedin_job_id>",
            "company_linkedin_url": "<company_profile_url>"
        }
