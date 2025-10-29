
import os
import sys
import json
import re
import time
import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple, Iterable, Dict, Any, Set
from urllib.parse import urljoin, urlparse, quote_plus

import base64
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText


sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive",
]

RECIPIENT_EMAILS = [
    "briankim1027@gmail.com",
    "briankim@sk.com",
]
_env_recipients = os.getenv("RECIPIENT_EMAILS")
if _env_recipients:
    parsed_emails = None
    try:
        loaded = json.loads(_env_recipients)
        if isinstance(loaded, list):
            parsed_emails = [str(item).strip() for item in loaded if str(item).strip()]
    except json.JSONDecodeError:
        parsed_emails = None
    if parsed_emails is None:
        temp_emails = []
        for raw in _env_recipients.split(","):
            cleaned = raw.strip().strip('"').strip("'")
            if cleaned:
                temp_emails.append(cleaned)
        parsed_emails = temp_emails
    if parsed_emails:
        RECIPIENT_EMAILS = parsed_emails
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/117.0.0.0 Safari/537.36"
)

DEFAULT_VALUE = "정보 없음"
HEADERS = [
    "행사명",
    "행사 Homepage",
    "날짜",
    "도시/국가",
    "핵심 주제",
    "Key note",
    "참가 비용",
    "참석 우선순위",
]

POSITIVE_KEYWORDS = [
    "successful",
    "great",
    "insightful",
    "valuable",
    "must-attend",
    "well received",
    "sold out",
    "positive",
    "excellent",
    "impactful",
    "award",
    "recognized",
    "innovation",
]

NEGATIVE_KEYWORDS = [
    "canceled",
    "cancelled",
    "postponed",
    "negative",
    "bad",
    "poor",
    "issue",
    "problem",
    "delay",
    "complaint",
    "criticized",
]

MUST_ATTEND_KEYWORDS = [
    "hyperscale",
    "ai",
    "sustainability",
    "ml",
    "gpt",
    "edge",
    "liquid cooling",
    "gartner",
    "aws",
    "google",
    "microsoft",
    "azure",
    "meta",
    "open compute",
    "summit",
    "world",
    "global",
]

NICE_ATTEND_KEYWORDS = [
    "cloud",
    "data center",
    "colocation",
    "network",
    "infrastructure",
    "telecom",
    "sme",
    "expo",
    "forum",
    "connect",
    "conference",
    "symposium",
]

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept-Language": "ko,en-US;q=0.8,en;q=0.6",
    }
)

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

@dataclass
class EventRecord:
    name: str
    homepage: str
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    location: str = ""
    main_topic: str = ""
    keynote: str = ""
    participation_fee: str = ""
    sentiment_summary: str = DEFAULT_VALUE
    sentiment_score: float = 0.0
    attendance_priority: str = "Neutral"

    def normalized_key(self) -> Tuple[str, Optional[datetime.date], str]:
        return (
            self.name.lower().strip(),
            self.start_date or self.end_date,
            self.location.lower().strip(),
        )

    def date_label(self) -> str:
        if self.start_date and self.end_date:
            if self.start_date == self.end_date:
                return self.start_date.strftime("%Y-%m-%d")
            return (
                f"{self.start_date.strftime('%Y-%m-%d')} ~ "
                f"{self.end_date.strftime('%Y-%m-%d')}"
            )
        if self.start_date:
            return self.start_date.strftime("%Y-%m-%d")
        if self.end_date:
            return self.end_date.strftime("%Y-%m-%d")
        return DEFAULT_VALUE

    def as_row(self) -> List[str]:
        return [
            ensure_value(self.name),
            ensure_value(self.homepage),
            ensure_value(self.date_label()),
            ensure_value(self.location),
            ensure_value(self.main_topic),
            ensure_value(self.keynote),
            ensure_value(self.participation_fee),
            ensure_value(self.attendance_priority),
        ]


def ensure_value(value: Optional[str]) -> str:
    if not value:
        return DEFAULT_VALUE
    return value.strip()


