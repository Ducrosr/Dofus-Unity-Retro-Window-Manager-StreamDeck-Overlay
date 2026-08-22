import { execFile } from "node:child_process";
import { fileURLToPath } from "node:url";

export type ForegroundHelperRunner = (scriptPath: string) => Promise<string>;

export function foregroundHelperPath(moduleUrl: string = import.meta.url): string {
	return fileURLToPath(new URL("./minimize-streamdeck.ps1", moduleUrl));
}

export async function releaseStreamDeckForeground(
	runner: ForegroundHelperRunner = runPowerShellHelper,
	scriptPath: string = foregroundHelperPath(),
): Promise<boolean> {
	try {
		const output = (await runner(scriptPath)).trim().toLowerCase();
		return output.split(/\s+/u).includes("released");
	} catch {
		return false;
	}
}

function runPowerShellHelper(scriptPath: string): Promise<string> {
	return new Promise((resolve, reject) => {
		execFile(
			"powershell.exe",
			["-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", scriptPath],
			{
				encoding: "utf8",
				timeout: 3000,
				windowsHide: true,
			},
			(error, stdout) => {
				if (error) {
					reject(error);
					return;
				}
				resolve(stdout);
			},
		);
	});
}
