# passai/core/icons.py
#
# Heavy imports (requests, PIL) are lazy — imported inside functions only
# when a network download is actually needed.  This keeps startup import
# time to near-zero and avoids flagging AV scanners that watch for
# "load image library + open network socket" patterns at process start.

import re
from pathlib import Path
from typing import Optional

# ── Domain mapping ────────────────────────────────────────────────────────────

KNOWN_DOMAINS = {
    # Social Media
    "instagram": "instagram.com",
    "insta": "instagram.com",
    "facebook": "facebook.com",
    "fb": "facebook.com",
    "twitter": "twitter.com",
    "x": "twitter.com",
    "tiktok": "tiktok.com",
    "snapchat": "snapchat.com",
    "linkedin": "linkedin.com",
    "reddit": "reddit.com",
    "pinterest": "pinterest.com",
    "tumblr": "tumblr.com",
    "telegram": "telegram.org",
    "whatsapp": "whatsapp.com",
    "messenger": "messenger.com",
    "discord": "discord.com",
    "slack": "slack.com",
    # Email & Communication
    "gmail": "gmail.com",
    "google mail": "gmail.com",
    "outlook": "outlook.com",
    "yahoo": "yahoo.com",
    "yahoo mail": "mail.yahoo.com",
    "protonmail": "protonmail.com",
    "proton": "proton.me",
    "icloud": "icloud.com",
    "zoho": "zoho.com",
    # Gaming
    "steam": "steampowered.com",
    "epic games": "epicgames.com",
    "epicgames": "epicgames.com",
    "origin": "origin.com",
    "ea": "ea.com",
    "ubisoft": "ubisoft.com",
    "battle.net": "battle.net",
    "battlenet": "battle.net",
    "blizzard": "blizzard.com",
    "riot games": "riotgames.com",
    "riot": "riotgames.com",
    "gog": "gog.com",
    "playstation": "playstation.com",
    "ps": "playstation.com",
    "xbox": "xbox.com",
    "nintendo": "nintendo.com",
    "twitch": "twitch.tv",
    "roblox": "roblox.com",
    "minecraft": "minecraft.net",
    # Streaming & Entertainment
    "netflix": "netflix.com",
    "spotify": "spotify.com",
    "youtube": "youtube.com",
    "prime video": "primevideo.com",
    "amazon prime": "primevideo.com",
    "disney+": "disneyplus.com",
    "disney plus": "disneyplus.com",
    "hulu": "hulu.com",
    "hbo": "hbo.com",
    "hbo max": "hbomax.com",
    "apple tv": "tv.apple.com",
    "peacock": "peacocktv.com",
    "paramount": "paramountplus.com",
    "soundcloud": "soundcloud.com",
    "deezer": "deezer.com",
    "apple music": "music.apple.com",
    # Shopping & E-commerce
    "amazon": "amazon.com",
    "ebay": "ebay.com",
    "aliexpress": "aliexpress.com",
    "etsy": "etsy.com",
    "walmart": "walmart.com",
    "target": "target.com",
    "bestbuy": "bestbuy.com",
    "best buy": "bestbuy.com",
    "shopify": "shopify.com",
    "alibaba": "alibaba.com",
    # Finance & Banking
    "paypal": "paypal.com",
    "venmo": "venmo.com",
    "cashapp": "cash.app",
    "cash app": "cash.app",
    "stripe": "stripe.com",
    "chase": "chase.com",
    "bank of america": "bankofamerica.com",
    "wells fargo": "wellsfargo.com",
    "citibank": "citibank.com",
    "capital one": "capitalone.com",
    "american express": "americanexpress.com",
    "amex": "americanexpress.com",
    "coinbase": "coinbase.com",
    "robinhood": "robinhood.com",
    "binance": "binance.com",
    # Cloud & Productivity
    "google": "google.com",
    "microsoft": "microsoft.com",
    "apple": "apple.com",
    "dropbox": "dropbox.com",
    "onedrive": "onedrive.com",
    "google drive": "drive.google.com",
    "notion": "notion.so",
    "evernote": "evernote.com",
    "trello": "trello.com",
    "asana": "asana.com",
    "monday": "monday.com",
    "zoom": "zoom.us",
    "teams": "teams.microsoft.com",
    "skype": "skype.com",
    "github": "github.com",
    "gitlab": "gitlab.com",
    "bitbucket": "bitbucket.org",
    # Office & Microsoft
    "office": "office.com",
    "office 365": "office.com",
    "microsoft 365": "microsoft.com",
    # Education
    "coursera": "coursera.org",
    "udemy": "udemy.com",
    "khan academy": "khanacademy.org",
    "duolingo": "duolingo.com",
    "canvas": "canvas.com",
    "blackboard": "blackboard.com",
    # Transport & Other
    "airbnb": "airbnb.com",
    "uber": "uber.com",
    "lyft": "lyft.com",
    "doordash": "doordash.com",
    "grubhub": "grubhub.com",
    "yelp": "yelp.com",
    "tripadvisor": "tripadvisor.com",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def guess_domain(service_name: str) -> Optional[str]:
    if not service_name:
        return None
    normalized = service_name.lower().strip()
    if normalized in KNOWN_DOMAINS:
        return KNOWN_DOMAINS[normalized]
    no_spaces = normalized.replace(" ", "")
    if no_spaces in KNOWN_DOMAINS:
        return KNOWN_DOMAINS[no_spaces]
    if len(no_spaces) > 2 and no_spaces.isalnum():
        return f"{no_spaces}.com"
    return None


def _download_icon(url: str) -> Optional[bytes]:
    """Download image bytes — timeout is short (2 s) to fail fast."""
    try:
        import requests  # lazy import — not loaded at startup
        resp = requests.get(url, timeout=2, headers={'User-Agent': 'PassAI/1.0'})
        if resp.status_code == 200:
            ct = resp.headers.get('Content-Type', '')
            if 'image' in ct or len(resp.content) > 100:
                return resp.content
    except Exception:
        pass
    return None


def _to_png(image_data: bytes, size: int = 64) -> Optional[bytes]:
    """Convert arbitrary image bytes to a square PNG — lazy PIL import."""
    try:
        import io
        from PIL import Image  # lazy import — not loaded at startup
        img = Image.open(io.BytesIO(image_data))
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
        buf = io.BytesIO()
        canvas.save(buf, format='PNG')
        return buf.getvalue()
    except Exception:
        return None


def fetch_icon_for_service(service_name: str, cache_dir: Path) -> Optional[Path]:
    """
    Return a cached PNG path for service_name, downloading if necessary.
    Network I/O only happens when the icon is not already on disk.
    Call from a background thread — this may take up to ~6 s on first fetch.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(service_name)
    if not slug:
        return None

    icon_path = cache_dir / f"{slug}.png"
    if icon_path.exists():
        return icon_path

    domain = guess_domain(service_name)
    if not domain:
        return None

    for url in (
        f"https://logo.clearbit.com/{domain}",
        f"https://www.google.com/s2/favicons?domain={domain}&sz=128",
        f"https://icons.duckduckgo.com/ip3/{domain}.ico",
    ):
        data = _download_icon(url)
        if data:
            png = _to_png(data)
            if png:
                try:
                    icon_path.write_bytes(png)
                    return icon_path
                except Exception:
                    pass

    return None


def get_emoji_for_service(service_name: str) -> str:
    url_lower = service_name.lower()
    emoji_map = {
        "google": "🔍", "facebook": "👥", "twitter": "🐦",
        "instagram": "📷", "github": "💻", "linkedin": "💼",
        "amazon": "📦", "netflix": "🎬", "spotify": "🎵",
        "apple": "🍎", "microsoft": "🪟", "reddit": "🤖",
        "youtube": "📺", "gmail": "📧", "yahoo": "💌",
        "dropbox": "📂", "slack": "💬", "discord": "🎮",
        "paypal": "💳", "bank": "🏦", "steam": "🎮",
        "epic": "🎮", "game": "🎮", "mail": "📧",
        "shop": "🛒", "card": "💳",
    }
    for keyword, emoji in emoji_map.items():
        if keyword in url_lower:
            return emoji
    return "🔐"


# ── IconManager ───────────────────────────────────────────────────────────────

class IconFetchError(Exception):
    pass


class IconManager:
    """
    Manage application icons.

    get_icon_path_cached() — instant disk-only check, no network (use on UI thread)
    get_icon_path()        — same as cached (kept for API compat)
    fetch_icon_blocking()  — full download; call from a background thread
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Path.home() / ".passai" / "icons")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # In-memory set of slugs known to have a cached file — avoids repeated
        # stat() calls when the same service appears multiple times.
        self._disk_hit: set[str] = set()

    def get_icon_path_cached(self, service_name: str) -> Optional[Path]:
        """
        Return the icon path if it is already on disk — otherwise None.
        Never makes a network request.  Safe to call from the UI thread.
        """
        slug = slugify(service_name)
        if not slug:
            return None
        if slug in self._disk_hit:
            return self.cache_dir / f"{slug}.png"
        path = self.cache_dir / f"{slug}.png"
        if path.exists():
            self._disk_hit.add(slug)
            return path
        return None

    def get_icon_path(self, service_name: str) -> Optional[Path]:
        """Alias for get_icon_path_cached — no network on UI thread."""
        return self.get_icon_path_cached(service_name)

    def fetch_icon_blocking(self, service_name: str) -> Optional[Path]:
        """
        Download + cache icon.  May block for up to ~6 s.
        Must be called from a background thread.
        """
        try:
            path = fetch_icon_for_service(service_name, self.cache_dir)
            if path:
                self._disk_hit.add(slugify(service_name))
            return path
        except Exception:
            return None

    def get_emoji(self, service_name: str) -> str:
        return get_emoji_for_service(service_name)
