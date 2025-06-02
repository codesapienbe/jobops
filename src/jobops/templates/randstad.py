"""Randstad Belgium Job Scraping Template

This template defines the configuration for scraping job listings from randstad.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class RandstadBelgiumTemplate:
    """Randstad Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.randstad\.be/jobs/.*",
        r"https://www\.randstad\.be/nl/jobs/.*",
        r"https://www\.randstad\.be/fr/jobs/.*",
        r"https://www\.randstad\.be/en/jobs/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["randstad.be", "www.randstad.be"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.randstad\.be/.*/job-search/.*",
        r"https://www\.randstad\.be/.*/recherche-emploi/.*",
        r"https://www\.randstad\.be/.*/my-randstad/.*",
        r"https://www\.randstad\.be/.*/mon-randstad/.*",
        r"https://www\.randstad\.be/.*/salary-checker/.*",
        r"https://www\.randstad\.be/.*/career-advice/.*",
        r"https://www\.randstad\.be/.*/conseils-carriere/.*",
        r"https://www\.randstad\.be/.*/about-us/.*",
        r"https://www\.randstad\.be/.*/contact/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.5
    MAX_REQUEST_DELAY: float = 4.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["randstad.be", "www.randstad.be"]:
                for pattern in RandstadBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Randstad Belgium"""
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
            user_agent=RandstadBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=RandstadBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=RandstadBelgiumTemplate.MAX_REQUEST_DELAY
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
            "employment_type": "<temporary_permanent>",
            "salary_range": "<salary_range>",
            "sector": "<industry_sector>",
            "function_category": "<function_category>",
            "experience_level": "<experience_level>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "working_hours": "<working_hours>",
            "benefits": "<benefits_package>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "consultant_contact": "<recruiter_contact>",
            "posted_date": "<posted_date>",
            "job_reference": "<randstad_reference>",
            "office_location": "<randstad_office>"
        }
