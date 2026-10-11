"""Industry packs: each industry's own themes, default revenue assumptions and graphs.

A pack changes what the analysis LOOKS FOR and which industry graphs appear. It does not change the engine, and it
is not a trained model: themes are matched by curated word lists, and trends come from simple, explainable
statistics. Trained models would need labeled examples that only real usage can supply."""
from typing import Dict, List, Optional

DEFAULT = "casual_dining"


def _t(id_, label, keywords):
    return {"id": id_, "label": label, "keywords": keywords}


PACKS: Dict[str, dict] = {
    "casual_dining": {
        "label": "Casual dining", "group": "Restaurants", "available": True, "default_aov": 35,
        "description": "Everyday sit-down and fast-casual restaurants: waits, order accuracy, value and families.",
        "subratings": False,
        # Which data sources fit this industry (Google reviews are always included). Everything is optional.
        "integrations": {"recommended": ["yelp", "doordash", "ubereats", "grubhub"], "optional": ["opentable"], "hidden": []},
        # Headline numbers for the industry: the share of written reviews that mention a theme, or an OpenTable score.
        "kpis": [{"id": "wait", "label": "Mention waiting", "kind": "theme", "key": "wait"}, {"id": "accuracy", "label": "Order mistakes", "kind": "theme", "key": "accuracy"}, {"id": "takeout", "label": "Takeout & delivery", "kind": "theme", "key": "takeout"}, {"id": "value", "label": "Portions & value", "kind": "theme", "key": "value"}],
        "themes": [
            _t("wait", "Wait times", ["wait", "waited", "waiting", "line", "long time", "took forever", "slow", "an hour"]),
            _t("accuracy", "Order accuracy", ["wrong order", "wrong", "missing", "forgot", "mistake", "incorrect", "not what i ordered"]),
            _t("value", "Portions & value", ["portion", "portions", "small", "tiny", "overpriced", "expensive", "worth", "value", "cheap", "price"]),
            _t("staff", "Staff friendliness", ["friendly", "rude", "attitude", "welcoming", "unfriendly", "server", "waitress", "waiter"]),
            _t("family", "Families & kids", ["kids", "children", "family", "high chair", "kid-friendly", "kid friendly"]),
            _t("cleanliness", "Cleanliness", ["clean", "dirty", "filthy", "sticky", "bathroom", "restroom", "spotless"]),
            _t("noise", "Noise & atmosphere", ["loud", "noisy", "noise", "atmosphere", "vibe", "crowded", "music"]),
            _t("takeout", "Takeout & delivery", ["delivery", "takeout", "take out", "to-go", "to go", "packaging", "arrived cold", "pickup", "pick up"]),
        ],
    },
    "fine_dining": {
        "label": "Fine dining", "group": "Restaurants", "available": True, "default_aov": 120,
        "description": "Upscale, reservation-led restaurants: pacing, ambiance, value for price, occasions and wine.",
        "subratings": True,   # OpenTable's food / service / ambience / value scores
        "integrations": {"recommended": ["opentable", "yelp"], "optional": ["doordash", "ubereats", "grubhub"], "hidden": []},
        "kpis": [{"id": "score_value", "label": "Value score (OpenTable)", "kind": "sub", "key": "value"}, {"id": "score_service", "label": "Service score (OpenTable)", "kind": "sub", "key": "service"}, {"id": "pacing", "label": "Pacing complaints", "kind": "theme", "key": "pacing"}, {"id": "occasion", "label": "Special occasions", "kind": "theme", "key": "occasion"}],
        "themes": [
            _t("pacing", "Pacing between courses", ["pacing", "paced", "rushed", "between courses", "took forever", "dragged", "long wait", "waited"]),
            _t("service", "Service & attentiveness", ["attentive", "inattentive", "sommelier", "server", "waiter", "service", "ignored", "knowledgeable", "polished"]),
            _t("ambiance", "Ambiance & noise", ["ambiance", "ambience", "atmosphere", "decor", "romantic", "intimate", "loud", "noisy", "lighting", "music"]),
            _t("value", "Value for price", ["overpriced", "not worth", "worth it", "worth the", "expensive", "pricey", "price", "bill", "value"]),
            _t("occasion", "Special occasions", ["anniversary", "birthday", "special occasion", "celebrate", "celebration", "proposal", "engagement", "date night"]),
            _t("food", "Food & tasting menu", ["tasting menu", "dish", "dishes", "flavor", "flavors", "plating", "course", "seasonal", "fresh"]),
            _t("wine", "Wine & drinks", ["wine", "pairing", "pairings", "cocktail", "cocktails", "sommelier", "drinks"]),
            _t("reservation", "Reservations & seating", ["reservation", "reserved", "booked", "booking", "seated", "table", "cancel", "cancelled", "overbooked"]),
        ],
    },
    "general": {
        "label": "Other / not listed", "group": "Other", "available": True, "default_aov": 35,
        "description": "A general-purpose set of themes for any business that isn't listed yet.",
        "subratings": False,
        "integrations": {"recommended": ["yelp"], "optional": ["opentable", "doordash", "ubereats", "grubhub"], "hidden": []},
        "kpis": [{"id": "service", "label": "Service", "kind": "theme", "key": "service"}, {"id": "price", "label": "Price & value", "kind": "theme", "key": "price"}, {"id": "wait", "label": "Wait times", "kind": "theme", "key": "wait"}],
        "themes": [
            _t("service", "Service", ["service", "staff", "rude", "friendly", "helpful", "unhelpful"]),
            _t("quality", "Quality", ["quality", "poor quality", "excellent", "great quality", "broken", "defective"]),
            _t("price", "Price & value", ["price", "expensive", "cheap", "overpriced", "value", "worth"]),
            _t("wait", "Wait times", ["wait", "waited", "waiting", "line", "slow", "long time"]),
            _t("clean", "Cleanliness", ["clean", "dirty", "filthy", "spotless"]),
        ],
    },
    # Announced, not built: shown disabled so people can see what's coming.
    "retail": {"label": "Retail", "group": "Retail", "available": False, "description": "Stores: stock, checkout lines, returns and staff help.", "themes": [], "default_aov": 60, "subratings": False, "integrations": {"recommended": [], "optional": [], "hidden": []}, "kpis": []},
    # (Healthcare segments follow below, added after the dict is built.)
}


