"""ArXiv search backend for the literature search system."""
from __future__ import annotations
import re
import time
import xml.etree.ElementTree as ET

import requests

ATOM = "{http://www.w3.org/2005/Atom}"


class SearchResult:
    def __init__(self, title, url, abstract, source, published="", authors=""):
        self.title = title
        self.url = url
        self.abstract = abstract
        self.source = source
        self.published = published
        self.authors = authors

    def to_dict(self):
        return dict(title=self.title, url=self.url, abstract=self.abstract,
                    source=self.source, published=self.published, authors=self.authors)


class ArxivBackend:
    name = "arxiv"
    endpoint = "http://export.arxiv.org/api/query"

    def __init__(self, max_results=10, timeout=30, politeness=3.0):
        self.max_results = max_results
        self.timeout = timeout
        self.politeness = politeness
        self._last = 0.0

    def search(self, query: str) -> list[SearchResult]:
        wait = self.politeness - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "relevance",
        }
        response = requests.get(self.endpoint, params=params, timeout=self.timeout,
                                headers={"User-Agent": "literature-search/1.0"})
        response.raise_for_status()
        root = ET.fromstring(response.text)
        results = []
        for entry in root.findall(f"{ATOM}entry"):
            title = (entry.findtext(f"{ATOM}title") or "").strip()
            abstract = (entry.findtext(f"{ATOM}summary") or "").strip()
            url = (entry.findtext(f"{ATOM}id") or "").strip()
            published = (entry.findtext(f"{ATOM}published") or "")[:10]
            authors = ", ".join(
                (a.findtext(f"{ATOM}name") or "").strip()
                for a in entry.findall(f"{ATOM}author"))
            if title and url:
                results.append(SearchResult(
                    title=re.sub(r"\s+", " ", title),
                    url=url,
                    abstract=re.sub(r"\s+", " ", abstract),
                    source="arxiv", published=published, authors=authors))
        return results


def build_backend(config):
    s = config.get("search", {})
    return ArxivBackend(
        max_results=s.get("max_results_per_query", 10),
        timeout=s.get("request_timeout_seconds", 30),
        politeness=s.get("politeness_seconds", 3.0))
