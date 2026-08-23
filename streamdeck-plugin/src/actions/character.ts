import type {
	DidReceiveSettingsEvent,
	KeyAction,
	KeyDownEvent,
	SendToPluginEvent,
	WillAppearEvent,
} from "@elgato/streamdeck";
import streamDeck, { action, SingletonAction } from "@elgato/streamdeck";
import type { JsonValue } from "@elgato/utils";

import { type CharacterAccent, normalizeCharacterAccent, sanitizeCharacterAccents } from "../appearance-preferences";
import { findSelectedWindow } from "../character-selection";
import {
	characterPreferenceKey,
	type DisplayMode,
	normalizeDisplay,
	resolveCharacterName,
	sanitizeDisplayPreferences,
} from "../display-preferences";
import { type BridgeState, dwmClient } from "../dwm-client";
import {
	buildCharacterKeySvg,
	type CharacterTextLayout,
	defaultTextLayout,
	initialLayoutFromSettings,
	layoutFromSettings,
	layoutSignature,
	layoutToSettings,
	sanitizeTextLayouts,
	svgToDataUrl,
	type TextLayoutSettings,
} from "../text-layout";

type CharacterSettings = TextLayoutSettings & {
	character?: string;
	slot?: number | string;
	display?: DisplayMode;
	accentColor?: CharacterAccent;
};

type PluginGlobalSettings = {
	characterDisplayByCharacter?: Record<string, DisplayMode>;
	characterTextLayoutByCharacter?: Record<string, CharacterTextLayout>;
	characterAccentByCharacter?: Record<string, CharacterAccent>;
};

type ActionBinding = {
	characterKey?: string;
	display: DisplayMode;
	layoutSignature: string;
	accent: CharacterAccent;
};

type DataSourceItem = {
	label: string;
	value: string;
	disabled?: boolean;
};

const CHARACTER_DATA_SOURCE = "getCharacters";

@action({ UUID: "com.remyducros.dofuswindowmanager.character" })
export class CharacterAction extends SingletonAction<CharacterSettings> {
	private globalSettings: PluginGlobalSettings = {};
	private displayPreferences: Record<string, DisplayMode> = {};
	private textLayouts: Record<string, CharacterTextLayout> = {};
	private accentPreferences: Record<string, CharacterAccent> = {};
	private preferencesLoaded?: Promise<void>;
	private preferenceWrites: Promise<void> = Promise.resolve();
	private readonly bindings = new Map<string, ActionBinding>();

	private readonly unsubscribe = dwmClient.subscribe((state) => {
		void this.renderAll(state);
		void this.publishCharacterOptions(state);
	});

	override async onWillAppear(ev: WillAppearEvent<CharacterSettings>): Promise<void> {
		if (!ev.action.isKey()) return;
		await this.ensurePreferencesLoaded();

		const state = dwmClient.getState();
		const window = state.status ? findSelectedWindow(state.status, ev.payload.settings) : undefined;
		const characterKey = state.status && window ? characterPreferenceKey(state.status, window) : undefined;
		let display = normalizeDisplay(ev.payload.settings.display);
		let layout = initialLayoutFromSettings(ev.payload.settings, display);
		let accent = normalizeCharacterAccent(ev.payload.settings.accentColor);

		if (characterKey) {
			const storedDisplay = this.displayPreferences[characterKey];
			if (storedDisplay) {
				display = storedDisplay;
			} else {
				await this.setCharacterDisplay(characterKey, display);
			}
			const storedLayout = this.textLayouts[characterKey];
			if (storedLayout) {
				layout = storedLayout;
			} else {
				layout = initialLayoutFromSettings(ev.payload.settings, display);
				await this.setCharacterLayout(characterKey, layout);
			}
			const storedAccent = this.accentPreferences[characterKey];
			if (storedAccent) {
				accent = storedAccent;
			} else {
				await this.setCharacterAccent(characterKey, accent);
			}
		}

		const settings = await this.syncActionSettings(
			ev.action,
			ev.payload.settings,
			window?.slot,
			characterKey,
			display,
			layout,
			accent,
		);
		await this.render(ev.action, settings, dwmClient.getState());
	}

