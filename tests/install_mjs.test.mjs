import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  buildAuthorizationHeaders,
  detectHosts,
  validateVerifyResponse,
  saveJsonConfig,
  summarizeVerifyResult,
} from "../skills/aihaoji/scripts/install.mjs";

test("uses the raw API key as the Authorization header", () => {
  assert.deepEqual(buildAuthorizationHeaders("sk-sraw"), {
    Authorization: "sk-sraw",
  });
});

test("writes secret config with owner-only permissions", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "aihaoji-install-"));
  const configPath = path.join(directory, "config.json");

  saveJsonConfig(configPath, { apiKey: "sk-sraw" });

  assert.equal(fs.statSync(configPath).mode & 0o777, 0o600);
});

test("verify summary hides internal IDs", () => {
  const summary = summarizeVerifyResult({
    code: 0,
    message: "success",
    data: {
      valid: true,
      membership_active: true,
      key_status: "active",
      permissions: ["note:list", "folder:list"],
      user_id: "user-secret",
      key_id: "key-secret",
    },
  });
  const serialized = JSON.stringify(summary);

  assert.equal(serialized.includes("user-secret"), false);
  assert.equal(serialized.includes("key-secret"), false);
  assert.equal(serialized.includes("user_id"), false);
  assert.equal(serialized.includes("key_id"), false);
  assert.equal(summary.data.valid, true);
});

test("rejects a business-level API key validation failure", () => {
  assert.throws(
    () => validateVerifyResponse({
      code: 40101,
      message: "invalid key",
      data: {
        valid: false,
        membership_active: false,
        key_status: "disabled",
      },
    }),
    /invalid key/,
  );
});

test("detects current Codex, Claude Code, and Hermes skill directories", () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "aihaoji-hosts-"));
  fs.mkdirSync(path.join(home, ".agents", "skills"), { recursive: true });
  fs.mkdirSync(path.join(home, ".claude", "skills"), { recursive: true });
  fs.mkdirSync(path.join(home, ".hermes", "skills"), { recursive: true });

  const hosts = detectHosts(home);

  assert.equal(hosts.codex, true);
  assert.equal(hosts.claude, true);
  assert.equal(hosts.hermes, true);
});

test("detects Hermes config without misreporting Claude Desktop as Claude Code", () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "aihaoji-hosts-"));
  fs.mkdirSync(path.join(home, "Library", "Application Support", "Claude"), { recursive: true });
  fs.writeFileSync(
    path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json"),
    "{}",
  );
  fs.mkdirSync(path.join(home, ".hermes"), { recursive: true });
  fs.writeFileSync(
    path.join(home, ".hermes", "config.yaml"),
    "skills:\n  external_dirs:\n    - ~/.agents/skills\n",
  );

  const hosts = detectHosts(home);

  assert.equal(hosts.claude, false);
  assert.equal(hosts.hermes, true);
});

test("runs the CLI when npm invokes it through a bin symlink", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "aihaoji-bin-"));
  const binPath = path.join(directory, "aihaoji-skills");
  const scriptPath = fileURLToPath(new URL("../skills/aihaoji/scripts/install.mjs", import.meta.url));
  fs.symlinkSync(scriptPath, binPath);

  const result = spawnSync(process.execPath, [binPath, "--help"], { encoding: "utf-8" });

  assert.equal(result.status, 0);
  assert.match(result.stdout, /npx aihaoji-skills setup/);
});
