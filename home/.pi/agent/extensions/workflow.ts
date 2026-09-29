import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const exec = promisify(execFile);
const inbox = `${process.env.HOME}/.claude/skills/harnesses/scripts/agent-inbox.py`;

type Result = { ok: boolean; text: string };
async function run(bin: string, args: string[], timeout = 6000): Promise<Result> {
  try {
    const r = await exec(bin, args, { timeout, maxBuffer: 512_000 });
    return { ok: true, text: r.stdout.trim() };
  } catch (e: any) {
    return { ok: false, text: `${e.stdout ?? ""}\n${e.stderr ?? e.message}`.trim() };
  }
}

function workspaceSurfaces(text: string, workspace: string): Set<string> {
  try {
    const data = JSON.parse(text);
    const ws = data.windows?.flatMap((w: any) => w.workspaces ?? []).find((w: any) => w.id === workspace);
    return new Set((ws?.panes ?? []).flatMap((p: any) => [...(p.surface_refs ?? []), ...(p.surface_ids ?? [])]));
  } catch {
    return new Set();
  }
}

function pidAlive(pid: unknown): boolean {
  const n = Number(pid);
  if (!Number.isInteger(n) || n <= 0) return false;
  try {
    process.kill(n, 0);
    return true;
  } catch {
    return false;
  }
}

function localNotifications(text: string, workspace: string): string {
  // cmux rows: index:id|workspace-uuid|surface-uuid|read|title|subtitle|body|timestamp
  return text.split(/\r?\n/).filter((line) => line.split("|")[1] === workspace).slice(-12).join("\n") || "ninguna";
}

function sessions(text: string, workspace: string, liveSurfaces: Set<string>) {
  try {
    const records = JSON.parse(text).sessions;
    if (!Array.isArray(records)) return "cmux sessions: formato desconocido";
    const active = records.filter((s: any) =>
      s.workspace_id === workspace &&
      s.active_for_surface &&
      (liveSurfaces.has(s.surface_id) || liveSurfaces.has(s.surface_ref) || pidAlive(s.pid))
    );
    return active.map((s: any) => `${s.agent} ${s.agent_lifecycle ?? "unknown"} ${s.surface_id ?? ""} ${s.cwd ?? ""}`).join("\n") || "Sin agentes activos registrados";
  } catch {
    return "No se pudo interpretar cmux sessions";
  }
}

export default function workflow(pi: ExtensionAPI) {
  pi.registerCommand("workflow", {
    description: "Cockpit cmux liviano: status, collect, watch, role",
    getArgumentCompletions: (prefix) => ["status", "collect", "watch", "role"].filter((s) => s.startsWith(prefix)).map((value) => ({ value, label: value })),
    handler: async (args, ctx) => {
      const [action = "status", ...rest] = args.trim().split(/\s+/);
      const workspace = process.env.CMUX_WORKSPACE_ID;
      if (!workspace) {
        ctx.ui.notify("Fuera de cmux: CMUX_WORKSPACE_ID no existe", "warning");
        return;
      }
      if (action === "role") {
        const title = rest.join(" ").trim();
        if (!/^(planner|executor|worker|reviewer)(?:[- ][a-zA-Z0-9._-]+)?$/.test(title)) {
          ctx.ui.notify("Uso: /workflow role planner|executor|worker-<task>|reviewer-<task>", "warning");
          return;
        }
        const [id, tree] = await Promise.all([
          run("cmux", ["identify", "--json"]),
          run("cmux", ["tree", "--workspace", workspace, "--json"]),
        ]);
        if (!id.ok || !tree.ok) {
          ctx.ui.notify("No pude verificar tu surface en cmux", "error");
          return;
        }
        try {
          const caller = JSON.parse(id.text).caller;
          if (!caller?.surface_ref || !workspaceSurfaces(tree.text, workspace).has(caller.surface_ref)) throw Error("surface fuera del workspace");
          const renamed = await run("cmux", ["rename-tab", "--surface", caller.surface_ref, title]);
          ctx.ui.notify(renamed.ok ? `Tab: ${title}` : `No pude renombrar: ${renamed.text}`, renamed.ok ? "info" : "error");
        } catch {
          ctx.ui.notify("No pude verificar tu surface en este workspace", "error");
        }
        return;
      }
      if (action === "watch") {
        if (!rest.length || rest.some((s) => !/^surface:\d+$/.test(s))) {
          ctx.ui.notify("Uso: /workflow watch surface:12 [surface:13] (espera hasta 60s)", "warning");
          return;
        }
        const tree = await run("cmux", ["tree", "--workspace", workspace, "--json"]);
        if (!tree.ok) {
          ctx.ui.notify(`No pude verificar workspace: ${tree.text}`, "error");
          return;
        }
        const allowed = workspaceSurfaces(tree.text, workspace);
        if (rest.some((s) => !allowed.has(s))) {
          ctx.ui.notify("Rechazado: una surface no pertenece a este workspace", "warning");
          return;
        }
        const result = await run(inbox, ["--state", `workflow-${workspace}`, "--timeout", "60", ...rest.flatMap((s) => ["--surface", s])], 66_000);
        ctx.ui.notify(result.text || "Sin novedades", result.ok ? "info" : "warning");
        return;
      }
      if (action !== "status" && action !== "collect") {
        ctx.ui.notify("Uso: /workflow status | collect | watch surface:N | role <rol-tarea>", "warning");
        return;
      }
      const [tree, treeJson, agents, notifications] = await Promise.all([
        run("cmux", ["tree", "--workspace", workspace], 5000),
        run("cmux", ["tree", "--workspace", workspace, "--json", "--id-format", "both"], 5000),
        run("cmux", ["sessions", "--workspace", workspace, "--json"], 6000),
        action === "collect" ? run("cmux", ["list-notifications"], 5000) : Promise.resolve({ ok: true, text: "" }),
      ]);
      if (!tree.ok && !agents.ok) {
        ctx.ui.notify(`cmux no responde: ${tree.text || agents.text}`, "error");
        return;
      }
      const liveSurfaces = treeJson.ok ? workspaceSurfaces(treeJson.text, workspace) : new Set<string>();
      const output = [`Workspace: ${workspace}`, sessions(agents.text, workspace, liveSurfaces), `Panes:\n${tree.text.slice(0, 2000)}`];
      if (action === "collect") output.push(`Notificaciones locales:\n${localNotifications(notifications.text, workspace).slice(-2000)}`);
      ctx.ui.notify(output.join("\n\n"), "info");
    },
  });
}
