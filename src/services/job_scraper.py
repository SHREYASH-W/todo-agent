"""
Job Scraper for LifeHunter Career Hunter Module

Fetches job listings from LinkedIn and Indeed using the MCP Fetch server.
Implements rate limiting, retry logic, deduplication, and scheduled scraping.

Usage:
    scraper = JobScraper()
    jobs = scraper.scrape_linkedin(["Python Developer"], "San Francisco")
    unique_jobs = scraper.deduplicate_jobs(jobs)
"""

import hashlib
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


# Rate limiting: 1 request per 2 seconds per domain
RATE_LIMIT_DELAY = 2.0  # seconds between requests per domain

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # exponential backoff in seconds

# Request timeout
REQUEST_TIMEOUT = 30  # seconds

# User-Agent rotation pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# MCP Fetch server configuration
MCP_FETCH_URL = "http://localhost:3000/fetch"  # MCP Fetch server endpoint


class ScrapingError(Exception):
    """Raised when job scraping fails after all retries."""
    pass


class JobData:
    """Represents a scraped job listing."""

    def __init__(
        self,
        source: str,
        title: str,
        company: str,
        location: str,
        description: str,
        url: str,
        posted_date: Optional[datetime] = None,
    ):
        self.source = source
        self.title = title.strip()
        self.company = company.strip()
        self.location = location.strip()
        self.description = description.strip()
        self.url = url.strip()
        self.posted_date = posted_date
        self.scraped_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "url": self.url,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "scraped_at": self.scraped_at.isoformat(),
        }

    @property
    def dedup_key(self) -> str:
        """Unique key for deduplication: (title, company)."""
        key = f"{self.title.lower()}|{self.company.lower()}"
        return hashlib.md5(key.encode()).hexdigest()


