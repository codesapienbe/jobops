"""Monster Belgium Job Scraping Template

This template defines the configuration for scraping job listings from monster.be
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class MonsterBelgiumTemplate:
    """Monster Belgium template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.monster\.be/job-openings/.*",
        r"https://www\.monster\.be/emploi/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: ["monster.be", "www.monster.be"])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.monster\.be/jobs/search/.*",
        r"https://www\.monster\.be/profile/.*",
        r"https://www\.monster\.be/company/.*",
        r"https://www\.monster\.be/career-advice/.*",
        r"https://www\.monster\.be/salary/.*",
        r"https://www\.monster\.be/login.*",
        r"https://www\.monster\.be/register.*",
        r"https://www\.monster\.be/my-monster/.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    
    # Request timing (in seconds)
    MIN_REQUEST_DELAY: float = 3.0
    MAX_REQUEST_DELAY: float = 5.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if parsed.netloc in ["monster.be", "www.monster.be"]:
                for pattern in MonsterBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for Monster Belgium"""
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
            user_agent=MonsterBelgiumTemplate.USER_AGENT,
            accept_language="nl-BE,fr-BE,en;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=35000,
            min_request_delay=MonsterBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=MonsterBelgiumTemplate.MAX_REQUEST_DELAY
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
            "experience_level": "<experience_level>",
            "industry": "<industry>",
            "skills": "<required_skills>",
            "benefits": "<employee_benefits>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "job_id": "<monster_job_id>"
        }
