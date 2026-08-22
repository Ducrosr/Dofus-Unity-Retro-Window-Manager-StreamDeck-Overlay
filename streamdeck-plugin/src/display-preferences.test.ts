import assert from "node:assert/strict";
import test from "node:test";

import {
	characterPreferenceKey,
	resolveCharacterName,
	resolveDisplayLabel,
	sanitizeDisplayPreferences,
} from "./display-preferences.ts";
import type { DofusWindow, DwmStatus } from "./dwm-client";

const status: DwmStatus = {
	api_version: 1,
	app_version: "2.15.0",
	game_mode: "unity",
	windows: [],
};

function korra(slot: number): DofusWindow {
	return {
		slot,
		hwnd: 100 + slot,
		pseudo: "Korra",
		alias: "",
		name: "Korra",
		character_class: "Féca",
		title: "Korra - Féca - 3.4.1.17",
		active: false,
	};
}

test("la préférence conserve la même clé quand le personnage change de case", () => {
	assert.equal(characterPreferenceKey(status, korra(1)), characterPreferenceKey(status, korra(8)));
});

test("deux personnages conservent des préférences indépendantes après réordonnancement", () => {
	const iop = { ...korra(1), pseudo: "Ragna", name: "Ragna", character_class: "Iop", title: "Iop - Ragna" };
	const preferences = {
		[characterPreferenceKey(status, korra(1))]: "class",
		[characterPreferenceKey(status, iop)]: "name",
	} as const;

	assert.equal(preferences[characterPreferenceKey(status, korra(8))], "class");
	assert.equal(preferences[characterPreferenceKey(status, { ...iop, slot: 2 })], "name");
});

test("le nom peut être retrouvé lorsque l'ancien scan a renvoyé la classe", () => {
	const oldScan = {
		...korra(1),
		pseudo: "Féca",
		name: "Féca",
		title: "Féca - Korra - 3.4.1.17",
	};

	assert.equal(resolveCharacterName(oldScan), "Korra");
});

test("un ancien alias ne remplace plus le véritable nom du personnage", () => {
	const nealla = {
		...korra(4),
		pseudo: "Nealla",
		alias: "Pandala",
		name: "Pandala",
		character_class: "Pandawa",
		title: "Nealla - Pandawa - 3.4.1.17",
	};

	assert.equal(resolveCharacterName(nealla), "Nealla");
	assert.equal(resolveDisplayLabel(nealla, "name"), "Nealla");
	assert.equal(resolveDisplayLabel(nealla, "class"), "Pandawa");
	assert.equal(resolveDisplayLabel(nealla, "alias"), "Pandala");
});

test("le mode alias affiche un tiret quand aucun alias n'est défini", () => {
	assert.equal(resolveDisplayLabel(korra(1), "alias"), "—");
});

test("les réglages globaux invalides sont ignorés", () => {
	assert.deepEqual(sanitizeDisplayPreferences({ korra: "class", ragna: "name", nealla: "alias", bad: "pseudo" }), {
		korra: "class",
		ragna: "name",
		nealla: "alias",
	});
});
