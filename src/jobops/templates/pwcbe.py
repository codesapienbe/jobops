"""PwC Belgium Careers Job Scraping Template

This template defines the configuration for scraping job listings from pwc.be careers
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class PwCBelgiumTemplate:
    """PwC Belgium template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.pwc\.be/.*/careers/.*",
        r"https://www\.pwc\.be/.*/jobs/.*",
        r"https://jobs\.pwc\.com/.*belgium.*",
        r"https://careers\.pwc\.com/be/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: [
        "pwc.be", "www.pwc.be",
        "jobs.pwc.com", "careers.pwc.com"
    ])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.pwc\.be/.*/services/.*",
        r"https://www\.pwc\.be/.*/industries/.*",
        r"https://www\.pwc\.be/.*/insights/.*",
        r"https://www\.pwc\.be/.*/about/.*",
        r"https://jobs\.pwc\.com/.*search.*",
        r"https://careers\.pwc\.com/.*search.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 3.5
    MAX_REQUEST_DELAY: float = 5.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if any(domain in parsed.netloc for domain in ["pwc.be", "pwc.com"]):
                for pattern in PwCBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for PwC Belgium"""
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
            user_agent=PwCBelgiumTemplate.USER_AGENT,
            accept_language="en,nl,fr;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=35000,
            min_request_delay=PwCBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=PwCBelgiumTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "PwC",
            "location": "<location>",
            "country": "Belgium",
            "office": "<brussels_antwerp_ghent_liege>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "line_of_service": "<assurance_tax_advisory_consulting>",
            "business_unit": "<pwc_business_area>",
            "industry_group": "<industry_specialization>",
            "service_offering": "<service_line_specialization>",
            "career_level": "<associate_senior_associate_manager_senior_manager_partner>",
            "experience_level": "<experience_years>",
            "education": "<degree_requirements>",
            "certifications": "<professional_qualifications>",
            "technical_skills": "<required_technical_skills>",
            "languages": "<required_languages>",
            "client_service": "<client_interaction_level>",
            "travel_requirement": "<travel_expectations>",
            "security_clearance": "<clearance_requirements>",
            "specializations": "<functional_industry_technical>",
            "leadership_opportunities": "<team_leadership_scope>",
            "digital_skills": "<digital_technology_capabilities>",
            "regulatory_knowledge": "<regulatory_compliance_expertise>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "pwc_job_id": "<pwc_reference>",
            "requisition_number": "<req_id>",
            "company_type": "Big Four Professional Services"
        }
