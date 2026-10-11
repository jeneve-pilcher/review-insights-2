"""White-label branding for companies that sign a larger deal (set by an administrator, never self-serve).

A company gets: a brand name, a logo, colors, and an SSO email domain. The login page looks the domain up
before sign-in, so the company's own branding appears around its SSO button. Everything here is validated:
colors must be readable, the logo must be an https link, and the public lookup only ever exposes brand details."""
import re
import time
from collections import defaultdict, deque
from typing import Optional

_HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_DOMAIN = re.compile(r"^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")
MIN_PRIMARY_CONTRAST = 4.5     # white button text on the primary color (WCAG AA for normal text)
MIN_ACCENT_CONTRAST = 3.0      # accents are lines and icons, so the lower bar for graphics applies


def normalize_hex(value: str) -> str:
    m = _HEX.match((value or "").strip())
    if not m:
        raise ValueError("Colors must be hex values like #0a5c36.")
    h = m.group(1).lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h


def _rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _luminance(hex_color: str) -> float:
    def chan(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(v) for v in _rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def _mix(color: str, other: str, amount: float) -> str:
    """Moves `color` toward `other` by `amount` (0..1)."""
    c, o = _rgb(color), _rgb(other)
    return "#" + "".join(f"{round(c[i] + (o[i] - c[i]) * amount):02x}" for i in range(3))


def derive_palette(primary: str, accent: Optional[str] = None) -> dict:
    """Everything the interface needs from one or two chosen colors."""
    return {
        "primary": primary,
        "hover": _mix(primary, "#000000", 0.12),    # button hover
        "soft": _mix(primary, "#ffffff", 0.92),     # tinted backgrounds
        "border": _mix(primary, "#ffffff", 0.75),   # tinted borders
        "accent": accent or primary,
    }


def validate_brand(*, primary=None, accent=None, name=None, logo_url=None, sso_domain=None) -> dict:
    """Returns only the fields that were provided, cleaned. Raises ValueError with a plain message."""
    out = {}
    if primary is not None:
        p = normalize_hex(primary)
        ratio = contrast_ratio(p, "#ffffff")
        if ratio < MIN_PRIMARY_CONTRAST:
            raise ValueError(f"The primary color {p} is too light for white button text (contrast {ratio}:1; it needs at least "
                             f"{MIN_PRIMARY_CONTRAST}:1). Try a darker shade.")
        out["brand_primary"] = p
    if accent is not None:
        a = normalize_hex(accent)
        ratio = contrast_ratio(a, "#ffffff")
        if ratio < MIN_ACCENT_CONTRAST:
            raise ValueError(f"The accent color {a} is too light to show up on white (contrast {ratio}:1; it needs at least {MIN_ACCENT_CONTRAST}:1).")
        out["brand_accent"] = a
    if name is not None:
        n = re.sub(r"[\x00-\x1f]", "", name).strip()
        if not n or len(n) > 60 or "<" in n or ">" in n:
            raise ValueError("The brand name must be 1-60 characters, without < or >.")
        out["brand_name"] = n
    if logo_url is not None:
        u = logo_url.strip()
        if not u.lower().startswith("https://") or len(u) > 500 or re.search(r"[\s\"'<>]", u):
            raise ValueError("The logo must be an https:// link (no spaces or quotes), up to 500 characters.")
        out["brand_logo_url"] = u
    if sso_domain is not None:
        d = sso_domain.strip().lower().lstrip("@")
        if not _DOMAIN.match(d):
            raise ValueError("The SSO domain must look like acme.com.")
        out["sso_domain"] = d
    return out


def public_branding(org: Optional[dict]) -> Optional[dict]:
    """The only company details ever shown to someone who isn't signed in."""
    if not org or not org.get("white_label") or not org.get("brand_primary"):
        return None
    return {
        "name": org.get("brand_name") or org.get("name"),
        "logo_url": org.get("brand_logo_url"),
        "palette": derive_palette(org["brand_primary"], org.get("brand_accent")),
        "sso_domain": org.get("sso_domain"),
        "sso": bool(org.get("sso_domain")),
    }


def domain_of(email: str) -> Optional[str]:
    email = (email or "").strip().lower()
    if "@" not in email:
        return None
    d = email.rsplit("@", 1)[1]
    return d if _DOMAIN.match(d) else None


# --- a small per-address limiter for the public lookup (stops anyone from scanning for company domains)
_hits = defaultdict(deque)
LOOKUPS_PER_MINUTE = 20


def allow_lookup(key: str, now: Optional[float] = None) -> bool:
    now = now if now is not None else time.time()
    q = _hits[key]
    while q and q[0] <= now - 60:
        q.popleft()
    if len(q) >= LOOKUPS_PER_MINUTE:
        return False
    q.append(now)
    return True


def apply_branding(store, org_ref: str, *, enable=None, primary=None, accent=None, name=None, logo_url=None,
                   sso_domain=None, industry=None, provider_data=None) -> dict:
    """What an administrator runs when a deal is signed (see scripts/set_branding.py). Returns the updated company."""
    orgs = store.list_orgs()
    matches = [o for o in orgs if o["id"] == org_ref] or [o for o in orgs if o["name"].lower() == org_ref.strip().lower()]
    if not matches:
        raise ValueError(f"No company found matching '{org_ref}'.")
    if len(matches) > 1:
        raise ValueError(f"More than one company is called '{org_ref}'. Use its id instead.")
    org = matches[0]
    fields = validate_brand(primary=primary, accent=accent, name=name, logo_url=logo_url, sso_domain=sso_domain)
    if "sso_domain" in fields:
        taken = [o for o in orgs if o.get("sso_domain") == fields["sso_domain"] and o["id"] != org["id"]]
        if taken:
            raise ValueError(f"The domain {fields['sso_domain']} already belongs to '{taken[0]['name']}'.")
    if industry is not None:
        from analysis import industries
        if not industries.is_selectable(industry):
            raise ValueError(f"'{industry}' isn't an available industry.")
        fields["industry"] = industry
    if enable is not None:
        fields["white_label"] = bool(enable)
    if provider_data is not None:
        fields["provider_data_enabled"] = bool(provider_data)     # individual-doctor data: an administrator decision
    merged = {**org, **fields}
    if merged.get("white_label") and not merged.get("brand_primary"):
        raise ValueError("Set a primary color before enabling white-label branding.")
    if fields:
        store.update_org(org["id"], **fields)
    return store.get_org(org["id"])
