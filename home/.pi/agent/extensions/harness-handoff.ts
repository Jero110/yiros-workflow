import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile as execFileCb } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";

const execFile = promisify(execFileCb);

async function run(cmd: string, args: string[], cwd?: string) {
  return execFile(cmd, args, { cwd, env: process.env });
}

function parseSurface(stdout: string): string | undefined {
  const match = stdout.match(/surface:([^\s]+)/);
  return match ? match[1] : undefined;
}

function splitArgs(args: string): string[] {
  return args.match(/(?:[^\s"]+|"[^"]*")+/g)?.map((s) => s.replace(/^"|"$/g, "")) ?? [];
}

export default function (pi: ExtensionAPI) {
  pi.registerCommand("to-cc", {
    description: "Open a Claude Code pane from Pi. Usage: /to-cc [--close] [model] [brief]",
    handler: async (args, ctx) => {
      const parts = splitArgs(args.trim());
      const closePi = parts[0] === "--close";
      if (closePi) parts.shift();

      const model = parts[0] && !parts[0].startsWith("-") ? parts.shift()! : "opus";
      const brief = parts.join(" ").trim();
      const cwd = process.cwd();
      const session = `cc-handoff-${new Date().toISOString().replace(/[:.]/g, "-")}`;

      try {
        const command = `cd ${JSON.stringify(cwd)} && cc ${session} --model ${model}`;
        const { stdout } = await run("cmux", ["new-pane", "--direction", "right", "--focus", "false", "--command", command]);
        const surface = parseSurface(stdout);

        if (surface && brief) {
          await new Promise((resolve) => setTimeout(resolve, 1200));
          await run("cmux", ["send", "--surface", surface, brief]);
          await run("cmux", ["send-key", "--surface", surface, "enter"]);
        }

        ctx.ui.notify(`Opened Claude Code ${model}${surface ? ` on ${surface}` : ""}`, "info");
        if (closePi) ctx.shutdown();
      } catch (err) {
        ctx.ui.notify(`Failed to open Claude Code: ${err instanceof Error ? err.message : String(err)}`, "error");
      }
    },
  });

  pi.registerCommand("cc-executor", {
    description: "Open a Claude Code executor pane for a planner plan. Usage: /cc-executor [--close] <plan.md> [model]",
    handler: async (args, ctx) => {
      const parts = splitArgs(args.trim());
      const closePi = parts[0] === "--close";
      if (closePi) parts.shift();

      const planPath = parts.shift();
      if (!planPath) {
        ctx.ui.notify("Usage: /cc-executor [--close] <plan.md> [model]", "error");
        return;
      }

      const model = parts.shift() ?? "opus";
      const cwd = process.cwd();
      const project = path.basename(planPath).replace(/\.md$/, "").replace(/^\d{4}-\d{2}-\d{2}-/, "");
      const session = `${project}-executor`;
      const brief = `Run the executor skill on ${planPath}. Load cmux and harnesses first. Use Claude Code for planner/executor judgment and Pi for routine workers when Harness:auto allows it.`;

      try {
        const command = `cd ${JSON.stringify(cwd)} && cc ${session} --model ${model}`;
        const { stdout } = await run("cmux", ["new-pane", "--direction", "right", "--focus", "false", "--command", command]);
        const surface = parseSurface(stdout);

        if (surface) {
          await new Promise((resolve) => setTimeout(resolve, 1200));
          await run("cmux", ["send", "--surface", surface, brief]);
          await run("cmux", ["send-key", "--surface", surface, "enter"]);
        }

        ctx.ui.notify(`Opened Claude executor ${model}${surface ? ` on ${surface}` : ""}`, "info");
        if (closePi) ctx.shutdown();
      } catch (err) {
        ctx.ui.notify(`Failed to open Claude executor: ${err instanceof Error ? err.message : String(err)}`, "error");
      }
    },
  });
}
