import re
from collections import Counter
from typing import Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


COMMON_STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "are", "our", "that", "this",
    "from", "have", "has", "was", "were", "will", "can", "all", "not",
    "but", "use", "using", "into", "their", "they", "them", "more", "about",
    "what", "when", "where", "which", "who", "how", "why", "get", "new",
    "now", "out", "one", "two", "see", "learn", "contact", "home",
    "privacy", "terms", "login", "signup", "sign", "copyright", "rights",
    "reserved", "cookie", "cookies"
}


def normalize_url(url: str) -> str:
    """
    Ensure the website URL has a valid HTTP/HTTPS scheme.

    Users often enter example.com instead of https://example.com.
    This function makes scraping more forgiving.
    """
    parsed = urlparse(url)

    if not parsed.scheme:
        return f"https://{url}"

    return url


def clean_text(text: str) -> str:
    """
    Clean whitespace and remove excessive spacing from extracted website text.
    """
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_meta_description(soup: BeautifulSoup) -> str:
    """
    Extract the page meta description if available.
    """
    description_tag = soup.find("meta", attrs={"name": "description"})

    if description_tag and description_tag.get("content"):
        return clean_text(description_tag["content"])

    og_description = soup.find("meta", attrs={"property": "og:description"})

    if og_description and og_description.get("content"):
        return clean_text(og_description["content"])

    return ""


def extract_headings(soup: BeautifulSoup) -> List[str]:
    """
    Extract visible H1, H2, and H3 headings from the page.

    Headings usually reveal the company's positioning and key services.
    """
    headings = []

    for tag in soup.find_all(["h1", "h2", "h3"]):
        heading_text = clean_text(tag.get_text(" ", strip=True))

        if heading_text and len(heading_text) > 2:
            headings.append(heading_text)

    return headings[:12]


def extract_page_text(soup: BeautifulSoup) -> str:
    """
    Extract readable text from paragraphs, list items, and selected sections.
    """
    for unwanted in soup(["script", "style", "noscript", "svg", "footer", "nav"]):
        unwanted.decompose()

    text_parts = []

    for tag in soup.find_all(["p", "li", "section", "article"]):
        text = clean_text(tag.get_text(" ", strip=True))

        if len(text) >= 40:
            text_parts.append(text)

    combined_text = " ".join(text_parts)
    return combined_text[:5000]


def detect_keywords(text: str, max_keywords: int = 12) -> List[str]:
    """
    Detect simple business-relevant keywords from extracted text.

    This is intentionally lightweight and dependency-free for the prototype.
    """
    words = re.findall(r"\b[a-zA-Z][a-zA-Z]{3,}\b", text.lower())

    useful_words = [
        word for word in words
        if word not in COMMON_STOPWORDS and len(word) >= 4
    ]

    counter = Counter(useful_words)

    return [word for word, _ in counter.most_common(max_keywords)]


def build_fallback_enrichment(
    company_name: str,
    company_website: str,
    industry: str | None = None,
    message: str | None = None,
    reason: str | None = None,
) -> Dict[str, str]:
    """
    Build fallback enrichment when scraping fails.

    This keeps the workflow moving instead of crashing.
    """
    fallback_summary = (
        f"{company_name} submitted a lead inquiry"
        f"{f' in the {industry} industry' if industry else ''}. "
        "The website could not be fully scraped, so the report should rely on "
        "the submitted company details and general business automation opportunities."
    )

    if message:
        fallback_summary += f" The prospect mentioned: {message}"

    return {
        "status": "fallback",
        "website_url": company_website,
        "title": company_name,
        "meta_description": "",
        "headings": "",
        "summary_text": fallback_summary,
        "keywords": industry or "lead automation, business operations, AI workflow",
        "error": reason or "Website enrichment failed.",
    }


def enrich_company(
    company_name: str,
    company_website: str,
    industry: str | None = None,
    message: str | None = None,
) -> Dict[str, str]:
    """
    Research a submitted company website and return structured context.

    The returned dictionary is later used by the AI/report generation layer.
    """

    normalized_url = normalize_url(company_website)

    try:
        response = requests.get(
            normalized_url,
            headers=HEADERS,
            timeout=12,
            allow_redirects=True,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title = ""
        if soup.title and soup.title.string:
            title = clean_text(soup.title.string)

        meta_description = extract_meta_description(soup)
        headings = extract_headings(soup)
        page_text = extract_page_text(soup)

        combined_context = " ".join(
            [
                title,
                meta_description,
                " ".join(headings),
                page_text,
                industry or "",
                message or "",
            ]
        )

        keywords = detect_keywords(combined_context)

        if not page_text and not headings and not meta_description:
            return build_fallback_enrichment(
                company_name=company_name,
                company_website=company_website,
                industry=industry,
                message=message,
                reason="Website loaded but no useful text was found.",
            )

        return {
            "status": "success",
            "website_url": normalized_url,
            "title": title or company_name,
            "meta_description": meta_description,
            "headings": " | ".join(headings),
            "summary_text": page_text[:3000],
            "keywords": ", ".join(keywords),
            "error": "",
        }

    except requests.RequestException as exc:
        return build_fallback_enrichment(
            company_name=company_name,
            company_website=company_website,
            industry=industry,
            message=message,
            reason=str(exc),
        )