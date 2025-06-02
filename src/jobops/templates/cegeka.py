"""Cegeka Careers Job Scraping Template

This template defines the configuration for scraping job listings from cegeka.com careers pages
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class CegekaCareersTemplate:
    """Cegeka Careers template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.cegeka\.com/.*/jobs/.*",
        r"https://www\.cegeka\.com/.*/careers/.*",
        r"https://www\.cegeka\.com/.*/vacatures/.*",
        r"https://careers\.cegeka\.com/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: [
        "cegeka.com", "www.cegeka.com", 
        "careers.cegeka.com"
    ])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.cegeka\.com/.*/solutions/.*",
        r"https://www\.cegeka\.com/.*/services/.*",
        r"https://www\.cegeka\.com/.*/about/.*",
        r"https://www\.cegeka\.com/.*/news/.*",
        r"https://www\.cegeka\.com/.*/contact/.*",
        r"https://www\.cegeka\.com/.*/products-platforms/.*"
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
            if any(domain in parsed.netloc for domain in ["cegeka.com"]):
                for pattern in CegekaCareersTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Cegeka Careers"""
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
            user_agent=CegekaCareersTemplate.USER_AGENT,
            accept_language="en,nl,fr;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=CegekaCareersTemplate.MIN_REQUEST_DELAY,
            max_request_delay=CegekaCareersTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "Cegeka",
            "location": "<location>",
            "country": "<belgium_netherlands_other>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "business_unit": "<cegeka_division>",
            "service_area": "<infrastructure_software_cloud_data>",
            "technology_focus": "<microsoft_dynamics_devops_security>",
            "experience_level": "<experience_level>",
            "technical_skills": "<required_technologies>",
            "programming_languages": "<programming_languages>",
            "cloud_platforms": "<azure_aws_gcp>",
            "certifications": "<microsoft_certifications>",
            "soft_skills": "<soft_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "remote_work": "<remote_policy>",
            "client_interaction": "<customer_facing_role>",
            "project_scope": "<project_type>",
            "career_level": "<junior_senior_lead_architect>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "cegeka_reference": "<cegeka_job_id>",
            "company_type": "IT Consultancy"
        }