def get_pack(industry: Optional[str]) -> dict:
    """The pack for a saved industry. Anything missing, unknown or not yet available falls back to the default."""
    pack = PACKS.get(industry or "")
    if pack is None or not pack["available"]:
        pack = PACKS[DEFAULT]
        industry = DEFAULT
    return {"id": industry, **pack}


def is_selectable(industry: str) -> bool:
    return bool(PACKS.get(industry, {}).get("available"))


def public_pack(pack: dict) -> dict:
    return {"id": pack["id"], "label": pack["label"], "group": pack["group"], "default_aov": pack["default_aov"],
            "themes": [{"id": t["id"], "label": t["label"]} for t in pack["themes"]], "kpis": pack.get("kpis", []),
            "replies_allowed": pack.get("replies_allowed", True), "provider_level": pack.get("provider_level", False)}


def catalog() -> List[dict]:
    return [{"id": k, "label": v["label"], "group": v["group"], "available": v["available"],
             "description": v["description"], "default_aov": v["default_aov"],
             "themes": [t["label"] for t in v["themes"]], "integrations": v["integrations"],
             "replies_allowed": v.get("replies_allowed", True), "provider_level": v.get("provider_level", False)} for k, v in PACKS.items()]


# ---- Healthcare. Replies are OFF (answering a patient's review can disclose protected health information), tone
# scoring treats clinical words as neutral, and provider-level data (individual doctors) is a separate, opt-in feature.
_HIDDEN_FOR_CLINICS = ["opentable", "doordash", "ubereats", "grubhub"]


def _clinic(label, description, aov, themes, kpis):
    return {"label": label, "group": "Healthcare", "available": True, "default_aov": aov, "description": description,
            "subratings": False, "clinical": True, "replies_allowed": False, "provider_level": True,
            "integrations": {"recommended": ["yelp"], "optional": [], "hidden": _HIDDEN_FOR_CLINICS},
            "themes": themes, "kpis": kpis}


def _k(id_, label, key): return {"id": id_, "label": label, "kind": "theme", "key": key}


