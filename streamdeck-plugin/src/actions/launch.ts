import type { KeyDownEvent } from "@elgato/streamdeck";
import streamDeck, { action } from "@elgato/streamdeck";

import { type ActionKind, type EmptySettings, ThemeAwareAction } from "../action-key";
import { dwmClient } from "../dwm-client";
import { launchRegisteredApp } from "../launcher";

@action({ UUID: "com.remyducros.dofuswindowmanager.launch" })
export class LaunchAction extends ThemeAwareAction {
	protected readonly actionKind: ActionKind = "launch";
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		try {
			try {
				await dwmClient.show();
			} catch {
				await launchRegisteredApp();
			}
			ev.action.showOk();
		} catch (error) {
			streamDeck.logger.error("Lancement de Dofus Window Manager impossible :", error);
			ev.action.showAlert();
		}
	}
}
