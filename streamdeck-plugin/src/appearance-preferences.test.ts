import assert from "node:assert/strict";
import test from "node:test";

import { characterBorderColor, normalizeCharacterAccent, sanitizeCharacterAccents } from "./appearance-preferences.ts";

test("une couleur invalide revient au mode automatique", () => {
	assert.equal(normalizeCharacterAccent("inconnue"), "auto");
});

test("les couleurs globales invalides sont ignorées", () => {
	assert.deepEqual(sanitizeCharacterAccents({ korra: "water", nealla: "earth", bad: "yellow" }), {
		korra: "water",
		nealla: "earth",
	});
});

test("chaque élément possède une couleur de bordure stable", () => {
	assert.equal(characterBorderColor("fire"), "#fb7185");
	assert.equal(characterBorderColor("air"), "#4ade80");
});
