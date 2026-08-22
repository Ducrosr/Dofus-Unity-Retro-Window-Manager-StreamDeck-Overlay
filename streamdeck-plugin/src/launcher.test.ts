import assert from "node:assert/strict";
import test from "node:test";

import { launcherDescriptorPath, parseLauncherDescriptor } from "./launcher.ts";

test("le chemin du lanceur utilise le dossier AppData de l'utilisateur", () => {
	const path = launcherDescriptorPath({ APPDATA: "C:\\Users\\Remy\\AppData\\Roaming" });

	assert.match(path, /DofusUnityWindowManager[\\/]streamdeck-launcher\.json$/);
});

test("un descripteur absolu valide est accepté", () => {
	const descriptor = parseLauncherDescriptor({
		version: 1,
		executable: "C:\\DWM\\DofusWindowManager.exe",
		arguments: [],
		working_directory: "C:\\DWM",
	});

	assert.equal(descriptor.executable, "C:\\DWM\\DofusWindowManager.exe");
});

test("un chemin relatif est refusé", () => {
	assert.throws(
		() =>
			parseLauncherDescriptor({
				version: 1,
				executable: "DofusWindowManager.exe",
				arguments: [],
				working_directory: ".",
			}),
		/chemin de l'application est invalide/,
	);
});