def normalize_whitespace(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def month_to_number(month_name: str) -> Optional[int]:
    if not month_name:
        return None
    return MONTH_MAP.get(month_name.lower())


def safe_date(year: int, month: int, day: int) -> Optional[datetime.date]:
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def try_parse_with_formats(text: str) -> Optional[datetime.date]:
    formats = [
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%Y/%m/%d",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%b %d %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%m/%d/%Y",
        "%m/%d/%y",
    ]
    cleaned = re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", text, flags=re.IGNORECASE)
    for fmt in formats:
        try:
            return datetime.datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def parse_single_date(text: str, fallback_year: Optional[int] = None) -> Optional[datetime.date]:
    if not text:
        return None
    cleaned = normalize_whitespace(text)
    parsed = try_parse_with_formats(cleaned)
    if parsed:
        return parsed
    cleaned = re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", cleaned, flags=re.IGNORECASE)
    tokens = cleaned.replace(",", " ").split()
    if not tokens:
        return None
    year = None
    month = None
    day = None
    for token in tokens:
        lower = token.lower()
        if lower in MONTH_MAP and month is None:
            month = MONTH_MAP[lower]
            continue
        if token.isdigit():
            num = int(token)
            if num > 1900:
                year = num
            elif day is None:
                day = num
            elif year is None and 1 <= num <= 31:
                day = num
    if year is None:
        if fallback_year:
            year = fallback_year
        else:
            today = datetime.date.today()
            year = today.year
            if month and month < today.month:
                year += 1
    if month is None or day is None:
        return None
    return safe_date(year, month, day)


def parse_date_range(text: str) -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
    if not text:
        return (None, None)
    value = normalize_whitespace(text)
    if not value:
        return (None, None)

    iso_matches = re.findall(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}", value)
    if iso_matches:
        start = parse_single_date(iso_matches[0])
        end = parse_single_date(iso_matches[-1])
        if not end:
            end = start
        return start, end

    separators = [" ~ ", " – ", " — ", " to "]
    for sep in separators:
        if sep in value:
            first, last = value.split(sep, 1)
            start = parse_single_date(first)
            end = parse_single_date(last, fallback_year=start.year if start else None)
            if start and end and end < start and end.year == start.year:
                end = safe_date(end.year + 1, end.month, end.day)
            if start and not end:
                end = start
            return start, end

    match = re.search(
        r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
        value,
        re.IGNORECASE,
    )
    if match:
        day1, day2, month_name, year = match.groups()
        month = month_to_number(month_name)
        year = int(year)
        start = safe_date(year, month, int(day1))
        end = safe_date(year, month, int(day2))
        return start, end or start

    match = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s*[-–]\s*(\d{1,2}),?\s*(\d{4})",
        value,
        re.IGNORECASE,
    )
    if match:
        month_name, day1, day2, year = match.groups()
        month = month_to_number(month_name)
        year = int(year)
        start = safe_date(year, month, int(day1))
        end = safe_date(year, month, int(day2))
        return start, end or start

    start = parse_single_date(value)
    return start, start


def parse_fee_text(text: str) -> str:
    if not text:
        return DEFAULT_VALUE
    lower = text.lower()
    if "free" in lower or "무료" in lower:
        return "무료"
    currency_match = re.search(r"(\$|€|£|₩)\s*\d[\d,./]*", text)
    if currency_match:
        return currency_match.group(0)
    return normalize_whitespace(text)

def fetch_soup(url: str) -> Tuple[Optional[BeautifulSoup], Optional[str]]:
    try:
        response = SESSION.get(url, timeout=15)
        response.raise_for_status()
        if response.encoding is None:
            response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        return soup, response.url
    except requests.RequestException as exc:
        print(f"    [경고] {url} 요청 중 오류 발생: {exc}")
        return None, None


