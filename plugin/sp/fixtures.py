"""`sp fixtures --perf --seed 42`: generate the perf store (test-data.md, ADR-0009).

Synthetic only. The same seed always produces the same files. Counts match
test-data.md exactly; the run prints them.
"""
import datetime
import os
import random
import shutil
import uuid

from .frontmatter import emit

NS = uuid.UUID("2f6b3c0a-9d4e-4b8a-8c1e-7a5d3e2f1b00")
COUNTS = {"profile": 1, "profile_link": 4, "preference": 24, "tag": 60, "project": 1000, "project_tag": 3200,
          "ship_event": 5000, "decision": 1500, "design_asset": 400, "handoff": 300, "index_build": 50}
WORDS = ("amber atlas birch cobalt delta ember fable garnet harbor indigo juniper kestrel lumen maple nimbus onyx "
         "pivot quartz raven sable tidal umber vesper willow xenon yarrow zephyr argon basil cedar dune ether flint "
         "grove helix iris jade karma lotus mesa nova orbit prism quill ridge solace thorn ultra vale wren axis bloom "
         "crest drift echo forge glint haze isle jolt knoll").split()


def _uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def _ts(dt):
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _exact_split(total, weights, rng):
    """Split `total` into len(weights) integers that sum exactly to total."""
    raw = [total * w / sum(weights) for w in weights]
    out = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - out[i], reverse=True)[: total - sum(out)]:
        out[i] += 1
    return out


