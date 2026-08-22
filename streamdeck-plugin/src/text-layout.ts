import { type CharacterAccent, characterBorderColor } from "./appearance-preferences.ts";
import { type DisplayMode, resolveCharacterAlias, resolveCharacterName } from "./display-preferences.ts";
import type { DofusWindow } from "./dwm-client";

export type TextLine = "hidden" | "1" | "2" | "3" | "4";

export type CharacterTextLayout = {
	position: TextLine;
	name: TextLine;
	alias: TextLine;
	class: TextLine;
};

export type TextLayoutSettings = {
	positionLine?: TextLine;
	nameLine?: TextLine;
	aliasLine?: TextLine;
	classLine?: TextLine;
};

const VALID_LINES = new Set<TextLine>(["hidden", "1", "2", "3", "4"]);

export function defaultTextLayout(): CharacterTextLayout {
	return {
		position: "1",
		name: "2",
		alias: "4",
		class: "3",
	};
}

export function layoutForLegacyDisplay(display: DisplayMode): CharacterTextLayout {
	return {
		position: "1",
		name: display === "name" ? "4" : "hidden",
		alias: display === "alias" ? "4" : "hidden",
		class: display === "class" ? "4" : "hidden",
	};
}

export function hasTextLayoutSettings(settings: TextLayoutSettings): boolean {
	return [settings.positionLine, settings.nameLine, settings.aliasLine, settings.classLine].some(
		(value) => typeof value === "string",
	);
}

export function initialLayoutFromSettings(
	settings: TextLayoutSettings & { display?: unknown },
	display: DisplayMode,
): CharacterTextLayout {
	if (hasTextLayoutSettings(settings)) return layoutFromSettings(settings, defaultTextLayout());
	if (settings.display === "name" || settings.display === "class" || settings.display === "alias") {
		return layoutForLegacyDisplay(display);
	}
	return defaultTextLayout();
}

export function layoutFromSettings(settings: TextLayoutSettings, fallback: CharacterTextLayout): CharacterTextLayout {
	if (!hasTextLayoutSettings(settings)) return { ...fallback };
	return {
		position: normalizeLine(settings.positionLine, fallback.position),
		name: normalizeLine(settings.nameLine, fallback.name),
		alias: normalizeLine(settings.aliasLine, fallback.alias),
		class: normalizeLine(settings.classLine, fallback.class),
	};
}

export function layoutToSettings(layout: CharacterTextLayout): Required<TextLayoutSettings> {
	return {
		positionLine: layout.position,
		nameLine: layout.name,
		aliasLine: layout.alias,
		classLine: layout.class,
	};
}

export function sanitizeTextLayouts(value: unknown): Record<string, CharacterTextLayout> {
	if (!value || typeof value !== "object" || Array.isArray(value)) return {};

	const layouts: Record<string, CharacterTextLayout> = {};
	for (const [key, candidate] of Object.entries(value)) {
		if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) continue;
		const raw = candidate as Partial<CharacterTextLayout>;
		const fallback = layoutForLegacyDisplay("name");
		layouts[key] = {
			position: normalizeLine(raw.position, fallback.position),
			name: normalizeLine(raw.name, fallback.name),
			alias: normalizeLine(raw.alias, fallback.alias),
			class: normalizeLine(raw.class, fallback.class),
		};
	}
	return layouts;
}

export function layoutSignature(layout: CharacterTextLayout): string {
	return `${layout.position}:${layout.name}:${layout.alias}:${layout.class}`;
}

export function buildCharacterKeySvg(
	window: DofusWindow,
	slot: number,
	layout: CharacterTextLayout,
	active: boolean,
	accent: CharacterAccent = "auto",
): string {
	const lines = new Map<TextLine, Array<{ label: string; color: string }>>();
	const add = (line: TextLine, label: string, color: string): void => {
		if (line === "hidden" || !label.trim()) return;
		const items = lines.get(line) ?? [];
		if (!items.some((item) => item.label === label)) items.push({ label, color });
		lines.set(line, items);
	};

	add(layout.position, window.position === null ? "—" : String(window.position ?? slot), "#38bdf8");
	add(layout.name, resolveCharacterName(window), "#f8fafc");
	add(layout.alias, resolveCharacterAlias(window), "#fbbf24");
	add(layout.class, window.character_class?.trim() ?? "", "#c4b5fd");

	const yByLine: Record<Exclude<TextLine, "hidden">, number> = { "1": 24, "2": 56, "3": 88, "4": 120 };
	const textElements = (["1", "2", "3", "4"] as const)
		.map((line) => {
			const items = lines.get(line);
			if (!items?.length) return "";
			const label = items.map((item) => item.label).join(" · ");
			const color = items.length === 1 ? items[0].color : "#f8fafc";
			const fontSize = label.length <= 8 ? 22 : label.length <= 13 ? 18 : label.length <= 20 ? 15 : 12;
			const fit = label.length > 18 ? ' textLength="116" lengthAdjust="spacingAndGlyphs"' : "";
			return `<text x="72" y="${yByLine[line]}" fill="${color}" font-family="Arial, sans-serif" font-size="${fontSize}" font-weight="700" text-anchor="middle" dominant-baseline="middle"${fit}>${escapeXml(label)}</text>`;
		})
		.join("");

	const background = active ? "#052e2b" : "#101827";
	const border = window.ignored ? "#f87171" : characterBorderColor(accent);
	const activeMarker = active ? '<circle cx="126" cy="18" r="7" fill="#4ade80"/>' : "";
	return `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144"><rect width="144" height="144" rx="18" fill="${background}"/><rect x="5" y="5" width="134" height="134" rx="15" fill="none" stroke="${border}" stroke-width="4" opacity="0.8"/><path d="M18 40h108M18 72h108M18 104h108" stroke="${border}" stroke-width="1" opacity="0.12"/>${activeMarker}${textElements}</svg>`;
}

export function svgToDataUrl(svg: string): string {
	return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

function normalizeLine(value: unknown, fallback: TextLine): TextLine {
	return typeof value === "string" && VALID_LINES.has(value as TextLine) ? (value as TextLine) : fallback;
}

function escapeXml(value: string): string {
	return value.replace(/[&<>"']/gu, (character) => {
		const replacements: Record<string, string> = {
			"&": "&amp;",
			"<": "&lt;",
			">": "&gt;",
			'"': "&quot;",
			"'": "&apos;",
		};
		return replacements[character];
	});
}
