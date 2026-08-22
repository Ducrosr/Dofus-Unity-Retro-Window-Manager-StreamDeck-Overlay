import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import { isAbsolute, join, win32 } from "node:path";

export type LauncherDescriptor = {
	version: 1;
	executable: string;
	arguments: string[];
	working_directory: string;
};

export function launcherDescriptorPath(environment: Record<string, string | undefined> = process.env): string {
	const appData = environment.APPDATA || environment.LOCALAPPDATA;
	if (!appData) throw new Error("Le dossier AppData de Windows est introuvable.");
	return join(appData, "DofusUnityWindowManager", "streamdeck-launcher.json");
}

export function parseLauncherDescriptor(value: unknown): LauncherDescriptor {
	if (!value || typeof value !== "object") throw new Error("Le lanceur enregistré est invalide.");
	const descriptor = value as Record<string, unknown>;
	const executable = descriptor.executable;
	const workingDirectory = descriptor.working_directory;
	const argumentsValue = descriptor.arguments;

	if (descriptor.version !== 1) throw new Error("Version de lanceur non prise en charge.");
	if (typeof executable !== "string" || (!isAbsolute(executable) && !win32.isAbsolute(executable))) {
		throw new Error("Le chemin de l'application est invalide.");
	}
	if (typeof workingDirectory !== "string" || (!isAbsolute(workingDirectory) && !win32.isAbsolute(workingDirectory))) {
		throw new Error("Le dossier de lancement est invalide.");
	}
	if (
		!Array.isArray(argumentsValue) ||
		argumentsValue.length > 8 ||
		argumentsValue.some((argument) => typeof argument !== "string" || argument.length > 32768)
	) {
		throw new Error("Les paramètres de lancement sont invalides.");
	}

	return {
		version: 1,
		executable,
		arguments: argumentsValue as string[],
		working_directory: workingDirectory,
	};
}

export async function loadLauncherDescriptor(): Promise<LauncherDescriptor> {
	const contents = await readFile(launcherDescriptorPath(), "utf8");
	return parseLauncherDescriptor(JSON.parse(contents) as unknown);
}

export async function launchRegisteredApp(): Promise<void> {
	const descriptor = await loadLauncherDescriptor();
	await new Promise<void>((resolve, reject) => {
		const child = spawn(descriptor.executable, descriptor.arguments, {
			cwd: descriptor.working_directory,
			detached: true,
			stdio: "ignore",
			windowsHide: false,
		});
		child.once("error", reject);
		child.once("spawn", () => {
			child.unref();
			resolve();
		});
	});
}
