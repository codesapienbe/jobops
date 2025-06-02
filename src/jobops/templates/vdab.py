"""VDAB Job Scraping Template

This template defines the configuration for scraping job listings from VDAB.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class VDABTemplate:
    """VDAB template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.vdab\.be/vindeenjob/vacatures/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["vdab.be", "www.vdab.be"])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.vdab\.be/vindeenjob/.*utm_.*",
        r"https://www\.vdab\.be/vindeenjob/jobsuggesties",
        r"https://www\.vdab\.be/vindeenjob/bewaarde-vacatures",
        r"https://www\.vdab\.be/vindeenjob/bedrijven/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (compatible; Crawl4AI/1.0; +https://crawl4ai.example.com)"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 3.0
    MAX_REQUEST_DELAY: float = 5.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc.endswith("vdab.be"):
                for pattern in VDABTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for VDAB"""
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
            user_agent=VDABTemplate.USER_AGENT
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000,
            min_request_delay=VDABTemplate.MIN_REQUEST_DELAY,
            max_request_delay=VDABTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        # This is a placeholder for actual extraction logic
        # In a real implementation, you would parse the markdown to extract:
        # - Job Title
        # - Location
        # - Company Name
        # - Job Type
        # - Working Hours
        # - Required Skills & Technologies
        # - Job Description
        # - Application Link
        return {
            "title": "<job_title>",
            "company": "<company_name>",
            "location": "<location>",
            "job_type": "<job_type>",
            "working_hours": "<working_hours>",
            "skills": "<required_skills>",
            "description": markdown_content,
            "application_link": "<application_link>"
        } 