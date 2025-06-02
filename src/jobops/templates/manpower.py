"""Manpower Belgium Job Scraping Template

This template defines the configuration for scraping job listings from manpower.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class ManpowerBelgiumTemplate:
    """Manpower Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.manpower\.be/nl/jobs/.*",
        r"https://www\.manpower\.be/fr/jobs/.*",
        r"https://www\.manpower\.be/en/jobs/.*",
        r"https://www\.manpower\.be/jobs/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["manpower.be", "www.manpower.be"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.manpower\.be/.*/job-search/.*",
        r"https://www\.manpower\.be/.*/recherche-emploi/.*",
        r"https://www\.manpower\.be/.*/candidates/.*",
        r"https://www\.manpower\.be/.*/candidats/.*",
        r"https://www\.manpower\.be/.*/employers/.*",
        r"https://www\.manpower\.be/.*/employeurs/.*",
        r"https://www\.manpower\.be/.*/talent-solutions/.*",
        r"https://www\.manpower\.be/.*/solutions-talent/.*",
        r"https://www\.manpower\.be/.*/about/.*",
        r"https://www\.manpower\.be/.*/contact/.*"
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
            if parsed.netloc in ["manpower.be", "www.manpower.be"]:
                for pattern in ManpowerBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Manpower Belgium"""
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
            user_agent=ManpowerBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=ManpowerBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=ManpowerBelgiumTemplate.MAX_REQUEST_DELAY
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
            "assignment_type": "<temporary_permanent>",
            "salary_indication": "<salary_indication>",
            "sector": "<industry_sector>",
            "function_area": "<function_area>",
            "experience_level": "<experience_level>",
            "skills": "<required_skills>",
            "certifications": "<required_certifications>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "working_schedule": "<working_schedule>",
            "assignment_duration": "<assignment_duration>",
            "benefits": "<benefits_package>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "recruiter_contact": "<recruiter_contact>",
            "office_location": "<manpower_office>",
            "posted_date": "<posted_date>",
            "job_reference": "<manpower_reference>",
            "client_company": "<client_company_type>"
        }
