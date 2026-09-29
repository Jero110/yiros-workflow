import type { AssistantMessage } from "@earendil-works/pi-ai";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { truncateToWidth } from "@earendil-works/pi-tui";
import { execFile as execFileCb, spawn } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCb);

type LimitStatus = {
  label: string;
  fiveHour?: number;
  weekly?: number;
  resetAt?: number;
  weeklyResetAt?: number;
  note?: string;
};

type Cache = {
  claude: LimitStatus;
  openai: LimitStatus;
  pi: LimitStatus;
  updated: string;
};

const cache: Cache = {
  claude: { label: "Claude", note: "…" },
  openai: { label: "Codex", note: "…" },
  pi: { label: "Pi", note: "…" },
  updated: "never",
};

let enabled = true;
let timer: NodeJS.Timeout | undefined;
let refreshInFlight: Promise<void> | undefined;

function cleanPath(): string {
  return (process.env.PATH ?? "")
    .split(":")
    .filter((p) => !p.includes("cmux-cli-shims"))
    .join(":");
}

async function cmd(name: string, args: string[], timeout = 25000): Promise<string> {
  const { stdout, stderr } = await execFile(name, args, {
    timeout,
    env: { ...process.env, PATH: cleanPath() },
  });
  return `${stdout}${stderr}`.trim();
}

