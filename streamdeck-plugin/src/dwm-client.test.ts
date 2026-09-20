import assert from "node:assert/strict";
import test from "node:test";

import { DwmClient } from "./dwm-client";

test("non-idempotent rotate is never retried after an HTTP failure", async () => {
	const originalFetch = globalThis.fetch;
	let calls = 0;
	globalThis.fetch = (async () => {
		calls += 1;
		return {
			ok: false,
			status: 504,
			json: async () => ({
				ok: false,
				error: "La commande a commencé mais sa réponse n'est pas arrivée à temps.",
				error_code: "command_timeout_after_start",
				execution: "started",
			}),
		} as Response;
	}) as typeof fetch;

	try {
		const client = new DwmClient();
		await assert.rejects(client.rotate("forward"), /command_timeout_after_start/);
		assert.equal(calls, 1);
	} finally {
		globalThis.fetch = originalFetch;
	}
});

test("focus sends one request with the published mode and profile context", async () => {
	const originalFetch = globalThis.fetch;
	const requests: Array<Record<string, unknown>> = [];

	globalThis.fetch = (async (_input, init) => {
		requests.push(JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown>);
		return {
			ok: true,
			status: 200,
			json: async () => ({ ok: true }),
		} as Response;
	}) as typeof fetch;

	try {
		const client = new DwmClient();
		const writable = client as unknown as {
			state: {
				connected: boolean;
				status: {
					api_version: number;
					app_version: string;
					game_mode: "retro";
					profile: string;
					windows: [];
				};
			};
		};
		writable.state = {
			connected: true,
			status: {
				api_version: 1,
				app_version: "test",
				game_mode: "retro",
				profile: "Team Retro",
				windows: [],
			},
		};
		await client.focus({ hwnd: 123, slot: 2, pseudo: "Nealla" });

		assert.equal(requests.length, 1);
		assert.deepEqual(requests[0], {
			hwnd: 123,
			slot: 2,
			pseudo: "Nealla",
			game_mode: "retro",
			profile: "Team Retro",
		});
	} finally {
		globalThis.fetch = originalFetch;
	}
});
