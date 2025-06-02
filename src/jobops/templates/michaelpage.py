"""Michael Page Benelux Job Scraping Template

This template defines the configuration for scraping job listings from michaelpage.nl and michaelpage.lu
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class MichaelPageBeneluxTemplate:
    """Michael Page Benelux template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.michaelpage\.nl/job-listing/.*",
        r"https://www\.michaelpage\.lu/job-listing/.*",
        r"https://www\.michaelpage\.nl/vacatures/.*",
        r"https://www\.michaelpage\.lu/emplois/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: [
        "michaelpage.nl", "www.michaelpage.nl",
        "michaelpage.lu", "www.michaelpage.lu"
    ])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.michaelpage\.(nl|lu)/job-search.*",
        r"https://www\.michaelpage\.(nl|lu)/vacature-zoeken.*",
        r"https://www\.michaelpage\.(nl|lu)/recherche-emploi.*",
        r"https://www\.michaelpage\.(nl|lu)/advice/.*",
        r"https://www\.michaelpage\.(nl|lu)/advies/.*",
        r"https://www\.michaelpage\.(nl|lu)/conseils/.*",
        r"https://www\.michaelpage\.(nl|lu)/about-us/.*",
        r"https://www\.michaelpage\.(nl|lu)/contact/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 3.0
    MAX_REQUEST_DELAY: float = 5.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if any(domain in parsed.netloc for domain in ["michaelpage.nl", "michaelpage.lu"]):
                for pattern in MichaelPageBeneluxTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Michael Page Benelux"""
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
            user_agent=MichaelPageBeneluxTemplate.USER_AGENT,
            accept_language="nl,fr,de,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=MichaelPageBeneluxTemplate.MIN_REQUEST_DELAY,
            max_request_delay=MichaelPageBeneluxTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "country": "<netherlands_luxembourg>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "specialization": "<michael_page_division>",
            "sector": "<industry_sector>",
            "seniority_level": "<seniority_level>",
            "experience_years": "<years_experience>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "benefits": "<benefits_package>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "consultant_name": "<consultant_name>",
            "consultant_contact": "<consultant_contact>",
            "posted_date": "<posted_date>",
            "job_reference": "<michael_page_reference>",
            "benelux_region": "<benelux_coverage>"
        }