def parse_json_ld_events(soup: BeautifulSoup, base_url: str) -> List[EventRecord]:
    records: List[EventRecord] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            raw = script.string or ""
            if not raw.strip():
                continue
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = [item for item in data if isinstance(item, dict)]
        else:
            continue
        for item in items:
            item_type = item.get("@type")
            if isinstance(item_type, list):
                item_type = item_type[0]
            if item_type not in {"Event", "ExhibitionEvent", "BusinessEvent"}:
                continue
            name = item.get("name")
            if not name:
                continue
            location = ""
            loc_data = item.get("location")
            if isinstance(loc_data, dict):
                address = loc_data.get("address")
                if isinstance(address, dict):
                    locality = address.get("addressLocality") or ""
                    country = address.get("addressCountry") or ""
                    location = normalize_whitespace(
                        ", ".join(filter(None, [locality, country]))
                    )
                else:
                    location = normalize_whitespace(str(loc_data.get("name", "")))
            start_date = parse_single_date(item.get("startDate", ""))
            end_date = parse_single_date(
                item.get("endDate", ""), fallback_year=start_date.year if start_date else None
            )
            url_value = item.get("url") or base_url
            if url_value and not url_value.startswith("http"):
                url_value = urljoin(base_url, url_value)
            theme = item.get("about") or item.get("description") or ""
            keynote = ""
            performers = item.get("performer") or item.get("performers")
            if isinstance(performers, list) and performers:
                keynote = normalize_whitespace(str(performers[0].get("name", "")))
            elif isinstance(performers, dict):
                keynote = normalize_whitespace(str(performers.get("name", "")))
            participation_fee = DEFAULT_VALUE
            offers = item.get("offers")
            if isinstance(offers, dict):
                price = offers.get("price")
                currency = offers.get("priceCurrency", "")
                participation_fee = parse_fee_text(f"{currency} {price}".strip())
            elif isinstance(offers, list):
                for offer in offers:
                    if isinstance(offer, dict):
                        price = offer.get("price")
                        currency = offer.get("priceCurrency", "")
                        participation_fee = parse_fee_text(f"{currency} {price}".strip())
                        break
            records.append(
                EventRecord(
                    name=normalize_whitespace(name),
                    homepage=url_value or base_url,
                    start_date=start_date,
                    end_date=end_date,
                    location=location,
                    main_topic=normalize_whitespace(theme),
                    keynote=normalize_whitespace(keynote),
                    participation_fee=participation_fee,
                )
            )
    return records


def parse_eventseye(soup: BeautifulSoup, base_url: str) -> List[EventRecord]:
    events: List[EventRecord] = []
    rows = soup.select("table.fairs_list tr[id^='f_list_']")
    if not rows:
        rows = soup.select("div.event-card, div.event-item, div.listing-row")
    for row in rows:
        link_tag = row.select_one("td.name a, td.fair a, h3 a")
        if not link_tag:
            continue
        name = normalize_whitespace(link_tag.get_text(strip=True))
        if not name:
            continue
        homepage = link_tag.get("href") or base_url
        if homepage and not homepage.startswith("http"):
            homepage = urljoin(base_url, homepage)
        date_cell = row.select_one("td.date, .date")
        date_text = normalize_whitespace(date_cell.get_text(" ", strip=True)) if date_cell else ""
        start_date, end_date = parse_date_range(date_text)
        country_cell = row.select_one("td.country, .country")
        country = normalize_whitespace(country_cell.get_text(strip=True)) if country_cell else ""
        city_cell = row.select_one("td.city, .city")
        city = normalize_whitespace(city_cell.get_text(strip=True)) if city_cell else ""
        location = normalize_whitespace(
            ", ".join(filter(None, [city, country]))
        )
        topic_cell = row.select_one("td.sector, td.description, .sector, .description")
        main_topic = normalize_whitespace(topic_cell.get_text(" ", strip=True)) if topic_cell else ""
        keynote = ""
        if "Keynote" in main_topic:
            parts = main_topic.split("Keynote", 1)
            main_topic = normalize_whitespace(parts[0])
            keynote = normalize_whitespace(parts[1])
        fee_cell = row.select_one("td.price, td.fees, .price, .fees")
        participation_fee = parse_fee_text(fee_cell.get_text(" ", strip=True)) if fee_cell else DEFAULT_VALUE
        events.append(
            EventRecord(
                name=name,
                homepage=homepage,
                start_date=start_date,
                end_date=end_date,
                location=location,
                main_topic=main_topic,
                keynote=keynote,
                participation_fee=participation_fee,
            )
        )
    return events


