import assert from "node:assert/strict";
import test from "node:test";

import { normalizeTheme, resolveTheme } from "./theme.ts";

test("les thèmes Unity et Retro utilisent les mêmes identifiants que l'application", () => {
	assert.equal(normalizeTheme("unity-bonta"), "unity-bonta");
	assert.equal(normalizeTheme("dwm-retro", "retro"), "dwm-retro");
	assert.equal(resolveTheme("unity-wabbit").accent, "#acc862");
});

test("un ancien thème ou une valeur invalide reçoit un thème sûr", () => {
	assert.equal(normalizeTheme("dwm-dark"), "unity-standard");
	assert.equal(normalizeTheme("arc", "retro"), "dwm-retro");
});
