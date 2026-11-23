"""Isolated local budget-reservation experiment; NOT the PHAGE authority engine."""
import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def integer(value, name):
    if type(value) is not int or value < 0 or value > 2**53 - 1:
        raise ValueError(f"{name} must be a nonnegative safe integer")
    return value


def string(value, name):
    if type(value) is not str or not value.strip() or len(value) > 200:
        raise ValueError(f"{name} must be a nonempty string (max 200 characters)")
    return value


def validate_policy(p):
    keys = {"id", "agents", "actions", "targets", "currency", "start", "end", "per_action", "total", "review_above"}
    if type(p) is not dict or set(p) != keys:
        raise ValueError("policy fields do not match the supported schema")
    for key in ["id", "currency"]:
        string(p[key], key)
    for key in ["agents", "actions", "targets"]:
        if type(p[key]) is not list or not 1 <= len(p[key]) <= 100:
            raise ValueError(f"{key} must contain 1 to 100 exact values")
        for v in p[key]:
            string(v, key)
    for key in ["start", "end", "per_action", "total", "review_above"]:
        integer(p[key], key)
    if p["end"] <= p["start"] or p["per_action"] > p["total"] or p["review_above"] > p["per_action"]:
        raise ValueError("invalid time window or budget thresholds")
    return p


class Guard:
    def __init__(self, path, clock=time.time):
        self.path, self.clock = str(path), clock

    def connection(self):
        c = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        c.row_factory = sqlite3.Row
        return c

    def initialize(self):
        c = self.connection()
        try:
            c.executescript('''
                CREATE TABLE IF NOT EXISTS policies(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reservations(
                  policy_id TEXT NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL,
                  amount INTEGER NOT NULL, created_at INTEGER NOT NULL,
                  PRIMARY KEY(policy_id, request_id));
                CREATE TABLE IF NOT EXISTS audit(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER NOT NULL,
                  policy_id TEXT NOT NULL, request_id TEXT NOT NULL,
                  digest TEXT NOT NULL, decision TEXT NOT NULL, reason TEXT NOT NULL);
            ''')
        finally:
            c.close()

    def add_policy(self, policy):
        """Trusted local operator only. Existing policy IDs cannot be overwritten."""
        body = canonical(validate_policy(policy))
        c = self.connection()
        try:
            c.execute("BEGIN IMMEDIATE")
            existing = c.execute("SELECT body FROM policies WHERE id=?", (policy["id"],)).fetchone()
            if existing and existing[0] != body:
                raise ValueError("policy ID is immutable; use a new authorization and time window")
            c.execute("INSERT OR IGNORE INTO policies VALUES (?,?)", (policy["id"], body))
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def reserve(self, request):
        keys = {"policy_id", "request_id", "agent", "action", "target", "currency", "amount"}
        if type(request) is not dict or set(request) != keys:
            raise ValueError("request fields do not match the supported schema")
        for key in keys - {"amount"}:
            string(request[key], key)
        integer(request["amount"], "amount")
        digest = hashlib.sha256(canonical(request).encode()).hexdigest()
        c = self.connection()
        try:
            # One SQLite write transaction covers sum inspection AND reservation.
            c.execute("BEGIN IMMEDIATE")
            now = int(self.clock())
            row = c.execute("SELECT body FROM policies WHERE id=?", (request["policy_id"],)).fetchone()
            policy = json.loads(row[0]) if row else None
            reason, decision, reused = "UNKNOWN_POLICY", "DENY", False
            total = 0
            if policy:
                total = c.execute("SELECT COALESCE(SUM(amount),0) FROM reservations WHERE policy_id=?", (policy["id"],)).fetchone()[0]
                if not policy["start"] <= now < policy["end"]:
                    reason = "OUTSIDE_WINDOW"
                elif request["agent"] not in policy["agents"]:
                    reason = "AGENT_OUT_OF_SCOPE"
                elif request["action"] not in policy["actions"]:
                    reason = "ACTION_OUT_OF_SCOPE"
                elif request["target"] not in policy["targets"]:
                    reason = "TARGET_OUT_OF_SCOPE"
                elif request["currency"] != policy["currency"]:
                    reason = "CURRENCY_MISMATCH"
                elif request["amount"] > policy["per_action"]:
                    reason = "PER_ACTION_LIMIT"
                else:
                    prior = c.execute("SELECT digest FROM reservations WHERE policy_id=? AND request_id=?", (policy["id"], request["request_id"])).fetchone()
                    if prior:
                        if prior[0] == digest:
                            decision, reason, reused = "RESERVED", "EXISTING_RESERVATION_DO_NOT_REEXECUTE", True
                        else:
                            reason = "REQUEST_ID_CONFLICT"
                    elif request["amount"] > policy["review_above"]:
                        decision, reason = "REVIEW_REQUIRED", "NO_APPROVAL_VERIFIER_IMPLEMENTED"
                    elif request["amount"] > policy["total"] - total:
                        reason = "AGGREGATE_LIMIT"
                    else:
                        c.execute("INSERT INTO reservations VALUES (?,?,?,?,?)", (policy["id"], request["request_id"], digest, request["amount"], now))
                        total += request["amount"]
                        decision, reason = "RESERVED", "LOCAL_BUDGET_RESERVED_NOT_EXECUTED"
            c.execute("INSERT INTO audit(at,policy_id,request_id,digest,decision,reason) VALUES (?,?,?,?,?,?)", (now, request["policy_id"], request["request_id"], digest, decision, reason))
            audit_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            c.commit()
            return {"decision": decision, "reason": reason, "reused": reused,
                    "audit_id": audit_id, "reserved_total": total,
                    "remaining": policy["total"] - total if policy else None,
                    "executes_external_action": False}
        except Exception:
            c.rollback()
            raise  # Storage failures never become an allow/reserved decision.
        finally:
            c.close()

    def ledger(self):
        c = self.connection()
        try:
            return [dict(r) for r in c.execute("SELECT * FROM audit ORDER BY seq")]
        finally:
            c.close()


def load_json(path):
    if Path(path).stat().st_size > 65536:
        raise ValueError("JSON file exceeds 64 KiB")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="guard.sqlite")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("ledger")
    sub.add_parser("add-policy").add_argument("file")
    sub.add_parser("reserve").add_argument("file")
    args = parser.parse_args()
    guard = Guard(args.db)
    try:
        if args.command == "init":
            guard.initialize()
            result = {"initialized": True}
        elif args.command == "add-policy":
            guard.add_policy(load_json(args.file))
            result = {"policy_added": True}
        elif args.command == "reserve":
            result = guard.reserve(load_json(args.file))
        else:
            result = guard.ledger()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, sqlite3.Error) as error:
        print(json.dumps({"decision": "ERROR_NO_PERMISSION_GRANTED", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