function oneLine(s: string): string {
  return s.replace(/\x1b\[[0-9;?]*[A-Za-z]/g, "").replace(/\s+/g, " ").trim();
}

function fmt(n: number): string {
  if (!Number.isFinite(n)) return "0";
  return n < 1000 ? `${Math.round(n)}` : `${(n / 1000).toFixed(1)}k`;
}

function clock(epochSeconds?: number): string {
  if (!epochSeconds) return "--:--";
  return new Date(epochSeconds * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

function day(epochSeconds?: number): string {
  if (!epochSeconds) return "--";
  return new Date(epochSeconds * 1000).toLocaleDateString([], { weekday: "short" });
}

const ui = {
  reset: "\x1b[0m",
  soft: "\x1b[38;2;232;226;242m",
  text: "\x1b[38;2;216;211;223m",
  muted: "\x1b[38;2;180;172;196m",
  dim: "\x1b[38;2;128;120;142m",
  line: "\x1b[38;2;72;66;82m",
  purple: "\x1b[38;2;201;178;230m",
  blue: "\x1b[38;2;165;191;218m",
  green: "\x1b[38;2;184;172;214m",
  amber: "\x1b[38;2;196;166;106m",
  red: "\x1b[38;2;201;147;120m",
};

function c(color: keyof typeof ui, text: string): string {
  return `${ui[color]}${text}${ui.reset}`;
}

function sep(): string {
  return c("line", "  ·  ");
}

function bar(n?: number, size = 10): string {
  if (!Number.isFinite(n)) return c("dim", "──────────");
  const pct = Math.max(0, Math.min(100, Math.round(n!)));
  const full = Math.round((pct / 100) * size);
  const color = pct >= 90 ? "red" : pct >= 70 ? "amber" : pct >= 45 ? "blue" : "green";
  return c(color, "━".repeat(full)) + c("line", "━".repeat(size - full));
}

function parseClaudeReset(text?: string): number | undefined {
  if (!text) return undefined;

  // Claude prints e.g. "resets Sep 16 at 6:50pm (America/Mexico_City)".
  // Date.parse cannot read the "at", and the string omits the year.
  const match = text.match(/resets\s+([A-Za-z]+)\s+(\d{1,2})\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)/i);
  if (!match) return undefined;

  const [, month, day, hour, minute = "00", ampm] = match;
  const parsed = Date.parse(`${month} ${day} ${new Date().getFullYear()} ${hour}:${minute} ${ampm.toUpperCase()}`);
  return Number.isFinite(parsed) ? Math.floor(parsed / 1000) : undefined;
}

function parseClaudeUsage(out: string): LimitStatus {
  const sessionLine = out.match(/Current session:\s*(\d+)% used[^\n]*/i)?.[0];
  const weekLine = out.match(/Current week \(all models\):\s*(\d+)% used[^\n]*/i)?.[0];
  const fiveHour = sessionLine ? Number(sessionLine.match(/(\d+)%/)?.[1]) : undefined;
  const weekly = weekLine ? Number(weekLine.match(/(\d+)%/)?.[1]) : undefined;
  return {
    label: "Claude",
    fiveHour,
    weekly,
    resetAt: parseClaudeReset(sessionLine),
    weeklyResetAt: parseClaudeReset(weekLine),
    note: fiveHour === undefined && weekly === undefined ? oneLine(out).slice(0, 36) : undefined,
  };
}

async function readPiRateLimits(): Promise<LimitStatus> {
  const authPath = join(process.env.HOME ?? "", ".pi", "agent", "auth.json");
  const raw = JSON.parse(await readFile(authPath, "utf8"));
  const piAuth = raw[process.env.PI_PROVIDER ?? "openai-codex"] ?? raw["openai-codex"];
  if (!piAuth?.access || !piAuth?.refresh || !piAuth?.accountId) return { label: "Pi", note: "no openai-codex auth" };

  const dir = await mkdtemp(join(tmpdir(), "pi-codex-auth-"));
  try {
    await writeFile(
      join(dir, "auth.json"),
      JSON.stringify({
        auth_mode: "chatgpt",
        OPENAI_API_KEY: null,
        tokens: {
          // Codex CLI requires id_token to exist; Pi stores only the access JWT.
          // For account/rateLimits/read this is enough and avoids touching ~/.codex.
          id_token: piAuth.access,
          access_token: piAuth.access,
          refresh_token: piAuth.refresh,
          account_id: piAuth.accountId,
        },
        last_refresh: new Date().toISOString(),
      }),
      { mode: 0o600 },
    );
    return await readOpenAIRateLimits({ CODEX_HOME: dir }, "Pi");
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

async function readOpenAIRateLimits(extraEnv: Record<string, string> = {}, label = "Codex"): Promise<LimitStatus> {
  return await new Promise((resolve, reject) => {
    const child = spawn("codex", ["app-server", "--stdio"], {
      env: { ...process.env, ...extraEnv, PATH: cleanPath() },
      stdio: ["pipe", "pipe", "pipe"],
    });

    let buffer = "";
    let stderr = "";
    let done = false;
    const finish = (fn: () => void) => {
      if (done) return;
      done = true;
      clearTimeout(timeout);
      child.kill();
      fn();
    };
    const timeout = setTimeout(() => finish(() => reject(new Error("codex app-server timed out"))), 25000);

    child.stdout.on("data", (buf) => {
      buffer += buf.toString();
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.includes('"id":2')) continue;
        try {
          const msg = JSON.parse(line);
          const rl = msg.result?.rateLimitsByLimitId?.codex ?? msg.result?.rateLimits;
          if (!rl) continue;
          finish(() =>
            resolve({
              label,
              fiveHour: Number(rl.primary?.usedPercent ?? NaN),
              weekly: Number(rl.secondary?.usedPercent ?? NaN),
              resetAt: Number(rl.primary?.resetsAt ?? NaN),
              weeklyResetAt: Number(rl.secondary?.resetsAt ?? NaN),
            }),
          );
        } catch {
          // keep waiting for a complete JSON line
        }
      }
    });
    child.stderr.on("data", (buf) => (stderr += buf.toString()));
    child.on("error", (err) => finish(() => reject(err)));
    child.on("exit", () => {
      if (!done) finish(() => reject(new Error(stderr.trim() || "codex app-server exited before rate limits")));
    });

    child.stdin.write(
      JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
          clientInfo: { name: "pi-usage-footer", version: "0.2" },
          capabilities: { experimentalApi: true },
        },
      }) + "\n",
    );
    child.stdin.write(
      JSON.stringify({
        jsonrpc: "2.0",
        id: 2,
        method: "account/rateLimits/read",
        params: { excludeResetCreditDetails: true, supportsLunaReserve: true },
      }) + "\n",
    );
  });
}

async function refresh(): Promise<void> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      cache.claude = parseClaudeUsage(await cmd("claude", ["-p", "/usage"], 35000));
    } catch (err) {
      cache.claude = { label: "Claude", note: `error: ${err instanceof Error ? err.message.split("\n")[0] : String(err)}` };
    }

    try {
      cache.openai = await readOpenAIRateLimits();
    } catch (err) {
      try {
        const login = oneLine(await cmd("codex", ["login", "status"], 20000));
        cache.openai = { label: "Codex", note: /Logged in using ChatGPT/i.test(login) ? "ChatGPT ✓" : login.slice(0, 32) };
      } catch {
        cache.openai = { label: "Codex", note: `error: ${err instanceof Error ? err.message.split("\n")[0] : String(err)}` };
      }
    }

    try {
      cache.pi = await readPiRateLimits();
    } catch (err) {
      // A codex app-server timeout here used to be an unhandled rejection that killed Pi.
      // Keep the last known numbers; only show the error if we never had any.
      if (cache.pi.fiveHour === undefined) cache.pi = { label: "Pi", note: `error: ${err instanceof Error ? err.message.split("\n")[0] : String(err)}` };
    }
    cache.updated = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  })().finally(() => {
    refreshInFlight = undefined;
  });
  return refreshInFlight;
}

