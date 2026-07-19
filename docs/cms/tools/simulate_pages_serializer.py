from __future__ import annotations
from copy import deepcopy


def sanitize_object(value):
    """Mirror the current Pages CMS recursive empty-value sanitizer."""
    def empty(v):
        return v is None or v == ""

    if isinstance(value, list):
        mapped = [sanitize_object(v) if isinstance(v, (dict, list)) else v for v in value]
        return [v for v in mapped if not empty(v)]

    if isinstance(value, dict):
        output = dict(value)
        for key in list(output):
            if isinstance(output[key], (dict, list)):
                output[key] = sanitize_object(output[key])
            child = output[key]
            if (
                isinstance(child, list) and all(empty(v) for v in child)
            ) or (
                isinstance(child, dict) and not child
            ) or empty(child):
                del output[key]
        return output

    return value


def deep_merge(existing, submitted):
    """Mirror merge semantics: nested objects merge, submitted arrays replace."""
    if isinstance(existing, dict) and isinstance(submitted, dict):
        result = deepcopy(existing)
        for key, value in submitted.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result
    return deepcopy(submitted)


def expand_field(field, config):
    if "component" not in field:
        return deepcopy(field)
    expanded = deepcopy(config["components"][field["component"]])
    expanded.update({key: deepcopy(value) for key, value in field.items() if key != "component"})
    return expanded


def default_value(field):
    if "default" in field:
        return deepcopy(field["default"])
    if field.get("list"):
        return []
    if field.get("type") == "object":
        return {}
    if field.get("type") == "boolean":
        return False
    if field.get("type") == "number":
        return 0
    return ""


def form_submission(data, fields, config):
    output = {}
    for raw in fields:
        field = expand_field(raw, config)
        name = field["name"]
        value = data.get(name)
        if field.get("list"):
            if isinstance(value, list):
                if field.get("type") == "object" or field.get("component"):
                    output[name] = [
                        form_submission(item or {}, field.get("fields", []), config)
                        for item in value
                    ]
                else:
                    output[name] = deepcopy(value)
            else:
                output[name] = []
        elif field.get("type") == "object":
            if isinstance(value, dict):
                output[name] = form_submission(value, field.get("fields", []), config)
            elif field.get("required"):
                output[name] = form_submission({}, field.get("fields", []), config)
            else:
                output[name] = {}
        else:
            output[name] = default_value(field) if value is None else deepcopy(value)
    return output


def schema_for(config, name):
    return next(item for item in config["content"] if item["name"] == name)


def hosted_update(record, schema, config):
    submitted = form_submission(record, schema["fields"], config)
    merged = (
        deep_merge(record, submitted)
        if config.get("settings", {}).get("content", {}).get("merge")
        else submitted
    )
    return sanitize_object(merged)


def hosted_create(record, schema, config):
    submitted = form_submission(record, schema["fields"], config)
    return sanitize_object(submitted)
