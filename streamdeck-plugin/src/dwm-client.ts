import { releaseStreamDeckForeground } from "./streamdeck-foreground";

const BASE_URL = "http://127.0.0.1:32145/v1";
const POLL_INTERVAL_MS = 750;
const REQUEST_TIMEOUT_MS = 600;

export type DofusWindow = {
	slot: number;
	position?: number | null;
	hwnd: number;
	pseudo: string;
	alias: string;
	name: string;
	character_class?: string;
	title: string;
	active: boolean;
	ignored?: boolean;
	attention?: boolean;
	portrait?: string;
	badge?: string;
	badge_image?: string;
};

export type DwmStatus = {
	api_version: number;
	app_version: string;
	game_mode: "unity" | "retro";
	theme?: string;
	language?: "fr" | "en" | "es";
	scan_revision?: number;
	show_character_portraits?: boolean;
	show_character_badges?: boolean;
	attention_blink_enabled?: boolean;
	attention_blink_phase?: boolean;
	windows: DofusWindow[];
};

export type ToggleIgnoreResult = {
	ignored: boolean;
	hwnd: number;
	name: string;
};

type RefreshResult = {
	accepted?: boolean;
	target_revision?: number;
};

export type BridgeState = {
	connected: boolean;
	status?: DwmStatus;
};

type Listener = (state: BridgeState) => void;

class DwmClient {
	private readonly listeners = new Set<Listener>();
	private state: BridgeState = { connected: false };
	private timer?: NodeJS.Timeout;
	private polling = false;
	private signature = "";

	subscribe(listener: Listener): () => void {
		this.listeners.add(listener);
		listener(this.state);
		if (!this.timer) {
			void this.poll();
			this.timer = setInterval(() => void this.poll(), POLL_INTERVAL_MS);
		}

		return () => {
			this.listeners.delete(listener);
			if (this.listeners.size === 0 && this.timer) {
				clearInterval(this.timer);
				this.timer = undefined;
			}
		};
	}

	getState(): BridgeState {
		return this.state;
	}

	async focus(window: Pick<DofusWindow, "hwnd" | "slot">): Promise<void> {
		await this.focusCommand("focus", { hwnd: window.hwnd, slot: window.slot });
	}

	async rotate(direction: "forward" | "backward"): Promise<void> {
		await this.focusCommand("rotate", { direction });
	}

	async show(): Promise<void> {
		await this.command("show", {});
	}

	async reorder(direction: "up" | "down"): Promise<void> {
		await this.command("reorder", { direction });
		await this.poll();
	}

	async refresh(): Promise<void> {
		const result = await this.command<RefreshResult>("refresh", {});
		const targetRevision = Number(result.target_revision);
		if (Number.isFinite(targetRevision)) {
			await this.waitForScanRevision(targetRevision);
		} else {
			await delay(300);
			await this.poll();
		}
	}

	async toggleIgnore(): Promise<ToggleIgnoreResult> {
		const result = await this.command<ToggleIgnoreResult>("toggle-ignore", {});
		await this.poll();
		return result;
	}

	private async poll(): Promise<void> {
		if (this.polling) return;
		this.polling = true;
		try {
			const response = await fetch(`${BASE_URL}/status`, {
				signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
			});
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			const status = (await response.json()) as DwmStatus;
			const signature = JSON.stringify(status);
			if (!this.state.connected || signature !== this.signature) {
				this.signature = signature;
				this.state = { connected: true, status };
				this.notify();
			}
		} catch {
			if (this.state.connected || this.signature !== "disconnected") {
				this.signature = "disconnected";
				this.state = { connected: false };
				this.notify();
			}
		} finally {
			this.polling = false;
		}
	}

	private async waitForScanRevision(targetRevision: number): Promise<void> {
		const deadline = Date.now() + 6000;
		while (Date.now() < deadline) {
			await delay(120);
			await this.poll();
			if ((this.state.status?.scan_revision ?? -1) >= targetRevision) return;
		}
		throw new Error("Le scan des fenêtres n'a pas répondu dans le délai prévu.");
	}

	private async command<TResult extends object>(path: string, payload: Record<string, unknown>): Promise<TResult> {
		const response = await fetch(`${BASE_URL}/${path}`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
			signal: AbortSignal.timeout(2000),
		});
		const result = (await response.json().catch(() => ({}))) as TResult & { error?: string };
		if (response.ok) return result;
		throw new Error(result.error || `HTTP ${response.status}`);
	}

	private async focusCommand(path: "focus" | "rotate", payload: Record<string, unknown>): Promise<void> {
		try {
			await this.command(path, payload);
			return;
		} catch (initialError) {
			// If Stream Deck runs at a higher integrity level than DWM, Windows can
			// reject every minimization request coming from the Python process. The
			// plugin inherits Stream Deck's level, so it can release its own desktop
			// window and retry the exact command once.
			if (!(await releaseStreamDeckForeground())) throw initialError;
			await delay(160);
			await this.command(path, payload);
		}
	}

	private notify(): void {
		for (const listener of this.listeners) listener(this.state);
	}
}

export const dwmClient = new DwmClient();

function delay(milliseconds: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
