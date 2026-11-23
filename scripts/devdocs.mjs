#!/usr/bin/env node
// Keeps the developer docs in src/content/devdocs/ in step with the OMAR code.
//
//   node scripts/devdocs.mjs sync --omar <checkout of omar main>
//       Bring main's docs up to date with the checkout (writes them from
//       scratch when there are none). Prints the summary file path.
//   node scripts/devdocs.mjs freeze <tag> --omar <omar clone with tags>
//       Write the frozen docs for a release, starting from main's. A release
//       that already has docs is never touched again.
//   node scripts/devdocs.mjs pending --omar <omar clone with tags>
//       List release tags newer than the newest frozen release.
//
// The writing is done by `codex exec` with .github/devdocs/prompt.md, run in
// the version's directory so it can only write there; afterwards the script
// checks that nothing else in this repository changed.
import { execFileSync, spawnSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const site = resolve(import.meta.dirname, "..");
const docs = join(site, "src/content/devdocs");
const prompt = readFileSync(join(site, ".github/devdocs/prompt.md"), "utf8");
const codex = process.env.CODEX_BIN || "codex";

const git = (cwd, ...args) =>
  execFileSync("git", args, { cwd, encoding: "utf8" }).trim();

function fail(message) {
  console.error(`devdocs: ${message}`);
  process.exit(1);
}

function arg(name) {
  const at = process.argv.indexOf(name);
  return at === -1 ? undefined : process.argv[at + 1];
}

// v0.4.10 sorts after v0.4.9.
const semver = (tag) =>
  tag
    .replace(/^v/, "")
    .split(/[.-]/)
    .map((part) => Number(part) || 0);
function compare(a, b) {
  const [x, y] = [semver(a), semver(b)];
  for (let i = 0; i < Math.max(x.length, y.length); i++) {
    if ((x[i] ?? 0) !== (y[i] ?? 0)) return (x[i] ?? 0) - (y[i] ?? 0);
  }
  return 0;
}

const pages = (dir) =>
  existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith(".md")) : [];
const frozen = () =>
  existsSync(docs)
    ? readdirSync(docs)
        .filter((d) => /^v\d/.test(d))
        .sort(compare)
    : [];
const readMeta = (dir) =>
  existsSync(join(dir, "_meta.json"))
    ? JSON.parse(readFileSync(join(dir, "_meta.json"), "utf8"))
    : undefined;
function writeMeta(dir, ref, commit) {
  const meta = { ref, commit, synced: new Date().toISOString().slice(0, 10) };
  writeFileSync(join(dir, "_meta.json"), JSON.stringify(meta, null, 2) + "\n");
}

// What the docs must now account for: the PRs merged in old..new. OMAR
// squash-merges, so each PR is one commit whose subject ends in (#N).
function changes(omar, from, to) {
  const log = git(omar, "log", "--format=%h %s", `${from}..${to}`);
  const stat = git(omar, "diff", "--stat=120", from, to).split("\n");
  return [
    "Merged since the docs were last synced:",
    log || "(nothing)",
    "",
    `Diff range: ${from}..${to} (run \`git -C ${omar} diff ${from} ${to} -- <path>\` to read a change)`,
    "Files changed (summary):",
    ...stat.slice(-60),
  ].join("\n");
}

// Not git(): its trim would eat the first line's leading status column.
const changed = () =>
  new Set(
    execFileSync("git", ["status", "--porcelain", "--untracked-files=all"], {
      cwd: site,
      encoding: "utf8",
    })
      .split("\n")
      .filter(Boolean)
      .map((line) => line.slice(3)),
  );

