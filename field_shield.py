import json
import os
import re
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


VALID_CHECKIN_STATUS = {"ok", "delayed", "unsafe", "detained", "medical"}
VALID_INCIDENT_TYPES = {
    "detention",
    "assault",
    "injury",
    "property_seizure",
    "surveillance",
    "threat",
    "other",
}
VALID_ALERT_PROVIDERS = {"sms", "signal"}


class ValidationError(Exception):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_dict(payload: Any) -> Dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValidationError("JSON body must be an object")
    return payload


def _validate_str(value: Any, field: str, max_len: int, required: bool = False) -> str:
    if value is None:
        if required:
            raise ValidationError(f"{field} is required")
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string")
    v = value.strip()
    if required and not v:
        raise ValidationError(f"{field} is required")
    if len(v) > max_len:
        raise ValidationError(f"{field} exceeds max length {max_len}")
    return v


def _validate_iso(value: Any, field: str) -> str:
    if value in (None, ""):
        return utc_now_iso()
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be an ISO timestamp")
    v = value.strip()
    if not v:
        return utc_now_iso()
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError(f"{field} must be a valid ISO-8601 timestamp")
    return v


def _coerce_int(value: Any, field: str, min_value: int, max_value: int, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValidationError(f"{field} must be an integer")
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be an integer")
    if not (min_value <= n <= max_value):
        raise ValidationError(f"{field} must be between {min_value} and {max_value}")
    return n


def _coerce_float(value: Any, field: str, min_value: float, max_value: float) -> Optional[float]:
    if value is None:
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be numeric")
    if not (min_value <= n <= max_value):
        raise ValidationError(f"{field} must be between {min_value} and {max_value}")
    return n


def _root() -> Path:
    p = Path(os.environ.get("FIELD_SHIELD_DATA_DIR", "data/field_shield"))
    (p / "sessions").mkdir(parents=True, exist_ok=True)
    (p / "packets").mkdir(parents=True, exist_ok=True)
    return p


def _session_path(session_id: str) -> Path:
    return _root() / "sessions" / f"{session_id}.json"


def save_session(session: Dict[str, Any]) -> None:
    session["updated_at"] = utc_now_iso()
    with _session_path(session["session_id"]).open("w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)


def load_session(session_id: str) -> Dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9\-]{36}", session_id):
        raise ValidationError("session_id must be a UUID")
    path = _session_path(session_id)
    if not path.exists():
        raise FileNotFoundError("session not found")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def start_session(payload: Any) -> Dict[str, Any]:
    data = _ensure_dict(payload)

    raw_contacts = data.get("trusted_contacts") or []
    if not isinstance(raw_contacts, list):
        raise ValidationError("trusted_contacts must be a list")
    if len(raw_contacts) > 15:
        raise ValidationError("trusted_contacts max length is 15")

    trusted_contacts: List[Dict[str, str]] = []
    for i, c in enumerate(raw_contacts):
        if not isinstance(c, dict):
            raise ValidationError(f"trusted_contacts[{i}] must be an object")
        trusted_contacts.append(
            {
                "name": _validate_str(c.get("name"), f"trusted_contacts[{i}].name", 80, required=True),
                "channel": _validate_str(c.get("channel"), f"trusted_contacts[{i}].channel", 24, required=True).lower(),
                "target": _validate_str(c.get("target"), f"trusted_contacts[{i}].target", 160, required=True),
            }
        )

    now = utc_now_iso()
    session = {
        "session_id": str(uuid.uuid4()),
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "metadata": {
            "organizer_alias": _validate_str(data.get("organizer_alias"), "organizer_alias", 80),
            "device_id": _validate_str(data.get("device_id"), "device_id", 128),
            "start_location": _validate_str(data.get("location"), "location", 200),
            "consent_ack": bool(data.get("consent_ack", False)),
            "trusted_contacts": trusted_contacts,
            # TODO(security): encrypt sensitive metadata at rest with per-session keys.
        },
        "checkins": [],
        "incidents": [],
        "media_manifest": [],
        "alerts_sent": [],
    }
    save_session(session)
    return session


def add_checkin(payload: Any) -> Dict[str, Any]:
    data = _ensure_dict(payload)
    session_id = _validate_str(data.get("session_id"), "session_id", 36, required=True)
    session = load_session(session_id)

    status = _validate_str(data.get("status") or "ok", "status", 24, required=True).lower()
    if status not in VALID_CHECKIN_STATUS:
        raise ValidationError(f"status must be one of: {', '.join(sorted(VALID_CHECKIN_STATUS))}")

    checkin = {
        "checkin_id": str(uuid.uuid4()),
        "timestamp": _validate_iso(data.get("timestamp"), "timestamp"),
        "status": status,
        "location": _validate_str(data.get("location"), "location", 200),
        "note": _validate_str(data.get("note"), "note", 1000),
        "battery_level": _coerce_int(data.get("battery_level"), "battery_level", 0, 100, default=None),
    }

    session["checkins"].append(checkin)
    save_session(session)
    return checkin


def _validate_media(raw: Any) -> List[Dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValidationError("media must be a list")
    if len(raw) > 50:
        raise ValidationError("media max length is 50")
    out = []
    for i, m in enumerate(raw):
        if not isinstance(m, dict):
            raise ValidationError(f"media[{i}] must be an object")
        out.append(
            {
                "media_id": str(uuid.uuid4()),
                "type": _validate_str(m.get("type") or "unknown", f"media[{i}].type", 40, required=True),
                "name": _validate_str(m.get("name"), f"media[{i}].name", 200),
                "uri": _validate_str(m.get("uri"), f"media[{i}].uri", 500),
                "sha256": _validate_str(m.get("sha256"), f"media[{i}].sha256", 128),
                "size_bytes": _coerce_int(m.get("size_bytes"), f"media[{i}].size_bytes", 0, 50_000_000, default=0),
                # TODO(security): replace plain URI references with encrypted blob handles.
            }
        )
    return out


def _safe_list(raw: Any, field: str, max_len: int, item_max: int) -> List[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValidationError(f"{field} must be a list")
    if len(raw) > max_len:
        raise ValidationError(f"{field} max length is {max_len}")
    vals = []
    for i, item in enumerate(raw):
        vals.append(_validate_str(item, f"{field}[{i}]", item_max, required=True))
    return vals


def add_incident(payload: Any) -> Dict[str, Any]:
    data = _ensure_dict(payload)
    session_id = _validate_str(data.get("session_id"), "session_id", 36, required=True)
    session = load_session(session_id)

    incident_type = _validate_str(data.get("incident_type"), "incident_type", 40, required=True).lower()
    if incident_type not in VALID_INCIDENT_TYPES:
        raise ValidationError(f"incident_type must be one of: {', '.join(sorted(VALID_INCIDENT_TYPES))}")

    incident = {
        "incident_id": str(uuid.uuid4()),
        "timestamp": _validate_iso(data.get("timestamp"), "timestamp"),
        "incident_type": incident_type,
        "severity": _coerce_int(data.get("severity"), "severity", 1, 5, default=3),
        "description": _validate_str(data.get("description"), "description", 5000, required=True),
        "location": _validate_str(data.get("location"), "location", 200),
        "latitude": _coerce_float(data.get("latitude"), "latitude", -90.0, 90.0),
        "longitude": _coerce_float(data.get("longitude"), "longitude", -180.0, 180.0),
        "persons_involved": _safe_list(data.get("persons_involved"), "persons_involved", 25, 120),
        "badge_numbers": _safe_list(data.get("badge_numbers"), "badge_numbers", 25, 40),
        "witness_contacts": _safe_list(data.get("witness_contacts"), "witness_contacts", 25, 200),
        "media": _validate_media(data.get("media")),
    }

    session["incidents"].append(incident)
    for media in incident["media"]:
        entry = deepcopy(media)
        entry["incident_id"] = incident["incident_id"]
        entry["added_at"] = utc_now_iso()
        session["media_manifest"].append(entry)

    save_session(session)
    return incident


def send_alert(payload: Any) -> Dict[str, Any]:
    data = _ensure_dict(payload)
    session_id = _validate_str(data.get("session_id"), "session_id", 36, required=True)
    session = load_session(session_id)

    providers = data.get("providers") or ["sms"]
    if not isinstance(providers, list) or not providers:
        raise ValidationError("providers must be a non-empty list")

    clean_providers = []
    for i, p in enumerate(providers):
        provider = _validate_str(p, f"providers[{i}]", 20, required=True).lower()
        if provider not in VALID_ALERT_PROVIDERS:
            raise ValidationError(f"provider '{provider}' is not supported")
        clean_providers.append(provider)

    recipients = data.get("recipients")
    if recipients is None:
        recipients = [c.get("target") for c in session.get("metadata", {}).get("trusted_contacts", []) if c.get("target")]
    if not isinstance(recipients, list) or not recipients:
        raise ValidationError("recipients must be a non-empty list or available trusted_contacts")

    clean_recipients = []
    for i, r in enumerate(recipients):
        clean_recipients.append(_validate_str(r, f"recipients[{i}]", 160, required=True))

    dispatches = []
    for provider in clean_providers:
        env_name = "FIELD_SHIELD_SMS_WEBHOOK_URL" if provider == "sms" else "FIELD_SHIELD_SIGNAL_WEBHOOK_URL"
        endpoint = os.environ.get(env_name, "").strip()
        dispatches.append(
            {
                "provider": provider,
                "configured": bool(endpoint),
                "endpoint_hint": endpoint[:60] if endpoint else None,
                "status": "stubbed",
                # TODO(security): sign outbound alert payloads and enforce relay auth.
            }
        )

    alert = {
        "alert_id": str(uuid.uuid4()),
        "timestamp": _validate_iso(data.get("timestamp"), "timestamp"),
        "alert_type": _validate_str(data.get("alert_type") or "distress", "alert_type", 40, required=True).lower(),
        "message": _validate_str(data.get("message") or "Emergency alert from Field Shield session.", "message", 2000, required=True),
        "providers": clean_providers,
        "recipients": clean_recipients,
        "dispatches": dispatches,
    }

    session["alerts_sent"].append(alert)
    save_session(session)
    return alert


def _summary_text(session: Dict[str, Any]) -> str:
    lines = [
        "FIELD SHIELD LEGAL PACKET SUMMARY",
        "================================",
        f"Session ID: {session.get('session_id', '')}",
        f"Created (UTC): {session.get('created_at', '')}",
        f"Updated (UTC): {session.get('updated_at', '')}",
        f"Organizer Alias: {session.get('metadata', {}).get('organizer_alias', '')}",
        f"Start Location: {session.get('metadata', {}).get('start_location', '')}",
        "",
        f"Check-ins: {len(session.get('checkins', []))}",
        f"Incidents: {len(session.get('incidents', []))}",
        f"Media Items: {len(session.get('media_manifest', []))}",
        f"Alerts Sent: {len(session.get('alerts_sent', []))}",
        "",
        "Incident Timeline:",
    ]

    incidents = session.get("incidents", [])
    if not incidents:
        lines.append("- No incidents reported.")
    for idx, inc in enumerate(incidents, start=1):
        lines.append(
            f"{idx}. [{inc.get('timestamp','')}] {inc.get('incident_type','')} (severity {inc.get('severity','')}) @ {inc.get('location','')}: {inc.get('description','')}"
        )

    lines += ["", "Alerts:"]
    alerts = session.get("alerts_sent", [])
    if not alerts:
        lines.append("- No alerts sent.")
    for idx, alert in enumerate(alerts, start=1):
        lines.append(
            f"{idx}. [{alert.get('timestamp','')}] {alert.get('alert_type','')} to {len(alert.get('recipients', []))} recipients via {', '.join(alert.get('providers', []))}"
        )

    lines += [
        "",
        "Notes:",
        "- JSON and plain text exports are generated for legal handoff.",
        "- TODO(security): add tamper-evident signatures + chain-of-custody hashes.",
    ]
    return "\n".join(lines)


def generate_packet(session_id: str) -> Dict[str, Any]:
    session = load_session(session_id)
    packet = {
        "packet_version": "0.1",
        "generated_at": utc_now_iso(),
        "session": session,
        "counts": {
            "checkins": len(session.get("checkins", [])),
            "incidents": len(session.get("incidents", [])),
            "media_manifest": len(session.get("media_manifest", [])),
            "alerts_sent": len(session.get("alerts_sent", [])),
        },
    }
    text_summary = _summary_text(session)

    packet_dir = _root() / "packets"
    json_path = packet_dir / f"{session_id}.json"
    txt_path = packet_dir / f"{session_id}.txt"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2, ensure_ascii=False)
    with txt_path.open("w", encoding="utf-8") as f:
        f.write(text_summary)

    packet["exports"] = {
        "json_path": str(json_path),
        "txt_path": str(txt_path),
        "pdf_path": None,
        "pdf_status": "not_generated",
        "pdf_note": "PDF dependencies not configured; JSON + TXT generated.",
    }

    return {"packet": packet, "text_summary": text_summary}
