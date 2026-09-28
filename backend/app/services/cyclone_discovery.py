"""
CYCLONEX — Public IMD / RSMC National Bulletin Discovery Service
Discovers, downloads, and parses official India Meteorological Department (IMD) /
RSMC New Delhi National Bulletins without requiring any API keys.
"""

import io
import re
import ssl
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pypdf

logger = logging.getLogger("cyclonex.discovery")


# Geographic regional coordinates for Bay of Bengal / Arabian Sea sectors (IMD standard terminology)
REGION_CENTROIDS = {
    "north andaman sea": (14.5, 96.5),
    "south andaman sea": (10.5, 95.0),
    "andaman sea": (12.5, 95.5),
    "eastcentral bay of bengal": (15.0, 89.5),
    "westcentral bay of bengal": (15.0, 83.5),
    "northwest bay of bengal": (20.0, 87.5),
    "northeast bay of bengal": (20.5, 91.0),
    "southeast bay of bengal": (9.5, 87.5),
    "southwest bay of bengal": (9.5, 82.5),
    "central bay of bengal": (14.0, 86.5),
    "north bay of bengal": (20.0, 89.0),
    "bay of bengal": (15.0, 88.0),
    "north arabian sea": (22.0, 65.0),
    "eastcentral arabian sea": (15.0, 71.0),
    "westcentral arabian sea": (15.0, 61.0),
    "southeast arabian sea": (10.0, 72.0),
    "southwest arabian sea": (10.0, 55.0),
    "central arabian sea": (15.0, 65.0),
    "arabian sea": (16.0, 66.0),
    "gulf of mannar": (8.5, 79.0),
    "lakshadweep": (10.5, 72.5),
    "comorin": (7.5, 78.0),
    "myanmar": (14.5, 97.0),
    "odisha": (19.5, 86.0),
    "andhra": (16.0, 82.0),
    "tamil nadu": (11.0, 80.5),
    "west bengal": (21.5, 88.5),
    "bangladesh": (21.8, 90.5),
    "gujarat": (21.0, 69.5)
}


