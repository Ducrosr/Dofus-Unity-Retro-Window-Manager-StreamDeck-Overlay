import assert from "node:assert/strict";
import test from "node:test";

import { foregroundHelperPath, releaseStreamDeckForeground } from "./streamdeck-foreground.ts";

test("le chemin du secours PowerShell suit le module compile", () => {
	const path = foregroundHelperPath("file:///C:/Plugins/DWM/bin/plugin.js");
	assert.match(path.replaceAll("\\", "/"), /\/bin\/minimize-streamdeck\.ps1$/u);
});

test("le secours confirme uniquement une reduction effective", async () => {
	assert.equal(await releaseStreamDeckForeground(async () => "released", "helper.ps1"), true);
	assert.equal(await releaseStreamDeckForeground(async () => "not-foreground", "helper.ps1"), false);
	assert.equal(await releaseStreamDeckForeground(async () => "blocked", "helper.ps1"), false);
});

test("une panne du secours ne masque pas l'erreur initiale", async () => {
	const released = await releaseStreamDeckForeground(async () => {
		throw new Error("PowerShell indisponible");
	}, "helper.ps1");
	assert.equal(released, false);
});
