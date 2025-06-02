"""Deloitte Belgium Careers Job Scraping Template

This template defines the configuration for scraping job listings from deloitte.com Belgium careers
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class DeloitteBelgiumTemplate:
    """Deloitte Belgium template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www2\.deloitte\.com/be/.*/careers/.*",
        r"https://careers\.deloitte\.com/be/.*",
        r"https://jobs\.deloitte\.com/.*belgium.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: [
        "deloitte.com", "www2.deloitte.com",
        "careers.deloitte.com", "jobs.deloitte.com"
    ])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www2\.deloitte\.com/be/.*/services/.*",
        r"https://www2\.deloitte\.com/be/.*/insights/.*",
        r"https://www2\.deloitte\.com/be/.*/about/.*",
        r"https://careers\.deloitte\.com/.*search.*",
        r"https://jobs\.deloitte\.com/.*search.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 4.0
    MAX_REQUEST_DELAY: float = 6.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if any(domain in parsed.netloc for domain in ["deloitte.com"]):
                for pattern in DeloitteBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Deloitte Belgium"""
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
            user_agent=DeloitteBelgiumTemplate.USER_AGENT,
            accept_language="en,nl,fr;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=35000,
            min_request_delay=DeloitteBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=DeloitteBelgiumTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "Deloitte",
            "location": "<location>",
            "country": "Belgium",
            "office": "<brussels_antwerp_ghent>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "service_line": "<audit_consulting_financial_advisory_tax_risk>",
            "industry_focus": "<industry_specialization>",
            "practice_area": "<practice_specialization>",
            "career_level": "<analyst_consultant_senior_manager_partner>",
            "experience_level": "<experience_years>",
            "education": "<education_requirements>",
            "certifications": "<professional_certifications>",
            "technical_skills": "<required_skills>",
            "languages": "<required_languages>",
            "client_interaction": "<client_facing_role>",
            "travel_requirement": "<travel_percentage>",
            "security_clearance": "<clearance_required>",
            "specializations": "<functional_technical_industry>",
            "leadership_level": "<team_leadership_responsibility>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "deloitte_job_id": "<deloitte_reference>",
            "requisition_id": "<req_number>",
            "company_type": "Big Four Consulting"
        }
