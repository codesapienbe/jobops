"""McKinsey & Company Belgium Job Scraping Template

This template defines the configuration for scraping job listings from mckinsey.com careers
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from crawl4ai import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

@dataclass
class McKinseyBelgiumTemplate:
    """McKinsey Belgium template configuration"""
    
    # Target URL patterns to match
    TARGET_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.mckinsey\.com/careers/search-jobs/jobs/.*",
        r"https://careers\.mckinsey\.com/.*"
    ])
    
    # Allowed domains
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: [
        "mckinsey.com", "www.mckinsey.com",
        "careers.mckinsey.com"
    ])
    
    # Excluded URL patterns
    EXCLUDED_PATTERNS: List[str] = field(default_factory=lambda: [
        r"https://www\.mckinsey\.com/industries/.*",
        r"https://www\.mckinsey\.com/business-functions/.*",
        r"https://www\.mckinsey\.com/insights/.*",
        r"https://www\.mckinsey\.com/about-us/.*",
        r"https://www\.mckinsey\.com/careers/search-jobs.*\?.*"
    ])
    
    # Custom User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Request timing (in seconds) - Prestigious firm, be respectful
    MIN_REQUEST_DELAY: float = 4.5
    MAX_REQUEST_DELAY: float = 7.0
    
    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if a URL matches this template"""
        try:
            parsed = urlparse(url)
            if any(domain in parsed.netloc for domain in ["mckinsey.com"]):
                for pattern in McKinseyBelgiumTemplate.TARGET_PATTERNS:
                    import re
                    if re.match(pattern, url):
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def get_crawler_config() -> CrawlerRunConfig:
        """Get the crawler configuration for McKinsey Belgium"""
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
            user_agent=McKinseyBelgiumTemplate.USER_AGENT,
            accept_language="en,nl,fr;q=0.8"
        )
        
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=40000,
            min_request_delay=McKinseyBelgiumTemplate.MIN_REQUEST_DELAY,
            max_request_delay=McKinseyBelgiumTemplate.MAX_REQUEST_DELAY
        )
    
    @staticmethod
    def extract_job_info(markdown_content: str) -> dict:
        """Extract job information from markdown content"""
        return {
            "title": "<job_title>",
            "company": "McKinsey & Company",
            "location": "<location>",
            "country": "Belgium",
            "office": "<brussels_antwerp>",
            "job_type": "<job_type>",
            "contract_type": "<contract_type>",
            "salary_range": "<salary_range>",
            "practice": "<strategy_operations_organization_marketing_digital>",
            "industry_focus": "<industry_expertise>",
            "functional_expertise": "<function_specialization>",
            "career_level": "<business_analyst_associate_engagement_manager_principal_partner>",
            "experience_level": "<experience_years>",
            "education": "<mba_advanced_degree_requirements>",
            "academic_background": "<academic_disciplines>",
            "consulting_experience": "<prior_consulting_experience>",
            "analytical_skills": "<quantitative_analytical_capabilities>",
            "leadership_experience": "<leadership_background>",
            "languages": "<required_languages>",
            "client_sectors": "<client_industry_focus>",
            "problem_solving": "<case_interview_skills>",
            "international_mobility": "<global_staffing_willingness>",
            "entrepreneurial_experience": "<startup_business_building>",
            "digital_capabilities": "<digital_analytics_tech_skills>",
            "description": markdown_content,
            "application_link": "<application_link>",
            "posted_date": "<posted_date>",
            "mckinsey_job_id": "<mckinsey_reference>",
            "recruiting_season": "<recruiting_cycle>",
            "company_type": "Strategy Consulting"
        }
