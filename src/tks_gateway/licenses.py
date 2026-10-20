"""Third-party components and their licenses, determined at runtime.

Everything is read from the running environment, nothing is maintained by
hand: the Python distributions reachable from ``tks-gateway`` (plus the WSGI
server ``waitress`` if installed) via their metadata, and the JavaScript files
bundled in ``static/vendor/`` via the original ``<name>.package.json`` from npm
that lies next to them. From the same data a CycloneDX 1.5 SBOM is built.
"""

from __future__ import annotations

import hashlib
import importlib.metadata as md
import json
import platform
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .i18n import _

ROOT = "tks-gateway"
OPTIONAL_ROOTS = ("waitress",)  # used by "tks-gateway web" if installed
VENDOR_DIR = Path(__file__).parent / "static" / "vendor"

# SPDX ids for license texts / trove classifiers without a License-Expression
_TEXT_MARKERS = (
    ("Apache License", "Version 2.0", "Apache-2.0"),
    ("Zope Public License (ZPL) Version 2.1", "", "ZPL-2.1"),
    ("Permission is hereby granted, free of charge", "", "MIT"),
    ("Redistribution and use in source and binary forms", "Neither the name", "BSD-3-Clause"),
    ("Redistribution and use in source and binary forms", "", "BSD-2-Clause"),
    ("Permission to use, copy, modify, and/or distribute", "", "ISC"),
)
_CLASSIFIERS = {
    "MIT License": "MIT",
    "Apache Software License": "Apache-2.0",
    "ISC License (ISCL)": "ISC",
}
_LICENSE_FILE = re.compile(r"(^|/)(LICEN[CS]E|COPYING|NOTICE)[^/]*$", re.I)


@dataclass
class Component:
    name: str
    version: str
    license: str  # SPDX id/expression if known, otherwise the declared name
    spdx: bool  # license is an SPDX id/expression
    kind: str  # "python" or "javascript"
    url: str = ""
    author: str = ""
    purl: str = ""
    summary: str = ""
    texts: list[dict] = field(default_factory=list)  # [{"file": ..., "text": ...}]
    requires: list[str] = field(default_factory=list)  # names of direct dependencies
    bundled: list[str] = field(default_factory=list)  # bundled npm dependencies (declared ranges)
    sha256: str = ""
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _detect_from_text(texts: list[dict]) -> str | None:
    for t in texts:
        for marker, extra, spdx in _TEXT_MARKERS:
            if marker in t["text"] and extra in t["text"]:
                return spdx
    return None


def _license_of(meta, texts: list[dict]) -> tuple[str, bool]:
    if expr := meta.get("License-Expression"):
        return expr.strip(), True
    if spdx := _detect_from_text(texts):
        return spdx, True
    for c in meta.get_all("Classifier") or []:
        if c.startswith("License :: "):
            short = c.rsplit(" :: ", 1)[-1]
            if short in _CLASSIFIERS:
                return _CLASSIFIERS[short], True
            return short, False
    declared = (meta.get("License") or "").strip()
    if declared and "\n" not in declared and len(declared) < 60:
        return declared, False
    return "NOASSERTION", False


def _url_of(meta) -> str:
    for entry in meta.get_all("Project-URL") or []:
        label, _, url = entry.partition(",")
        if label.strip().lower() in ("source", "source code", "repository", "homepage"):
            return url.strip()
    return (meta.get("Home-page") or "").strip()


def _requirement_names(dist) -> list[str]:
    names = []
    for req in dist.requires or []:
        spec, _, marker = req.partition(";")
        if "extra" in marker:  # optional feature, not installed by default
            continue
        m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", spec)
        if m:
            names.append(m.group(1))
    return names


def _author_of(meta) -> str:
    if author := (meta.get("Author") or "").strip():
        return author
    # "Name <mail>, ..." – keep the names only
    return ", ".join(re.sub(r"\s*<[^>]*>", "", a).strip() for a in (meta.get("Author-email") or "").split(",") if a.strip())


def _python_component(dist) -> Component:
    meta = dist.metadata
    texts = []
    for f in dist.files or []:
        path = str(f)
        if _LICENSE_FILE.search(path) and ".dist-info/" in path:
            try:
                texts.append({"file": Path(path).name, "text": Path(f.locate()).read_text(encoding="utf-8", errors="replace")})
            except OSError:
                pass
    name = meta["Name"]
    if not texts and _norm(name) == ROOT:  # editable install: no license in the dist-info
        project_license = Path(__file__).resolve().parents[2] / "LICENSE"
        if project_license.is_file():
            texts.append({"file": "LICENSE", "text": project_license.read_text(encoding="utf-8")})
    lic, spdx = _license_of(meta, texts)
    return Component(
        name=name, version=dist.version, license=lic, spdx=spdx, kind="python",
        url=_url_of(meta), author=_author_of(meta), purl=f"pkg:pypi/{_norm(name)}@{dist.version}",
        summary=(meta.get("Summary") or "").strip(), texts=texts,
        note="" if texts else _("The installed package contains no license file – see the project page."),
    )


