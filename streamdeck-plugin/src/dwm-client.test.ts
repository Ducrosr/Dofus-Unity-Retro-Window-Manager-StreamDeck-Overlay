import assert from "node:assert/strict";
import test from "node:test";

import { DwmCommandError, dwmClient } from "./dwm-client.ts";

test("une mutation échouée n'est jamais rejouée après réponse ambiguë", async () => {
	const originalFetch = globalThis.fetch;
	let calls = 0;
	globalThis.fetch = (async () => {
		calls += 1;
		return new Response(
			JSON.stringify({
				ok: false,
				error_code: "completion_unknown",
				error: "Résultat inconnu.",
				request_id: "request-1",
			}),
			{
				status: 504,
				headers: { "Content-Type": "application/json" },
			},
		);
	}) as typeof fetch;

	try {
		await assert.rejects(
			() => dwmClient.rotate("forward"),
			(error: unknown) =>
				error instanceof DwmCommandError &&
				error.code === "completion_unknown" &&
				error.requestId === "request-1",
		);
		assert.equal(calls, 1);
	} finally {
		globalThis.fetch = originalFetch;
	}
});
