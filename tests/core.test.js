import assert from "node:assert/strict";
import test from "node:test";

import { maskEmail, parseAccounts, redactText, sanitizedExport } from "../web/core.js";

const line = "lina@example.com----12345678-1234-4234-9234-1234567890ab----synthetic-refresh-token-value----consumers";

test("parses modern OAuth record without a password field", () => {
  const records = parseAccounts(line);
  assert.equal(records.length, 1);
  assert.equal(records[0].tenant, "consumers");
  assert.equal(Object.hasOwn(records[0], "password"), false);
});

test("rejects duplicates and malformed client IDs", () => {
  assert.throws(() => parseAccounts(`${line}\n${line}`), /重复/);
  assert.throws(() => parseAccounts("lina@example.com----bad----token"), /UUID/);
});

test("masks addresses in sender exports", () => {
  assert.equal(maskEmail("lina@example.com"), "l***@example.com");
  assert.equal(redactText("Lina <lina@example.com>"), "Lina <l***@example.com>");
  const exported = sanitizedExport([
    {
      account: "l***@example.com",
      status: "ok",
      messages: [{ sender: "Lina <lina@example.com>", subject: "Private", preview: "Secret", codes: ["482731"] }],
    },
  ]);
  assert.deepEqual(exported[0].messages[0], { date: undefined, code_count: 1 });
  assert.equal(JSON.stringify(exported).includes("lina@example.com"), false);
  assert.equal(JSON.stringify(exported).includes("482731"), false);
});
