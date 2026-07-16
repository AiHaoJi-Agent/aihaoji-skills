import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  buildValidatorCandidates,
  resolveValidatorPath,
} from "../scripts/validate_skill.mjs";

test("prefers an explicitly configured skill validator", () => {
  const candidates = buildValidatorCandidates({
    env: {
      AIHAOJI_SKILL_VALIDATOR: "/opt/skill-validator/quick_validate.py",
      CODEX_HOME: "/opt/codex",
    },
    homeDir: "/home/example",
  });

  assert.equal(candidates[0], "/opt/skill-validator/quick_validate.py");
});

test("uses CODEX_HOME before the default user directory", () => {
  const candidates = buildValidatorCandidates({
    env: { CODEX_HOME: "/opt/codex" },
    homeDir: "/home/example",
  });

  assert.equal(
    candidates[0],
    path.join(
      "/opt/codex",
      "skills",
      ".system",
      "skill-creator",
      "scripts",
      "quick_validate.py",
    ),
  );
  assert.equal(
    candidates[1],
    path.join(
      "/home/example",
      ".codex",
      "skills",
      ".system",
      "skill-creator",
      "scripts",
      "quick_validate.py",
    ),
  );
});

test("resolves the first validator that exists", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "aihaoji-validator-"));
  const missing = path.join(directory, "missing.py");
  const existing = path.join(directory, "quick_validate.py");
  fs.writeFileSync(existing, "# test validator\n");

  assert.equal(resolveValidatorPath([missing, existing]), existing);
});

test("returns null when no validator exists", () => {
  assert.equal(
    resolveValidatorPath(["/missing/first.py", "/missing/second.py"]),
    null,
  );
});