def generate_perf(out, seed=42):
    rng = random.Random(seed)
    if os.path.isdir(out):
        shutil.rmtree(out)

    def write(rel, fields, body=""):
        path = os.path.join(out, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(emit(fields, body))

    base = datetime.datetime(2026, 11, 1, 9, 0, tzinfo=datetime.timezone.utc)
    t0 = _ts(base)
    write("store.md", {"schema_version": "1.0", "backend": "github", "owner_handle": "asha-rao",
                       "created_at": t0, "updated_at": t0})
    write("profile.md", {"display_name": "Asha Rao", "headline": "Product engineer, Pune",
                         "location": "Pune, India", "bio": "Builds and ships small products. " * 20,
                         "voice": "Direct and plain. " * 25, "created_at": t0, "updated_at": t0})
    for i, (label, url) in enumerate([("Portfolio", "https://asha.example.com"), ("GitHub", "https://code.example.com/asha-rao"),
                                      ("Dribbble", "https://dribbble.example.com/asha"),
                                      ("LinkedIn", "https://linkedin.example.com/in/asha")], start=1):
        lid = _uid("link", i)
        write("profile/links/%s.md" % lid[:8], {"id": lid, "label": label, "url": url, "sort_order": i, "created_at": t0})
    surfaces = [None] * 14 + ["code"] * 5 + ["chat"] * 3 + ["cowork"] * 2
    for i, surface in enumerate(surfaces):
        rid = _uid("rule", i)
        rule = ("Rule %d: " % i) + " ".join(rng.choice(WORDS) for _ in range(30))
        write("rules/%s.md" % rid[:8], {"id": rid, "rule": rule[:200], "surface": surface, "is_active": "true",
                                        "created_at": _ts(base + datetime.timedelta(minutes=i)), "updated_at": t0})
    tags = ["tag-%s" % w for w in WORDS[:60]]
    for slug in tags:
        write("tags/%s.md" % slug, {"id": _uid("tag", slug), "slug": slug, "label": slug[4:].title(), "created_at": t0})

    # 1,000 projects: the reserved `general` plus 999. Status mix from test-data.md.
    n = COUNTS["project"] - 1
    statuses = (["active"] * 80 + ["shipped"] * 220 + ["parked"] * 300 + ["archived"] * 350 + ["idea"] * 25
                + ["unknown"] * 25)[:n]
    while len(statuses) < n:
        statuses.append("parked")
    rng.shuffle(statuses)
    slugs = ["general"] + ["%s-%s-%d" % (rng.choice(WORDS), rng.choice(WORDS), i) for i in range(n)]
    # Three slugs collide with tag slugs on purpose.
    slugs[1], slugs[2], slugs[3] = tags[0], tags[1], tags[2]
    project_status = {"general": "active"}
    # Tags: Zipf-like weights, 0 to 8 per project, exactly 3,200 links in total.
    per_project = _exact_split(COUNTS["project_tag"], [rng.choice([1, 2, 3, 4, 5, 6, 7, 8]) for _ in range(n)], rng)
    per_project = [min(8, c) for c in per_project]
    deficit = COUNTS["project_tag"] - sum(per_project)
    i = 0
    while deficit > 0:
        if per_project[i % n] < 8:
            per_project[i % n] += 1
            deficit -= 1
        i += 1
    weights = [1.0 / (k + 1) ** 0.8 for k in range(len(tags))]
    for idx, slug in enumerate(slugs):
        status = "active" if slug == "general" else statuses[idx - 1]
        project_status[slug] = status
        count = 0 if slug == "general" else per_project[idx - 1]
        chosen = []
        while len(chosen) < count:
            tag = rng.choices(tags, weights=weights)[0]
            if tag not in chosen:
                chosen.append(tag)
        updated = base - datetime.timedelta(hours=rng.randint(0, 24 * 700))
        fields = {"id": _uid("project", slug), "slug": slug, "name": slug.replace("-", " ").title(), "status": status,
                  "type": "other" if slug == "general" else rng.choice(
                      ["product", "client_site", "concept", "skill", "tool", "content"]),
                  "one_liner": ("A %s that " % rng.choice(WORDS)) + " ".join(rng.choice(WORDS) for _ in range(20))}
        fields["one_liner"] = fields["one_liner"][:140]
        if rng.random() < 0.5:
            fields["outcome"] = " ".join(rng.choice(WORDS) for _ in range(40))
        if rng.random() < 0.3:
            fields["live_url"] = "https://%s.example.com" % slug
        if rng.random() < 0.4:
            fields["repo_url"] = "https://code.example.com/asha-rao/%s" % slug
        fields["last_verified_at"] = t0
        if status == "archived":
            fields["archived_at"] = _ts(updated)
        fields.update({"created_at": _ts(updated - datetime.timedelta(days=30)), "updated_at": _ts(updated),
                       "tags": chosen})
        write("projects/%s.md" % slug, fields)

    shipped = [s for s in slugs[1:] if project_status[s] == "shipped"]
    others = [s for s in slugs[1:] if project_status[s] != "shipped"]
    kinds = ["shipped", "deployed", "launched", "milestone", "metric", "published"]
    for i in range(COUNTS["ship_event"]):
        slug = rng.choice(shipped) if i < int(COUNTS["ship_event"] * 0.7) else rng.choice(others)
        when = base - datetime.timedelta(minutes=rng.randint(0, 3 * 365 * 24 * 60))
        eid = _uid("event", i)
        fields = {"id": eid, "project": slug, "kind": "metric" if i % 10 == 0 else rng.choice(kinds),
                  "surface": rng.choice(["code", "chat", "cowork"]),
                  "summary": ("Event %d: " % i + " ".join(rng.choice(WORDS) for _ in range(50)))[:280]}
        if i % 10 >= 3:
            fields["proof_url"] = "https://proof.example.com/%d" % i
        if i % 10 == 0:
            fields.update({"metric_label": "signups", "metric_value": str(rng.randint(1, 5000)), "metric_unit": "users"})
        fields.update({"occurred_at": _ts(when), "created_at": _ts(when + datetime.timedelta(minutes=5))})
        d = when.date().isoformat()
        write("events/%s/%s-%s-%s.md" % (d[:4], d, slug, eid[:8]), fields)

    # 1,500 decisions; 15% superseded, in chains up to 3 deep.
    decision_ids = [_uid("decision", i) for i in range(COUNTS["decision"])]
    superseded = {}
    i = 0
    while len(superseded) < int(COUNTS["decision"] * 0.15):
        depth = rng.choice([1, 2])
        chain = decision_ids[i:i + depth + 1]
        for old, new in zip(chain, chain[1:]):
            superseded[old] = new
        i += depth + 1
    owner = {}
    for idx, did in enumerate(decision_ids):
        new = superseded.get(did)
        slug = owner.get(did) or rng.choice(slugs)
        if new:
            owner[new] = slug
        when = base - datetime.timedelta(days=rng.randint(0, 700), minutes=idx)
        fields = {"id": did, "project": slug, "status": "superseded" if new else "accepted",
                  "surface": rng.choice(["code", "chat", "cowork"]), "superseded_by": new,
                  "title": ("Decision %d " % idx + " ".join(rng.choice(WORDS) for _ in range(20)))[:120],
                  "reason": " ".join(rng.choice(WORDS) for _ in range(60)), "decided_at": _ts(when),
                  "created_at": _ts(when), "updated_at": t0}
        write("decisions/%s/%s-%s.md" % (slug, when.date().isoformat(), did[:8]), fields)

    # 400 design assets: 150 approved design systems, 20 handoff bundles, the rest drafts.
    systems = rng.sample(slugs[1:], 150)
    for i in range(COUNTS["design_asset"]):
        aid = _uid("asset", i)
        if i < 150:
            slug, kind, status = systems[i], "design_system", "approved"
        elif i < 170:
            slug, kind, status = rng.choice(slugs[1:]), "handoff_bundle", "approved"
        else:
            slug, kind, status = rng.choice(slugs[1:]), rng.choice(["screen_set", "prototype"]), "draft"
        fields = {"id": aid, "project": slug, "kind": kind, "status": status, "surface": "code",
                  "title": "%s %d" % (kind.replace("_", " ").title(), i)}
        if kind == "design_system":
            fields.update({"tokens_repo_url": "https://code.example.com/asha-rao/%s" % slug, "tokens_path": "design/tokens.json"})
        fields.update({"created_at": t0, "updated_at": _ts(base - datetime.timedelta(hours=i))})
        write("design/%s/%s.md" % (slug, aid[:8]), fields)

    # 300 handoffs: 40 open (25 to code, 10 to chat, 5 to cowork), the rest done or dropped.
    targets = ["code"] * 25 + ["chat"] * 10 + ["cowork"] * 5
    for i in range(COUNTS["handoff"]):
        hid = _uid("handoff", i)
        created = base - datetime.timedelta(hours=i * 3)
        if i < 40:
            status, to, src = "open", targets[i], "chat" if targets[i] != "chat" else "code"
            picked, done = None, None
        else:
            status, to, src = rng.choice(["done", "dropped"]), rng.choice(["code", "chat", "cowork"]), "chat"
            if to == src:
                src = "code"
            picked, done = _ts(created + datetime.timedelta(hours=1)), _ts(created + datetime.timedelta(hours=2))
        write("handoffs/%s.md" % hid[:8],
              {"id": hid, "project": rng.choice(slugs), "from_surface": src, "to_surface": to, "status": status,
               "title": ("Handoff %d " % i + " ".join(rng.choice(WORDS) for _ in range(20)))[:120],
               "created_at": _ts(created), "picked_up_at": picked, "done_at": done},
              "## Brief\n\n" + " ".join(rng.choice(WORDS) for _ in range(200)))

    # 50 earlier builds, 3 of them failed.
    from .index import render_builds
    rows = []
    for i in range(COUNTS["index_build"]):
        when = _ts(base - datetime.timedelta(hours=i))
        failed = i in (7, 21, 40)
        rows.append({"started_at": when, "status": "failed" if failed else "succeeded",
                     "commit_sha": "%040x" % rng.getrandbits(160), "entry_count": "" if failed else 8000 + i,
                     "boot_chars": "" if failed else 7000, "finished_at": when,
                     "error": "1 check errors, first: projects/x.md: status: bad" if failed else ""})
    os.makedirs(os.path.join(out, "index"), exist_ok=True)
    with open(os.path.join(out, "index", "builds.md"), "w", encoding="utf-8") as handle:
        handle.write(render_builds(rows, "built: %s from fixture schema 1.0" % t0))
    return "wrote %s: " % out + ", ".join("%s %d" % kv for kv in COUNTS.items())
