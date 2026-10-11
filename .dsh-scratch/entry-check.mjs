import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { isAbsolute, resolve, dirname } from "node:path";
const file = "C:\\Users\\85292\\.dsh\\profiles\\desktop\\cordis.patch.yml";
const raw = readFileSync(file, "utf8");
// The loader's rule: an absolute or ./-relative inserted name becomes a file URL beside the patch file.
const match = /^\s*name: '(.*)'$/m.exec(raw);
const name = match[1];
const base = dirname(resolve(file));
const url = pathToFileURL(isAbsolute(name) ? name : resolve(base, name)).href;
const mod = await import(url);
console.log("resolved entry:", url);
console.log("module name:", mod.name, "| inject:", JSON.stringify(mod.inject), "| Config keys:", Object.keys(mod.Config).join(","));
const tools = new Map();
mod.apply({ tools: { register: (d) => tools.set(d.name, d) }, provide: () => {}, on: () => {}, logger: () => ({ info: () => {}, warn: () => {} }) },
  { repoRoot: "E:\\新增資料夾\\SBA-work", remote: "origin", timeoutMs: 60000, credentialsFile: "C:\\Users\\85292\\.dsh\\storages\\github-link\\credentials.json", sync: { enabled: false, ignore: [".dsh-scratch"] } });
console.log("tools registered:", [...tools.keys()].join(", "));
const out = await tools.get("github").execute({ action: "status" }, {});
console.log("--- github status ---");
console.log(out.split("\n").slice(0, 4).join("\n"));
