import type { DofusWindow, DwmStatus } from "./dwm-client";

export type DisplayMode = "name" | "class" | "alias";

export function normalizeDisplay(display: unknown): DisplayMode {
	return display === "class" || display === "alias" ? display : "name";
}

export function sanitizeDisplayPreferences(value: unknown): Record<string, DisplayMode> {
	if (!value || typeof value !== "object" || Array.isArray(value)) return {};

	const preferences: Record<string, DisplayMode> = {};
	for (const [key, display] of Object.entries(value)) {
		if (display === "name" || display === "class" || display === "alias") preferences[key] = display;
	}
	return preferences;
}

export function characterPreferenceKey(status: DwmStatus, window: DofusWindow): string {
	const characterClass = normalizeLabel(window.character_class ?? "");
	const detectedPseudo = window.pseudo?.trim();
	const identity =
		detectedPseudo && normalizeLabel(detectedPseudo) !== characterClass ? detectedPseudo : resolveCharacterName(window);
	return `v1:${status.game_mode}:${normalizeLabel(identity)}`;
}

export function resolveCharacterName(window: DofusWindow): string {
	const characterClass = normalizeLabel(window.character_class ?? "");
	const detectedPseudo = window.pseudo?.trim();
	if (detectedPseudo && normalizeLabel(detectedPseudo) !== characterClass) return detectedPseudo;

	const parts = window.title
		.split(/\s+(?:-|–|—|\|)\s+/u)
		.map((part) => part.trim())
		.filter(Boolean);
	const classIndex = parts.findIndex((part) => normalizeLabel(part) === characterClass);
	if (classIndex >= 0) {
		for (const candidateIndex of [classIndex - 1, classIndex + 1]) {
			const candidate = parts[candidateIndex];
			if (candidate && isCharacterNameCandidate(candidate, characterClass)) return candidate.split(/\s+/u)[0];
		}
	}

	return window.pseudo?.trim() || window.name?.trim() || `Case ${window.slot}`;
}

export function resolveCharacterAlias(window: DofusWindow): string {
	return window.alias?.trim() || "—";
}

export function resolveDisplayLabel(window: DofusWindow, display: DisplayMode): string {
	if (display === "class" && window.character_class?.trim()) return window.character_class.trim();
	if (display === "alias") return resolveCharacterAlias(window);
	return resolveCharacterName(window);
}

function isCharacterNameCandidate(candidate: string, characterClass: string): boolean {
	const normalized = normalizeLabel(candidate);
	if (!normalized || normalized === characterClass) return false;
	if (/^v?\d+(?:\.\d+)+$/iu.test(candidate)) return false;
	return !/(?:^|\s)(?:dofus|release|beta|unity|ankama|launcher)(?:\s|$)/iu.test(normalized);
}

function normalizeLabel(value: string): string {
	return value
		.normalize("NFD")
		.replace(/[\u0300-\u036f]/gu, "")
		.trim()
		.toLocaleLowerCase("fr");
}