def parse_hostdime(soup: BeautifulSoup, base_url: str) -> List[EventRecord]:
    events: List[EventRecord] = []
    headings = soup.select("h2, h3")
    for heading in headings:
        name = normalize_whitespace(heading.get_text(strip=True))
        if not name or len(name) < 4:
            continue
        event_homepage = base_url
        date_text = ""
        location = ""
        theme = ""
        keynote = ""
        fee = DEFAULT_VALUE
        current = heading.find_next_sibling()
        while current and current.name not in {"h2", "h3"}:
            text = normalize_whitespace(current.get_text(" ", strip=True))
            if text:
                lower = text.lower()
                if ("when" in lower or "date" in lower) and ":" in text and not date_text:
                    date_text = text.split(":", 1)[1]
                if ("where" in lower or "location" in lower or "venue" in lower) and ":" in text:
                    location = normalize_whitespace(text.split(":", 1)[1])
                if ("theme" in lower or "focus" in lower or "topic" in lower) and ":" in text:
                    theme = normalize_whitespace(text.split(":", 1)[1])
                if "keynote" in lower and ":" in text:
                    keynote = normalize_whitespace(text.split(":", 1)[1])
                if ("cost" in lower or "fee" in lower or "price" in lower) and ":" in text:
                    fee = parse_fee_text(text.split(":", 1)[1])
            current = current.find_next_sibling()
        start_date, end_date = parse_date_range(date_text)
        main_topic = theme or "HostDime 추천 이벤트"
        events.append(
            EventRecord(
                name=name,
                homepage=event_homepage,
                start_date=start_date,
                end_date=end_date,
                location=location,
                main_topic=main_topic,
                keynote=keynote,
                participation_fee=fee,
            )
        )
    return events

def parse_generic_cards(soup: BeautifulSoup, base_url: str) -> List[EventRecord]:
    events: List[EventRecord] = []
    event_blocks = soup.select("[class*='event'], article, li")
    for block in event_blocks:
        if len(events) > 40:
            break
        title_tag = block.find(["h1", "h2", "h3"])
        if not title_tag:
            continue
        name = normalize_whitespace(title_tag.get_text(strip=True))
        if not name or len(name) < 4:
            continue
        link = title_tag.find("a")
        homepage = base_url
        if link and link.get("href"):
            href = link.get("href")
            if href.startswith("http"):
                homepage = href
            elif not href.startswith("#"):
                homepage = urljoin(base_url, href)
        date_text = ""
        location = ""
        main_topic = ""
        keynote = ""
        fee = DEFAULT_VALUE
        for child in block.find_all(["time", "p", "span", "div"], limit=6):
            text = normalize_whitespace(child.get_text(" ", strip=True))
            if not text:
                continue
            lower = text.lower()
            if not date_text and re.search(r"\d{4}", text):
                date_text = text
            if any(keyword in lower for keyword in ["location", "city", "country", "venue"]):
                if ":" in text:
                    location = normalize_whitespace(text.split(":", 1)[1])
                else:
                    location = text
            if any(keyword in lower for keyword in ["theme", "topic", "focus", "agenda", "track"]):
                if ":" in text:
                    main_topic = normalize_whitespace(text.split(":", 1)[1])
                else:
                    main_topic = text
            if "keynote" in lower and ":" in text:
                keynote = normalize_whitespace(text.split(":", 1)[1])
            if any(keyword in lower for keyword in ["fee", "cost", "price", "입장료", "등록비", "ticket"]):
                if ":" in text:
                    fee = parse_fee_text(text.split(":", 1)[1])
                else:
                    fee = parse_fee_text(text)
        start_date, end_date = parse_date_range(date_text)
        events.append(
            EventRecord(
                name=name,
                homepage=homepage,
                start_date=start_date,
                end_date=end_date,
                location=location,
                main_topic=main_topic,
                keynote=keynote,
                participation_fee=fee,
            )
        )
    return events


def extract_events_from_url(url: str) -> List[EventRecord]:
    soup, final_url = fetch_soup(url)
    if not soup or not final_url:
        return []
    domain = urlparse(final_url).netloc.lower()
    records: List[EventRecord] = []
    records.extend(parse_json_ld_events(soup, final_url))
    if "eventseye.com" in domain:
        records.extend(parse_eventseye(soup, final_url))
    elif "hostdime.com" in domain:
        records.extend(parse_hostdime(soup, final_url))
    else:
        records.extend(parse_generic_cards(soup, final_url))
    return records


def search_google_links(query: str, max_links: int = 6) -> List[str]:
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    soup, _ = fetch_soup(url)
    if not soup:
        return []
    links: List[str] = []
    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if not href:
            continue
        if href.startswith("/url?q=") and "webcache" not in href and "accounts.google.com" not in href:
            actual = href.split("/url?q=")[1].split("&sa=")[0]
            if actual.startswith("http") and actual not in links:
                links.append(actual)
        if len(links) >= max_links:
            break
    time.sleep(0.6)
    return links


