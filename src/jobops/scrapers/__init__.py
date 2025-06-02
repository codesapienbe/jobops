
import asyncio
import json
import logging
from typing import Optional, Protocol

from bs4 import BeautifulSoup
import requests
from jobops.models import JobData
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, PruningContentFilter, DefaultMarkdownGenerator
from jobops.clients import BaseLLMBackend

class JobScraper(Protocol):
    def scrape_job_description(self, url: str, company: str = None, title: str = None, location: str = None) -> JobData: ...

class Crawl4AIJobScraper:
    def __init__(self, llm_backend: BaseLLMBackend, base_url: str = "https://api.crawl4ai.com"):
        # TODO: check if crawl4ai is available using simple ping
        def ping_crawl4ai():
            try:
                response = requests.get(f"{base_url}/health")
                return response.status_code == 200
            except Exception as e:
                return False

        if not ping_crawl4ai():
            raise ImportError("Crawl4AI package not available")
        self.llm_backend = llm_backend
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def scrape_job_description(self, url: str, company: str = None, title: str = None, location: str = None) -> JobData:
        self._logger.info(f"Scraping job description from: {url}")
        try:
            asyncio.run(self._crawl_url(url))
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                markdown_content = loop.run_until_complete(self._crawl_url(url))
            finally:
                loop.close()

            # If all fields are provided, skip LLM extraction and use them directly
            if company and title and location is not None:
                return JobData(
                    url=url,
                    title=title,
                    company=company,
                    location=location,
                    description=markdown_content[:3000],
                    requirements="",
                    company_profile_url=None,
                    company_profile=None
                )
            # Otherwise, fallback to LLM extraction as before
            system_prompt = (
                "You are an expert job posting parser. Extract the following information from the job posting markdown below and return ONLY a valid JSON object (no markdown, no code blocks, no extra text):\n"
                "{\n  'title': '...',\n  'company': '...',\n  'location': '...',\n  'company_profile_url': '...',  // If not present, suggest a likely URL such as '/about' or '/about-us', or null if unknown\n  'company_profile': '...'       // If a company profile/description is present in the markdown or at the profile URL, include it here, otherwise null\n}\n"
                "Instructions:\n"
                "- Carefully search the markdown for job title, company name, and location.\n"
                "- If the company profile or description is present, extract it. If not, suggest a likely company profile URL (e.g., '/about', '/about-us') based on the company website or job URL.\n"
                "- If you cannot find a field, use null.\n"
                "- Return ONLY the JSON object, with no extra text, markdown, or code blocks."
            )
            prompt = f"""
            Extract the following information from the job posting markdown below and return ONLY a valid JSON object (no markdown, no code blocks, no extra text):
            {{
              "title": "...",
              "company": "...",
              "location": "...",
              "company_profile_url": "...",  // If not present, suggest a likely URL such as '/about' or '/about-us', or null if unknown
              "company_profile": "..."       // If a company profile/description is present in the markdown or at the profile URL, include it here, otherwise null
            }}

            Markdown:
            {markdown_content[:10000]}
            """
            import json
            try:
                response = self.llm_backend.generate_response(prompt, system_prompt)
                cleaned_response = response.strip()
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                job_info = json.loads(cleaned_response.strip())
                # Use user-provided overrides if present
                title_val = title if title else job_info.get('title', '').strip() or "Unknown Position"
                company_val = company if company else job_info.get('company', '').strip() or "Unknown Company"
                location_val = location if location else job_info.get('location', '').strip() or None
                company_profile_url = job_info.get('company_profile_url', None)
                company_profile = job_info.get('company_profile', None)
            except Exception as e:
                self._logger.warning(f"LLM job field extraction failed, using fallback: {e}")
                lines = markdown_content.split('\n')
                title_val = title if title else next((line.strip('# ').strip() for line in lines if line.startswith('#')), "Unknown Position")
                company_val = company if company else "Unknown Company"
                location_val = location if location else None
                company_profile_url = None
                company_profile = None

            return JobData(
                url=url,
                title=title_val,
                company=company_val,
                location=location_val,
                description=markdown_content[:3000],
                requirements="",
                company_profile_url=company_profile_url,
                company_profile=company_profile
            )
        except Exception as e:
            self._logger.error(f"Error scraping job description: {e}")
            raise Exception(f"Failed to scrape job description: {str(e)}")
    
    async def _crawl_url(self, url: str) -> str:
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
            verbose=False
        )
        
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            if result and result.success:
                return result.markdown.fit_markdown or result.markdown.raw_markdown
            else:
                raise Exception(f"Failed to crawl URL: {result.error_message if result else 'Unknown error'}")
    
    def _extract_job_data_from_markdown(self, url: str, markdown_content: str) -> JobData:
        output_schema = JobData.model_json_schema()
        
        prompt = f"""
        Extract job information from the following job posting markdown and return ONLY valid JSON that matches this exact schema:

        {json.dumps(output_schema, indent=2)}

        Job posting content:
        {markdown_content[:4000]}

        Return only the JSON object with no additional text, formatting, or code blocks.
        """
        
        try:
            response = self.llm_backend.generate_response(prompt)
            
            cleaned_response = response.strip()
            if cleaned_response.startswith('```markdown'):
                cleaned_response = cleaned_response[11:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            job_info = json.loads(cleaned_response.strip())
            job_info['url'] = url
            
            return JobData(**job_info)
        except Exception as e:
            self._logger.warning(f"LLM extraction failed, using fallback: {e}")
            return self._fallback_extraction(url, markdown_content)
    
    def _fallback_extraction(self, url: str, markdown_content: str) -> JobData:
        lines = markdown_content.split('\n')
        title = next((line.strip('# ') for line in lines if line.startswith('#')), "Unknown Position")
        
        return JobData(
            url=url,
            title=title,
            company="Unknown Company",
            description=markdown_content[:1500],
            requirements=""
        )

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
        text_content = soup.get_text(separator='\n', strip=True)
        output_schema = JobData.model_json_schema()
        
        prompt = f"""
        Extract job information from the following web page content and return ONLY valid JSON that matches this exact schema:

        {json.dumps(output_schema, indent=2)}

        Web page content:
        {text_content[:4000]}

        Return only the JSON object with no additional text, formatting, or code blocks.
        """
        
        try:
            response = self.llm_backend.generate_response(prompt)
            
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            job_info = json.loads(cleaned_response.strip())
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
        
        return "Unknown Company"
    
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
        
        return "Could not extract job description"
    
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
        
        return ""
    
class ScraperFactory:
    @staticmethod
    def create(scraper_type: str, llm_backend: BaseLLMBackend) -> JobScraper:
        if scraper_type == "crawl4ai":
            return Crawl4AIJobScraper(llm_backend)
        elif scraper_type == "web":
            return WebJobScraper(llm_backend)
        else:
            raise ValueError(f"Invalid scraper type: {scraper_type}")

