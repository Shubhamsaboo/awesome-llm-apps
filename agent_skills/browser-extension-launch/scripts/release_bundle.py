#!/usr/bin/env python3
"""Check a Chrome MV3 build and make a deterministic, root-level release ZIP.

Only Python's standard library is used. This is a conservative release-directory
check, not a complete Chrome manifest validator, security audit or browser test.
Run ``release_bundle.py --help`` for the command-line interface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import struct
import sys
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit  # URL parsing only; no network I/O. skillscan:allow


BLOCKED_DIRS = {"node_modules", ".git", ".hg", ".svn", ".ssh"}
BLOCKED_NAMES = {  # Protective denylist; these files are rejected, never read. skillscan:allow
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".npmrc", ".pypirc",  # skillscan:allow
    ".envrc", ".netrc", "credentials.json", "service-account.json", "service_account.json",  # skillscan:allow
}
PRIVATE_HEADER = re.compile(rb"-----BEGIN (?:[A-Z0-9 ]*PRIVATE KEY|PGP PRIVATE KEY BLOCK)-----")
MESSAGE = re.compile(r"__MSG_([A-Za-z0-9_@]+)__")
BUILTIN_MESSAGES = {
    "@@extension_id", "@@ui_locale", "@@bidi_dir", "@@bidi_reversed_dir",
    "@@bidi_start_edge", "@@bidi_end_edge",
}
TEXT_SUFFIXES = {".js", ".mjs", ".cjs", ".html", ".htm", ".css", ".json", ".ts", ".tsx", ".jsx"}
SCAN_LIMIT = 8 * 1024 * 1024
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def version_tuple(value: object) -> tuple[int, int, int, int] | None:
    """Chrome: 1–4 decimal components, <=65535, no leading zeros, not all zero."""
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]{0,4})(?:\.(?:0|[1-9][0-9]{0,4})){0,3}", value):
        return None
    parts = tuple(int(part) for part in value.split("."))
    if max(parts) > 65535 or not any(parts):
        return None
    return parts + (0,) * (4 - len(parts))


def issue(report: dict, level: str, code: str, path: str, message: str) -> None:
    item = {"code": code, "path": path, "message": message}
    if item not in report[level]:
        report[level].append(item)


def read_regular(root: Path, relative: str) -> bytes:
    """Refuse symlinks and non-regular files, including symlinked parent folders."""
    if root.is_symlink():
        raise ValueError("构建目录已变为符号链接，请重新检查。")
    path = root
    for part in PurePosixPath(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("资源已变为符号链接，请重新检查构建目录。")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    if os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"):
        # On POSIX, anchor each lookup to a directory descriptor to prevent
        # a parent directory being swapped for a symlink between path checks.
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            parts = PurePosixPath(relative).parts
            for part in parts[:-1]:
                following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                os.close(directory)
                directory = following
            descriptor = os.open(parts[-1], flags, dir_fd=directory)
        finally:
            os.close(directory)
    else:
        descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("资源不是普通文件。")
        return handle.read()


def read_json(data: bytes, report: dict, path: str) -> object | None:
    def reject_constant(value):
        raise ValueError("JSON 不能包含 NaN 或 Infinity。")

    def unique_object(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("JSON 含重复字段，无法确定实际生效值。")
            result[key] = value
        return result

    try:
        return json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (UnicodeDecodeError, ValueError):
        issue(report, "errors", "invalid_json", path, "文件必须是有效的 UTF-8 JSON，且不能包含重复字段。")
        return None


def iter_strings(value: object, at: str = "manifest"):
    if isinstance(value, str):
        yield at, value
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_strings(child, f"{at}[{index}]")
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from iter_strings(child, f"{at}.{key}")


class PageResources(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.resources: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "img", "iframe", "source", "audio", "video"} and attrs.get("src"):
            self.resources.append(("script" if tag == "script" else "asset", attrs["src"]))
        if tag == "link" and attrs.get("href"):
            rel = (attrs.get("rel") or "").lower().split()
            if any(part in {"stylesheet", "icon", "modulepreload", "preload"} for part in rel):
                self.resources.append(("script" if "modulepreload" in rel or attrs.get("as") == "script" else "asset", attrs["href"]))


def check_bundle(build_dir: str | Path, previous_version: str | None = None) -> dict:
    original = Path(build_dir).expanduser()
    root = original.resolve()
    report = {
        "schema_version": 1,
        "status": "blocked",
        "build_dir": str(root),
        "manifest": {},
        "errors": [],
        "warnings": [],
        "inventory": [],
        "checks_scope": {
            "performed": ["MV3 基础字段与版本", "manifest 声明的本地资源", "HTML 常见静态资源", "默认语言消息", "图标存在与 PNG 尺寸", "敏感文件与路径", "部分远程执行和开发地址启发式"],
            "not_performed": ["完整 Chrome manifest schema 校验", "全部动态依赖分析", "完整安全与隐私审计", "浏览器安装和功能测试", "商店后台检查", "审核或发布"],
            "warning_policy": "警告必须由开发者逐项复核；零警告也不代表没有远程代码、隐私问题或功能故障。",
        },
    }
    if original.is_symlink() or not root.is_dir():
        issue(report, "errors", "invalid_build_dir", str(original), "构建目录必须是实际目录，不能是符号链接。")
        return report

    files: dict[str, bytes] = {}

    def walk_error(error):
        issue(report, "errors", "unreadable_directory", str(error.filename or root), "目录无法读取；检查不会静默忽略它。")

    for current, directories, filenames in os.walk(root, followlinks=False, onerror=walk_error):
        current_path = Path(current)
        for name in sorted(directories):
            child = current_path / name
            relative = child.relative_to(root).as_posix()
            if "\\" in relative or ":" in relative:
                issue(report, "errors", "unsafe_archive_path", relative, "文件名含反斜杠或冒号，无法安全地跨平台解压。")
            if child.is_symlink():
                issue(report, "errors", "symlink", relative, "发布目录不能包含符号链接。")
                directories.remove(name)
            elif name.lower() in BLOCKED_DIRS:
                issue(report, "errors", "development_directory", relative, "发布目录含依赖、版本控制或凭证目录；请重新输出干净的正式构建。")
                directories.remove(name)
        directories.sort()
        for name in sorted(filenames):
            child = current_path / name
            relative = child.relative_to(root).as_posix()
            if "\\" in relative or ":" in relative:
                issue(report, "errors", "unsafe_archive_path", relative, "文件名含反斜杠或冒号，无法安全地跨平台解压。")
            if child.is_symlink():
                issue(report, "errors", "symlink", relative, "发布目录不能包含符号链接。")
                continue
            try:
                data = read_regular(root, relative)
            except (OSError, ValueError):
                issue(report, "errors", "unreadable_file", relative, "文件无法读取或不是普通文件。")
                continue
            files[relative] = data
            report["inventory"].append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
            lowered = name.lower()
            if lowered == ".env" or lowered.startswith(".env.") or lowered in BLOCKED_NAMES or child.suffix.lower() in {".p12", ".pfx", ".keystore", ".jks"}:
                issue(report, "errors", "sensitive_file", relative, "发现可能含密钥或凭证的文件；不要把环境配置、凭证或私钥放入扩展包。")
            if PRIVATE_HEADER.search(data):
                issue(report, "errors", "private_key", relative, "发现私钥标记；请移出发布目录，并检查是否需要更换已暴露的密钥。")
            if lowered == ".ds_store" or lowered in {"package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock"} or child.suffix.lower() in {".map", ".ts", ".tsx", ".jsx"}:
                issue(report, "warnings", "development_artifact", relative, "包含常见开发文件；请确认确实需要随正式扩展分发。")

    report["inventory"].sort(key=lambda item: item["path"])
    if "manifest.json" not in files:
        issue(report, "errors", "missing_manifest", "manifest.json", "正式构建目录根部必须有 manifest.json。")
        return report
    manifest = read_json(files["manifest.json"], report, "manifest.json")
    if not isinstance(manifest, dict):
        issue(report, "errors", "manifest_object", "manifest.json", "manifest.json 顶层必须是对象。")
        return report
    if type(manifest.get("manifest_version")) is not int or manifest.get("manifest_version") != 3:
        issue(report, "errors", "manifest_version", "manifest.manifest_version", "此工具面向 Chrome Manifest V3，manifest_version 必须为 3。")

    locales: dict[str, dict] = {}
    for path, data in files.items():
        parts = PurePosixPath(path).parts
        if len(parts) == 3 and parts[0] == "_locales" and parts[2] == "messages.json":
            messages = read_json(data, report, path)
            if not isinstance(messages, dict):
                issue(report, "errors", "locale_object", path, "语言消息文件顶层必须是对象。")
                continue
            normalized = {}
            for key, value in messages.items():
                if not isinstance(value, dict) or not isinstance(value.get("message"), str):
                    issue(report, "errors", "locale_message", path, "每个语言条目必须包含字符串 message。")
                    continue
                if key.lower() in normalized:
                    issue(report, "errors", "locale_duplicate", path, "语言消息名称不能只靠大小写区分。")
                normalized[key.lower()] = value["message"]
            locales[parts[1]] = normalized
    message_refs = [(at, key) for at, value in iter_strings(manifest) for key in MESSAGE.findall(value)]
    locale = manifest.get("default_locale")
    if locale is not None and (not isinstance(locale, str) or not re.fullmatch(r"[A-Za-z0-9_@-]+", locale)):
        issue(report, "errors", "default_locale", "manifest.default_locale", "default_locale 必须是合法的语言目录名称。")
        locale = None
    if (any(path.startswith("_locales/") for path in files) or any(key.lower() not in BUILTIN_MESSAGES for _, key in message_refs)) and not locale:
        issue(report, "errors", "missing_default_locale", "manifest.default_locale", "存在本地化消息时必须设置 default_locale 并提供对应 messages.json。")
    if locale and locale not in locales:
        issue(report, "errors", "missing_locale", f"_locales/{locale}/messages.json", "默认语言消息文件不存在。")
    default_messages = locales.get(locale, {})
    for at, key in message_refs:
        if key.lower() not in BUILTIN_MESSAGES and key.lower() not in default_messages:
            issue(report, "errors", "missing_message", at, f"默认语言缺少消息 {key}。")

    def localize(value):
        if isinstance(value, str):
            return MESSAGE.sub(lambda match: default_messages.get(match.group(1).lower(), match.group(0)), value)
        if isinstance(value, list):
            return [localize(child) for child in value]
        if isinstance(value, dict):
            return {key: localize(child) for key, child in value.items()}
        return value

    manifest = localize(manifest)
    for key, limit in (("name", 75), ("description", 132)):
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            issue(report, "errors", f"invalid_{key}", f"manifest.{key}", f"{key} 必须是非空字符串，且不能超过 {limit} 个字符。")
    version = manifest.get("version")
    current_version = version_tuple(version)
    if current_version is None:
        issue(report, "errors", "invalid_version", "manifest.version", "版本须为 1–4 段整数，每段 0–65535、无前导零，且不能全为零，例如 1.0.0。")
    if previous_version is not None:
        previous = version_tuple(previous_version)
        if previous is None:
            issue(report, "errors", "invalid_previous_version", "--previous-version", "上个发布版本不符合 Chrome 版本格式。")
        elif current_version is not None and current_version <= previous:
            issue(report, "errors", "version_not_increased", "manifest.version", "更新版本必须大于上个发布版本；末尾补零视为同一版本。")
        report["previous_version"] = previous_version
    report["manifest"] = {key: manifest.get(key) for key in ("name", "version", "description", "manifest_version")}

    def resolve_resource(value, at, *, glob=False):
        if not isinstance(value, str) or not value:
            issue(report, "errors", "resource_type", at, "资源路径必须是非空字符串。")
            return []
        decoded = unquote(value)
        if "\\" in decoded or "\x00" in decoded or decoded.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", decoded) or ".." in PurePosixPath(decoded).parts:
            issue(report, "errors", "unsafe_resource_path", at, "资源必须使用构建目录内的相对路径，不能含外部地址、反斜杠或上级目录。")
            return []
        relative = PurePosixPath(decoded).as_posix()
        if glob:
            # Chrome's resources field uses '*' as a wildcard, not shell '?' or '[...]'.
            pattern = re.compile("^" + re.escape(relative).replace(r"\*", ".*") + "$")
            matches = [path for path in files if pattern.fullmatch(path)]
        else:
            matches = [relative] if relative in files else []
        if not matches:
            issue(report, "errors", "missing_resource", at, f"资源不存在或没有匹配文件：{value}")
        return matches

    def icon_resources(value, at, require128=False):
        if isinstance(value, str) and not require128:
            resolve_resource(value, at)
            return
        if not isinstance(value, dict) or not value:
            issue(report, "errors", "icons_object", at, "图标配置必须是尺寸到本地图片路径的非空对象。")
            return
        if require128 and "128" not in value:
            issue(report, "errors", "missing_icon_128", at, "商店发布包需在 icons 中提供 128 × 128 图标。")
        for size, path in value.items():
            for match in resolve_resource(path, f"{at}.{size}"):
                data = files[match]
                if data.startswith(b"\x89PNG\r\n\x1a\n"):
                    if len(data) < 33 or data[12:16] != b"IHDR" or struct.unpack(">I", data[8:12])[0] != 13:
                        issue(report, "errors", "invalid_png", match, "PNG 文件头损坏，无法读取图标尺寸。")
                    else:
                        width, height = struct.unpack(">II", data[16:24])
                        if not size.isdigit() or width != int(size) or height != int(size):
                            level = "errors" if require128 and size == "128" else "warnings"
                            issue(report, level, "icon_dimensions", match, f"PNG 为 {width} × {height}，与声明尺寸 {size} 不符。")
                else:
                    if require128 and size == "128":
                        issue(report, "errors", "icon_128_requires_png", match, "Chrome Web Store 发布包中的 128 × 128 图标必须为 PNG；请转换图片并更新 icons.128 引用。")
                    else:
                        issue(report, "warnings", "icon_format_review", match, "非 PNG 图标：请核实 Chrome 支持此图片格式、图片有效且尺寸与声明一致；本工具不验证其尺寸。")

    icon_resources(manifest.get("icons"), "manifest.icons", require128=True)
    for key in ("options_page", "devtools_page"):
        if key in manifest:
            resolve_resource(manifest[key], f"manifest.{key}")
    for parent, resource_key in (("action", "default_popup"), ("options_ui", "page"), ("side_panel", "default_path"), ("background", "service_worker"), ("storage", "managed_schema")):
        if parent not in manifest:
            continue
        value = manifest[parent]
        if not isinstance(value, dict):
            issue(report, "errors", "field_type", f"manifest.{parent}", "此字段必须是对象。")
            continue
        if resource_key in value and not (parent == "action" and value[resource_key] == ""):
            resolve_resource(value[resource_key], f"manifest.{parent}.{resource_key}")
        if parent == "action" and "default_icon" in value:
            icon_resources(value["default_icon"], "manifest.action.default_icon")
        if parent == "background" and ("scripts" in value or "page" in value):
            issue(report, "errors", "mv2_background", "manifest.background", "MV3 后台应使用 service_worker；请移除 MV2 的 scripts/page 配置。")

    overrides = manifest.get("chrome_url_overrides", {})
    if not isinstance(overrides, dict):
        issue(report, "errors", "field_type", "manifest.chrome_url_overrides", "此字段必须是对象。")
    else:
        for key, path in overrides.items():
            resolve_resource(path, f"manifest.chrome_url_overrides.{key}")

    def records(value, at):
        if not isinstance(value, list):
            issue(report, "errors", "field_type", at, "此字段必须是数组。")
            return []
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                issue(report, "errors", "field_type", f"{at}[{index}]", "此条目必须是对象。")
        return [(index, item) for index, item in enumerate(value) if isinstance(item, dict)]

    def resource_array(value, at, *, glob=False):
        if not isinstance(value, list):
            issue(report, "errors", "field_type", at, "资源列表必须是数组。")
            return
        for index, path in enumerate(value):
            resolve_resource(path, f"{at}[{index}]", glob=glob)

    for index, entry in records(manifest.get("content_scripts", []), "manifest.content_scripts"):
        for kind in ("js", "css"):
            if kind in entry:
                resource_array(entry[kind], f"manifest.content_scripts[{index}].{kind}")
    for index, entry in records(manifest.get("web_accessible_resources", []), "manifest.web_accessible_resources"):
        resource_array(entry.get("resources"), f"manifest.web_accessible_resources[{index}].resources", glob=True)
    sandbox = manifest.get("sandbox", {})
    if isinstance(sandbox, dict):
        if "pages" in sandbox:
            resource_array(sandbox["pages"], "manifest.sandbox.pages")
    else:
        issue(report, "errors", "field_type", "manifest.sandbox", "此字段必须是对象。")
    dnr = manifest.get("declarative_net_request", {})
    if isinstance(dnr, dict):
        for index, entry in records(dnr.get("rule_resources", []), "manifest.declarative_net_request.rule_resources"):
            resolve_resource(entry.get("path"), f"manifest.declarative_net_request.rule_resources[{index}].path")
    else:
        issue(report, "errors", "field_type", "manifest.declarative_net_request", "此字段必须是对象。")

    # Heuristics report file/line and category, never source excerpts or secrets.
    remote_import = re.compile(r"(?:\bimport\s*(?:\(|[^;\n]*?\bfrom\s*)?|\bexport\s+[^;\n]*?\bfrom\s*|\bimportScripts\s*\()\s*['\"](?:https?:)?//", re.I)
    execution = re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(")
    development = re.compile(r"(?:https?|wss?)://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(?=[:/\s'\"]|$)|/@vite/|@vite/client", re.I)
    for path, data in files.items():
        suffix = PurePosixPath(path).suffix.lower()
        if suffix not in TEXT_SUFFIXES:
            continue
        if len(data) > SCAN_LIMIT:
            issue(report, "warnings", "static_scan_limit", path, "文件大于 8 MiB，启发式代码扫描未执行；请单独复核此文件。")
            continue
        try:
            source = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            issue(report, "warnings", "text_encoding_review", path, "无法按 UTF-8 扫描文本，请单独复核文件内容及编码。")
            continue
        patterns = [(development, "development_endpoint", "发现本机服务或开发工具地址；确认正式功能不依赖开发环境。")]
        if suffix in {".js", ".mjs", ".cjs", ".html", ".htm", ".ts", ".tsx", ".jsx"}:
            patterns.extend([(remote_import, "remote_code_review", "发现疑似远程脚本导入；核实 MV3 要求并把执行代码随包提供。"), (execution, "dynamic_execution_review", "发现 eval/new Function 的静态特征；请复核真实执行路径、CSP 和 MV3 要求。")])
        for pattern, code, message in patterns:
            match = pattern.search(source)
            if match:
                line = source.count("\n", 0, match.start()) + 1
                issue(report, "warnings", code, f"{path}:{line}", message + " 此项是启发式线索，可能命中注释或字符串。")
        if suffix in {".html", ".htm"}:
            parser = PageResources()
            try:
                parser.feed(source)
            except (ValueError, AssertionError):
                issue(report, "warnings", "html_parse_review", path, "HTML 解析未完成，请在浏览器中检查实际资源加载。")
                continue
            for kind, reference in parser.resources:
                try:
                    url = urlsplit(reference)
                except ValueError:
                    issue(report, "warnings", "html_url_review", path, "HTML 含无法解析的资源 URL，请手动检查。")
                    continue
                if url.scheme or url.netloc:
                    if kind == "script" and url.scheme not in {"chrome-extension"}:
                        issue(report, "warnings", "remote_code_review", path, "HTML 引用了包外脚本或特殊 URL 脚本；请核实代码来源及 MV3 要求。")
                    continue
                if not url.path:
                    continue
                decoded = unquote(url.path)
                if "\\" in decoded or "\x00" in decoded:
                    issue(report, "errors", "unsafe_resource_path", path, "HTML 资源路径含反斜杠或空字符。")
                    continue
                # HTML uses URL resolution: ../ inside the extension is legitimate.
                relative = (root / decoded.lstrip("/")) if decoded.startswith("/") else (root / path).parent / decoded
                resolved = relative.resolve()
                try:
                    normalized = resolved.relative_to(root).as_posix()
                except ValueError:
                    issue(report, "errors", "unsafe_resource_path", path, "HTML 资源路径超出构建目录。")
                    continue
                if normalized not in files:
                    issue(report, "errors", "missing_html_resource", path, f"HTML 引用的本地资源不存在：{reference}")

    if not report["errors"]:
        report["status"] = "checks_passed"
    return report


def safe_output(path: Path, root: Path, overwrite: bool) -> Path:
    if path.is_symlink():
        raise ValueError("输出位置不能是符号链接。")
    resolved = path.expanduser().resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError("ZIP 和报告必须保存到构建目录外，避免把旧报告或 ZIP 装入新发布包。")
    if resolved.exists() and (not overwrite or not resolved.is_file()):
        raise ValueError("输出已存在；请选择新路径，或明确添加 --overwrite 覆盖普通文件。")
    return resolved


def commit_temp(temporary: Path, destination: Path, overwrite: bool):
    if overwrite:
        if destination.is_symlink() or (destination.exists() and not destination.is_file()):
            raise ValueError("输出位置已经变化，不允许覆盖链接或非普通文件。")
        os.replace(temporary, destination)
    else:
        # Hard linking atomically avoids replacing a file created after preflight.
        os.link(temporary, destination)
        temporary.unlink()


def write_report(report: dict, destination: Path, overwrite: bool):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".extension-report-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        commit_temp(temporary, destination, overwrite)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def pack_bundle(report: dict, destination: Path, overwrite: bool = False):
    if report["errors"]:
        raise ValueError("检查存在错误，不能生成发布 ZIP。")
    root = Path(report["build_dir"])
    destination = safe_output(destination, root, overwrite)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".extension-release-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for entry in report["inventory"]:
                data = read_regular(root, entry["path"])
                if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise ValueError("构建文件在检查后发生变化；请重新执行打包。")
                info = zipfile.ZipInfo(entry["path"], date_time=FIXED_ZIP_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        size = temporary.stat().st_size
        commit_temp(temporary, destination, overwrite)
        report["status"] = "packed"
        report["archive"] = {"path": str(destination), "bytes": size, "sha256": digest, "file_count": len(report["inventory"]), "manifest_at_root": True}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="检查 Chrome MV3 正式构建并生成可追溯的 ZIP。此工具不代替浏览器实测、隐私审计或商店审核。")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "pack"):
        child = subparsers.add_parser(command, help="只做静态检查" if command == "check" else "检查通过后打包")
        child.add_argument("build_dir", type=Path, help="包含根 manifest.json 的正式构建目录")
        child.add_argument("--report", type=Path, help="JSON 报告路径，必须在构建目录外")
        child.add_argument("--previous-version", help="上个发布版本；提供后要求本次版本严格递增")
        child.add_argument("--overwrite", action="store_true", help="明确允许覆盖已有 ZIP / 报告普通文件")
        if command == "pack":
            child.add_argument("--output", type=Path, required=True, help="新 ZIP 路径，必须在构建目录外")
    args = parser.parse_args(argv)
    root = args.build_dir.expanduser().resolve()
    try:
        report_path = safe_output(args.report, root, args.overwrite) if args.report else None
        output = safe_output(args.output, root, args.overwrite) if args.command == "pack" else None
        if output is not None and output == report_path:
            raise ValueError("ZIP 和 JSON 报告必须使用不同路径。")
        if output is not None and report_path is not None and (output in report_path.parents or report_path in output.parents):
            raise ValueError("ZIP 和报告路径不能互为父目录。")
    except (OSError, ValueError) as error:
        print(f"无法准备输出：{error}", file=sys.stderr)
        return 2
    try:
        report = check_bundle(args.build_dir, args.previous_version)
        if output is not None and not report["errors"]:
            try:
                pack_bundle(report, output, args.overwrite)
            except (OSError, ValueError, zipfile.BadZipFile) as error:
                issue(report, "errors", "pack_failed", str(output), f"打包未完成：{error}")
                report["status"] = "blocked"
        if report_path is not None:
            write_report(report, report_path, args.overwrite)
    except (OSError, ValueError) as error:
        print(f"检查或写入失败：{error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