def deduplicate_events(events: Iterable[EventRecord]) -> List[EventRecord]:
    unique: Dict[Tuple[str, Optional[datetime.date], str], EventRecord] = {}
    for event in events:
        key = event.normalized_key()
        if key in unique:
            existing = unique[key]
            if len(event.main_topic) > len(existing.main_topic):
                existing.main_topic = event.main_topic
            if len(event.keynote) > len(existing.keynote):
                existing.keynote = event.keynote
            if existing.participation_fee == DEFAULT_VALUE and event.participation_fee != DEFAULT_VALUE:
                existing.participation_fee = event.participation_fee
        else:
            unique[key] = event
    return list(unique.values())


def collect_events(search_queries: List[str]) -> List[EventRecord]:
    collected: List[EventRecord] = []
    visited: Set[str] = set()
    for query in search_queries:
        print(f"검색 실행: {query}")
        if query.startswith("http"):
            collected.extend(extract_events_from_url(query))
            continue
        links = search_google_links(query)
        for link in links:
            if link in visited:
                continue
            visited.add(link)
            collected.extend(extract_events_from_url(link))
    return deduplicate_events(collected)

def filter_upcoming_events(
    events: Iterable[EventRecord], months: int, reference_date: datetime.date
) -> List[EventRecord]:
    horizon = reference_date + datetime.timedelta(days=months * 31)
    filtered: List[EventRecord] = []
    for event in events:
        date_value = event.start_date or event.end_date
        if not date_value:
            continue
        if date_value < reference_date:
            continue
        if date_value > horizon:
            continue
        filtered.append(event)
    return filtered


def filter_events_for_month(events: Iterable[EventRecord], reference_date: datetime.date) -> List[EventRecord]:
    month_events: List[EventRecord] = []
    for event in events:
        date_value = event.start_date or event.end_date
        if not date_value:
            continue
        if date_value.year == reference_date.year and date_value.month == reference_date.month:
            month_events.append(event)
    return month_events


def analyze_sentiment(event: EventRecord) -> Tuple[str, float]:
    query = f"{event.name} review data center conference feedback"
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    soup, _ = fetch_soup(url)
    if not soup:
        return ("리뷰 데이터를 수집하지 못했습니다.", 0.0)
    snippets: List[str] = []
    for snippet in soup.select("div.BNeawe.s3v9rd.AP7Wnd, div.kCrYT span"):
        text = normalize_whitespace(snippet.get_text(" ", strip=True))
        if text and text not in snippets:
            snippets.append(text)
        if len(snippets) >= 5:
            break
    combined = " ".join(snippets) if snippets else "관련 리뷰가 충분하지 않습니다."
    lower = combined.lower()
    score = 0.0
    for word in POSITIVE_KEYWORDS:
        if word in lower:
            score += 1.0
    for word in NEGATIVE_KEYWORDS:
        if word in lower:
            score -= 1.0
    time.sleep(0.6)
    return combined[:500], score


def update_sentiment(events: Iterable[EventRecord]) -> None:
    for event in events:
        summary, score = analyze_sentiment(event)
        event.sentiment_summary = summary
        event.sentiment_score = score


def determine_attendance_priority(event: EventRecord, today: datetime.date) -> str:
    if event.start_date and event.start_date < today:
        return "Just Information"
    if event.sentiment_score <= -1:
        return "Just Information"

    text_bundle = " ".join(
        [
            event.name.lower(),
            event.main_topic.lower(),
            event.keynote.lower(),
            event.sentiment_summary.lower(),
        ]
    )

    must_score = sum(1 for keyword in MUST_ATTEND_KEYWORDS if keyword in text_bundle)
    nice_score = sum(1 for keyword in NICE_ATTEND_KEYWORDS if keyword in text_bundle)

    if "keynote" in event.sentiment_summary.lower() or len(event.keynote) > 20:
        must_score += 1
    if "annual" in event.name.lower() or "summit" in event.name.lower():
        nice_score += 1

    if event.sentiment_score >= 2:
        must_score += 1
    elif event.sentiment_score > 0:
        nice_score += 1

    if must_score >= 2:
        return "Must attend"
    if nice_score >= 1 or must_score == 1:
        return "Nice to attend"
    return "Neutral"


