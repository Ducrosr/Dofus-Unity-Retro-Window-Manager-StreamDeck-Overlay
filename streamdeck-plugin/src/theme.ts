export type ThemePalette = {
	bg: string;
	bg2: string;
	bg3: string;
	fg: string;
	muted: string;
	line: string;
	accent: string;
	header: string;
};

export const STANDARD_THEME = "unity-standard";
export const RETRO_THEME = "dwm-retro";

const palettes: Record<string, ThemePalette> = {
	"unity-standard": palette("#191a2d", "#292c4c", "#3a3d58", "#78789f", "#cbd750", "#737298", "#b9bad5"),
	"unity-bonta": palette("#25272e", "#343842", "#434a57", "#7e8895", "#d7b384", "#5c7caf", "#b9c4d2"),
	"unity-brakmar": palette("#1c1c1c", "#282828", "#373535", "#6d696a", "#d4af7e", "#993c4b", "#c2b9b9"),
	"unity-tribute": palette("#1f211b", "#292c25", "#373a30", "#797d71", "#acc962", "#777775", "#b9beaf"),
	"unity-gold-steel": palette("#1e1e1e", "#2b2825", "#3b3630", "#988f86", "#d6b180", "#9f734f", "#c8beb2"),
	"unity-belladone": palette("#221c2a", "#332c3c", "#423d53", "#857693", "#bcc764", "#867696", "#c5b9cf"),
	"unity-unicorn": palette("#231f1f", "#342d34", "#493f49", "#857583", "#d795c8", "#8f5b90", "#cdbdca"),
	"unity-emerald-mine": palette("#1c2322", "#25302e", "#293331", "#6e8289", "#80cfb6", "#5b878b", "#b5cbc7"),
	"unity-sufokia": palette("#25272e", "#343842", "#434a57", "#7e8895", "#d7cd84", "#477d7f", "#bbc9cc"),
	"unity-pandala": palette("#1e1e1e", "#2c2d27", "#3b3630", "#8f9279", "#d6cb80", "#6f8d4a", "#c2c6b0"),
	"unity-wabbit": palette("#211f1b", "#2d2b25", "#373a30", "#7e786d", "#acc862", "#c16344", "#c6bdaf"),
	"dwm-retro": palette("#d5d1b3", "#c5ba9d", "#50493a", "#948a6f", "#f27922", "#3a352b", "#6e6757", "#332e27"),
};

export function normalizeTheme(theme: unknown, gameMode: "unity" | "retro" = "unity"): string {
	const requested = String(theme ?? "").trim().toLowerCase();
	const migrated = requested === "dwm-dark" || requested === "equilux" || requested === "black" ? STANDARD_THEME : requested;
	if (palettes[migrated]) return migrated;
	return gameMode === "retro" ? RETRO_THEME : STANDARD_THEME;
}

export function resolveTheme(theme: unknown, gameMode: "unity" | "retro" = "unity"): ThemePalette {
	return palettes[normalizeTheme(theme, gameMode)];
}

function palette(
	bg: string,
	bg2: string,
	bg3: string,
	line: string,
	accent: string,
	header: string,
	muted: string,
	fg = "#f4f4f2",
): ThemePalette {
	return { bg, bg2, bg3, fg, muted, line, accent, header };
}
