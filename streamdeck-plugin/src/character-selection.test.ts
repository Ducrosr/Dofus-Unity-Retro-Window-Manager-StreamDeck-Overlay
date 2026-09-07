import assert from "node:assert/strict";
import test from "node:test";

import { findSelectedWindow } from "./character-selection.ts";
import { characterPreferenceKey } from "./display-preferences.ts";
import type { DofusWindow, DwmStatus } from "./dwm-client";

const windows: DofusWindow[] = [
	{
		slot: 1,
		position: 1,
		hwnd: 101,
		pseudo: "Nealla",
		alias: "",
		name: "Nealla",
		character_class: "Pandawa",
		title: "Nealla - Pandawa - Dofus",
		active: true,
	},
	{
		slot: 2,
		position: null,
		hwnd: 102,
		pseudo: "Nat",
		alias: "",
		name: "Nat",
		character_class: "Eniripsa",
		title: "Nat - Eniripsa - Dofus",
		active: false,
		ignored: true,
	},
];

const status: DwmStatus = {
	api_version: 1,
	app_version: "2.15.1",
	game_mode: "unity",
	windows,
};

test("une case absente reste réservée jusqu’à la reconnexion", () => {
	const offline = { ...windows[0], hwnd: -1, available: false };
	const disconnected = { ...status, windows: [offline, windows[1]] };
	assert.equal(findSelectedWindow(disconnected, { slot: 1 })?.pseudo, "Nealla");
	assert.equal(findSelectedWindow(disconnected, { slot: 1 })?.available, false);
	assert.equal(findSelectedWindow(disconnected, { slot: 2 })?.hwnd, 102);
	const reconnected = { ...status, windows: [{ ...offline, hwnd: 900, available: true }, windows[1]] };
	assert.equal(findSelectedWindow(reconnected, { slot: 1 })?.hwnd, 900);
});

test("une ancienne association par case est migrable", () => {
	assert.equal(findSelectedWindow(status, { slot: "2" })?.pseudo, "Nat");
});

test("la case est prioritaire afin que le bouton suive l'ordre de l'application", () => {
	const character = characterPreferenceKey(status, windows[1]);
	assert.equal(findSelectedWindow(status, { character, slot: "1" })?.pseudo, "Nealla");
});

test("une ancienne identité sans case est migrable", () => {
	const character = characterPreferenceKey(status, windows[1]);
	const selected = findSelectedWindow(status, { character });

	assert.equal(selected?.hwnd, 102);
	assert.equal(selected?.ignored, true);
});

test("une case ignorée reste sélectionnable", () => {
	const selected = findSelectedWindow(status, { slot: "2" });

	assert.equal(selected?.pseudo, "Nat");
	assert.equal(selected?.ignored, true);
});
