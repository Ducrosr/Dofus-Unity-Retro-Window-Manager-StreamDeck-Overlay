const BASE_URL = "http://127.0.0.1:32145/v1";
const POLL_INTERVAL_MS = 750;
const REQUEST_TIMEOUT_MS = 600;

export type DofusWindow = {
	slot: number;
	position?: number | null;
	hwnd: number;
	available?: boolean;
	pseudo: string;
	alias: string;
	name: string;
	character_class?: string;
	title: string;
	active: boolean;
	ignored?: boolean;
	attention?: boolean;
	attention_order?: number | null;
	portrait?: string;
	badge?: string;
	badge_image?: string;
};

export type DwmStatus = {
	api_version: number;
	app_version: string;
	game_mode: "unity" | "retro";
	profile?: string;
	theme?: string;
	language?: "fr" | "en" | "es";
	scan_revision?: number;
	show_character_portraits?: boolean;
	show_character_badges?: boolean;
	attention_blink_enabled?: boolean;
	attention_blink_phase?: boolean;
	attention_count?: number;
	next_attention_hwnd?: number | null;
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

	async focus(window: Pick<DofusWindow, "hwnd" | "slot" | "pseudo">): Promise<void> {
		await this.focusCommand("focus", { hwnd: window.hwnd, slot: window.slot, pseudo: window.pseudo, game_mode: this.state.status?.game_mode, profile: this.state.status?.profile });
	}

	async rotate(direction: "forward" | "backward"): Promise<void> {
		await this.focusCommand("rotate", {
			direction,
			game_mode: this.state.status?.game_mode,
			profile: this.state.status?.profile,
		});
	}

	async nextAttention(): Promise<void> {
		await this.focusCommand("next-attention", {
			game_mode: this.state.status?.game_mode,
			profile: this.state.status?.profile,
		});
	}

	async show(): Promise<void> {
		await this.command("show", {});
	}

	async reorder(direction: "up" | "down"): Promise<void> {
		await this.command("reorder", {
			direction,
			game_mode: this.state.status?.game_mode,
			profile: this.state.status?.profile,
		});
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
		const result = await this.command<ToggleIgnoreResult>("toggle-ignore", {
			game_mode: this.state.status?.game_mode,
			profile: this.state.status?.profile,
		});
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
		const result = (await response.json().catch(() => ({}))) as TResult & {
			error?: string;
			error_code?: string;
			execution?: string;
		};
		if (response.ok) return result;
		const detail = result.error_code
			? `${result.error || `HTTP ${response.status}`} [${result.error_code}]`
			: result.error || `HTTP ${response.status}`;
		throw new Error(detail);
	}

	private async focusCommand(
		path: "focus" | "rotate" | "next-attention",
		payload: Record<string, unknown>,
	): Promise<void> {
		// Mutating commands are deliberately sent exactly once. A timed-out HTTP
		// response does not prove that the backend mutation failed.
		await this.command(path, payload);
	}
	private notify(): void {
		for (const listener of this.listeners) listener(this.state);
	}
}

export const dwmClient = new DwmClient();

function delay(milliseconds: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
