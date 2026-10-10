import test from "node:test";
import assert from "node:assert/strict";
import { slugify, excerpt } from "../src/posts.js";

test("slugify", () => {
  assert.equal(slugify("Hello World"), "hello-world");
});
test("excerpt truncates", () => {
  assert.equal(excerpt("a".repeat(100), 10), "a".repeat(10) + "...");
});