	override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<CharacterSettings>): Promise<void> {
		if (!ev.action.isKey()) return;
		await this.ensurePreferencesLoaded();

		const state = dwmClient.getState();
		const window = state.status ? findSelectedWindow(state.status, ev.payload.settings) : undefined;
		const characterKey = state.status && window ? characterPreferenceKey(state.status, window) : undefined;
		const previousBinding = this.bindings.get(ev.action.id);
		const requestedDisplay = normalizeDisplay(ev.payload.settings.display);
		const requestedAccent = normalizeCharacterAccent(ev.payload.settings.accentColor);
		let display = requestedDisplay;
		let layout = initialLayoutFromSettings(ev.payload.settings, display);
		let accent = requestedAccent;
		let preferenceChanged = false;

		if (characterKey) {
			const storedDisplay = this.displayPreferences[characterKey];
			const storedLayout = this.textLayouts[characterKey];
			const storedAccent = this.accentPreferences[characterKey];
			const selectedCharacterChanged = previousBinding !== undefined && previousBinding.characterKey !== characterKey;

			if (selectedCharacterChanged) {
				display = storedDisplay ?? "name";
				if (!storedDisplay) preferenceChanged = await this.setCharacterDisplay(characterKey, display);
				layout = storedLayout ?? defaultTextLayout();
				if (!storedLayout) {
					preferenceChanged = (await this.setCharacterLayout(characterKey, layout)) || preferenceChanged;
				}
			} else if (!previousBinding && storedDisplay) {
				display = storedDisplay;
				layout = storedLayout ?? initialLayoutFromSettings(ev.payload.settings, display);
				if (!storedLayout) {
					preferenceChanged = (await this.setCharacterLayout(characterKey, layout)) || preferenceChanged;
				}
			} else {
				display = storedDisplay ?? requestedDisplay;
				if (!storedDisplay) preferenceChanged = await this.setCharacterDisplay(characterKey, display);
				layout = layoutFromSettings(ev.payload.settings, storedLayout ?? defaultTextLayout());
				preferenceChanged = (await this.setCharacterLayout(characterKey, layout)) || preferenceChanged;
			}

			if (selectedCharacterChanged) {
				accent = storedAccent ?? "auto";
				if (!storedAccent) {
					preferenceChanged = (await this.setCharacterAccent(characterKey, accent)) || preferenceChanged;
				}
			} else if (!previousBinding && storedAccent) {
				accent = storedAccent;
			} else {
				accent = requestedAccent;
				preferenceChanged = (await this.setCharacterAccent(characterKey, accent)) || preferenceChanged;
			}
		}

		const settings = await this.syncActionSettings(
			ev.action,
			ev.payload.settings,
			window?.slot,
			characterKey,
			display,
			layout,
			accent,
		);
		await this.render(ev.action, settings, state);
		if (preferenceChanged) await this.renderAll(state);
	}

	override async onKeyDown(ev: KeyDownEvent<CharacterSettings>): Promise<void> {
		try {
			const status = dwmClient.getState().status;
			const window = status ? findSelectedWindow(status, ev.payload.settings) : undefined;
			if (!window) throw new Error("Le personnage attribué n'est pas disponible.");
			await dwmClient.focus(window);
			ev.action.showOk();
		} catch (error) {
			streamDeck.logger.error("Impossible d'activer le personnage :", error);
			ev.action.showAlert();
		}
	}

	override async onSendToPlugin(ev: SendToPluginEvent<JsonValue, CharacterSettings>): Promise<void> {
		if (isCharacterDataSourceRequest(ev.payload)) {
			await this.publishCharacterOptions(dwmClient.getState());
		}
	}

	private async renderAll(state: BridgeState): Promise<void> {
		for (const visibleAction of this.actions) {
			if (!visibleAction.isKey()) continue;
			const settings = await visibleAction.getSettings<CharacterSettings>();
			await this.render(visibleAction, settings, state);
		}
	}

	private async render(action: KeyAction, settings: CharacterSettings, state: BridgeState): Promise<void> {
		await this.ensurePreferencesLoaded();
		if (!state.connected || !state.status) {
			await action.setState(0);
			await Promise.all([action.setImage(), action.setTitle("DWM\nfermé")]);
			return;
		}

		const window = findSelectedWindow(state.status, settings);
		if (!window) {
			await action.setState(0);
			await Promise.all([action.setImage(), action.setTitle("Personnage\nindisponible")]);
			return;
		}

		const characterKey = characterPreferenceKey(state.status, window);
		const previousBinding = this.bindings.get(action.id);
		let display = this.displayPreferences[characterKey];
		if (!display) {
			display =
				previousBinding?.characterKey && previousBinding.characterKey !== characterKey
					? "name"
					: normalizeDisplay(settings.display);
			await this.setCharacterDisplay(characterKey, display);
		}
		let layout = this.textLayouts[characterKey];
		if (!layout) {
			layout =
				previousBinding?.characterKey && previousBinding.characterKey !== characterKey
					? defaultTextLayout()
					: initialLayoutFromSettings(settings, display);
			await this.setCharacterLayout(characterKey, layout);
		}
		let accent = this.accentPreferences[characterKey];
		if (!accent) {
			accent =
				previousBinding?.characterKey && previousBinding.characterKey !== characterKey
					? "auto"
					: normalizeCharacterAccent(settings.accentColor);
			await this.setCharacterAccent(characterKey, accent);
		}
		await this.syncActionSettings(action, settings, window.slot, characterKey, display, layout, accent);
		const image = svgToDataUrl(
			buildCharacterKeySvg(
				window,
				window.slot,
				layout,
				window.active,
				accent,
				state.status.show_character_portraits !== false,
				state.status.show_character_badges !== false,
				state.status.theme,
				state.status.attention_blink_enabled !== false,
				state.status.attention_blink_phase !== false,
			),
		);
		await action.setState(window.active ? 1 : 0);
		await action.setTitle("");
		await action.setImage(image);
	}

	private async publishCharacterOptions(state: BridgeState): Promise<void> {
		const items: DataSourceItem[] = [];
		const language = state.status?.language === "en" || state.status?.language === "es" ? state.status.language : "fr";
		const text = {
			fr: { disconnected: "Dofus Window Manager non connecté", empty: "Aucune fenêtre Dofus détectée", alias: "alias", ignored: "ignorée", attention: "demande votre attention" },
			en: { disconnected: "Dofus Window Manager is not connected", empty: "No Dofus window detected", alias: "alias", ignored: "ignored", attention: "needs your attention" },
			es: { disconnected: "Dofus Window Manager no está conectado", empty: "No se detectó ninguna ventana de Dofus", alias: "alias", ignored: "ignorada", attention: "requiere tu atención" },
		}[language];

		if (!state.connected || !state.status) {
			items.push({ label: text.disconnected, value: "", disabled: true });
		} else if (state.status.windows.length === 0) {
			items.push({ label: text.empty, value: "", disabled: true });
		} else {
			for (const window of state.status.windows) {
				const characterName = resolveCharacterName(window);
				const classSuffix = window.character_class ? ` (${window.character_class})` : "";
				const alias = window.alias?.trim();
				const aliasSuffix = alias && alias !== characterName ? ` · ${text.alias} : ${alias}` : "";
				const position = window.position == null ? "—" : String(window.position);
				const ignoredSuffix = window.ignored ? ` · ${text.ignored}` : "";
				const attentionSuffix = window.attention ? ` · ${text.attention}` : "";
				items.push({
					label: `${position} — ${characterName}${classSuffix}${aliasSuffix}${ignoredSuffix}${attentionSuffix}`,
					value: String(window.slot),
				});
			}
		}

		await streamDeck.ui.sendToPropertyInspector({
			event: CHARACTER_DATA_SOURCE,
			items,
		});
	}

	private ensurePreferencesLoaded(): Promise<void> {
		if (!this.preferencesLoaded) {
			this.preferencesLoaded = streamDeck.settings
				.getGlobalSettings<PluginGlobalSettings>()
				.then((settings) => {
					this.globalSettings = settings;
					this.displayPreferences = sanitizeDisplayPreferences(settings.characterDisplayByCharacter);
					this.textLayouts = sanitizeTextLayouts(settings.characterTextLayoutByCharacter);
					this.accentPreferences = sanitizeCharacterAccents(settings.characterAccentByCharacter);
				})
				.catch((error) => {
					streamDeck.logger.warn("Impossible de lire les préférences globales des personnages :", error);
					this.globalSettings = {};
					this.displayPreferences = {};
					this.textLayouts = {};
					this.accentPreferences = {};
				});
		}
		return this.preferencesLoaded;
	}

	private async setCharacterDisplay(characterKey: string, display: DisplayMode): Promise<boolean> {
		await this.ensurePreferencesLoaded();
		if (this.displayPreferences[characterKey] === display) return false;

		this.displayPreferences = { ...this.displayPreferences, [characterKey]: display };
		this.globalSettings = {
			...this.globalSettings,
			characterDisplayByCharacter: { ...this.displayPreferences },
		};
		const settingsSnapshot = this.globalSettings;
		const write = this.preferenceWrites
			.catch(() => undefined)
			.then(() => streamDeck.settings.setGlobalSettings(settingsSnapshot));
		this.preferenceWrites = write;
		try {
			await write;
		} catch (error) {
			streamDeck.logger.error("Impossible d'enregistrer la préférence du personnage :", error);
		}
		return true;
	}

	private async setCharacterLayout(characterKey: string, layout: CharacterTextLayout): Promise<boolean> {
		await this.ensurePreferencesLoaded();
		if (this.textLayouts[characterKey] && layoutSignature(this.textLayouts[characterKey]) === layoutSignature(layout)) {
			return false;
		}

		this.textLayouts = { ...this.textLayouts, [characterKey]: { ...layout } };
		this.globalSettings = {
			...this.globalSettings,
			characterTextLayoutByCharacter: { ...this.textLayouts },
		};
		const settingsSnapshot = this.globalSettings;
		const write = this.preferenceWrites
			.catch(() => undefined)
			.then(() => streamDeck.settings.setGlobalSettings(settingsSnapshot));
		this.preferenceWrites = write;
		try {
			await write;
		} catch (error) {
			streamDeck.logger.error("Impossible d'enregistrer la mise en page du personnage :", error);
		}
		return true;
	}

	private async setCharacterAccent(characterKey: string, accent: CharacterAccent): Promise<boolean> {
		await this.ensurePreferencesLoaded();
		if (this.accentPreferences[characterKey] === accent) return false;

		this.accentPreferences = { ...this.accentPreferences, [characterKey]: accent };
		this.globalSettings = {
			...this.globalSettings,
			characterAccentByCharacter: { ...this.accentPreferences },
		};
		const settingsSnapshot = this.globalSettings;
		const write = this.preferenceWrites
			.catch(() => undefined)
			.then(() => streamDeck.settings.setGlobalSettings(settingsSnapshot));
		this.preferenceWrites = write;
		try {
			await write;
		} catch (error) {
			streamDeck.logger.error("Impossible d'enregistrer la couleur du personnage :", error);
		}
		return true;
	}

	private async syncActionSettings(
		action: KeyAction,
		settings: CharacterSettings,
		slot: number | undefined,
		characterKey: string | undefined,
		display: DisplayMode,
		layout: CharacterTextLayout,
		accent: CharacterAccent,
	): Promise<CharacterSettings> {
		const normalizedSlot = String(slot ?? settings.slot ?? 1);
		const layoutSettings = layoutToSettings(layout);
		const character = characterKey ?? settings.character;
		const synchronized = {
			...settings,
			character,
			slot: normalizedSlot,
			display,
			accentColor: accent,
			...layoutSettings,
		};
		this.bindings.set(action.id, {
			characterKey,
			display,
			layoutSignature: layoutSignature(layout),
			accent,
		});
		if (
			settings.character !== character ||
			settings.slot !== normalizedSlot ||
			settings.display !== display ||
			settings.accentColor !== accent ||
			settings.positionLine !== layoutSettings.positionLine ||
			settings.nameLine !== layoutSettings.nameLine ||
			settings.aliasLine !== layoutSettings.aliasLine ||
			settings.classLine !== layoutSettings.classLine
		) {
			await action.setSettings(synchronized);
		}
		return synchronized;
	}
}

function isCharacterDataSourceRequest(payload: JsonValue): boolean {
	return payload instanceof Object && "event" in payload && payload.event === CHARACTER_DATA_SOURCE;
}