function runCodex(dir, details) {
  const before = changed();
  const summary = join(mkdtempSync(join(tmpdir(), "devdocs-")), "summary.md");
  const input = `${prompt}\n## Run details\n\n${details}\n`;
  const args = [
    "exec",
    "--sandbox",
    "workspace-write",
    "--cd",
    dir,
    "--skip-git-repo-check",
    "--ephemeral",
    "--color",
    "never",
    "--output-last-message",
    summary,
  ];
  if (process.env.DEVDOCS_MODEL)
    args.push("--model", process.env.DEVDOCS_MODEL);
  args.push("-");
  const run = spawnSync(codex, args, {
    input,
    stdio: ["pipe", "inherit", "inherit"],
  });
  if (run.status !== 0) fail(`codex exited with ${run.status}`);
  // Codex runs with write access to `dir` only, but check rather than trust.
  const own = `src/content/devdocs/${dir.split("/").pop()}/`;
  const stray = [...changed()].filter(
    (path) => !before.has(path) && !path.startsWith(own),
  );
  if (stray.length)
    fail(`codex changed files outside ${dir}:\n${stray.join("\n")}`);
  if (!pages(dir).length) fail(`codex left no pages in ${dir}`);
  return summary;
}

function sync(omar) {
  const dir = join(docs, "main");
  const head = git(omar, "rev-parse", "HEAD");
  const meta = readMeta(dir);
  const create = !pages(dir).length;
  if (!create && meta?.commit === head) {
    console.log(`devdocs: main docs already describe ${head}`);
    return;
  }
  mkdirSync(dir, { recursive: true });
  const details = [
    `Mode: ${create ? "create" : "update"}`,
    `OMAR checkout (read the code here): ${resolve(omar)}`,
    `Commit: ${head}`,
    "LINK_REF: main",
    ...(create ? [] : ["", changes(omar, meta.commit, head)]),
  ].join("\n");
  const summary = runCodex(dir, details);
  // Only a page change is worth proposing. Without one, _meta.json stays put
  // and the next run looks at these PRs again along with newer ones.
  if (!create && !git(site, "status", "--porcelain", "--", dir)) {
    console.log("devdocs: the code changes needed no page changes");
    return;
  }
  writeMeta(dir, "main", head);
  console.log(`devdocs: summary in ${summary}`);
}

function freeze(omar, tag) {
  const dir = join(docs, tag);
  if (existsSync(dir))
    fail(`${tag} already has docs, and a release's docs are frozen`);
  if (!pages(join(docs, "main")).length) fail("main has no docs to start from");
  const commit = git(omar, "rev-list", "-n", "1", tag);
  const checkout = mkdtempSync(join(tmpdir(), `omar-${tag}-`));
  git(omar, "worktree", "add", "--detach", checkout, commit);
  try {
    mkdirSync(dir);
    for (const page of pages(join(docs, "main"))) {
      cpSync(join(docs, "main", page), join(dir, page));
    }
    const details = [
      "Mode: freeze",
      `Release: ${tag}`,
      `OMAR checkout of the release (read the code here): ${checkout}`,
      `Commit: ${commit}`,
      `LINK_REF: ${commit}`,
    ].join("\n");
    const summary = runCodex(dir, details);
    writeMeta(dir, tag, commit);
    console.log(`devdocs: summary in ${summary}`);
  } finally {
    git(omar, "worktree", "remove", "--force", checkout);
  }
}

function pending(omar) {
  const newest = frozen().at(-1);
  if (!newest) return [];
  return git(omar, "tag", "--list", "v*")
    .split("\n")
    .filter((tag) => /^v\d+\.\d+\.\d+$/.test(tag) && compare(tag, newest) > 0)
    .sort(compare);
}

const [command, maybeTag] = process.argv.slice(2);
const omar =
  arg("--omar") ?? fail("--omar <path to an omar checkout> is required");
if (command === "sync") sync(omar);
else if (command === "freeze")
  freeze(omar, maybeTag ?? fail("freeze needs a tag"));
else if (command === "pending") console.log(pending(omar).join("\n"));
else fail("usage: devdocs.mjs sync|freeze <tag>|pending --omar <path>");
