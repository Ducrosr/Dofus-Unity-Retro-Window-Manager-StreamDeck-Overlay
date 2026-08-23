import type { KeyAction, WillAppearEvent } from "@elgato/streamdeck";
import { SingletonAction } from "@elgato/streamdeck";

import { type BridgeState, dwmClient } from "./dwm-client";
import { svgToDataUrl } from "./text-layout";
import { resolveTheme } from "./theme";

export type ActionKind = "launch" | "next" | "previous" | "next-attention" | "move-up" | "move-down" | "refresh" | "toggle-ignore";
export type EmptySettings = Record<string, never>;

const glyphs: Record<ActionKind, string> = {
	launch: "DWM",
	next: "→",
	previous: "←",
	"next-attention": "!",
	"move-up": "↑",
	"move-down": "↓",
	refresh: "↻",
	"toggle-ignore": "◉",
};

const labels: Record<"fr" | "en" | "es", Record<ActionKind, string>> = {
	fr: { launch: "OUVRIR", next: "SUIVANT", previous: "PRÉC.", "next-attention": "ALERTE", "move-up": "MONTER", "move-down": "BAISSER", refresh: "SCAN", "toggle-ignore": "IGNORER" },
	en: { launch: "OPEN", next: "NEXT", previous: "PREV.", "next-attention": "ALERT", "move-up": "MOVE UP", "move-down": "MOVE DOWN", refresh: "SCAN", "toggle-ignore": "IGNORE" },
	es: { launch: "ABRIR", next: "SIG.", previous: "ANT.", "next-attention": "ALERTA", "move-up": "SUBIR", "move-down": "BAJAR", refresh: "ESCANEAR", "toggle-ignore": "IGNORAR" },
};

export abstract class ThemeAwareAction extends SingletonAction<EmptySettings> {
	protected abstract readonly actionKind: ActionKind;

	constructor() {
		super();
		dwmClient.subscribe((state) => void this.renderAll(state));
	}

	override async onWillAppear(ev: WillAppearEvent<EmptySettings>): Promise<void> {
		if (ev.action.isKey()) await this.render(ev.action, dwmClient.getState());
	}

	private async renderAll(state: BridgeState): Promise<void> {
		for (const visibleAction of this.actions) {
			if (visibleAction.isKey()) await this.render(visibleAction, state);
		}
	}

	private async render(action: KeyAction, state: BridgeState): Promise<void> {
		const status = state.status;
		const palette = resolveTheme(status?.theme, status?.game_mode);
		const language = status?.language === "en" || status?.language === "es" ? status.language : "fr";
		const connected = state.connected && !!status;
		const attentionCount = Math.max(0, Number(status?.attention_count ?? 0));
		const hasAttention = this.actionKind === "next-attention" && attentionCount > 0;
		const glyph = hasAttention ? `!${attentionCount}` : glyphs[this.actionKind];
		const label = connected ? labels[language][this.actionKind] : "DWM OFF";
		const glyphSize = glyph.length > 2 ? 30 : 66;
		const actionColor = hasAttention ? "#f59e0b" : palette.accent;
		const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144"><rect width="144" height="144" rx="18" fill="${palette.bg}"/><rect x="5" y="5" width="134" height="134" rx="15" fill="none" stroke="${connected ? actionColor : palette.line}" stroke-width="${hasAttention ? 7 : 4}"/><path d="M18 106h108" stroke="${palette.line}" stroke-width="2" opacity=".65"/><text x="72" y="62" fill="${hasAttention ? actionColor : connected ? palette.fg : palette.muted}" font-family="Arial, sans-serif" font-size="${glyphSize}" font-weight="800" text-anchor="middle" dominant-baseline="middle">${glyph}</text><text x="72" y="122" fill="${connected ? actionColor : palette.muted}" font-family="Arial, sans-serif" font-size="14" font-weight="800" text-anchor="middle">${label}</text></svg>`;
		await Promise.all([action.setTitle(""), action.setImage(svgToDataUrl(svg))]);
	}
}
