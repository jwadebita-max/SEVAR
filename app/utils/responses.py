from flask import jsonify


def success(message="OK", data=None, status=200, **extra):
    payload = {"success": True, "message": message, "data": data or {}}
    payload.update(extra)
    return jsonify(payload), status


def error(message="Error", status=400, errors=None):
    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return jsonify(payload), status
