"""Dornan Engineering Belgium Job Scraping Template

This template defines the configuration for scraping job listings from dornan.ie careers pages
"""

from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class DornanEngineeringTemplate:
    """Dornan Engineering template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = [
        r"https://www\.dornan\.ie/careers/.*",
        r"https://www\.dornan\.ie/jobs/.*",
        r"https://careers\.dornan\.ie/.*"
    ]
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = [
        "dornan.ie", "www.dornan.ie", 
        "careers.dornan.ie"
    ]
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = [
        r"https://www\.dornan\.ie/projects/.*",
        r"https://www\.dornan\.ie/services/.*",
        r"https://www\.dornan\.ie/about/.*",
        r"https://www\.dornan\.ie/news/.*",
        r"https://www\.dornan\.ie/contact/.*"
    ]
    
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
            if any(domain in parsed.netloc for domain in ["dornan.ie"]):
                for pattern in DornanEngineeringTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Dornan Engineering"""
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
            user_agent=DornanEngineeringTemplate.USER_AGENT,
            accept_language="en,nl,fr;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=DornanEngineeringTemplate.MIN_REQUEST_DELAY,
            max_request_delay=DornanEngineeringTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "Dornan Engineering",
            "location": "<location>",
            "country": "<ireland_belgium_uk_netherlands>",
            "office_location": "<antwerp_dublin_cork_london_amsterdam>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "engineering_discipline": "<mechanical_electrical_hvac_instrumentation>",
            "project_type": "<data_centers_life_sciences_industrial>",
            "sector": "<pharmaceutical_tech_manufacturing>",
            "experience_level": "<experience_years>",
            "qualifications": "<engineering_qualifications>",
            "certifications": "<professional_certifications>",
            "technical_skills": "<engineering_skills>",
            "software_proficiency": "<cad_project_management_tools>",
            "languages": "<required_languages>",
            "project_scale": "<major_projects_infrastructure>",
            "travel_requirement": "<international_projects>",
            "safety_requirements": "<health_safety_compliance>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "dornan_reference": "<dornan_job_id>",
            "company_type": "M&E Engineering Contractor"
        }
