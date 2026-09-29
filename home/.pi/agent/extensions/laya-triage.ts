// Laya is local, not an API model. One advisory decision per ambiguous reply.
// For many calls, start `laya-ask --serve` separately to keep the model warm.
// No server starts on extension load; no background polling or extra context.
import { Type } from "typebox";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const exec = promisify(execFile);
const options = [
  "done=The task is completed",
  "blocked=The worker cannot proceed without external intervention",
  "question=The worker requests an answer",
  "working=The worker is actively progressing or investigating a failure",
  "other=The status is unclear",
];

export default function layaTriage(pi: ExtensionAPI) {
  pi.registerTool({
    name: "workflow_triage",
    label: "Laya triage",
    description: "Cheap local triage for an AMBIGUOUS short worker reply. First handle explicit DONE/BLOCKED and cmux needsInput with rules; don't call per event. Returns unknown under 0.85 confidence. Advisory only: verify before review/handoff; never approve code or control panes from this label.",
    parameters: Type.Object({ text: Type.String({ description: "One short ambiguous worker reply (not a transcript or secret)" }) }),
    async execute(_id, params) {
      const text = params.text.slice(0, 1200);
      try {
        const { stdout } = await exec("laya-ask", ["--quiet", text, "What is the worker's current status?", ...options], { timeout: 12000, maxBuffer: 20000 });
        const answer = JSON.parse(stdout)?.answers?.answer;
        const confidence = Number(answer?.answer_confidence);
        const labels = ["done", "blocked", "question", "working", "other"];
        const choice = labels.includes(answer?.choice) ? answer.choice : "other";
        const usable = Number.isFinite(confidence) && confidence >= 0.85 && choice !== "other";
        const result = { suggestion: usable ? choice : "unknown", confidence: Number.isFinite(confidence) ? confidence : null, advisory: true };
        return { content: [{ type: "text" as const, text: JSON.stringify(result) }], details: result };
      } catch (err) {
        const result = { suggestion: "unknown", confidence: null, advisory: true, error: err instanceof Error ? err.message.slice(0, 200) : "Laya unavailable" };
        return { content: [{ type: "text" as const, text: JSON.stringify(result) }], details: result };
      }
    },
  });
}
