#!/usr/bin/env python3
"""
Agent 8 helper — find the Benchling IDs you need for `.env`.

Prints projects (to find "Hackathon26"'s project_id), folders within a project (to find
"AIFG"'s folder_id, mostly useful for double-checking you're in the right place — Results
themselves are scoped by schema + project, not folder), and assay result schemas (to find
the schema_id for whatever you name the "next experiment" and "results" schemas).

Usage:
    uv run agent8_benchling_sync/list_resources.py --project Hackathon26
"""

import argparse
import os

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main() -> None:
    parser = argparse.ArgumentParser(description="List Benchling projects/folders/schemas to find IDs for .env")
    parser.add_argument("--project", default=None, help="Project name to filter folders by, e.g. Hackathon26")
    args = parser.parse_args()

    api_key = os.environ.get("BENCHLING_API_KEY")
    tenant_url = os.environ.get("BENCHLING_TENANT_URL")
    if not api_key or not tenant_url:
        raise SystemExit("Set BENCHLING_API_KEY and BENCHLING_TENANT_URL in .env first.")

    benchling = Benchling(url=tenant_url, auth_method=ApiKeyAuth(api_key))

    print("=== Projects ===")
    project_id = None
    for page in benchling.projects.list(name=args.project):
        for project in page:
            print(f"  {project.name!r}  id={project.id}")
            if args.project and project.name == args.project:
                project_id = project.id

    print("\n=== Folders" + (f" in project {args.project!r}" if project_id else "") + " ===")
    for page in benchling.folders.list(project_id=project_id):
        for folder in page:
            print(f"  {folder.name!r}  id={folder.id}")

    print("\n=== Assay Result Schemas ===")
    for page in benchling.schemas.list_assay_result_schemas():
        for schema in page:
            print(f"  {schema.name!r}  id={schema.id}")

    print("\n=== Custom Entity Schemas ===")
    for page in benchling.schemas.list_entity_schemas():
        for schema in page:
            print(f"  {schema.name!r}  id={schema.id}")


if __name__ == "__main__":
    main()