function mountFooter(ctx: ExtensionContext, notify = false) {
  if (!enabled || ctx.mode !== "tui") return;

  ctx.ui.setFooter((tui, _theme, footerData) => {
    const unsub = footerData.onBranchChange(() => tui.requestRender());
    const repaint = setInterval(() => tui.requestRender(), 15 * 1000);

    const pct = (n?: number) => {
      if (!Number.isFinite(n)) return c("dim", "--%");
      const rounded = Math.round(n!);
      const color = rounded >= 90 ? "red" : rounded >= 70 ? "amber" : rounded >= 45 ? "blue" : "green";
      return c(color, `${rounded}%`.padStart(4));
    };

    const limitLine = (s: LimitStatus) => {
      const name = s.label.toLowerCase().padEnd(6);
      if (s.note) return [c("muted", name), c("line", " ─ "), c("text", s.note)].join("");
      return [
        c("muted", name),
        c("line", "  "),
        c("dim", "5h "),
        bar(s.fiveHour),
        c("line", " "),
        pct(s.fiveHour),
        c("line", " "),
        c("dim", "reset "),
        c("text", clock(s.resetAt)),
        c("line", "   "),
        c("dim", "week "),
        pct(s.weekly),
        c("line", " "),
        c("dim", "reset "),
        c("text", day(s.weeklyResetAt)),
      ].join("");
    };

    return {
      dispose() {
        unsub();
        clearInterval(repaint);
      },
      invalidate() {},
      render(width: number): string[] {
        let input = 0;
        let output = 0;
        let cost = 0;
        for (const e of ctx.sessionManager.getBranch()) {
          if (e.type === "message" && e.message.role === "assistant") {
            const m = e.message as AssistantMessage;
            input += m.usage.input;
            output += m.usage.output;
            cost += m.usage.cost.total;
          }
        }

        const cwd = ctx.cwd.split("/").filter(Boolean).pop() ?? "~";
        const model = ctx.model?.id ?? "no-model";
        const usage = ctx.getContextUsage();
        const branch = footerData.getGitBranch();

        const line1 = [
          c("soft", `~/${cwd}`),
          branch ? c("dim", `  ${branch}`) : "",
          sep(),
          c("purple", model),
          sep(),
          c("muted", "ctx "),
          c("text", usage?.tokens == null ? "--" : `${fmt(usage.tokens)}/${fmt(usage.contextWindow)}`),
          c("dim", usage?.tokens == null ? "" : ` ${Math.round(usage.percent ?? 0)}%`),
          sep(),
          c("muted", "↑"),
          c("text", fmt(input)),
          c("line", " "),
          c("muted", "↓"),
          c("text", fmt(output)),
          sep(),
          c("green", `$${cost.toFixed(3)}`),
        ].join("");

        return [line1, limitLine(cache.openai), limitLine(cache.pi), limitLine(cache.claude)].map((line) => truncateToWidth(line, width));
      },
    };
  });

  if (!timer) timer = setInterval(() => void refresh(), 5 * 60 * 1000);
  void refresh();
  if (notify) ctx.ui.notify("Pi footer minimal enabled", "info");
}

export default function (pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    mountFooter(ctx);
  });

  pi.registerCommand("usage-refresh", {
    description: "Refresh OpenAI and Claude account status for the Pi footer",
    handler: async (_args, ctx) => {
      await refresh();
      ctx.ui.notify(`Usage refreshed: OpenAI ${cache.openai.fiveHour ?? "?"}% · Claude ${cache.claude.fiveHour ?? "?"}%`, "info");
    },
  });

  pi.registerCommand("usage-footer", {
    description: "Toggle the minimal 4-line Pi footer",
    handler: async (_args, ctx) => {
      enabled = !enabled;
      if (!enabled) {
        if (timer) clearInterval(timer);
        timer = undefined;
        ctx.ui.setFooter(undefined);
        ctx.ui.notify("Pi footer disabled", "info");
        return;
      }
      mountFooter(ctx, true);
    },
  });
}
