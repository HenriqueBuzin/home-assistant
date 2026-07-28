import { expect, test } from "@playwright/test";

test("Home Assistant responde pela interface HTTP", async ({ request }) => {
  const response = await request.get("/");
  expect(response.ok()).toBeTruthy();
});
