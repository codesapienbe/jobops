"""Hays Belgium Job Scraping Template

This template defines the configuration for scraping job listings from hays.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class HaysBelgiumTemplate:
    """Hays Belgium template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.hays\.be/job/.*",
        r"https://www\.hays\.be/nl/job/.*",
        r"https://www\.hays\.be/fr/job/.*",
        r"https://www\.hays\.be/en/job/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["hays.be", "www.hays.be"])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.hays\.be/.*/jobs/.*\?.*",
        r"https://www\.hays\.be/.*/job-search/.*",
        r"https://www\.hays\.be/.*/recherche-emploi/.*",
        r"https://www\.hays\.be/.*/my-hays/.*",
        r"https://www\.hays\.be/.*/mon-hays/.*",
        r"https://www\.hays\.be/.*/employers/.*",
        r"https://www\.hays\.be/.*/employeurs/.*",
        r"https://www\.hays\.be/.*/salary-guide/.*",
        r"https://www\.hays\.be/.*/guide-salarial/.*",
        r"https://www\.hays\.be/.*/career-advice/.*",
        r"https://www\.hays\.be/.*/conseils-carriere/.*",
        r"https://www\.hays\.be/.*/about/.*",
        r"https://www\.hays\.be/.*/contact/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 3.0
    MAX_REQUEST_DELAY: float = 5.5
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["hays.be", "www.hays.be"]:
                for pattern in HaysBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Hays Belgium"""
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
            user_agent=HaysBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=HaysBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=HaysBelgiumTemplate.MAX_REQUEST_DELAY
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
            "employment_type": "<permanent_contract_interim>",
            "salary_range": "<salary_range>",
            "specialization": "<specialization_area>",
            "sector": "<industry_sector>",
            "seniority_level": "<seniority_level>",
            "experience_years": "<years_experience>",
            "skills": "<required_skills>",
            "technical_skills": "<technical_competencies>",
            "soft_skills": "<soft_skills>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "certifications": "<professional_certifications>",
            "benefits": "<benefits_package>",
            "company_culture": "<company_culture_info>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "consultant_name": "<hays_consultant>",
            "consultant_specialization": "<consultant_expertise>",
            "posted_date": "<posted_date>",
            "job_reference": "<hays_reference>",
            "office_location": "<hays_office>",
            "urgency_level": "<urgency_indicator>"
        }
