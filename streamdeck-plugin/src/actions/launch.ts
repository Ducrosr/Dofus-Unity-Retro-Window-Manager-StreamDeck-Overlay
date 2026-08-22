import type { KeyDownEvent } from "@elgato/streamdeck";
import streamDeck, { action, SingletonAction } from "@elgato/streamdeck";

import { dwmClient } from "../dwm-client";
import { launchRegisteredApp } from "../launcher";

type EmptySettings = Record<string, never>;

@action({ UUID: "com.remyducros.dofuswindowmanager.launch" })
export class LaunchAction extends SingletonAction<EmptySettings> {
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
