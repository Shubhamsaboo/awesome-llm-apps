#!/usr/bin/env python3
"""Check real-browser acceptance records against the exact current extension.

This gate validates record completeness, artifact locations, and file hashes.
It cannot certify that a person or browser tool actually performed an operation.
Produce the report during the real browser workflow; never fabricate passed
records from this checker, a mock, a static review, or an unexecuted template.

Artifact paths are relative to the evidence JSON's directory and must stay
inside it. Put browser screenshots, recordings and logs beneath that directory.
The build directory must be a clean runnable extension containing manifest.json;
every file, including hidden files, participates in its fingerprint.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import sys


SCHEMA_VERSION = 1
REQUIRED_SCENARIOS = frozenset(("install", "native_entry", "primary_flow", "reopen", "repeat_use"))
ALLOWED_METHODS = frozenset(("real_browser_tool", "witnessed_manual"))
ALLOWED_ENTRIES = frozenset((
    "native_action", "context_menu", "keyboard_command",
    "native_side_panel", "browser_extension_entry",
))
ALLOWED_INSTALLATIONS = frozenset(("unpacked", "store", "enterprise"))
DEFAULT_E2E_PROVIDER = "playwright-mcp"
ALLOWED_PROVIDERS = frozenset((DEFAULT_E2E_PROVIDER, "chrome-devtools-mcp", "browser-mcp", "controlled-browser"))


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def nonempty_text(value):
    return isinstance(value, str) and bool(value.strip())


def safe_relative_path(value):
    if not nonempty_text(value) or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return (not path.is_absolute() and not PureWindowsPath(value).drive
            and value == path.as_posix() and all(part not in (".", "..") for part in path.parts)
            and bool(path.parts))


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint_build(build_directory):
    """Return the candidate object to copy into a real acceptance report."""
    supplied = Path(build_directory).expanduser()
    if supplied.is_symlink():
        raise ValueError("候选运行目录不能是符号链接。")
    root = supplied.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("候选运行目录不存在或不是目录。")
    manifest = root / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("候选运行目录根部必须有非符号链接的 manifest.json。")
    files = []

    def fail_walk(error):
        raise error

    for current, directories, filenames in os.walk(root, followlinks=False, onerror=fail_walk):
        for name in directories:
            path = Path(current) / name
            if path.is_symlink():
                raise ValueError(f"候选目录包含符号链接：{path.relative_to(root).as_posix()}")
        for name in filenames:
            path = Path(current) / name
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
                raise ValueError(f"候选目录含非普通文件：{path.relative_to(root).as_posix()}")
            path.resolve(strict=True).relative_to(root)
            files.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)})
    files.sort(key=lambda item: item["path"])
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"fingerprint_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(), "files": files}


def check_artifact(root, relative):
    """Check location and nonempty regular file only; do not read its contents."""
    if not safe_relative_path(relative):
        raise ValueError("证据路径必须是 JSON 同目录内的规范子路径，不允许绝对路径或 ../。")
    path = root
    for part in PurePosixPath(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("证据路径不允许符号链接。")
    path.resolve(strict=True).relative_to(root)
    details = path.stat()
    if not stat.S_ISREG(details.st_mode) or details.st_size == 0:
        raise ValueError("证据必须是非空的普通文件。")


def validate_candidate(recorded, current, errors):
    if not isinstance(recorded, dict):
        errors.append("candidate 缺失或不是对象；请从 fingerprint 命令取得真实候选目录指纹。")
        return
    entries = recorded.get("files")
    if not isinstance(entries, list) or not entries:
        errors.append("candidate.files 必须记录全部候选运行文件及 SHA-256。")
        return
    recorded_files = {}
    for entry in entries:
        if not isinstance(entry, dict) or not safe_relative_path(entry.get("path")):
            errors.append("candidate.files 中存在无效的文件路径。")
            return
        name, digest = entry["path"], entry.get("sha256")
        if name in recorded_files:
            errors.append(f"candidate.files 重复记录文件：{name}")
            return
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            errors.append(f"candidate.files 文件指纹无效：{name}")
            return
        recorded_files[name] = digest
    current_files = {item["path"]: item["sha256"] for item in current["files"]}
    if recorded_files != current_files:
        added = sorted(set(current_files) - set(recorded_files))
        removed = sorted(set(recorded_files) - set(current_files))
        changed = sorted(name for name in current_files.keys() & recorded_files.keys()
                         if current_files[name] != recorded_files[name])
        errors.append(f"候选运行文件与验收记录不一致；新增={added}，缺少={removed}，变化={changed}。请重验受影响场景并记录当前版本。")
    if recorded.get("fingerprint_sha256") != current["fingerprint_sha256"]:
        errors.append("候选目录 fingerprint_sha256 已改变或缺失，不能沿用旧验收记录。")


def validate_browser_choice(report, evidence_path, errors):
    """Require the default MCP or an evidenced user choice of a real alternative."""
    environment = report.get("environment")
    provider = environment.get("automation_provider") if isinstance(environment, dict) else None
    if not isinstance(provider, str) or provider not in ALLOWED_PROVIDERS:
        errors.append("environment.automation_provider 必须为 playwright-mcp、chrome-devtools-mcp、browser-mcp 或 controlled-browser；缺失、模拟和纯手工供应商不能通过。")
        return None
    choice = report.get("browser_choice")
    if provider == DEFAULT_E2E_PROVIDER and choice is None:
        return None
    if not isinstance(choice, dict):
        errors.append("非默认验收工具必须记录 browser_choice：先说明 Playwright MCP 不支持的原因并请用户选择，不能静默切换。")
        return None
    if choice.get("default_provider") != DEFAULT_E2E_PROVIDER:
        errors.append("browser_choice.default_provider 必须为 playwright-mcp。")
    if choice.get("selected_provider") != provider:
        errors.append("browser_choice.selected_provider 必须与 environment.automation_provider 一致。")
    if not nonempty_text(choice.get("reason")):
        errors.append("browser_choice.reason 必须说明默认 Playwright MCP 不支持的具体原因。")
    decision = choice.get("user_decision")
    if not isinstance(decision, dict) or decision.get("status") != "approved":
        errors.append("browser_choice.user_decision 必须记录用户已同意的选择 status=approved；沉默或 AI 自行决定不算授权。")
        return None
    relative = decision.get("evidence_path")
    try:
        check_artifact(evidence_path.parent, relative)
        if (evidence_path.parent / relative).resolve() == evidence_path:
            raise ValueError("验收汇总 JSON 不能充当用户选择的原始证据。")
    except (OSError, ValueError, TypeError) as error:
        errors.append(f"browser_choice.user_decision.evidence_path 无效：{error}")
        return None
    return relative


def check_acceptance(build_directory, evidence_file):
    errors = []
    result = {
        "schema_version": SCHEMA_VERSION,
        "gate_passed": False,
        "candidate_fingerprint_sha256": None,
        "required_scenarios": [],
        "checked_artifacts": 0,
        "state_updated": False,
        "claims_authenticated": False,
        "errors": errors,
        "message": "仅核对真实验收报告的完整性、证据可核查性和版本对应；不公证操作真实性，不修改项目状态。",
    }
    try:
        current = fingerprint_build(build_directory)
        result["candidate_fingerprint_sha256"] = current["fingerprint_sha256"]
    except (OSError, ValueError) as error:
        errors.append(str(error))
        return result
    supplied = Path(evidence_file).expanduser()
    if supplied.is_symlink():
        errors.append("验收 JSON 不能是符号链接。")
        return result
    try:
        evidence_path = supplied.resolve(strict=True)
        report = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        errors.append(f"无法读取验收 JSON：{error}")
        return result
    if not isinstance(report, dict) or report.get("schema_version") != SCHEMA_VERSION:
        errors.append("验收 JSON 必须是 schema_version=1 的对象。")
        return result
    validate_candidate(report.get("candidate"), current, errors)
    choice_artifact = validate_browser_choice(report, evidence_path, errors)

    environment = report.get("environment")
    if not isinstance(environment, dict):
        errors.append("缺少 environment：需要真实浏览器名称、版本、扩展 ID 和安装方式。")
    else:
        for field in ("browser_name", "browser_version", "extension_id"):
            if not nonempty_text(environment.get(field)):
                errors.append(f"environment.{field} 为空，不能证明对应浏览器与扩展。")
        if environment.get("installation_type") not in ALLOWED_INSTALLATIONS:
            errors.append("environment.installation_type 必须是 unpacked、store 或 enterprise。")

    required = report.get("required_scenarios")
    if not isinstance(required, list) or not required or not all(nonempty_text(item) for item in required):
        errors.append("required_scenarios 必须是非空的场景编号列表。")
        required = []
    if len(required) != len(set(required)):
        errors.append("required_scenarios 不允许重复编号。")
    required_set = set(required)
    result["required_scenarios"] = sorted(required_set)
    missing_minimum = REQUIRED_SCENARIOS - required_set
    if missing_minimum:
        errors.append(f"必需场景清单缺少：{', '.join(sorted(missing_minimum))}。")
    scenarios = report.get("scenarios")
    if not isinstance(scenarios, list):
        errors.append("scenarios 必须是实际执行场景记录列表。")
        scenarios = []
    seen = set()
    checked_paths = {choice_artifact} if choice_artifact else set()
    for scenario in scenarios:
        if not isinstance(scenario, dict) or not nonempty_text(scenario.get("id")):
            errors.append("scenarios 中有缺少 id 的记录。")
            continue
        scenario_id = scenario["id"]
        if scenario_id in seen:
            errors.append(f"重复场景编号：{scenario_id}。")
            continue
        seen.add(scenario_id)
        is_required = scenario_id in required_set
        if scenario.get("required") is not is_required:
            errors.append(f"{scenario_id} 的 required 与 required_scenarios 清单不一致。")
        # Optional unexecuted scenarios are allowed; all claimed passes are checked.
        if not is_required and scenario.get("status") != "passed":
            continue
        if scenario.get("status") != "passed":
            errors.append(f"必需场景 {scenario_id} 尚未 passed。")
        if scenario.get("method") not in ALLOWED_METHODS:
            errors.append(f"{scenario_id} 必须来自 real_browser_tool 或 witnessed_manual；模拟、静态检查或未执行模板不能替代。")
        steps = scenario.get("steps")
        if not isinstance(steps, list) or not steps or not all(nonempty_text(step) for step in steps):
            errors.append(f"{scenario_id} 缺少实际执行步骤 steps。")
        for field in ("expected", "actual"):
            if not nonempty_text(scenario.get(field)):
                errors.append(f"{scenario_id} 缺少 {field} 的可观察结果。")
        if scenario_id == "native_entry" and scenario.get("entry_kind") not in ALLOWED_ENTRIES:
            errors.append("native_entry 缺少真实入口类型 entry_kind；直接打开 popup.html 或普通标签页不算原生入口。")
        if scenario_id == "repeat_use":
            rounds = scenario.get("rounds")
            if (not isinstance(rounds, list) or len(rounds) < 2
                    or any(not isinstance(item, dict)
                           or not nonempty_text(item.get("entry"))
                           or not nonempty_text(item.get("outcome")) for item in rounds)):
                errors.append("repeat_use 必须记录至少两轮实际使用，每轮包含 entry 和 outcome。")
            for field in ("continuation", "exit_or_recovery"):
                if not nonempty_text(scenario.get(field)):
                    errors.append(f"repeat_use 缺少 {field}：需记录可发现的继续路径与实际退出或恢复结果。")
        artifacts = scenario.get("artifactPaths")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"{scenario_id} 缺少浏览器证据 artifactPaths。")
            continue
        for relative in artifacts:
            try:
                check_artifact(evidence_path.parent, relative)
                if (evidence_path.parent / relative).resolve() == evidence_path:
                    raise ValueError("验收汇总 JSON 不能充当自己的浏览器原始证据。")
                checked_paths.add(relative)
            except (OSError, ValueError) as error:
                errors.append(f"{scenario_id} 证据 {relative!r} 无效：{error}")
    missing_records = required_set - seen
    if missing_records:
        errors.append(f"缺少必需场景实际记录：{', '.join(sorted(missing_records))}。")
    result["checked_artifacts"] = len(checked_paths)
    result["gate_passed"] = not errors
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="检查当前插件构建是否具有完整且对应版本的真实浏览器验收记录。")
    commands = parser.add_subparsers(dest="command", required=True)
    fingerprint = commands.add_parser("fingerprint", help="输出 candidate 对象；只计算文件指纹，不生成 passed 记录")
    fingerprint.add_argument("build_directory")
    check = commands.add_parser("check", help="缺少真实验收记录或版本变化时返回非零状态")
    check.add_argument("build_directory")
    check.add_argument("--evidence", required=True, type=Path, help="真实浏览器流程生成的 JSON；证据文件放在其目录下")
    check.add_argument("--report", type=Path, help="将校验结果写入新 JSON 文件；不会覆盖或修改主状态")
    args = parser.parse_args(argv)
    try:
        if args.command == "fingerprint":
            print(json_text(fingerprint_build(args.build_directory)), end="")
            return 0
        result = check_acceptance(args.build_directory, args.evidence)
        if args.report:
            with args.report.expanduser().open("x", encoding="utf-8") as handle:
                handle.write(json_text(result))
        print(json_text(result), end="")
        return 0 if result["gate_passed"] else 1
    except (OSError, ValueError) as error:
        print(json_text({"gate_passed": False, "errors": [str(error)], "state_updated": False}),
              file=sys.stderr, end="")
        return 1


if __name__ == "__main__":
    sys.exit(main())
