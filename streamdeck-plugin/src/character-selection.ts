import { characterPreferenceKey } from "./display-preferences.ts";
import type { DofusWindow, DwmStatus } from "./dwm-client";

export type CharacterSelection = {
	character?: string;
	slot?: number | string;
};

export function findSelectedWindow(status: DwmStatus, selection: CharacterSelection): DofusWindow | undefined {
	if (selection.slot !== undefined && String(selection.slot).trim()) {
		const slot = normalizeSlot(selection.slot);
		return status.windows.find((window) => window.slot === slot);
	}

	const character = selection.character?.trim();
	if (character) {
		return status.windows.find((window) => characterPreferenceKey(status, window) === character);
	}

	return status.windows.find((window) => window.slot === 1);
}

export function normalizeSlot(slot: number | string | undefined): number {
	const value = Number(slot ?? 1);
	if (!Number.isFinite(value)) return 1;
	return Math.max(1, Math.min(32, Math.trunc(value)));
}