def assign_priorities(events: Iterable[EventRecord], reference_date: datetime.date) -> None:
    for event in events:
        event.attendance_priority = determine_attendance_priority(event, reference_date)


def sort_events(events: List[EventRecord]) -> None:
    priority_order = {"Must attend": 0, "Nice to attend": 1, "Neutral": 2, "Just Information": 3}

    def sort_key(event: EventRecord) -> Tuple[int, datetime.date]:
        priority_rank = priority_order.get(event.attendance_priority, 3)
        date_value = event.start_date or event.end_date or (datetime.date.max)
        return (priority_rank, date_value)

    events.sort(key=sort_key)

def get_credentials() -> Credentials:
    creds: Optional[Credentials] = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())
    return creds


def ensure_drive_folder(drive_service, folder_name: str) -> Optional[str]:
    try:
        results = (
            drive_service.files()
            .list(
                q=f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id, name)",
                pageSize=1,
            )
            .execute()
        )
        files = results.get("files", [])
        if files:
            return files[0]["id"]
        metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
        folder = drive_service.files().create(body=metadata, fields="id").execute()
        return folder.get("id")
    except Exception as exc:
        print(f"[경고] Google Drive 폴더 확인 실패: {exc}")
        return None


def move_file_to_folder(drive_service, file_id: str, folder_id: Optional[str]) -> None:
    if not folder_id:
        return
    try:
        file = drive_service.files().get(fileId=file_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents", []))
        drive_service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()
    except Exception as exc:
        print(f"[경고] Google Drive 폴더 이동 실패: {exc}")


def create_spreadsheet(creds: Credentials, title: str, rows: List[List[str]]) -> Optional[str]:
    try:
        sheets_service = build("sheets", "v4", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)

        spreadsheet = {"properties": {"title": title}}
        sheet = (
            sheets_service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId,spreadsheetUrl")
            .execute()
        )
        spreadsheet_id = sheet.get("spreadsheetId")
        spreadsheet_url = sheet.get("spreadsheetUrl")
        print(f"Google 스프레드시트를 생성했습니다. ID: {spreadsheet_id}")

        body = {"values": rows}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="A1",
            valueInputOption="RAW",
            body=body,
        ).execute()
        print("시트에 데이터를 기록했습니다.")

        folder_id = ensure_drive_folder(drive_service, "Data Center Event Reports")
        move_file_to_folder(drive_service, spreadsheet_id, folder_id)

        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body={"type": "anyone", "role": "reader"},
            fields="id",
        ).execute()
        print("스프레드시트를 '링크 소유자 전체 공개'로 공유했습니다.")

        return spreadsheet_url
    except Exception as exc:
        print(f"[오류] 스프레드시트 생성 중 문제가 발생했습니다: {exc}")
        return None


def send_email(creds: Credentials, recipients: List[str], subject: str, body: str) -> None:
    cleaned_recipients: List[str] = []
    for email in recipients or []:
        cleaned = email.strip().strip('"').strip("'").strip()
        if cleaned and '@' in cleaned and cleaned not in cleaned_recipients:
            cleaned_recipients.append(cleaned)
    if not cleaned_recipients:
        print('[경고] 유효한 수신자 목록이 없어 이메일 발송을 건너뜁니다.')
        return
    try:
        service = build("gmail", "v1", credentials=creds)
        message = MIMEText(body)
        message["to"] = ", ".join(cleaned_recipients)
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        print("이메일을 성공적으로 발송했습니다.")
    except Exception as exc:
        print(f"[경고] 이메일 발송에 실패했습니다: {exc}")

