import type { KeyDownEvent } from "@elgato/streamdeck";
import streamDeck, { action } from "@elgato/streamdeck";

import { type ActionKind, type EmptySettings, ThemeAwareAction } from "../action-key";
import { dwmClient } from "../dwm-client";

abstract class CommandAction extends ThemeAwareAction {
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
	protected readonly actionKind: ActionKind = "next";
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.rotate("forward"));
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.previous" })
export class PreviousAction extends CommandAction {
	protected readonly actionKind: ActionKind = "previous";
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.rotate("backward"));
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.next-attention" })
export class NextAttentionAction extends CommandAction {
	protected readonly actionKind: ActionKind = "next-attention";
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.nextAttention());
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.move-up" })
export class MoveUpAction extends CommandAction {
	protected readonly actionKind: ActionKind = "move-up";
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.reorder("up"));
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.move-down" })
export class MoveDownAction extends CommandAction {
	protected readonly actionKind: ActionKind = "move-down";
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.reorder("down"));
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.refresh" })
export class RefreshAction extends CommandAction {
	protected readonly actionKind: ActionKind = "refresh";
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.refresh());
	}
}

@action({ UUID: "com.remyducros.dofuswindowmanager.toggle-ignore" })
export class ToggleIgnoreAction extends CommandAction {
	protected readonly actionKind: ActionKind = "toggle-ignore";
	override async onKeyDown(ev: KeyDownEvent<EmptySettings>): Promise<void> {
		await this.execute(ev, () => dwmClient.toggleIgnore());
	}
}