PACKS["urgent_care"] = _clinic(
    "Urgent care", "Walk-in and urgent care clinics: waits, quoted versus actual times, billing, communication and testing.", 180,
    [
        _t("wait", "Wait times", ["wait", "waited", "waiting", "hours", "an hour", "long time", "walk-in", "walk in", "line", "forever"]),
        _t("quoted", "Quoted vs actual wait", ["quoted", "estimated wait", "online check-in", "online check in", "check-in time", "checked in", "said it would be"]),
        _t("frontdesk", "Front desk & staff", ["front desk", "receptionist", "reception", "staff", "rude", "friendly", "attitude"]),
        _t("provider", "Provider communication", ["doctor", "provider", "nurse", "practitioner", "physician assistant", "listened", "explained", "dismissive", "rushed", "compassionate", "bedside manner", "caring"]),
        _t("billing", "Billing & insurance", ["bill", "billing", "insurance", "copay", "co-pay", "charged", "overcharged", "cost", "surprise", "out of network", "price"]),
        _t("clean", "Cleanliness", ["clean", "dirty", "filthy", "bathroom", "restroom", "waiting room", "sanitary"]),
        _t("kids", "Children", ["kids", "child", "children", "pediatric", "son", "daughter", "baby", "toddler"]),
        _t("tests", "Testing & imaging", ["x-ray", "xray", "lab", "labs", "test", "tests", "results", "covid test", "strep", "swab", "imaging"]),
        _t("convenience", "Hours & convenience", ["open late", "weekend", "weekends", "parking", "location", "convenient", "close to"]),
    ],
    [_k("wait", "Mention waiting", "wait"), _k("quoted", "Quoted vs actual", "quoted"), _k("billing", "Billing & insurance", "billing"), _k("provider", "Provider communication", "provider")])

PACKS["dental"] = _clinic(
    "Dental", "Dental practices: scheduling, comfort, explaining treatment, billing and cleanliness.", 250,
    [
        _t("access", "Scheduling & access", ["appointment", "scheduling", "schedule", "rescheduled", "cancelled", "canceled", "booked", "availability", "new patient"]),
        _t("wait", "Wait & punctuality", ["wait", "waited", "waiting room", "on time", "late", "running behind"]),
        _t("comfort", "Comfort & gentleness", ["gentle", "painless", "numb", "numbing", "hurt", "pain", "comfortable", "anxious", "nervous", "calm"]),
        _t("staff", "Hygienists & staff", ["hygienist", "assistant", "front desk", "receptionist", "staff", "friendly", "rude"]),
        _t("billing", "Billing & insurance", ["bill", "billing", "insurance", "charged", "cost", "price", "estimate", "copay", "out of pocket", "overcharged"]),
        _t("explanation", "Explaining treatment", ["explained", "explain", "options", "treatment plan", "unnecessary", "upsell", "pressure", "second opinion"]),
        _t("clean", "Cleanliness", ["clean", "dirty", "sterile", "spotless", "modern"]),
        _t("kids", "Children", ["kids", "child", "children", "pediatric", "son", "daughter"]),
        _t("emergency", "Emergency & same-day", ["emergency", "same day", "same-day", "urgent", "toothache", "cracked tooth", "walk-in"]),
    ],
    [_k("comfort", "Comfort & gentleness", "comfort"), _k("billing", "Billing & insurance", "billing"), _k("wait", "Wait & punctuality", "wait"), _k("access", "Scheduling & access", "access")])

PACKS["primary_care"] = _clinic(
    "Primary care", "Family and primary care practices: getting appointments, follow-up, communication and billing.", 160,
    [
        _t("access", "Getting appointments", ["appointment", "scheduling", "weeks", "booked", "new patient", "availability", "get in"]),
        _t("wait", "Wait in the office", ["wait", "waited", "waiting room", "running late", "behind schedule"]),
        _t("bedside", "Bedside manner", ["listened", "dismissive", "rushed", "compassionate", "caring", "bedside manner", "explained", "doctor", "arrogant", "took the time"]),
        _t("followup", "Follow-up & results", ["follow up", "follow-up", "referral", "referred", "test results", "lab results", "call back", "called back", "never heard"]),
        _t("reach", "Phone & portal", ["portal", "phone", "voicemail", "hold", "message", "messages", "email", "reach"]),
        _t("billing", "Billing & insurance", ["bill", "billing", "insurance", "copay", "charged", "cost", "price", "out of network", "surprise"]),
        _t("staff", "Front desk & nurses", ["front desk", "receptionist", "nurse", "medical assistant", "staff", "rude", "friendly"]),
        _t("continuity", "Continuity of care", ["different doctor", "turnover", "left the practice", "new doctor", "seen by", "stopped accepting", "waitlist"]),
    ],
    [_k("access", "Getting appointments", "access"), _k("followup", "Follow-up & results", "followup"), _k("billing", "Billing & insurance", "billing"), _k("bedside", "Bedside manner", "bedside")])
