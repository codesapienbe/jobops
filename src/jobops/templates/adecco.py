"""Adecco Belgium Job Scraping Template

This template defines the configuration for scraping job listings from adecco.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class AdeccoBelgiumTemplate:
    """Adecco Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.adecco\.be/nl-be/job-seekers/search-jobs/.*",
        r"https://www\.adecco\.be/fr-be/candidats/recherche-emplois/.*",
        r"https://www\.adecco\.be/en-be/job-seekers/search-jobs/.*",
        r"https://www\.adecco\.be/jobs/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["adecco.be", "www.adecco.be"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.adecco\.be/.*/search.*\?.*",
        r"https://www\.adecco\.be/.*/my-adecco/.*",
        r"https://www\.adecco\.be/.*/mon-adecco/.*",
        r"https://www\.adecco\.be/.*/employers/.*",
        r"https://www\.adecco\.be/.*/employeurs/.*",
        r"https://www\.adecco\.be/.*/about-us/.*",
        r"https://www\.adecco\.be/.*/a-propos/.*",
        r"https://www\.adecco\.be/.*/contact/.*",
        r"https://www\.adecco\.be/.*/salary-guide/.*",
        r"https://www\.adecco\.be/.*/guide-salarial/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 3.0
    MAX_REQUEST_DELAY: float = 5.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["adecco.be", "www.adecco.be"]:
                for pattern in AdeccoBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Adecco Belgium"""
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
            user_agent=AdeccoBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=AdeccoBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=AdeccoBelgiumTemplate.MAX_REQUEST_DELAY
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
            "employment_duration": "<temporary_permanent>",
            "salary_range": "<salary_range>",
            "sector": "<industry_sector>",
            "job_category": "<job_category>",
            "experience_level": "<experience_level>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "working_hours": "<working_hours>",
            "start_date": "<start_date>",
            "benefits": "<benefits_package>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "consultant_name": "<adecco_consultant>",
            "branch_office": "<adecco_branch>",
            "posted_date": "<posted_date>",
            "job_reference": "<adecco_reference>",
            "urgency": "<urgent_position>"
        }
