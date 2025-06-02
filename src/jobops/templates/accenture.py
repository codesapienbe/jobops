"""Accenture Belgium Careers Job Scraping Template

This template defines the configuration for scraping job listings from accenture.com Belgium careers
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class AccentureBelgiumTemplate:
    """Accenture Belgium template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.accenture\.com/.*/careers/jobdetails.*",
        r"https://www\.accenture\.com/.*/careers/job-details.*",
        r"https://jobs\.accenture\.com/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: [
        "accenture.com", "www.accenture.com",
        "jobs.accenture.com"
    ])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.accenture\.com/.*/careers/job-search.*",
        r"https://www\.accenture\.com/.*/careers/search.*",
        r"https://www\.accenture\.com/.*/services/.*",
        r"https://www\.accenture\.com/.*/insights/.*",
        r"https://www\.accenture\.com/.*/about/.*",
        r"https://www\.accenture\.com/.*/news/.*",
        r"https://www\.accenture\.com/.*/industries/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds) - Large corporate site
    MIN_REQUEST_DELAY: float = 3.5
    MAX_REQUEST_DELAY: float = 5.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if any(domain in parsed.netloc for domain in ["accenture.com"]):
                for pattern in AccentureBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Accenture Belgium"""
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
            user_agent=AccentureBelgiumTemplate.USER_AGENT,
            accept_language="en,nl,fr;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=35000,
            min_request_delay=AccentureBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=AccentureBelgiumTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "Accenture",
            "location": "<location>",
            "country": "<country>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "business_unit": "<accenture_division>",
            "service_line": "<strategy_consulting_technology_operations>",
            "industry_focus": "<industry_specialization>",
            "career_level": "<analyst_consultant_manager_senior_manager>",
            "experience_level": "<experience_years>",
            "technical_skills": "<required_technologies>",
            "consulting_skills": "<consulting_competencies>",
            "methodology": "<agile_lean_design_thinking>",
            "client_facing": "<client_interaction_level>",
            "travel_requirement": "<travel_percentage>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "certifications": "<professional_certifications>",
            "clearance_required": "<security_clearance>",
            "growth_opportunities": "<career_progression>",
            "training_programs": "<accenture_training>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "accenture_job_id": "<accenture_reference>",
            "requisition_id": "<req_id>",
            "company_type": "Global Consultancy"
        }
