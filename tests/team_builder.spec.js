const { test, expect } = require("@playwright/test");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const pageUrl = pathToFileURL(path.resolve(__dirname, "..", "index.html")).href;

test.beforeEach(async ({ page }) => {
  await page.goto(pageUrl);
  await page.evaluate(() => {
    localStorage.setItem(
      "tiles-survive-team-builder-v1",
      JSON.stringify({
        version: 2,
        heroes: {
          nikola: {
            owned: true,
            level: 120,
            stars: 0,
            skills: [1, 1, 1, 0],
            sigStars: 0,
          },
          rosie: {
            owned: true,
            level: 120,
            stars: 0,
            skills: [1, 1, 1, 0],
            sigStars: 0,
          },
        },
        inventory: {
          helmet: [10, 9, 8, 7, 6],
          armor: [10, 9, 8, 7, 6],
          legs: [10, 9, 8, 7, 6],
        },
      }),
    );
  });
  await page.reload();
});

test("keeps two teams independent and prevents duplicate gear in one team", async ({
  page,
}) => {
  await expect(page.getByTestId("team-panel-1")).toBeVisible();
  await expect(page.getByTestId("team-panel-2")).toBeVisible();
  await page.getByTestId("add-hero-nikola").click();
  await page.getByTestId("gear-1-nikola-helmet").selectOption("helmet-1");

  await page.getByTestId("copy-team-1-to-2").click();
  await expect(page.getByTestId("team-slot-2-1")).toContainText("Nikola");
  await expect(page.getByTestId("gear-2-nikola-helmet")).toHaveValue(
    "helmet-1",
  );

  await page.getByTestId("team-slot-1-2").click();
  await page.getByTestId("add-hero-rosie").click();
  await expect(page.getByTestId("team-slot-1-2")).toContainText("Rosie");

  const rosieOptions = await page
    .getByTestId("gear-1-rosie-helmet")
    .locator("option")
    .allTextContents();
  expect(rosieOptions.some((text) => text.includes("#1"))).toBeFalsy();

  await expect(page.getByTestId("team-slot-2-2")).not.toContainText("Rosie");
});