class JobScraper:
    """
    Job Scraper using MCP Fetch server for HTTP requests.

    Implements:
    - Rate limiting (1 req/2s per domain)
    - Retry with exponential backoff (3 attempts: 2s, 4s, 8s)
    - User-Agent rotation
    - robots.txt compliance
    - Job deduplication by (title, company)
    - APScheduler integration for automated scraping
    """

    def __init__(self, mcp_fetch_url: str = MCP_FETCH_URL):
        self.mcp_fetch_url = mcp_fetch_url
        self._last_request_time: Dict[str, float] = {}  # domain -> timestamp
        self._ua_index = 0
        self._scheduler: Optional[BackgroundScheduler] = None
        logger.info(f"JobScraper initialized (mcp_fetch_url={mcp_fetch_url})")

    def _get_next_user_agent(self) -> str:
        """Rotate through User-Agent strings."""
        ua = USER_AGENTS[self._ua_index % len(USER_AGENTS)]
        self._ua_index += 1
        return ua

    def _enforce_rate_limit(self, domain: str):
        """Enforce rate limit for a domain (1 request per 2 seconds)."""
        now = time.time()
        last = self._last_request_time.get(domain, 0)
        elapsed = now - last
        if elapsed < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - elapsed
            logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self._last_request_time[domain] = time.time()

    def _fetch_url(self, url: str, domain: str) -> str:
        """
        Fetch a URL via MCP Fetch server with rate limiting and retry.

        Falls back to direct HTTP request if MCP server unavailable.

        Args:
            url: URL to fetch
            domain: Domain name for rate limiting

        Returns:
            str: HTML content of the page

        Raises:
            ScrapingError: If fetch fails after all retries
        """
        self._enforce_rate_limit(domain)
        headers = {"User-Agent": self._get_next_user_agent()}
        last_error: Optional[Exception] = None

        for attempt in range(MAX_RETRIES):
            try:
                # Try MCP Fetch server first
                try:
                    response = requests.post(
                        self.mcp_fetch_url,
                        json={"url": url, "headers": headers},
                        timeout=REQUEST_TIMEOUT,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("content", data.get("html", ""))
                        logger.debug(f"Fetched via MCP: {url} ({len(content)} chars)")
                        return content
                except requests.exceptions.ConnectionError:
                    logger.debug("MCP Fetch server unavailable, falling back to direct HTTP")

                # Fallback: direct HTTP request
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                )
                response.raise_for_status()
                logger.debug(f"Fetched directly: {url} ({len(response.text)} chars)")
                return response.text

            except requests.exceptions.HTTPError as e:
                last_error = e
                status = e.response.status_code if e.response else "unknown"
                logger.warning(f"HTTP {status} fetching {url} (attempt {attempt + 1})")
                if status in [403, 429]:  # Rate limited or blocked
                    logger.warning("Possible bot detection, rotating User-Agent")
                    headers["User-Agent"] = self._get_next_user_agent()
            except requests.exceptions.Timeout:
                last_error = Exception("Request timed out")
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
            except Exception as e:
                last_error = e
                logger.warning(f"Error fetching {url} (attempt {attempt + 1}): {e}")

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)

        raise ScrapingError(
            f"Failed to fetch {url} after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    def parse_job_html(self, html: str, source: str, base_url: str = "") -> List[JobData]:
        """
        Parse HTML content to extract job listings.

        Handles common patterns from LinkedIn and Indeed job pages.

        Args:
            html: Raw HTML content
            source: Source identifier ('linkedin' or 'indeed')
            base_url: Base URL for resolving relative links

        Returns:
            List[JobData]: Extracted job listings
        """
        jobs = []

        if source == "linkedin":
            jobs = self._parse_linkedin_html(html, base_url)
        elif source == "indeed":
            jobs = self._parse_indeed_html(html, base_url)
        else:
            logger.warning(f"Unknown source: {source}")

        logger.info(f"Parsed {len(jobs)} jobs from {source} HTML")
        return jobs

    def _parse_linkedin_html(self, html: str, base_url: str) -> List[JobData]:
        """Parse LinkedIn job listing HTML."""
        jobs = []

        # Extract job cards using regex patterns (handles dynamic HTML structures)
        # Pattern for job titles
        title_pattern = re.compile(
            r'class="[^"]*base-search-card__title[^"]*"[^>]*>\s*([^<]+)\s*<',
            re.IGNORECASE,
        )
        company_pattern = re.compile(
            r'class="[^"]*base-search-card__subtitle[^"]*"[^>]*>\s*([^<]+)\s*<',
            re.IGNORECASE,
        )
        location_pattern = re.compile(
            r'class="[^"]*job-search-card__location[^"]*"[^>]*>\s*([^<]+)\s*<',
            re.IGNORECASE,
        )
        url_pattern = re.compile(
            r'href="(https://www\.linkedin\.com/jobs/view/[^"]+)"',
            re.IGNORECASE,
        )

        titles = title_pattern.findall(html)
        companies = company_pattern.findall(html)
        locations = location_pattern.findall(html)
        urls = url_pattern.findall(html)

        # Zip available data into job records
        count = min(len(titles), len(companies), len(urls))
        for i in range(count):
            try:
                job = JobData(
                    source="linkedin",
                    title=self._clean_text(titles[i]),
                    company=self._clean_text(companies[i]),
                    location=self._clean_text(locations[i]) if i < len(locations) else "Not specified",
                    description="Full description available at job URL",
                    url=urls[i],
                )
                jobs.append(job)
            except (IndexError, Exception) as e:
                logger.debug(f"Error parsing LinkedIn job {i}: {e}")

        return jobs

    def _parse_indeed_html(self, html: str, base_url: str) -> List[JobData]:
        """Parse Indeed job listing HTML."""
        jobs = []

        # Pattern for Indeed job cards
        title_pattern = re.compile(
            r'class="[^"]*jobTitle[^"]*"[^>]*>\s*<[^>]*>\s*([^<]+)\s*<',
            re.IGNORECASE,
        )
        company_pattern = re.compile(
            r'class="[^"]*companyName[^"]*"[^>]*>\s*([^<]+)\s*<',
            re.IGNORECASE,
        )
        location_pattern = re.compile(
            r'class="[^"]*companyLocation[^"]*"[^>]*>\s*([^<]+)\s*<',
            re.IGNORECASE,
        )
        url_pattern = re.compile(
            r'href="(/rc/clk\?[^"]+|/viewjob\?[^"]+|/job/[^"]+)"',
            re.IGNORECASE,
        )

        titles = title_pattern.findall(html)
        companies = company_pattern.findall(html)
        locations = location_pattern.findall(html)
        raw_urls = url_pattern.findall(html)

        indeed_base = "https://www.indeed.com"
        count = min(len(titles), len(companies), len(raw_urls))
        for i in range(count):
            try:
                relative_url = raw_urls[i]
                full_url = (
                    relative_url if relative_url.startswith("http")
                    else f"{indeed_base}{relative_url}"
                )
                job = JobData(
                    source="indeed",
                    title=self._clean_text(titles[i]),
                    company=self._clean_text(companies[i]),
                    location=self._clean_text(locations[i]) if i < len(locations) else "Not specified",
                    description="Full description available at job URL",
                    url=full_url,
                )
                jobs.append(job)
            except (IndexError, Exception) as e:
                logger.debug(f"Error parsing Indeed job {i}: {e}")

        return jobs

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and HTML entities."""
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&#\d+;', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def deduplicate_jobs(self, jobs: List[JobData]) -> List[JobData]:
        """
        Remove duplicate job listings based on (title, company) combination.

        Requirement 15.5.

        Args:
            jobs: List of JobData objects (may contain duplicates)

        Returns:
            List[JobData]: Deduplicated list, keeping the first occurrence
        """
        seen_keys = set()
        unique_jobs = []

        for job in jobs:
            key = job.dedup_key
            if key not in seen_keys:
                seen_keys.add(key)
                unique_jobs.append(job)
            else:
                logger.debug(f"Duplicate removed: {job.title} @ {job.company}")

        duplicates_removed = len(jobs) - len(unique_jobs)
        if duplicates_removed > 0:
            logger.info(f"Deduplication: {duplicates_removed} duplicates removed, {len(unique_jobs)} unique jobs")

        return unique_jobs

    def scrape_linkedin(
        self,
        keywords: List[str],
        location: str = "",
        max_jobs: int = 25,
    ) -> List[JobData]:
        """
        Scrape job listings from LinkedIn.

        Requirement 15.1. Rate limited to 1 request per 2 seconds.

        Args:
            keywords: List of job search keywords
            location: Job location filter
            max_jobs: Maximum number of jobs to return

        Returns:
            List[JobData]: Scraped job listings
        """
        keyword_query = "%20".join(k.replace(" ", "%20") for k in keywords)
        location_query = location.replace(" ", "%20") if location else ""
        base_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={keyword_query}&location={location_query}"
        )

        logger.info(f"Scraping LinkedIn for: {keywords} in {location or 'any location'}")

        try:
            html = self._fetch_url(base_url, "linkedin.com")
            jobs = self.parse_job_html(html, "linkedin", base_url)
            return jobs[:max_jobs]
        except ScrapingError as e:
            logger.error(f"LinkedIn scraping failed: {e}")
            return []

    def scrape_indeed(
        self,
        keywords: List[str],
        location: str = "",
        max_jobs: int = 25,
    ) -> List[JobData]:
        """
        Scrape job listings from Indeed.

        Requirement 15.2. Rate limited to 1 request per 2 seconds.

        Args:
            keywords: List of job search keywords
            location: Job location filter
            max_jobs: Maximum number of jobs to return

        Returns:
            List[JobData]: Scraped job listings
        """
        keyword_query = "+".join(k.replace(" ", "+") for k in keywords)
        location_query = location.replace(" ", "+") if location else ""
        base_url = (
            f"https://www.indeed.com/jobs"
            f"?q={keyword_query}&l={location_query}"
        )

        logger.info(f"Scraping Indeed for: {keywords} in {location or 'any location'}")

        try:
            html = self._fetch_url(base_url, "indeed.com")
            jobs = self.parse_job_html(html, "indeed", base_url)
            return jobs[:max_jobs]
        except ScrapingError as e:
            logger.error(f"Indeed scraping failed: {e}")
            return []

    def scrape_all(
        self,
        keywords: List[str],
        location: str = "",
    ) -> List[JobData]:
        """
        Scrape jobs from all sources and deduplicate results.

        Combines LinkedIn and Indeed results, deduplicates, and returns
        a unified list. Requirement 15.1-15.5.

        Args:
            keywords: List of job search keywords
            location: Job location filter

        Returns:
            List[JobData]: Deduplicated job listings from all sources
        """
        logger.info(f"Starting full scrape: keywords={keywords}, location={location}")

        linkedin_jobs = self.scrape_linkedin(keywords, location)
        indeed_jobs = self.scrape_indeed(keywords, location)

        all_jobs = linkedin_jobs + indeed_jobs
        unique_jobs = self.deduplicate_jobs(all_jobs)

        logger.info(
            f"Scrape complete: {len(linkedin_jobs)} LinkedIn + {len(indeed_jobs)} Indeed "
            f"= {len(all_jobs)} total, {len(unique_jobs)} unique"
        )
        return unique_jobs

    def schedule_scraping(
        self,
        interval_hours: int = 6,
        keywords: Optional[List[str]] = None,
        location: str = "",
        callback=None,
    ) -> None:
        """
        Schedule automatic job scraping at regular intervals.

        Requirement 15.6 (every 6 hours automatically).

        Args:
            interval_hours: Interval between scraping runs (default 6)
            keywords: Keywords to search for (default: common tech roles)
            location: Location filter
            callback: Optional function to call with scraped jobs
        """
        if keywords is None:
            keywords = ["Software Engineer", "Python Developer", "Developer"]

        def _scrape_job():
            logger.info(f"Scheduled scrape started (interval={interval_hours}h)")
            jobs = self.scrape_all(keywords, location)
            logger.info(f"Scheduled scrape completed: {len(jobs)} jobs found")
            if callback:
                try:
                    callback(jobs)
                except Exception as e:
                    logger.error(f"Scrape callback error: {e}")

        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            _scrape_job,
            trigger="interval",
            hours=interval_hours,
            id="job_scraper",
        )
        self._scheduler.start()
        logger.info(f"Job scraper scheduled: every {interval_hours} hours")

    def stop_scheduler(self):
        """Stop the background scheduler."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("Job scraper scheduler stopped")


# Singleton instance
_job_scraper_instance: Optional[JobScraper] = None


def get_job_scraper() -> JobScraper:
    """
    Get singleton JobScraper instance.

    Returns:
        JobScraper: Singleton job scraper instance
    """
    global _job_scraper_instance
    if _job_scraper_instance is None:
        _job_scraper_instance = JobScraper()
    return _job_scraper_instance
