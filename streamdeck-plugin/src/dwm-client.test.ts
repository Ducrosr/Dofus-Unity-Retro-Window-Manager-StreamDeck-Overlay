import assert from "node:assert/strict";
import test from "node:test";

import { DwmClient } from "./dwm-client.ts";

test("une mutation focus en erreur n'est jamais rejouee", async () => {
	const originalFetch = globalThis.fetch;
	const calls: Array<{ url: string; init?: RequestInit }> = [];
	globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
		calls.push({ url: String(url), init });
		return {
			ok: false,
			status: 504,
			json: async () => ({
				error: "L'application ne repond pas.",
				code: "backend_timeout",
			}),
		} as Response;
	}) as typeof fetch;

	let releases = 0;
	const client = new DwmClient(async () => {
		releases += 1;
		return true;
	});

	try {
		await assert.rejects(
			() => client.focus({ hwnd: 101, slot: 1, pseudo: "Nealla" }),
			/L'application ne repond pas/u,
		);
		assert.equal(releases, 1);
		assert.equal(calls.length, 1);
		assert.match(calls[0].url, /\/v1\/focus$/u);
		const payload = JSON.parse(String(calls[0].init?.body ?? "{}")) as Record<string, unknown>;
		assert.equal(payload.hwnd, 101);
		assert.match(String(payload.request_id), /^sd-/u);
	} finally {
		globalThis.fetch = originalFetch;
	}
});

test("une erreur reseau ambigue ne provoque pas de second POST", async () => {
	const originalFetch = globalThis.fetch;
	let calls = 0;
	globalThis.fetch = (async () => {
		calls += 1;
		throw new Error("timeout");
	}) as typeof fetch;

	const client = new DwmClient(async () => false);
	try {
		await assert.rejects(
			() => client.rotate("forward"),
			/timeout/u,
		);
		assert.equal(calls, 1);
	} finally {
		globalThis.fetch = originalFetch;
	}
});
