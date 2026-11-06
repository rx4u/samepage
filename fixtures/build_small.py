"""Write fixtures/small: a hand-specified 20-project store used by unit tests.

Run from the repo root: python3 fixtures/build_small.py
Every row is written explicitly below so each edge case is visible. Ids are
uuid5 values, so reruns produce identical files.
"""
import os
import shutil
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sp.frontmatter import emit  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "small")
NS = uuid.UUID("6d1c5b1e-6a8e-4c43-9a43-5a3c1f2d0b11")
T0 = "2026-11-01T09:00:00Z"


def uid(name):
    return str(uuid.uuid5(NS, name))


def write(rel, fields, body=""):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(emit(fields, body))


TAGS = {"nextjs": "Next.js", "supabase": "Supabase", "ai": "AI", "design-system": "Design system",
        "python": "Python", "notion": "Notion", "landing": "Landing page"}

# slug, name, status, type, tags, extras
PROJECTS = [
    ("general", "General", "active", "other", [], {}),
    ("halcyon", "Halcyon", "shipped", "product", ["nextjs", "supabase", "ai"],
     {"role": "Design and build", "outcome": "Live with 40 beta users", "live_url": "https://halcyon.example.com",
      "repo_url": "https://github.com/asha-rao/halcyon", "shipped_on": "2026-09-14"}),
    ("ledger-lite", "Ledger Lite", "shipped", "product", ["nextjs", "supabase"],
     {"live_url": "https://ledger.example.com", "shipped_on": "2026-06-02"}),
    ("ai", "AI Notes", "active", "tool", ["ai", "python"], {"problem": "Slug equals a tag slug on purpose"}),
    ("pearl-dental", "Pearl Dental", "shipped", "client_site", ["landing"],
     {"live_url": "https://pearl.example.com", "shipped_on": "2026-08-25"}),
    ("north-star-ds", "North Star DS", "active", "concept", ["design-system"], {}),
    ("runsheet", "Runsheet", "parked", "product", ["nextjs"], {}),
    ("freightflow", "FreightFlow", "archived", "concept", ["design-system"],
     {"archived_at": "2026-10-01T10:00:00Z", "outcome": "Concept closed, proof kept"}),
    ("kiosk-ev", "EV Kiosk", "shipped", "concept", ["design-system"], {"shipped_on": "2026-10-20"}),
    ("precis", "Précis", "active", "product", ["ai", "nextjs"], {"problem": "Legal précis: unicode in names"}),
    ("vault-cli", "Vault CLI", "idea", "tool", ["python"], {}),
    ("lahari", "Lahari Collections", "shipped", "client_site", ["landing", "nextjs"],
     {"live_url": "https://lahari.example.com", "shipped_on": "2026-05-19"}),
    ("ship-gate", "Ship Gate", "shipped", "skill", ["python"], {"repo_url": "https://github.com/asha-rao/ship-gate"}),
    ("dagboard", "Dagboard", "shipped", "tool", ["nextjs", "ai"], {"live_url": "https://dagboard.example.com"}),
    ("notion-sync", "Notion Sync", "unknown", "tool", ["notion"], {}),
    ("rams-kit", "Rams Kit", "active", "concept", ["design-system"], {}),
    ("solar-grid", "SolarGrid", "parked", "concept", ["design-system"], {}),
    ("cv-heap", "CV Heap", "archived", "product", [], {"archived_at": "2026-07-01T10:00:00Z"}),
    ("quote-bot", "Quote Bot", "active", "product", ["ai"], {"one_liner_override": "Answers quotes: fast, with a colon"}),
    ("wheelhouse", "Wheelhouse", "shipped", "client_site", ["nextjs", "supabase"], {"shipped_on": "2026-09-28"}),
]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    write("store.md", {"schema_version": "1.0", "backend": "github", "owner_handle": "asha-rao",
                       "created_at": T0, "updated_at": T0})
    write("profile.md", {"display_name": "Asha Rao", "headline": "Product engineer who designs and ships",
                         "location": "Pune, India", "bio": "Builds small products end to end.",
                         "voice": "Direct, lowercase, no fluff", "created_at": T0, "updated_at": T0},
          "Longer bio for humans. Never parsed.")
    for i, (label, url) in enumerate([("Portfolio", "https://asha.example.com"),
                                      ("GitHub", "https://github.com/asha-rao")], start=1):
        lid = uid("link-%d" % i)
        write("profile/links/%s.md" % lid[:8], {"id": lid, "label": label, "url": url, "sort_order": i,
                                                 "created_at": T0})
    rules = [("Never use em dashes.", None, "true"), ("Prefer tables for comparisons.", None, "true"),
             ("Run tests before every commit.", "code", "true"), ("Keep chat replies short.", "chat", "true"),
             ("Old rule, paused.", None, "false")]
    for i, (rule, surface, active) in enumerate(rules):
        rid = uid("rule-%d" % i)
        write("rules/%s.md" % rid[:8], {"id": rid, "rule": rule, "surface": surface, "is_active": active,
                                        "created_at": "2026-11-01T09:%02d:00Z" % i, "updated_at": T0})
    for slug, label in TAGS.items():
        write("tags/%s.md" % slug, {"id": uid("tag-" + slug), "slug": slug, "label": label, "created_at": T0})
    for n, (slug, name, status, ptype, tags, extra) in enumerate(PROJECTS):
        extra = dict(extra)
        one_liner = extra.pop("one_liner_override", "%s, a %s" % (name, ptype.replace("_", " ")))
        fields = {"id": uid("project-" + slug), "slug": slug, "name": name, "status": status, "type": ptype,
                  "one_liner": one_liner}
        for key in ("problem", "role", "outcome", "live_url", "repo_url", "started_on", "shipped_on"):
            if key in extra:
                fields[key] = extra[key]
        fields["last_verified_at"] = T0
        if "archived_at" in extra:
            fields["archived_at"] = extra["archived_at"]
        fields["created_at"] = T0
        fields["updated_at"] = "2026-11-%02dT10:00:00Z" % (1 + n % 5)
        fields["tags"] = tags
        write("projects/%s.md" % slug, fields)
    # 40 ship events: 2 per non-general project, plus 2 on archived freightflow kept for proof.
    shippers = [p for p in PROJECTS if p[0] != "general"]
    count = 0
    kinds = ["shipped", "deployed", "launched", "milestone", "metric", "published"]
    for i in range(40):
        slug = shippers[i % len(shippers)][0]
        eid = uid("event-%d" % i)
        day = "2026-%02d-%02d" % (5 + i % 6, 1 + i % 27)
        fields = {"id": eid, "project": slug, "kind": kinds[i % len(kinds)],
                  "surface": ["code", "chat", "cowork"][i % 3], "summary": "Event %d on %s" % (i, slug)}
        if i % 3 != 0:
            fields["proof_url"] = "https://proof.example.com/%d" % i
        if kinds[i % len(kinds)] == "metric":
            fields.update({"metric_label": "signups", "metric_value": str(10 * i), "metric_unit": "users"})
        fields["occurred_at"] = day + "T08:00:00Z"
        fields["created_at"] = day + "T08:05:00Z"
        write("events/%s/%s-%s-%s.md" % (day[:4], day, slug, eid[:8]), fields)
        count += 1
    # 10 decisions, one supersede chain of 3 on halcyon.
    d = [uid("decision-%d" % i) for i in range(10)]
    chain = {0: (d[1], "superseded"), 1: (d[2], "superseded")}
    for i in range(10):
        slug = "halcyon" if i < 3 else shippers[i][0]
        day = "2026-10-%02d" % (1 + i)
        superseded_by, status = chain.get(i, (None, "accepted"))
        if i == 9:
            status = "reversed"
        fields = {"id": d[i], "project": slug, "status": status, "surface": "chat", "superseded_by": superseded_by,
                  "title": "Decision %d" % i, "reason": "Reason %d: fits the targets" % i,
                  "decided_at": day + "T12:00:00Z", "created_at": day + "T12:00:00Z", "updated_at": T0}
        write("decisions/%s/%s-%s.md" % (slug, day, d[i][:8]), fields,
              "Detail for decision %d.\n\nSecond paragraph." % i if i % 2 == 0 else "")
    # Design assets: approved system, draft, handoff bundle.
    assets = [("halcyon", "design_system", "approved", "code", "Halcyon tokens",
               {"tokens_repo_url": "https://github.com/asha-rao/halcyon", "tokens_path": "design/tokens.json"}),
              ("halcyon", "screen_set", "draft", "chat", "Onboarding screens", {}),
              ("north-star-ds", "handoff_bundle", "approved", "code", "Design handoff, no link", {})]
    for i, (slug, kind, status, surface, title, extra) in enumerate(assets):
        aid = uid("asset-%d" % i)
        fields = {"id": aid, "project": slug, "kind": kind, "status": status, "surface": surface, "title": title}
        fields.update(extra)
        fields.update({"created_at": T0, "updated_at": T0})
        write("design/%s/%s.md" % (slug, aid[:8]), fields)
    # 5 handoffs: open to code, open to chat, picked up, done, general.
    handoffs = [("halcyon", "chat", "code", "open", None, None),
                ("precis", "code", "chat", "open", None, None),
                ("quote-bot", "chat", "code", "picked_up", "2026-11-02T10:00:00Z", None),
                ("wheelhouse", "chat", "code", "done", "2026-11-02T10:00:00Z", "2026-11-03T10:00:00Z"),
                ("general", "cowork", "chat", "open", None, None)]
    for i, (slug, src, dst, status, picked, done) in enumerate(handoffs):
        hid = uid("handoff-%d" % i)
        write("handoffs/%s.md" % hid[:8],
              {"id": hid, "project": slug, "from_surface": src, "to_surface": dst, "status": status,
               "title": "Handoff %d for %s" % (i, slug), "created_at": "2026-11-0%dT09:00:00Z" % (i + 1),
               "picked_up_at": picked, "done_at": done},
              "## Brief\n\nBuild step %d.\n\n- keep it small\n- test it" % i)
    print("wrote fixtures/small: %d projects, %d events, 10 decisions, 3 design assets, 5 handoffs"
          % (len(PROJECTS), count))


if __name__ == "__main__":
    main()
