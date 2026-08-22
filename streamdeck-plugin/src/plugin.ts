import streamDeck from "@elgato/streamdeck";

import { CharacterAction } from "./actions/character";
import {
	MoveDownAction,
	MoveUpAction,
	NextAction,
	PreviousAction,
	RefreshAction,
	ToggleIgnoreAction,
} from "./actions/commands";
import { LaunchAction } from "./actions/launch";

streamDeck.logger.setLevel("info");

streamDeck.actions.registerAction(new CharacterAction());
streamDeck.actions.registerAction(new LaunchAction());
streamDeck.actions.registerAction(new NextAction());
streamDeck.actions.registerAction(new PreviousAction());
streamDeck.actions.registerAction(new MoveUpAction());
streamDeck.actions.registerAction(new MoveDownAction());
streamDeck.actions.registerAction(new RefreshAction());
streamDeck.actions.registerAction(new ToggleIgnoreAction());

streamDeck.connect();
