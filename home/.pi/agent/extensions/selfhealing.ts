import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import os from "node:os";

type Note = {
  ts: string;
  area: string;
  severity: "low" | "medium" | "high";
  note: string;
  cwd?: string;
};

const dir = path.join(os.homedir(), ".pi", "agent", "workflow");
const notesPath = path.join(dir, "selfheal-notes.jsonl");

async function ensureDir() {
  await mkdir(dir, { recursive: true });
}

async function readNotes(): Promise<Note[]> {
  if (!existsSync(notesPath)) return [];
  const raw = await readFile(notesPath, "utf8");
  return raw
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line) as Note;
      } catch {
        return { ts: new Date().toISOString(), area: "parse-error", severity: "low", note: line } as Note;
      }
    });
}

async function appendNote(note: Note) {
  await ensureDir();
  await writeFile(notesPath, JSON.stringify(note) + "\n", { flag: "a" });
}

function parseNoteArgs(args: string): Pick<Note, "area" | "severity" | "note"> | null {
  const trimmed = args.trim();
  if (!trimmed) return null;
  let area = "general";
  let severity: Note["severity"] = "medium";
  const rest: string[] = [];
  for (const part of trimmed.split(/\s+/)) {
    if (part.startsWith("area=")) area = part.slice("area=".length) || area;
    else if (part.startsWith("severity=")) {
      const v = part.slice("severity=".length);
      if (v === "low" || v === "medium" || v === "high") severity = v;
      else rest.push(part);
    } else rest.push(part);
  }
  const note = rest.join(" ").trim();
  return note ? { area, severity, note } : null;
}

function formatNote(n: Note, i: number) {
  return `${i + 1}. [${n.severity}] ${n.area} — ${n.note} (${n.ts.slice(0, 10)})`;
}

export default function selfHealing(pi: ExtensionAPI) {
  pi.registerCommand("selfheal", {
    description: "Lean workflow self-healing notes: note/list/run/clear",
    getArgumentCompletions: (prefix) => {
      return ["note", "list", "run", "clear"].filter((x) => x.startsWith(prefix)).map((value) => ({ value, label: value }));
    },
    handler: async (args, ctx) => {
      const [cmd = "list", ...restParts] = args.trim().split(/\s+/).filter(Boolean);
      const rest = restParts.join(" ");

      if (cmd === "note") {
        const parsed = parseNoteArgs(rest);
        if (!parsed) {
          ctx.ui.notify('Usage: /selfheal note [area=reviewer] [severity=low|medium|high] "problem..."', "warning");
          return;
        }
        await appendNote({ ts: new Date().toISOString(), cwd: ctx.cwd, ...parsed });
        ctx.ui.notify(`Self-heal note saved: ${parsed.area}`, "info");
        return;
      }

      if (cmd === "list") {
        const notes = await readNotes();
        if (!notes.length) {
          ctx.ui.notify("No self-heal notes yet", "info");
          return;
        }
        const latest = notes.slice(-20).map(formatNote).join("\n");
        ctx.ui.notify(latest, "info");
        return;
      }

      if (cmd === "clear") {
        await ensureDir();
        await writeFile(notesPath, "", "utf8");
        ctx.ui.notify("Self-heal notes cleared", "info");
        return;
      }

      if (cmd === "run") {
        const notes = await readNotes();
        const scope = rest.trim() || "general workflow improvement";
        const noteText = notes.length ? notes.slice(-50).map(formatNote).join("\n") : "No saved notes.";
        const prompt = `Run a lightweight self-healing review for my Pi/cmux workflow.\n\nScope: ${scope}\n\nSaved notes:\n${noteText}\n\nInstructions:\n- Diagnose workflow, skill, prompt, or extension problems.\n- Focus on concrete fixes, not generic advice.\n- If edits are warranted, propose exact files and patch plan first.\n- Do not apply changes until I explicitly approve.\n- Keep it concise.`;
        if (!ctx.isIdle()) {
          pi.sendUserMessage(prompt, { deliverAs: "followUp" });
          ctx.ui.notify("Self-heal run queued", "info");
        } else {
          pi.sendUserMessage(prompt);
        }
        return;
      }

      ctx.ui.notify("Usage: /selfheal note|list|run|clear", "warning");
    },
  });
}
