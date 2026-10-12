import argparse
import json
import sys
from .builder import build_world
from .schema import ScenarioError, read_json, validate_world
from .simulation import simulate


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build and simulate local SOP scenarios.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("world")
    build = sub.add_parser("build")
    build.add_argument("world")
    build.add_argument("--output", required=True)
    run = sub.add_parser("simulate")
    run.add_argument("world")
    run.add_argument("trace")
    args = parser.parse_args(argv)
    try:
        world = read_json(args.world)
        if args.command == "validate":
            validate_world(world)
            result = {"valid": True, "scenario_id": world["scenario_id"]}
        elif args.command == "build":
            result = build_world(world, args.output)
        else:
            result = simulate(world, read_json(args.trace))
        print(json.dumps(result, indent=2))
        return 1 if args.command == "simulate" and result["rejected"] else 0
    except (ScenarioError, OSError, ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
