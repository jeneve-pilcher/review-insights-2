"""Who can do what. Roles: owner > admin > manager > viewer."""

ROLES = ("owner", "admin", "manager", "viewer")

ACTIONS = {
    "owner": {"manage_members", "manage_admins", "manage_locations", "run_location", "update_alert",
              "view_audit", "set_budget"},
    "admin": {"manage_members", "manage_locations", "run_location", "update_alert", "view_audit"},
    "manager": {"run_location", "update_alert"},   # only for the locations they manage
    "viewer": set(),                                # read-only, org-wide
}


def can(member: dict, action: str) -> bool:
    return action in ACTIONS.get(member.get("role"), set())


def manages(member: dict, location: dict) -> bool:
    email = (member.get("email") or "").lower()
    return bool(email) and email == (location.get("manager_email") or "").lower()


def can_see_location(member: dict, location: dict) -> bool:
    if member["role"] in ("owner", "admin", "viewer"):
        return True
    return manages(member, location)


def can_act_on_location(member: dict, location: dict, action: str) -> bool:
    if not can(member, action):
        return False
    return member["role"] in ("owner", "admin") or manages(member, location)
