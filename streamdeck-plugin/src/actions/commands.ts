import type { KeyDownEvent } from "@elgato/streamdeck";
import streamDeck, { action, SingletonAction } from "@elgato/streamdeck";

import { dwmClient } from "../dwm-client";

type EmptySettings = Record<string, never>;

abstract class CommandAction extends SingletonAction<EmptySettings> {
	protected async execute(ev: KeyDownEvent<EmptySettings>, command: () => Promise<unknown>): Promise<void> {
		try {
			await command();
			ev.action.showOk();
		} catch (error) {
			streamDeck.logger.error("Commande Dofus Window Manager impossible :", error);
			ev.action.showAlert();
		}
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.next" })
export class NextAction extends CommandAction {
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.rotate("forward"));
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.previous" })
export class PreviousAction extends CommandAction {
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.rotate("backward"));
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.move-up" })
export class MoveUpAction extends CommandAction {
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.reorder("up"));
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.move-down" })
export class MoveDownAction extends CommandAction {
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.reorder("down"));
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.refresh" })
export class RefreshAction extends CommandAction {
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.refresh());
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.toggle-ignore" })
export class ToggleIgnoreAction extends CommandAction {
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.toggleIgnore());
	}
}
