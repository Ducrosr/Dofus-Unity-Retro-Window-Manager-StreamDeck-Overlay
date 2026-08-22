import assert from "node:assert/strict";
import test from "node:test";

import type { DofusWindow } from "./dwm-client";
import {
	buildCharacterKeySvg,
	defaultTextLayout,
	initialLayoutFromSettings,
	layoutForLegacyDisplay,
	layoutFromSettings,
	sanitizeTextLayouts,
	svgToDataUrl,
} from "./text-layout.ts";

const nealla: DofusWindow = {
	slot: 4,
	position: 4,
	hwnd: 104,
	pseudo: "Nealla",
	alias: "Pan&dala",
	name: "Pan&dala",
	character_class: "Pandawa",
	title: "Nealla - Pandawa - 3.4.1.17",
	active: true,
};

test("la migration conserve l'ancien choix de classe", () => {
	assert.deepEqual(layoutForLegacyDisplay("class"), {
		position: "1",
		name: "hidden",
		alias: "hidden",
		class: "4",
	});
});

test("une nouvelle touche utilise les quatre lignes par défaut", () => {
	assert.deepEqual(defaultTextLayout(), {
		position: "1",
		name: "2",
		alias: "4",
		class: "3",
	});
	assert.deepEqual(initialLayoutFromSettings({}, "name"), defaultTextLayout());
});

test("une ancienne touche sans réglages de lignes conserve son ancien affichage", () => {
	assert.deepEqual(initialLayoutFromSettings({ display: "class" }, "class"), layoutForLegacyDisplay("class"));
});

test("chaque texte peut être placé sur une ligne indépendante", () => {
	const layout = layoutFromSettings(
		{ positionLine: "2", nameLine: "1", aliasLine: "4", classLine: "3" },
		layoutForLegacyDisplay("name"),
	);
	assert.deepEqual(layout, { position: "2", name: "1", alias: "4", class: "3" });
});

test("les mises en page globales invalides utilisent des valeurs sûres", () => {
	assert.deepEqual(sanitizeTextLayouts({ nealla: { position: "bad", name: "2", alias: "hidden", class: "4" } }), {
		nealla: { position: "1", name: "2", alias: "hidden", class: "4" },
	});
});

test("le SVG place et protège les quatre textes", () => {
	const svg = buildCharacterKeySvg(nealla, 4, { position: "1", name: "2", alias: "3", class: "4" }, true);
	assert.match(svg, /y="24"[^>]*>4<\/text>/u);
	assert.match(svg, /y="56"[^>]*>Nealla<\/text>/u);
	assert.match(svg, /y="88"[^>]*>Pan&amp;dala<\/text>/u);
	assert.match(svg, /y="120"[^>]*>Pandawa<\/text>/u);
	assert.match(svg, /fill="#4ade80"/u);
});

test("un alias supprimé est remplacé par un tiret", () => {
	const svg = buildCharacterKeySvg(
		{ ...nealla, alias: "", name: "Nealla" },
		4,
		{ position: "hidden", name: "hidden", alias: "4", class: "hidden" },
		false,
	);

	assert.match(svg, /y="120"[^>]*>—<\/text>/u);
	assert.doesNotMatch(svg, /Pan&amp;dala/u);
});

test("l'image dynamique utilise le format de données attendu par Stream Deck", () => {
	const svg = buildCharacterKeySvg(nealla, 4, { position: "1", name: "2", alias: "3", class: "4" }, true);
	const image = svgToDataUrl(svg);

	assert.match(image, /^data:image\/svg\+xml,%3Csvg/u);
	assert.equal(decodeURIComponent(image.slice("data:image/svg+xml,".length)), svg);
});

test("une fenêtre ignorée reste rendue et n'a plus de position de rotation", () => {
	const svg = buildCharacterKeySvg(
		{ ...nealla, position: null, ignored: true },
		4,
		{ position: "1", name: "2", alias: "hidden", class: "hidden" },
		false,
	);

	assert.match(svg, /y="24"[^>]*>—<\/text>/u);
	assert.match(svg, /stroke="#f87171"/u);
});

test("la couleur d’élément personnalise la bordure sans masquer l’état actif", () => {
	const svg = buildCharacterKeySvg(nealla, 4, { position: "1", name: "2", alias: "3", class: "4" }, true, "earth");

	assert.match(svg, /stroke="#d6a45d"/u);
	assert.match(svg, /fill="#4ade80"/u);
});
