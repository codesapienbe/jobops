"""Glassdoor Belgium Job Scraping Template

This template defines the configuration for scraping job listings from glassdoor.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class GlassdoorBelgiumTemplate:
    """Glassdoor Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.glassdoor\.be/job-listing/.*",
        r"https://www\.glassdoor\.be/Jobs/.*-jobs-.*\.htm\?jl=.*",
        r"https://www\.glassdoor\.com/Job/belgium-.*-jobs-.*\.htm\?jl=.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["glassdoor.be", "www.glassdoor.be", "glassdoor.com", "www.glassdoor.com"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.glassdoor\.(be|com)/Jobs/.*-jobs-.*\.htm$",
        r"https://www\.glassdoor\.(be|com)/Search/.*",
        r"https://www\.glassdoor\.(be|com)/Reviews/.*",
        r"https://www\.glassdoor\.(be|com)/Salaries/.*",
        r"https://www\.glassdoor\.(be|com)/Interview/.*",
        r"https://www\.glassdoor\.(be|com)/Benefits/.*",
        r"https://www\.glassdoor\.(be|com)/Photos/.*",
        r"https://www\.glassdoor\.(be|com)/Overview/.*",
        r"https://www\.glassdoor\.(be|com)/member/.*",
        r"https://www\.glassdoor\.(be|com)/profile/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds) - Glassdoor requires careful rate limiting
    MIN_REQUEST_DELAY: float = 4.0
    MAX_REQUEST_DELAY: float = 6.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if any(domain in parsed.netloc for domain in ["glassdoor.be", "glassdoor.com"]):
                for pattern in GlassdoorBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Glassdoor Belgium"""
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
            user_agent=GlassdoorBelgiumTemplate.USER_AGENT,
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
            page_timeout=35000,
            min_request_delay=GlassdoorBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=GlassdoorBelgiumTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "job_type": "<job_type>",
            "employment_type": "<employment_type>",
            "salary_estimate": "<salary_estimate>",
            "company_rating": "<company_rating>",
            "company_size": "<company_size>",
            "industry": "<industry>",
            "sector": "<sector>",
            "experience_level": "<experience_level>",
            "skills": "<required_skills>",
            "job_function": "<job_function>",
            "education": "<education_requirements>",
            "benefits": "<benefits_offered>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "easy_apply": "<easy_apply_available>",
            "posted_date": "<posted_date>",
            "glassdoor_job_id": "<glassdoor_job_id>",
            "company_glassdoor_url": "<company_profile_url>",
            "company_reviews_count": "<reviews_count>"
        }
