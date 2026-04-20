#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import readline from "node:readline";

const DEFAULT_BASE_URL = process.env.AIHAOJI_BASE_URL || "https://openapi.readlecture.cn";
const OPENCLAW_CONFIG_PATH = path.join(os.homedir(), ".openclaw", "openclaw.json");
const SHARED_CONFIG_PATH = path.join(os.homedir(), ".aihaoji", "config.json");
const CODEX_CONFIG_PATH = path.join(os.homedir(), ".codex", "config.toml");
const CLAUDE_CONFIG_PATH = path.join(os.homedir(), "Library", "Application Support", "Claude", "claude_desktop_config.json");
const KEY_CREATE_URL = "https://openapi.readlecture.cn/zh/keys";

function normalizeBaseUrl(baseUrl) {
  return (baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
}

function getAgentOpenApiBaseUrl(baseUrl) {
  return `${normalizeBaseUrl(baseUrl)}/agent-open/api/v1`;
}


function fail(message) {
  console.error(`[error] ${message}`);
  process.exit(1);
}

function info(message) {
  console.log(`[info] ${message}`);
}

async function prompt(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

async function promptApiKey() {
  info("当前还没有配置 Ai好记 API Key。");
  info(`请先前往以下地址创建开发者密钥：${KEY_CREATE_URL}`);
  const apiKey = await prompt("请输入 Ai好记 API Key（sk-s...）: ");
  if (!apiKey) {
    fail("未输入 API Key。");
  }
  if (!apiKey.startsWith("sk-s")) {
    fail("API Key 格式不正确，必须以 sk-s 开头。");
  }
  return apiKey;
}


async function checkApiKey(baseUrl, apiKey) {
  const url = `${getAgentOpenApiBaseUrl(baseUrl)}/auth/verify`;
  const response = await fetch(url, {
    headers: {
      Authorization: apiKey,
    },
  });
  if (!response.ok) {
    let errorMessage = `API Key 校验失败：HTTP ${response.status}`;
    try {
      const payload = await response.json();
      const detail = payload?.detail ?? payload?.message ?? payload;
      if (typeof detail === "string") {
        errorMessage = detail;
      } else if (detail?.message) {
        errorMessage = detail.message;
      }
    } catch {
      // ignore json parse failure and keep default message
    }
    fail(errorMessage);
  }
  return response.json();
}

function loadJsonConfig(configPath) {
  if (!fs.existsSync(configPath)) {
    return {};
  }
  return JSON.parse(fs.readFileSync(configPath, "utf-8"));
}

function saveJsonConfig(configPath, config) {
  fs.mkdirSync(path.dirname(configPath), { recursive: true });
  fs.writeFileSync(configPath, `${JSON.stringify(config, null, 2)}\n`, "utf-8");
}

function writeOpenClawSkillConfig(config, apiKey, baseUrl) {
  const nextConfig = config ?? {};
  nextConfig.skills ??= {};
  nextConfig.skills.entries ??= {};
  nextConfig.skills.entries.aihaoji = {
    apiKey,
    env: {
      AIHAOJI_API_KEY: apiKey,
      AIHAOJI_BASE_URL: normalizeBaseUrl(baseUrl),
    },
  };
  return nextConfig;
}

function writeSharedConfig(apiKey, baseUrl, verifyData) {
  return {
    provider: "aihaoji",
    apiKey,
    baseUrl: normalizeBaseUrl(baseUrl),
    userId: verifyData?.user_id || "",
    userName: verifyData?.user_name || "",
    keyId: verifyData?.key_id || "",
    keyName: verifyData?.key_name || "",
    updatedAt: new Date().toISOString(),
  };
}

function detectHosts() {
  return {
    openclaw: fs.existsSync(path.dirname(OPENCLAW_CONFIG_PATH)) || fs.existsSync(OPENCLAW_CONFIG_PATH),
    codex: fs.existsSync(path.join(os.homedir(), ".codex")) || fs.existsSync(CODEX_CONFIG_PATH),
    claude: fs.existsSync(path.dirname(CLAUDE_CONFIG_PATH)) || fs.existsSync(CLAUDE_CONFIG_PATH),
  };
}

async function install() {
  const baseUrl = normalizeBaseUrl(DEFAULT_BASE_URL);
  info("使用 skill 仓库内静态接口文档 references/agent-open-platform.md");

  const apiKey = process.argv.find((item) => item.startsWith("--api-key="))
    ? process.argv.find((item) => item.startsWith("--api-key=")).split("=")[1]
    : await promptApiKey();

  info("校验 API Key...");
  const result = await checkApiKey(baseUrl, apiKey);
  const hosts = detectHosts();
  const verifyData = result?.data ?? {};

  const sharedConfig = writeSharedConfig(apiKey, baseUrl, verifyData);
  saveJsonConfig(SHARED_CONFIG_PATH, sharedConfig);

  if (hosts.openclaw) {
    const openclawConfig = loadJsonConfig(OPENCLAW_CONFIG_PATH);
    const nextOpenClawConfig = writeOpenClawSkillConfig(openclawConfig, apiKey, baseUrl);
    saveJsonConfig(OPENCLAW_CONFIG_PATH, nextOpenClawConfig);
    info(`已写入 OpenClaw 配置：${OPENCLAW_CONFIG_PATH}`);
  } else {
    info("未检测到 OpenClaw，本次未写入 OpenClaw 配置。");
  }

  info(`已写入 Ai好记共享配置：${SHARED_CONFIG_PATH}`);
  info(`安装完成，当前用户是：${verifyData.user_name || verifyData.user_id || "未知用户"}`);
  info(`已绑定密钥：${verifyData.key_name || verifyData.key_id || "未知密钥"}`);
  info(`检测到宿主：OpenClaw=${hosts.openclaw ? "yes" : "no"}, Codex=${hosts.codex ? "yes" : "no"}, Claude=${hosts.claude ? "yes" : "no"}`);
  if (hosts.codex) {
    info(`已检测到 Codex：${CODEX_CONFIG_PATH}`);
  }
  if (hosts.claude) {
    info(`已检测到 Claude：${CLAUDE_CONFIG_PATH}`);
  }
  info("auth/verify 校验结果如下：");
  console.log(JSON.stringify(result, null, 2));
}

async function main() {
  const command = process.argv[2];
  if (!command || command === "install" || command === "setup") {
    await install();
    return;
  }
  if (command === "help" || command === "--help" || command === "-h") {
    console.log("用法：npx aihaoji-openclaw setup");
    console.log("兼容：npx aihaoji-openclaw install");
    console.log("可选：npx aihaoji-openclaw setup --api-key=sk-sxxxxxxxx");
    return;
  }
  fail(`不支持的命令：${command}`);
}

main().catch((error) => fail(error instanceof Error ? error.message : String(error)));
