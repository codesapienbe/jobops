import json
import logging
from typing import Protocol

from bs4 import BeautifulSoup
from markdownify import markdownify
import requests
from jobops.models import JobData
from jobops.clients import BaseLLMBackend

class JobScraper(Protocol):
    def scrape_job_description(self, url: str, company: str = None, title: str = None, location: str = None) -> JobData: ...

class WebJobScraper:
    def __init__(self, llm_backend: BaseLLMBackend):
        self.llm_backend = llm_backend
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def scrape_job_description(self, url: str, company: str = None, title: str = None, location: str = None) -> JobData:
        self._logger.info(f"Scraping job description from: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.extract()
            
            # If all fields are provided, skip LLM extraction and use them directly
            if company and title and location is not None:
                return JobData(
                    url=url,
                    title=title,
                    company=company,
                    location=location,
                    description=self._extract_description(soup),
                    requirements=self._extract_requirements(soup)
                )
            # Otherwise, fallback to LLM extraction as before
            if self.llm_backend:
                return self._extract_with_llm(url, soup, company, title, location)
            else:
                # Use user-provided overrides if present
                title_val = title if title else self._extract_title(soup)
                company_val = company if company else self._extract_company(soup)
                location_val = location if location else None
                return JobData(
                    url=url,
                    title=title_val,
                    company=company_val,
                    location=location_val,
                    description=self._extract_description(soup),
                    requirements=self._extract_requirements(soup)
                )
            
        except Exception as e:
            self._logger.error(f"Error scraping job description: {e}")
            raise Exception(f"Failed to scrape job description: {str(e)}")
    
    def _extract_with_llm(self, url: str, soup: BeautifulSoup, company: str = None, title: str = None, location: str = None) -> JobData:
        self._logger.info("Converting HTML to Markdown for cleaning and extraction")
        
        try:
            md_content = markdownify(str(soup), heading_style="ATX")
        except Exception:
            md_content = soup.get_text(separator='\n', strip=True)
        text_content = md_content
        output_schema = JobData.model_json_schema()
        
        prompt = f"""
You are given a job posting in markdown format. First, remove any content unrelated to the job posting such as cookie notices, navigation menus, external URLs, code blocks, advertisements, similar job listings, and pagination. Then extract the following fields and return ONLY valid JSON matching this exact schema:

- application_url
- job_title
- company_name
- company_location
- job_responsibilities
- job_requirements
- company_offers
- company_profile
- technology_stack
- job_reference_number
- content_language

{json.dumps(output_schema, indent=2)}

Web page content in markdown:
{text_content[:10000]}

Return ONLY the JSON object with no additional text, formatting, or code blocks.
"""
        
        try:
            response = self.llm_backend.generate_response(prompt)
            
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            job_info = json.loads(cleaned_response.strip())
            # Map new field names to JobData model fields for compatibility
            if 'application_url' in job_info:
                job_info['url'] = job_info.pop('application_url')
            if 'job_title' in job_info:
                job_info['title'] = job_info.pop('job_title')
            if 'company_name' in job_info:
                job_info['company'] = job_info.pop('company_name')
            if 'company_location' in job_info:
                job_info['location'] = job_info.pop('company_location')
            if 'job_requirements' in job_info:
                job_info['requirements'] = job_info.pop('job_requirements')
            job_info['url'] = url
            # Use user-provided overrides if present
            job_info['title'] = title if title else job_info.get('title', 'Unknown Position')
            job_info['company'] = company if company else job_info.get('company', 'Unknown Company')
            job_info['location'] = location if location else job_info.get('location', None)
            return JobData(**job_info)
        except Exception as e:
            self._logger.warning(f"LLM extraction failed, using fallback: {e}")
            return self._fallback_extraction(url, soup)
    
    def _fallback_extraction(self, url: str, soup: BeautifulSoup) -> JobData:
        return JobData(
            url=url,
            title=self._extract_title(soup),
            company=self._extract_company(soup),
            description=self._extract_description(soup),
            requirements=self._extract_requirements(soup)
        )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        selectors = [
            'h1', '.job-title', '.position-title',
            '[data-testid="job-title"]', '.jobsearch-JobTitle'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else "Unknown Position"
    
    def _extract_company(self, soup: BeautifulSoup) -> str:
        selectors = [
            '.company-name', '.employer-name',
            '[data-testid="company-name"]', '.jobsearch-InlineCompanyName'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "<company name not found>"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        selectors = [
            '.job-description', '.jobsearch-jobDescriptionText',
            '.jobs-description', '[data-testid="job-description"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator='\n', strip=True)
        
        main_content = soup.find('main') or soup.find('body')
        if main_content:
            return main_content.get_text(separator='\n', strip=True)[:3000]
        
        return "<job description not found>"
    
    def _extract_requirements(self, soup: BeautifulSoup) -> str:
        keywords = ['requirements', 'qualifications', 'skills', 'experience']
        
        for keyword in keywords:
            elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())
            for element in elements:
                parent = element.parent
                if parent:
                    req_text = parent.get_text(separator='\n', strip=True)
                    if len(req_text) > 50:
                        return req_text[:1000]
        
        return "<requirements not found>"
    
class ScraperFactory:
    @staticmethod
    def create(scraper_type: str, llm_backend: BaseLLMBackend) -> JobScraper:
        if scraper_type == "web":
            return WebJobScraper(llm_backend)
        else:
            raise ValueError(f"Invalid scraper type: {scraper_type}")

