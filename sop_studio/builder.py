from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import tempfile
import zipfile
from .schema import ScenarioError, canonical, validate_world


def build_world(world, output):
    validate_world(world)
    output = Path(output)
    if output.exists():
        raise ScenarioError("output already exists; choose a new directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".sop-") as temp:
        root = Path(temp) / "world"
        (root / "services").mkdir(parents=True)
        (root / "world.json").write_bytes(canonical(world))
        sop = "# Standard operating procedure\n\n" + "\n\n".join(f"## {c['id']}\n\n{c['text']}" for c in world["clauses"]) + "\n"
        (root / "SOP.md").write_text(sop, encoding="utf-8")
        services = defaultdict(list)
        for record in world["records"]:
            services[record["service"]].append(record)
        for service, records in sorted(services.items()):
            (root / "services" / f"{service}.json").write_bytes(canonical({"records": records}))
        budget = {"actors": len(world["actors"]), "records": len(world["records"]),
                  "by_service": dict(sorted(Counter(r["service"] for r in world["records"]).items())),
                  "declared_absences": world.get("absences", [])}
        (root / "budget.json").write_bytes(canonical(budget))
        hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(root.rglob("*")) if p.is_file()}
        (root / "checksums.json").write_bytes(canonical(hashes))
        with zipfile.ZipFile(root / "scenario.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.name == "scenario.zip":
                    continue
                info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())
        root.rename(output)
    return {"scenario_id": world["scenario_id"], "output": str(output), "budget": budget}
