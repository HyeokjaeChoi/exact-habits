import { expect, test } from 'bun:test';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// Repo rules as tests. The rule-to-check table is docs/agents/enforcement.md.
const at = (path: string) => resolve(import.meta.dir, path);
const agents = readFileSync(at('AGENTS.md'), 'utf8');
const BEGIN = '<!-- exact:begin', END = '<!-- exact:end -->';
// Replace this hash only after `bun exact.mjs update` rewrote the block.
const BLOCK_SHA256 = 'ba896af1cc682381c6a48afaaf2e0ccb6ec764fc6bb9b2f1765b8bdd11cc9e93';

test('AGENTS.md stays a short index (Claude Code docs: under 200 lines)', () => {
  expect(agents.trimEnd().split('\n').length).toBeLessThanOrEqual(125);
});

test('CLAUDE.md has the same content as AGENTS.md', () => {
  expect(readFileSync(at('CLAUDE.md'), 'utf8')).toBe(agents);
});

test('the Exact block is first, single and unchanged', () => {
  expect(agents.startsWith(BEGIN)).toBe(true);
  expect(agents.split(BEGIN).length).toBe(2);
  expect(agents.split(END).length).toBe(2);
  const block = agents.slice(0, agents.indexOf(END) + END.length);
  expect(new Bun.CryptoHasher('sha256').update(block).digest('hex')).toBe(BLOCK_SHA256);
});

test('each link in the index points to a file', () => {
  const index = agents.slice(agents.indexOf(END));
  const dead = [...index.matchAll(/\]\((?!https?:)([^)#]+)/g)].map(m => m[1]).filter(path => !existsSync(at(path)));
  expect(dead).toEqual([]);
});

test('.contract files use native symbol and colour roles only', () => {
  const bad: string[] = [];
  for (const file of new Bun.Glob('**/*.contract').scanSync(import.meta.dir))
    readFileSync(at(file), 'utf8').split('\n').forEach((line, i) => {
      if (/symbol:sf\/|["']#[0-9a-fA-F]{3,8}["']|rgba?\(/.test(line)) bad.push(`${file}:${i + 1}`);
    });
  expect(bad).toEqual([]);
});
