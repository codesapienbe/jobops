"""ICTJob.be Job Scraping Template

This template defines the configuration for scraping job listings from ictjob.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class ICTJobBelgiumTemplate:
    """ICTJob.be template configuration"""
    
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.ictjob\.be/job/.*",
        r"https://www\.ictjob\.be/en/job/.*",
        r"https://www\.ictjob\.be/fr/job/.*",
        r"https://www\.ictjob\.be/nl/job/.*"
    ])
    
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["ictjob.be", "www.ictjob.be"])
    
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.ictjob\.be/.*/search.*",
        r"https://www\.ictjob\.be/.*/recherche.*",
        r"https://www\.ictjob\.be/.*/zoeken.*",
        r"https://www\.ictjob\.be/.*/cv/.*",
        r"https://www\.ictjob\.be/.*/profile/.*",
        r"https://www\.ictjob\.be/.*/profil/.*",
        r"https://www\.ictjob\.be/.*/companies/.*",
        r"https://www\.ictjob\.be/.*/entreprises/.*",
        r"https://www\.ictjob\.be/.*/bedrijven/.*",
        r"https://www\.ictjob\.be/.*/login.*",
        r"https://www\.ictjob\.be/.*/register.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 2.5
    MAX_REQUEST_DELAY: float = 4.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["ictjob.be", "www.ictjob.be"]:
                for pattern in ICTJobBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for ICTJob.be"""
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
            user_agent=ICTJobBelgiumTemplate.USER_AGENT,
            accept_language="en,nl,fr;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=ICTJobBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=ICTJobBelgiumTemplate.MAX_REQUEST_DELAY
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
            "salary_range": "<salary_range>",
            "it_role": "<it_specialization>",
            "technology_stack": "<required_technologies>",
            "programming_languages": "<programming_languages>",
            "frameworks": "<frameworks_tools>",
            "experience_level": "<experience_level>",
            "seniority": "<junior_medior_senior>",
            "skills": "<technical_skills>",
            "soft_skills": "<soft_skills>",
            "certifications": "<it_certifications>",
            "languages": "<required_languages>",
            "education": "<education_level>",
            "remote_work": "<remote_hybrid_onsite>",
            "project_type": "<project_description>",
            "team_size": "<team_context>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "ictjob_reference": "<ictjob_job_id>",
            "specialization": "ICT/IT"
        }
