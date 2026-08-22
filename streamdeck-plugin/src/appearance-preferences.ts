export type CharacterAccent = "auto" | "earth" | "fire" | "water" | "air" | "neutral" | "violet";

const ACCENTS = new Set<CharacterAccent>(["auto", "earth", "fire", "water", "air", "neutral", "violet"]);

const BORDER_COLORS: Record<CharacterAccent, string> = {
	auto: "#38bdf8",
	earth: "#d6a45d",
	fire: "#fb7185",
	water: "#38bdf8",
	air: "#4ade80",
	neutral: "#f8fafc",
	violet: "#c4b5fd",
};

export function normalizeCharacterAccent(value: unknown): CharacterAccent {
	return typeof value === "string" && ACCENTS.has(value as CharacterAccent) ? (value as CharacterAccent) : "auto";
}

export function sanitizeCharacterAccents(value: unknown): Record<string, CharacterAccent> {
	if (!value || typeof value !== "object" || Array.isArray(value)) return {};

	const accents: Record<string, CharacterAccent> = {};
	for (const [key, accent] of Object.entries(value)) {
		if (typeof accent === "string" && ACCENTS.has(accent as CharacterAccent)) {
			accents[key] = accent as CharacterAccent;
		}
	}
	return accents;
}

export function characterBorderColor(accent: CharacterAccent): string {
	return BORDER_COLORS[accent];
}
