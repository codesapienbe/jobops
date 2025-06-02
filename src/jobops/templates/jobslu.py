"""Jobs.lu Luxembourg Job Scraping Template

This template defines the configuration for scraping job listings from jobs.lu
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class JobsLuxembourgTemplate:
    """Jobs.lu template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.jobs\.lu/emplois/.*",
        r"https://www\.jobs\.lu/jobs/.*",
        r"https://www\.jobs\.lu/stellenangebote/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["jobs.lu", "www.jobs.lu"])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.jobs\.lu/recherche.*",
        r"https://www\.jobs\.lu/search.*",
        r"https://www\.jobs\.lu/suche.*",
        r"https://www\.jobs\.lu/entreprises/.*",
        r"https://www\.jobs\.lu/companies/.*",
        r"https://www\.jobs\.lu/unternehmen/.*",
        r"https://www\.jobs\.lu/candidat/.*",
        r"https://www\.jobs\.lu/candidate/.*",
        r"https://www\.jobs\.lu/bewerber/.*",
        r"https://www\.jobs\.lu/salaires/.*",
        r"https://www\.jobs\.lu/salaries/.*",
        r"https://www\.jobs\.lu/gehalter/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.0
    MAX_REQUEST_DELAY: float = 3.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["jobs.lu", "www.jobs.lu"]:
                for pattern in JobsLuxembourgTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Jobs.lu"""
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
            user_agent=JobsLuxembourgTemplate.USER_AGENT,
            accept_language="fr,de,en,lu;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=JobsLuxembourgTemplate.MIN_REQUEST_DELAY,
            max_request_delay=JobsLuxembourgTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "region": "<luxembourg_region>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "sector": "<sector>",
            "function_category": "<function_category>",
            "experience_level": "<experience_level>",
            "skills": "<required_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "cross_border": "<cross_border_workers>",
            "financial_sector": "<financial_services>",
            "eu_institutions": "<eu_institutional_role>",
            "multilingual_requirement": "<multilingual_position>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "application_deadline": "<deadline>",
            "job_reference": "<jobs_lu_reference>",
            "country": "Luxembourg"
        }
