"""Nationale Vacaturebank Netherlands Job Scraping Template

This template defines the configuration for scraping job listings from nationalevacaturebank.nl
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class NationaleVacaturebankTemplate:
    """Nationale Vacaturebank template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.nationalevacaturebank\.nl/vacature/.*",
        r"https://www\.nationalevacaturebank\.nl/vacatures/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["nationalevacaturebank.nl", "www.nationalevacaturebank.nl"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.nationalevacaturebank\.nl/zoeken.*",
        r"https://www\.nationalevacaturebank\.nl/vacature-zoeken.*",
        r"https://www\.nationalevacaturebank\.nl/werkgevers/.*",
        r"https://www\.nationalevacaturebank\.nl/carriere-tips/.*",
        r"https://www\.nationalevacaturebank\.nl/salarissen/.*",
        r"https://www\.nationalevacaturebank\.nl/cv/.*",
        r"https://www\.nationalevacaturebank\.nl/profiel/.*",
        r"https://www\.nationalevacaturebank\.nl/inloggen.*",
        r"https://www\.nationalevacaturebank\.nl/registreren.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.5
    MAX_REQUEST_DELAY: float = 4.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["nationalevacaturebank.nl", "www.nationalevacaturebank.nl"]:
                for pattern in NationaleVacaturebankTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Nationale Vacaturebank"""
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
            user_agent=NationaleVacaturebankTemplate.USER_AGENT,
            accept_language="nl,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=NationaleVacaturebankTemplate.MIN_REQUEST_DELAY,
            max_request_delay=NationaleVacaturebankTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "province": "<dutch_province>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "sector": "<sector>",
            "function_group": "<function_group>",
            "experience_level": "<experience_level>",
            "working_hours": "<working_hours>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "company_size": "<company_size>",
            "benefits": "<benefits_package>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "application_deadline": "<deadline>",
            "job_reference": "<vacaturebank_reference>",
            "country": "Netherlands"
        }
