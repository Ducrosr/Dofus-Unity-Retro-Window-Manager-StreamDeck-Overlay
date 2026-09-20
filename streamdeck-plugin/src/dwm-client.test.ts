import assert from "node:assert/strict";
import test from "node:test";

import { DwmClient, DwmCommandError } from "./dwm-client";

test("non-idempotent rotate is never replayed after an ambiguous backend error", async () => {
	const originalFetch = globalThis.fetch;
	let calls = 0;
	globalThis.fetch = async () => {
		calls += 1;
		return new Response(
			JSON.stringify({
				ok: false,
				error: "Le résultat de la commande est indéterminé.",
				error_code: "outcome_unknown",
				request_id: "logical-1",
			}),
			{
				status: 504,
				headers: { "Content-Type": "application/json" },
			},
		);
	};

	try {
		const client = new DwmClient();
		await assert.rejects(
			client.rotate("forward"),
			(error: unknown) => {
				assert.ok(error instanceof DwmCommandError);
				assert.equal(error.status, 504);
				assert.equal(error.code, "outcome_unknown");
				assert.equal(error.requestId, "logical-1");
				return true;
			},
		);
		assert.equal(calls, 1);
	} finally {
		globalThis.fetch = originalFetch;
	}
});

test("rotation sends the current mode and profile context", async () => {
	const originalFetch = globalThis.fetch;
	let posted: Record<string, unknown> | undefined;
	globalThis.fetch = async (_input, init) => {
		posted = JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown>;
		return new Response(JSON.stringify({ ok: true }), {
			status: 200,
			headers: { "Content-Type": "application/json" },
		});
	};

	try {
		const client = new DwmClient();
		(
			client as unknown as {
				state: {
					connected: boolean;
					status: { game_mode: "retro"; profile: string; windows: [] };
				};
			}
		).state = {
			connected: true,
			status: { game_mode: "retro", profile: "Team 8", windows: [] },
		};
		await client.rotate("backward");

		assert.deepEqual(posted, {
			direction: "backward",
			game_mode: "retro",
			profile: "Team 8",
		});
	} finally {
		globalThis.fetch = originalFetch;
	}
});