def main() -> None:
    print("워크플로우를 실행합니다...")
    current_datetime = datetime.datetime.now()
    today = current_datetime.date()
    override_date = os.getenv('REFERENCE_DATE')
    if override_date:
        try:
            today = datetime.datetime.strptime(override_date, '%Y-%m-%d').date()
            print(f'[정보] 참조 날짜를 {today.isoformat()}로 강제 적용합니다.')
        except ValueError:
            print(f"[경고] 잘못된 REFERENCE_DATE 형식입니다: {override_date}. YYYY-MM-DD 형식으로 입력하세요.")

    sheet_title = f"Data Center Events Tracker - {today.strftime('%Y-%m')}"

    try:
        creds = get_credentials()
    except ValueError as exc:
        print(f"[오류] 자격 증명 준비 실패: {exc}")
        return

    search_queries = [
        "Data Center Conference 2025",
        "Data Center Exhibition 2025",
        "Cloud Infrastructure Events 2025",
        "AI Data Center Summit 2025",
        "Edge Computing Expo 2025",
        "Hyperscale data center conference",
        "November 2025 data center conference",
        "December 2025 data center conference",
        "data center events November 2025",
        "data center events December 2025",
        "2025 데이터센터 컨퍼런스 11월",
        "2025 데이터센터 컨퍼런스 12월",
        "AI 데이터센터 전시회 2025",
        "클라우드 인프라 박람회 2025",
        "데이터센터 투자 포럼 2025",
        "https://www.eventseye.com",
        "https://www.hostdime.com/blog/2025-data-center-conferences/",
        "https://datacenternation.com",
        "https://www.techexevent.com",
        "https://datacenterkorea.kr/eng/",
        "https://kdcc.or.kr/kdcc/bbsNew_list.do?bbs_data=aWR4PTQ2NyZzdGFydFBhZ2U9NDUmbGlzdE5vPTE1OSZ0YWJsZT1jc19iYnNfZGF0YV9uZXcmY29kZT1zdWIwNGEmc2VhcmNoX2l0ZW09JnNlYXJjaF9vcmRlcm0mdXJsPXN1YjA0YSZiYnNfbWFsbmFtZT0%3D%7C%7C",
        "https://clouddatacenter.events",
    ]

    print("[1단계] 이벤트 데이터 수집 중...")
    all_events = collect_events(search_queries)
    print(f"  총 {len(all_events)}건의 원시 이벤트를 수집했습니다.")

    upcoming_events = filter_upcoming_events(all_events, months=12, reference_date=today)
    print(f"  12개월 이내 이벤트 {len(upcoming_events)}건을 남겼습니다.")

    if not upcoming_events:
        print("  유효한 이벤트가 없어도 스프레드시트는 생성합니다.")

    print("[2단계] 산업 반응/감성 분석을 진행합니다...")
    update_sentiment(upcoming_events)

    print("[3단계] 우선순위 산정 및 정렬을 수행합니다...")
    assign_priorities(upcoming_events, reference_date=today)
    sort_events(upcoming_events)

    print("[4단계] 현재 월 이벤트만 필터링합니다...")
    month_events = filter_events_for_month(upcoming_events, reference_date=today)
    if not month_events:
        print("  이번 달에 해당하는 이벤트가 없습니다. 헤더만 작성합니다.")

    rows: List[List[str]] = [HEADERS]
    for event in month_events:
        rows.append(event.as_row())
    if len(rows) == 1:
        rows.append(
            [
                "이번 달에 공개된 글로벌 데이터센터 이벤트가 없습니다.",
                DEFAULT_VALUE,
                DEFAULT_VALUE,
                DEFAULT_VALUE,
                DEFAULT_VALUE,
                DEFAULT_VALUE,
                DEFAULT_VALUE,
                "Just Information",
            ]
        )

    spreadsheet_url = create_spreadsheet(creds, sheet_title, rows)
    if not spreadsheet_url:
        print("[오류] 스프레드시트 URL을 확보하지 못했습니다. 이메일은 발송하지 않습니다.")
        return

    print("[5단계] 이메일 알림을 전송합니다...")
    email_subject = f"[Google Opal] Monthly Data Center Events Report - {today.strftime('%Y-%m')}"
    body_lines = [
        "안녕하세요,",
        "",
        f"{today.strftime('%Y-%m')} 월의 데이터센터 이벤트 목록입니다.",
        "아래 스프레드시트에서 상세 정보를 확인해 주세요:",
        "",
        spreadsheet_url,
        "",
        "감사합니다.",
    ]
    if not month_events:
        body_lines.insert(
            4,
            "현재 월에 해당하는 이벤트가 없어 안내용 행만 포함되어 있습니다.",
        )
    send_email(creds, RECIPIENT_EMAILS, email_subject, "\n".join(body_lines))

    print("\n워크플로우가 정상 종료되었습니다.")


if __name__ == "__main__":
    main()





