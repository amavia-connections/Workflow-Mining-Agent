"""
Dynamic Field Mapping Engine for Enterprise ITSM Systems.
AI Builder Cup 2026.

Maps arbitrary JSON payloads from Jira, ServiceNow, or custom ticketing APIs
into canonical Workflow Mining Agent ticket structures.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from backend.models.connector import FieldMappingConfig


def _get_nested_val(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Helper to traverse dot-notated paths like 'fields.summary' or 'assigned_to.display_value'."""
    if not path or not data:
        return default
    parts = path.split(".")
    curr = data
    for p in parts:
        if isinstance(curr, dict) and p in curr:
            curr = curr[p]
        else:
            return default
    return curr if curr is not None else default


def _parse_datetime(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    val_str = str(val).strip()
    # Try common enterprise date formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            continue
    # Fallback default
    try:
        return datetime.fromisoformat(val_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()


class FieldMapper:
    def __init__(self, config: FieldMappingConfig = None):
        self.config = config or FieldMappingConfig()

    def map_jira_issue(self, raw_issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes a Jira Cloud/Data Center issue JSON into a canonical ticket dict.
        """
        key = raw_issue.get("key") or raw_issue.get("id") or "JIRA-UNKNOWN"
        fields = raw_issue.get("fields", {})

        title = _get_nested_val(raw_issue, self.config.title_field) or _get_nested_val(fields, "summary", "Untitled Jira Issue")
        desc = _get_nested_val(raw_issue, self.config.description_field) or _get_nested_val(fields, "description", "")
        if isinstance(desc, dict):
            # Atlassian Document Format (ADF) handling: extract text nodes
            desc = self._extract_text_from_adf(desc)

        # Resolution notes extraction: check explicit customfield, fallback to resolution or comments
        res_notes = ""
        for custom_field, canonical_target in self.config.custom_field_rules.items():
            if canonical_target == "resolution_notes":
                res_notes = _get_nested_val(fields, custom_field, "")
                break

        if not res_notes:
            res_notes = _get_nested_val(fields, self.config.resolution_notes_field, "")
            if not res_notes:
                # Check resolution description or last comment
                res_obj = fields.get("resolution")
                if isinstance(res_obj, dict):
                    res_notes = res_obj.get("description", res_obj.get("name", ""))
                
                # Check comments
                comment_container = fields.get("comment", {})
                if isinstance(comment_container, dict) and "comments" in comment_container:
                    comments = comment_container["comments"]
                    if comments and isinstance(comments, list):
                        last_c = comments[-1]
                        body = last_c.get("body", "")
                        if isinstance(body, dict):
                            body = self._extract_text_from_adf(body)
                        res_notes = f"Resolution Comment: {body}"

        category = _get_nested_val(fields, "issuetype.name") or _get_nested_val(fields, "project.name", "IT Support")
        priority = _get_nested_val(fields, "priority.name", "Medium")
        assignee = _get_nested_val(fields, "assignee.displayName") or _get_nested_val(fields, "assignee.name", "Unassigned")
        status = _get_nested_val(fields, "status.name", "Closed")

        created_dt = _parse_datetime(_get_nested_val(fields, self.config.created_at_field) or fields.get("created")) or datetime.utcnow()
        resolved_dt = _parse_datetime(_get_nested_val(fields, self.config.resolved_at_field) or fields.get("resolutiondate"))

        # Handling minutes calculation
        timespent_seconds = fields.get("timespent")
        handling_minutes = 20.0
        if timespent_seconds and isinstance(timespent_seconds, (int, float)):
            handling_minutes = round(timespent_seconds / 60.0, 1)
        elif resolved_dt and created_dt and resolved_dt > created_dt:
            # Fallback to duration (capped at 120 mins for realism if ticket was open overnight)
            diff_mins = (resolved_dt - created_dt).total_seconds() / 60.0
            handling_minutes = min(round(diff_mins, 1), 120.0)

        return {
            "ticket_id": key,
            "title": str(title),
            "description": str(desc),
            "category": str(category),
            "priority": str(priority),
            "created_at": created_dt.isoformat(),
            "resolved_at": resolved_dt.isoformat() if resolved_dt else None,
            "assignee": str(assignee),
            "resolution_notes": str(res_notes or "Resolved per standard IT support procedure."),
            "status": str(status),
            "estimated_active_handling_minutes": float(handling_minutes)
        }

    def map_servicenow_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes a ServiceNow Incident / Change / Request record into a canonical ticket dict.
        """
        ticket_id = raw_record.get("number") or raw_record.get("sys_id") or "SNOW-UNKNOWN"
        title = raw_record.get("short_description") or raw_record.get("summary") or "Untitled Incident"
        desc = raw_record.get("description") or ""

        # Close notes & Work notes
        res_notes = raw_record.get("close_notes") or ""
        if not res_notes:
            res_notes = raw_record.get("work_notes") or raw_record.get("comments_and_work_notes") or ""

        # Priority & Category mapping
        priority_val = raw_record.get("priority", "3")
        priority_map = {"1": "Critical", "2": "High", "3": "Medium", "4": "Low", "5": "Planning"}
        priority = priority_map.get(str(priority_val), str(priority_val))

        category = raw_record.get("category") or raw_record.get("subcategory") or "Service Desk"
        assignee_obj = raw_record.get("assigned_to", {})
        assignee = assignee_obj.get("display_value") if isinstance(assignee_obj, dict) else str(assignee_obj or "Service Desk Team")
        status = raw_record.get("state") or raw_record.get("incident_state") or "Closed"

        created_dt = _parse_datetime(raw_record.get("sys_created_on") or raw_record.get("opened_at")) or datetime.utcnow()
        resolved_dt = _parse_datetime(raw_record.get("resolved_at") or raw_record.get("closed_at") or raw_record.get("sys_updated_on"))

        # Time worked in ServiceNow
        time_worked = raw_record.get("time_worked") or raw_record.get("calendar_duration")
        handling_minutes = 25.0
        if time_worked is not None:
            try:
                handling_minutes = round(float(time_worked) / 60.0, 1)
            except (ValueError, TypeError):
                if resolved_dt and created_dt and resolved_dt > created_dt:
                    diff_mins = (resolved_dt - created_dt).total_seconds() / 60.0
                    handling_minutes = min(round(diff_mins, 1), 120.0)
        elif resolved_dt and created_dt and resolved_dt > created_dt:
            diff_mins = (resolved_dt - created_dt).total_seconds() / 60.0
            handling_minutes = min(round(diff_mins, 1), 120.0)

        return {
            "ticket_id": str(ticket_id),
            "title": str(title),
            "description": str(desc),
            "category": str(category),
            "priority": str(priority),
            "created_at": created_dt.isoformat(),
            "resolved_at": resolved_dt.isoformat() if resolved_dt else None,
            "assignee": str(assignee),
            "resolution_notes": str(res_notes or "Closed incident following standard remediation workflow."),
            "status": str(status),
            "estimated_active_handling_minutes": float(handling_minutes)
        }

    def _extract_text_from_adf(self, adf_node: Any) -> str:
        """
        Recursively parses Atlassian Document Format (ADF) JSON into structured,
        human-readable text preserving headings, paragraphs, and bullet lists.
        """
        if not isinstance(adf_node, dict):
            if isinstance(adf_node, str) and ('"type"' in adf_node and '"content"' in adf_node):
                try:
                    import json
                    parsed = json.loads(adf_node)
                    if isinstance(parsed, dict):
                        return self._extract_text_from_adf(parsed)
                except Exception:
                    pass
            return str(adf_node) if adf_node is not None else ""

        node_type = adf_node.get("type")

        # 1. Text node with marks (bold, italic, code)
        if node_type == "text":
            text = adf_node.get("text", "")
            for mark in adf_node.get("marks", []):
                m_type = mark.get("type")
                if m_type == "strong":
                    text = f"**{text}**"
                elif m_type == "em":
                    text = f"*{text}*"
                elif m_type == "code":
                    text = f"`{text}`"
            return text

        if node_type == "hardBreak":
            return "\n"

        content = adf_node.get("content", [])

        # 2. Document root
        if node_type == "doc":
            parts = [self._extract_text_from_adf(c).strip() for c in content]
            return "\n\n".join(p for p in parts if p)

        # 3. Headings (e.g. Context, Scope / To do)
        if node_type == "heading":
            heading_text = "".join(self._extract_text_from_adf(c) for c in content).strip()
            return f"### {heading_text}"

        # 4. Paragraphs
        if node_type == "paragraph":
            return "".join(self._extract_text_from_adf(c) for c in content).strip()

        # 5. Bullet Lists
        if node_type == "bulletList":
            items = []
            for item in content:
                if item.get("type") == "listItem":
                    item_text = "\n".join(self._extract_text_from_adf(c).strip() for c in item.get("content", []))
                    items.append(f"• {item_text}")
                else:
                    items.append(f"• {self._extract_text_from_adf(item).strip()}")
            return "\n".join(items)

        # 6. Ordered Lists
        if node_type == "orderedList":
            items = []
            for i, item in enumerate(content, 1):
                if item.get("type") == "listItem":
                    item_text = "\n".join(self._extract_text_from_adf(c).strip() for c in item.get("content", []))
                    items.append(f"{i}. {item_text}")
                else:
                    items.append(f"{i}. {self._extract_text_from_adf(item).strip()}")
            return "\n".join(items)

        # 7. Code Blocks
        if node_type == "codeBlock":
            code = "".join(self._extract_text_from_adf(c) for c in content)
            return f"```\n{code}\n```"

        # 8. List items
        if node_type == "listItem":
            return "\n".join(self._extract_text_from_adf(c).strip() for c in content)

        # 9. Blockquote
        if node_type == "blockquote":
            quote_text = "\n".join(self._extract_text_from_adf(c).strip() for c in content)
            return f"> {quote_text}"

        # Fallback for nested containers
        sub_texts = [self._extract_text_from_adf(c).strip() for c in content]
        return " ".join(t for t in sub_texts if t)