def python_components() -> list[Component]:
    """Installed distributions reachable from tks-gateway (and optional roots)."""
    seen: dict[str, Component] = {}
    todo = [ROOT, *OPTIONAL_ROOTS]
    while todo:
        name = todo.pop()
        key = _norm(name)
        if key in seen:
            continue
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            continue  # not installed (marker not met or optional root missing)
        comp = _python_component(dist)
        deps = _requirement_names(dist)
        installed = []
        for d in deps:
            try:
                md.distribution(d)
            except md.PackageNotFoundError:
                continue
            installed.append(_norm(d))
            todo.append(d)
        comp.requires = sorted(set(installed))
        seen[key] = comp
    root = seen.pop(_norm(ROOT), None)
    return ([root] if root else []) + sorted(seen.values(), key=lambda c: c.name.lower())


def vendored_components() -> list[Component]:
    """JavaScript bundled in static/vendor/, described by its npm package.json."""
    out = []
    for pkg_file in sorted(VENDOR_DIR.glob("*.package.json")):
        stem = pkg_file.name[: -len(".package.json")]
        pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
        lic_file = VENDOR_DIR / f"{stem}.LICENSE"
        texts = [{"file": lic_file.name, "text": lic_file.read_text(encoding="utf-8")}] if lic_file.exists() else []
        files = sorted(VENDOR_DIR.glob(f"{stem}*.js"))
        sha = hashlib.sha256(files[0].read_bytes()).hexdigest() if files else ""
        repo = pkg.get("repository")
        url = pkg.get("homepage") or (repo.get("url") if isinstance(repo, dict) else repo) or ""
        url = re.sub(r"^git\+|\.git$", "", url)
        bundled = sorted(f"{n}@{v}" for n, v in (pkg.get("dependencies") or {}).items())
        out.append(Component(
            name=pkg["name"], version=pkg["version"], license=pkg.get("license", "NOASSERTION"), spdx=True,
            kind="javascript", url=url, purl=f"pkg:npm/{pkg['name']}@{pkg['version']}",
            summary=pkg.get("description", ""), texts=texts, bundled=bundled, sha256=sha,
            note=_("The minified bundle also contains its npm dependencies (listed with their declared version "
                   "ranges); their licenses are documented by the respective projects.") if bundled else "",
        ))
    return out


def components() -> list[Component]:
    return python_components() + vendored_components()


# --------------------------------------------------------------------- SBOM


def _cdx_license(c: Component) -> list[dict]:
    if c.license == "NOASSERTION":
        return []
    if not c.spdx:
        return [{"license": {"name": c.license}}]
    if re.fullmatch(r"[A-Za-z0-9.+-]+", c.license):  # single SPDX id
        return [{"license": {"id": c.license}}]
    return [{"expression": c.license}]


def sbom() -> dict:
    """CycloneDX 1.5 SBOM of the running installation."""
    comps = components()
    root = next((c for c in comps if c.name == ROOT), None)
    by_norm = {_norm(c.name): c.purl for c in comps}

    def cdx(c: Component) -> dict:
        d = {"type": "application" if c is root else "library", "bom-ref": c.purl, "name": c.name,
             "version": c.version, "purl": c.purl}
        if c.author:
            d["author"] = c.author
        if c.summary:
            d["description"] = c.summary
        if lic := _cdx_license(c):
            d["licenses"] = lic
        if c.url:
            d["externalReferences"] = [{"type": "vcs" if "github.com" in c.url else "website", "url": c.url}]
        if c.sha256:
            d["hashes"] = [{"alg": "SHA-256", "content": c.sha256}]
        if c.bundled:
            d["properties"] = [{"name": "tks-gateway:bundled-dependency", "value": b} for b in c.bundled]
        return d

    deps = [{"ref": c.purl, "dependsOn": [by_norm[r] for r in c.requires if r in by_norm]}
            for c in comps if c.kind == "python"]
    if root:  # the web UI loads the vendored scripts
        for d in deps:
            if d["ref"] == root.purl:
                d["dependsOn"] += [c.purl for c in comps if c.kind == "javascript"]
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tools": {"components": [{"type": "application", "name": "tks-gateway licenses",
                                      "version": root.version if root else ""}]},
            "component": cdx(root) if root else {"type": "application", "name": ROOT},
            "properties": [{"name": "python:version", "value": platform.python_version()},
                           {"name": "python:implementation", "value": platform.python_implementation()}],
        },
        "components": [cdx(c) for c in comps if c is not root],
        "dependencies": deps,
    }