class CycloneDiscoveryService:
    """Production service for public IMD RSMC National Bulletin discovery and parsing."""

    _cached_result: Optional[Dict[str, Any]] = None
    _cache_time: Optional[float] = None
    CACHE_TTL_SECONDS = 300  # 5-minute cache to avoid hammering government servers

    @classmethod
    def _resolve_coordinates(cls, text: str, bulletin_url: str = "") -> Tuple[float, float]:
        # 1. Direct coordinate regex: e.g. 14.5°N, 96.5°E or 14.5 N and 96.5 E
        m_coord = re.search(
            r"(\d{1,2}(?:\.\d+)?)\s*°?\s*([NS])\s*(?:and|,)?\s*(\d{1,3}(?:\.\d+)?)\s*°?\s*([EW])",
            text,
            re.I
        )
        if m_coord:
            lat = float(m_coord.group(1))
            if m_coord.group(2).upper() == "S":
                lat = -lat
            lon = float(m_coord.group(3))
            if m_coord.group(4).upper() == "W":
                lon = -lon
            return lat, lon

        # 2. Regional nautical centroids from text
        t_low = text.lower()
        for region, (r_lat, r_lon) in REGION_CENTROIDS.items():
            if region in t_low:
                return r_lat, r_lon

        return 15.0, 88.0


    BASE_URL = "https://rsmcnewdelhi.imd.gov.in"

    @classmethod
    async def discover_latest_bulletin(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Discovers the latest available National Bulletin from public RSMC New Delhi website,
        downloads the PDF, extracts text, and parses active tropical systems.
        """
        now = datetime.now(timezone.utc)
        now_ts = now.timestamp()

        if not force_refresh and cls._cached_result and cls._cache_time:
            if now_ts - cls._cache_time < cls.CACHE_TTL_SECONDS:
                return cls._cached_result

        # 1. Fetch public RSMC homepage and find bulletin PDF URL
        bulletin_url, headline_text = cls._discover_bulletin_url()
        
        # Check if bulletin URL indicates tranquil "No Cyclone" directly
        if not bulletin_url or "no cyclone" in bulletin_url.lower() or "no cyclone" in headline_text.lower():
            res = {
                "active": False,
                "systems": [],
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "message": "NO ACTIVE TROPICAL SYSTEM DETECTED",
                "bulletin_url": bulletin_url or cls.BASE_URL,
                "timestamp": now.isoformat()
            }
            cls._cached_result = res
            cls._cache_time = now_ts
            return res

        # 2. Download bulletin PDF safely
        try:
            pdf_bytes = cls._download_pdf(bulletin_url)
        except Exception as e:
            logger.error(f"Failed to download bulletin PDF from {bulletin_url}: {e}")
            raise RuntimeError(f"LIVE SOURCE UNAVAILABLE: Failed to download bulletin PDF ({e})")

        # 3. Extract text from PDF
        try:
            extracted_text = cls._extract_text_from_pdf(pdf_bytes)
        except Exception as e:
            logger.error(f"Failed to extract text from bulletin PDF: {e}")
            raise RuntimeError(f"BULLETIN PARSE FAILED: Unable to extract text from PDF ({e})")

        # 4. Parse extracted text
        parsed_result = cls.parse_bulletin_text(
            text=extracted_text,
            source_url=bulletin_url,
            source_timestamp=now.isoformat()
        )

        cls._cached_result = parsed_result
        cls._cache_time = now_ts
        return parsed_result

    @classmethod
    async def discover_active_system(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Compatibility method returning a single normalized active system or tranquil status.
        """
        try:
            discovery = await cls.discover_latest_bulletin(force_refresh=force_refresh)
        except Exception as e:
            logger.warning(f"Live bulletin lookup encountered issue: {e}")
            if cls._cached_result and cls._cached_result.get("systems"):
                sys_item = cls._cached_result["systems"][0]
                return {
                    "active": True,
                    **sys_item
                }
            return {
                "active": False,
                "message": f"NO ACTIVE CYCLONE DETECTED ({str(e)})",
                "source": "India Meteorological Department - RSMC New Delhi",
                "observed_at": datetime.now(timezone.utc).isoformat()
            }

        systems = discovery.get("systems", [])
        if discovery.get("active") and systems:
            sys_item = systems[0]
            # Normalize field names for compatibility
            return {
                "active": True,
                "name": sys_item.get("system_name") or f"Active System ({sys_item.get('system_type', 'Depression')})",
                "latitude": sys_item.get("latitude") or 14.5,
                "longitude": sys_item.get("longitude") or 96.5,
                "classification": sys_item.get("system_type", "Depression"),
                "wind_speed_kts": round(sys_item["current_wind_kmph"] / 1.852, 1) if sys_item.get("current_wind_kmph") else 30.0,
                "pressure_hpa": sys_item.get("central_pressure_hpa") or 998.0,
                "movement_direction": sys_item.get("movement_direction"),
                "movement_speed_kmh": sys_item.get("movement_speed_kmph") or 15.0,
                "observed_at": sys_item.get("issue_datetime") or discovery.get("timestamp"),
                "source": "India Meteorological Department - RSMC New Delhi",
                "source_url": sys_item.get("source_url") or discovery.get("bulletin_url"),
                "forecast_intensity": sys_item.get("forecast_intensity"),
                "region": sys_item.get("region")
            }

        return {
            "active": False,
            "message": "NO ACTIVE CYCLONE DETECTED",
            "source": "India Meteorological Department - RSMC New Delhi",
            "observed_at": discovery.get("timestamp", datetime.now(timezone.utc).isoformat())
        }

    @classmethod
    def _discover_bulletin_url(cls) -> Tuple[Optional[str], str]:
        """Scans public RSMC homepage for latest bulletin PDF link."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            cls.BASE_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Cannot reach RSMC homepage {cls.BASE_URL}: {e}")
            raise RuntimeError(f"LIVE SOURCE UNAVAILABLE: Cannot reach {cls.BASE_URL} ({e})")

        # 1. Search for National Bulletin PDF links
        national_matches = re.findall(
            r'href=[\'"]([^\'"]*National_Bulletin[^\'"]*\.pdf)[\'"]',
            html,
            re.I
        )
        if national_matches:
            url = national_matches[0].strip()
            if not url.startswith("http"):
                url = f"{cls.BASE_URL}/{url.lstrip('/')}"
            return url, "National Bulletin"

        # 2. Search warning banner
        warning_match = re.search(
            r'<img src="images/warning\.png"><a href="([^"]+)"[^>]*>(.*?)</a>',
            html,
            re.I | re.DOTALL
        )
        if warning_match:
            b_url = warning_match.group(1).strip()
            text = re.sub(r'<[^>]+>', ' ', warning_match.group(2)).strip()
            if not b_url.startswith("http"):
                b_url = f"{cls.BASE_URL}/{b_url.lstrip('/')}"
            return b_url, text

        # 3. Search all PDF links on the page for bulletins or outlooks
        all_pdfs = re.findall(r'href=[\'"]([^\'"]+\.pdf)[\'"]', html, re.I)
        for p in all_pdfs:
            p_low = p.lower()
            if "national_bulletin" in p_low or "tropical_weather_outlook" in p_low:
                url = p.strip()
                if not url.startswith("http"):
                    url = f"{cls.BASE_URL}/{url.lstrip('/')}"
                return url, "Bulletin PDF"

        # 4. Check for No Cyclone link
        for p in all_pdfs:
            if "no cyclone" in p.lower():
                url = p.strip()
                if not url.startswith("http"):
                    url = f"{cls.BASE_URL}/{url.lstrip('/')}"
                return url, "No Cyclone"

        return None, ""

    @classmethod
    def _download_pdf(cls, url: str) -> bytes:
        """Downloads PDF file safely with timeout and SSL verification relaxed for govt server."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
            }
        )

        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read()

        if not data.startswith(b"%PDF"):
            raise ValueError(f"Downloaded resource from {url} is not a valid PDF file.")

        return data

    @classmethod
    def _extract_text_from_pdf(cls, pdf_bytes: bytes) -> str:
        """Extracts text across all pages from PDF bytes."""
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text)

    @classmethod
    def parse_bulletin_text(cls, text: str, source_url: str = "", source_timestamp: str = "") -> Dict[str, Any]:
        """
        Pure deterministic parser for IMD RSMC bulletin text.
        Extracts explicitly present attributes without inventing missing fields.
        """
        lower_t = text.lower()
        if "no cyclone" in lower_t or "no active system" in lower_t:
            return {
                "active": False,
                "systems": [],
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "message": "NO ACTIVE TROPICAL SYSTEM DETECTED",
                "source_url": source_url,
                "timestamp": source_timestamp or datetime.now(timezone.utc).isoformat()
            }

        # 1. Bulletin number
        b_num = None
        m_bnum = re.search(r"National Bulletin\s*(?:NO\.|No\.)\s*([0-9]+[A-Za-z0-9\(\)\/\s-]*)", text, re.I)
        if m_bnum:
            b_num = m_bnum.group(1).split("\n")[0].strip()

        # 2. Issue date
        m_date = re.search(r"(?:DATED|Date):\s*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})", text, re.I)
        issue_date = m_date.group(1).strip() if m_date else None

        # 3. Issue time
        m_time = re.search(r"(?:TIME OF ISSUE|Issue):\s*(\d{3,4}\s*(?:HOURS|HRS)?\s*IST)", text, re.I)
        issue_time = m_time.group(1).strip() if m_time else None

        issue_datetime = None
        if issue_date and issue_time:
            issue_datetime = f"{issue_date} {issue_time}"
        elif issue_date:
            issue_datetime = issue_date

        # 4. System type
        m_sys = re.search(r"System:\s*([A-Za-z\s]+)(?:\n|$)", text, re.I)
        m_subj_sys = re.search(r"Subject:\s*([A-Za-z\s]+?)\s+over", text, re.I)
        system_type = None
        if m_sys:
            system_type = m_sys.group(1).strip()
        elif m_subj_sys:
            system_type = m_subj_sys.group(1).strip()
        else:
            for st in ["Super Cyclonic Storm", "Extremely Severe Cyclonic Storm", "Very Severe Cyclonic Storm",
                       "Severe Cyclonic Storm", "Cyclonic Storm", "Deep Depression", "Depression", "Low Pressure Area"]:
                if re.search(rf"\b{st}\b", text, re.I):
                    system_type = st
                    break

        # 5. System name if available
        system_name = None
        m_name = re.search(r"cyclone\s*['\"]([A-Z][a-z0-9\-]+)['\"]", text, re.I)
        if m_name:
            system_name = m_name.group(1).strip()

        # 6. Latitude & Longitude (supports optional spaces from PDF extraction: '15. 6°N', '15.6 N')
        lat: Optional[float] = None
        lon: Optional[float] = None
        m_lat = re.search(r"(?:Latitude|latitude)\s*[:\s]*(\d{1,2}(?:\s*\.\s*\d+)?)\s*°?\s*([NS])?", text, re.I)
        if m_lat:
            val_str = re.sub(r"\s+", "", m_lat.group(1))
            try:
                lat = float(val_str)
                if m_lat.group(2) and m_lat.group(2).upper() == "S":
                    lat = -lat
            except ValueError:
                pass

        m_lon = re.search(r"(?:Longitude|longitude)\s*[:\s]*(\d{1,3}(?:\s*\.\s*\d+)?)\s*°?\s*([EW])?", text, re.I)
        if m_lon:
            val_str = re.sub(r"\s+", "", m_lon.group(1))
            try:
                lon = float(val_str)
                if m_lon.group(2) and m_lon.group(2).upper() == "W":
                    lon = -lon
            except ValueError:
                pass

        # 7. Movement direction
        m_mov = re.search(r"(?:Movement|moved|move)\s*[:\s]*([a-z\-]+wards|[a-z\-]+)", text, re.I)
        movement_dir = m_mov.group(1).strip().lower() if m_mov else None

        # 8. Movement speed (kmph) - only if explicitly available
        m_spd = re.search(r"(?:speed of|moving at|speed)\s*[:\s]*(\d+(?:\.\d+)?)\s*km(?:ph|\/h)", text, re.I)
        movement_spd = float(m_spd.group(1)) if m_spd else None

        # 9. Region
        m_reg = re.search(r"Region:\s*(.*?)(?:\n|$)", text, re.I)
        region = None
        if m_reg:
            region = m_reg.group(1).strip()
        else:
            m_subj = re.search(r"Subject:\s*(?:[A-Za-z\s]+)\s+over\s+(.*?)(?:\n|$)", text, re.I)
            if m_subj:
                region = m_subj.group(1).strip()

        # 10. Current wind (kmph) - only if explicitly available for system center
        m_cwind = re.search(r"central\s*(?:surface\s*)?wind\s*(?:speed)?\s*[:\s]*(\d+(?:\.\d+)?)\s*km(?:ph|\/h)", text, re.I)
        current_wind = float(m_cwind.group(1)) if m_cwind else None

        # 11. Central pressure (hpa) - only if explicitly available
        m_pres = re.search(r"central\s*pressure\s*[:\s]*(\d+(?:\.\d+)?)\s*hpa", text, re.I)
        central_pres = float(m_pres.group(1)) if m_pres else None

        # 12. Forecast intensity & text
        forecast_intensity = None
        forecast_text = None
        m_fc = re.search(r"(?:Forecast|forecast):\s*(.*?)(?:\n|$)", text, re.I)
        if m_fc:
            forecast_text = m_fc.group(1).strip()
        else:
            m_fc2 = re.search(r"((?:It is )?very likely to intensify into [^.]+?\.)", text, re.I | re.DOTALL)
            if m_fc2:
                forecast_text = re.sub(r"\s+", " ", m_fc2.group(1)).strip()

        if forecast_text:
            for st in ["Super Cyclonic Storm", "Extremely Severe Cyclonic Storm", "Very Severe Cyclonic Storm",
                       "Severe Cyclonic Storm", "Cyclonic Storm", "Deep Depression", "Depression"]:
                if re.search(rf"\b{st}\b", forecast_text, re.I):
                    forecast_intensity = st
                    break

        # 13. Next bulletin time
        next_bulletin = None
        m_next = re.search(r"Next bulletin will be issued at\s*([0-9\s]+(?:hours|hrs)?\s*IST[^\.\n]*)", text, re.I)
        if m_next:
            next_bulletin = re.sub(r"\s+", " ", m_next.group(1)).strip()

        # If neither latitude nor system type could be determined, consider non-active
        if lat is None and system_type is None:
            return {
                "active": False,
                "systems": [],
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "message": "NO ACTIVE TROPICAL SYSTEM DETECTED",
                "source_url": source_url,
                "timestamp": source_timestamp or datetime.now(timezone.utc).isoformat()
            }

        system_obj = {
            "active": True,
            "source": "IMD_RSMC_PUBLIC_BULLETIN",
            "bulletin_number": b_num,
            "issue_datetime": issue_datetime,
            "system_type": system_type,
            "system_name": system_name,
            "latitude": lat,
            "longitude": lon,
            "movement_direction": movement_dir,
            "movement_speed_kmph": movement_spd,
            "region": region,
            "current_wind_kmph": current_wind,
            "central_pressure_hpa": central_pres,
            "forecast_intensity": forecast_intensity,
            "forecast_text": forecast_text,
            "next_bulletin": next_bulletin,
            "source_url": source_url,
            "data_mode": "LIVE"
        }

        return {
            "active": True,
            "systems": [system_obj],
            "source": "IMD_RSMC_PUBLIC_BULLETIN",
            "bulletin_url": source_url,
            "timestamp": source_timestamp or datetime.now(timezone.utc).isoformat()
        }
