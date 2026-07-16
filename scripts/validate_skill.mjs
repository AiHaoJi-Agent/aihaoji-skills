#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const VALIDATOR_RELATIVE_PATH = path.join(
  "skills",
  ".system",
  "skill-creator",
  "scripts",
  "quick_validate.py",
);

export function buildValidatorCandidates({ env = process.env, homeDir = os.homedir() } = {}) {
  const candidates = [];

  if (env.AIHAOJI_SKILL_VALIDATOR) {
    candidates.push(path.resolve(env.AIHAOJI_SKILL_VALIDATOR));
  }
  if (env.CODEX_HOME) {
    candidates.push(path.join(env.CODEX_HOME, VALIDATOR_RELATIVE_PATH));
  }

  candidates.push(path.join(homeDir, ".codex", VALIDATOR_RELATIVE_PATH));
  candidates.push(
    path.join(
      homeDir,
      ".agents",
      "skills",
      "skill-creator",
      "scripts",
      "quick_validate.py",
    ),
  );

  return [...new Set(candidates)];
}

export function resolveValidatorPath(candidates, existsSync = fs.existsSync) {
  return candidates.find((candidate) => existsSync(candidate)) ?? null;
}

function main() {
  const candidates = buildValidatorCandidates();
  const validatorPath = resolveValidatorPath(candidates);

  if (!validatorPath) {
    console.error("未找到官方 Skill 校验器 quick_validate.py。");
    console.error("请安装 Codex skill-creator，或设置 AIHAOJI_SKILL_VALIDATOR 指向校验器文件。");
    console.error("已检查以下位置：");
    for (const candidate of candidates) {
      console.error(`- ${candidate}`);
    }
    process.exitCode = 1;
    return;
  }

  const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const skillPath = path.join(projectRoot, "skills", "aihaoji");
  const pythonCommand = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
  const result = spawnSync(pythonCommand, [validatorPath, skillPath], { stdio: "inherit" });

  if (result.error) {
    console.error(`运行 Skill 校验器失败：${result.error.message}`);
    process.exitCode = 1;
    return;
  }

  process.exitCode = result.status ?? 1;
}

const isMain = process.argv[1]
  && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isMain) {
  main();
}
