"""Dashboard server. Run with:  python app.py  (from the trading_bot folder)

Binds to 127.0.0.1 only — API keys and controls never leave your machine.
"""

import os
import time

from flask import Flask, jsonify, render_template, request, send_file

import store
from engine import ENGINE
from exchange import SUPPORTED_EXCHANGES, check_credentials
from strategies import STRATEGIES

app = Flask(__name__)

_LOCAL_ORIGINS = {"http://127.0.0.1:8300", "http://localhost:8300"}


@app.before_request
def _block_cross_origin_writes():
    """The server binds to 127.0.0.1, but any website open in the browser can
    still fire cross-origin POSTs at localhost. State-changing requests must
    come from our own dashboard page (or a non-browser client with no Origin)."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    origin = request.headers.get("Origin")
    if origin and origin not in _LOCAL_ORIGINS:
        return jsonify({"ok": False, "detail": "cross-origin request blocked"}), 403
    return None


@app.get("/")
def dashboard():
    return render_template("dashboard.html")


@app.get("/ai")
def ai_surface():
    """The ANDX AI assistant surface, served same-origin so its live link can
    read /api/state (and close sim positions) from the running engine."""
    path = os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "andi_preview.html"))
    return send_file(path)


@app.get("/api/state")
def state():
    snap = ENGINE.snapshot()
    cfg = store.load_config()
    snap["config"] = cfg
    snap["exchanges"] = SUPPORTED_EXCHANGES
    snap["strategies"] = {name: cls.label for name, cls in STRATEGIES.items()}
    snap["saved_key"] = store.masked_key(cfg["exchange"])
    return jsonify(snap)


@app.post("/api/settings")
def save_settings():
    body = request.get_json(force=True)
    cfg = store.load_config()
    if ENGINE.running:
        return jsonify({"ok": False, "detail": "stop the bot before changing settings"}), 400
    for key in ("exchange", "timeframe", "strategy", "mode"):
        if key in body:
            cfg[key] = body[key]
    if "symbols" in body:
        symbols = [s.strip() for s in body["symbols"] if s.strip()]
        if symbols:
            cfg["symbols"] = symbols
    if "paper_balance" in body:
        cfg["paper_balance"] = float(body["paper_balance"])
    if "poll_seconds" in body:
        cfg["poll_seconds"] = int(body["poll_seconds"])
    if "risk" in body:
        cfg["risk"] = {**cfg["risk"], **{k: v for k, v in body["risk"].items() if v not in ("", None)}}
    store.save_config(cfg)
    return jsonify({"ok": True})


@app.post("/api/keys")
def save_keys():
    body = request.get_json(force=True)
    exchange = body.get("exchange") or store.load_config()["exchange"]
    api_key = body.get("api_key", "").strip()
    api_secret = body.get("api_secret", "").strip()
    api_password = body.get("api_password", "").strip()
    username = body.get("username", "").strip()
    if not api_key or not api_secret:
        return jsonify({"ok": False, "detail": "API key and secret are both required"}), 400
    store.save_secrets(exchange, api_key, api_secret, api_password, username)
    result = check_credentials(
        exchange,
        {"api_key": api_key, "api_secret": api_secret,
         "api_password": api_password, "username": username},
        testnet=(store.load_config()["mode"] == "testnet"),
    )
    result["masked"] = store.masked_key(exchange)
    return jsonify(result)


@app.delete("/api/keys")
def delete_keys():
    exchange = request.args.get("exchange") or store.load_config()["exchange"]
    store.delete_secrets(exchange)
    return jsonify({"ok": True})


@app.post("/api/start")
def start():
    cfg = store.load_config()
    if cfg["mode"] == "live":
        confirmed = (request.get_json(silent=True) or {}).get("confirm_live")
        if not confirmed:
            return jsonify({"ok": False, "detail": "live mode requires confirmation",
                            "needs_confirmation": True}), 400
    ok, detail = ENGINE.start()
    return jsonify({"ok": ok, "detail": detail}), (200 if ok else 400)


@app.post("/api/stop")
def stop():
    flatten = (request.get_json(silent=True) or {}).get("flatten", False)
    ENGINE.stop(flatten=flatten)
    return jsonify({"ok": True})


@app.post("/api/slow_mode")
def slow_mode():
    on = bool((request.get_json(silent=True) or {}).get("on"))
    cfg = store.load_config()
    cfg["slow_mode"] = on
    store.save_config(cfg)
    restarted, detail = False, ""
    if ENGINE.running:
        ENGINE.stop(flatten=False)
        restarted, detail = ENGINE.start()
        if not restarted:
            ENGINE.log(f"restart after slow-mode toggle failed: {detail}", "error")
    return jsonify({"ok": True, "slow_mode": on, "restarted": restarted,
                    "detail": detail})


@app.post("/api/reset_paper")
def reset_paper():
    """Explicit practice-account reset — the ONLY way paper progress clears
    besides changing the configured starting balance."""
    cfg = store.load_config()
    if ENGINE.running and cfg.get("mode") == "paper":
        return jsonify({"ok": False,
                        "detail": "stop the bot first, then reset"}), 400
    store.reset_paper_state()
    ENGINE.log("practice account reset — next start begins fresh from the "
               "configured paper balance")
    return jsonify({"ok": True})


@app.post("/api/market_mode")
def market_mode():
    on = bool((request.get_json(silent=True) or {}).get("derivatives"))
    cfg = store.load_config()
    cfg["derivatives"] = on
    store.save_config(cfg)
    restarted, detail = False, ""
    if ENGINE.running:
        # switching markets closes everything first so no position is orphaned
        ENGINE.stop(flatten=True)
        restarted, detail = ENGINE.start()
        if not restarted:
            ENGINE.log(f"restart after market switch failed: {detail}", "error")
    return jsonify({"ok": True, "derivatives": on, "restarted": restarted,
                    "detail": detail})


@app.post("/api/trade_mode")
def trade_mode():
    body = request.get_json(silent=True) or {}
    result = ENGINE.set_trade_mode(body.get("mode", ""))
    ok = "error" not in result
    return jsonify({"ok": ok, **result}), (200 if ok else 400)


@app.post("/api/proposal")
def proposal_action():
    body = request.get_json(silent=True) or {}
    pid, action = body.get("id"), str(body.get("action", "")).lower()
    if action == "approve":
        result = ENGINE.approve_proposal(pid)
    elif action == "decline":
        result = ENGINE.decline_proposal(pid)
    else:
        return jsonify({"ok": False, "error": "action must be approve or decline"}), 400
    ok = "error" not in result
    return jsonify({"ok": ok, **result}), (200 if ok else 400)


@app.post("/api/routine")
def routine_action():
    body = request.get_json(silent=True) or {}
    try:
        rid = int(body.get("id"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "detail": "bad routine id"}), 400
    action = str(body.get("action", "")).lower()
    if action == "pause":
        return jsonify({"ok": store.set_routine_enabled(rid, False)})
    if action == "resume":
        ok = store.set_routine_enabled(rid, True)
        if ok:
            # resuming a long-paused routine must NOT fire it instantly —
            # re-anchor a past-due clock to the next scheduled slot
            r = next((x for x in store.list_routines() if x["id"] == rid), None)
            if r and r.get("next_run_ts") and r["next_run_ts"] <= time.time():
                store.reschedule_routine(
                    rid, ENGINE.next_routine_run(r["schedule"], time.time()))
        return jsonify({"ok": ok})
    if action == "delete":
        return jsonify({"ok": store.delete_routine(rid)})
    return jsonify({"ok": False, "detail": "action must be pause, resume, or delete"}), 400


@app.delete("/api/alert")
def delete_alert():
    try:
        alert_id = int(request.args.get("id", ""))
    except ValueError:
        return jsonify({"ok": False, "detail": "bad alert id"}), 400
    return jsonify({"ok": store.delete_alert(alert_id)})


@app.get("/api/ai_status")
def ai_status():
    import ai_brain
    key = ai_brain.get_api_key()
    return jsonify({"ok": True, "has_key": bool(key),
                    "masked": ai_brain.masked_key(), "model": ai_brain.MODEL})


@app.post("/api/ai_key")
def ai_key():
    body = request.get_json(force=True)
    key = (body.get("api_key") or "").strip()
    if not key.startswith("sk-ant-") or len(key) < 20:
        return jsonify({"ok": False, "detail": "that doesn't look like an Anthropic key (sk-ant-…)"}), 400
    store.save_secrets("anthropic", key, "-")
    import ai_brain
    return jsonify({"ok": True, "masked": ai_brain.masked_key()})


@app.post("/api/chat")
def ai_chat():
    import ai_brain
    body = request.get_json(force=True) or {}
    messages = body.get("messages") or []
    if not isinstance(messages, list):
        return jsonify({"ok": False, "error": "bad_request"}), 400
    result = ai_brain.chat(messages)
    status = 200 if result.get("ok") else (401 if result.get("error") in ("no_key", "bad_key") else 502)
    return jsonify(result), status


@app.post("/api/close")
def close_position():
    symbol = (request.get_json(force=True)).get("symbol", "")
    try:
        ok = ENGINE.close_position(symbol)
        return jsonify({"ok": ok})
    except Exception as e:
        ENGINE.log(f"manual close failed for {symbol}: {e}", "error")
        return jsonify({"ok": False, "detail": str(e)}), 400


if __name__ == "__main__":
    print("\n  ANDX Trading Bot — dashboard: http://127.0.0.1:8300\n")
    app.run(host="127.0.0.1", port=8300, debug=False)
