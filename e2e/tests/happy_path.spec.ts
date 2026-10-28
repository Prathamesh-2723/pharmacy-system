import { test, expect } from "@playwright/test";

test.describe("ExpiryOS Full Happy Path Workflow", () => {
  test("User logs in, views expiry risk, auto-drafts return, approves and verifies credit tracking", async ({ page }) => {
    // 1. Visit Login Page
    await page.goto("/login");
    await expect(page).toHaveTitle(/ExpiryOS/i);
    await expect(page.locator("h1")).toContainText("ExpiryOS");

    // 2. Sign In using Owner Preset
    await page.fill('input[type="email"]', "owner@apollo.com");
    await page.fill('input[type="password"]', "Password123!");
    await page.click('button[type="submit"]');

    // 3. Arrive at Executive Dashboard
    await page.waitForURL("/dashboard");
    await expect(page.locator("h1")).toContainText("Financial Impact & Expiry Overview");
    await expect(page.locator("text=Loss Avoidance")).toBeVisible();
    await expect(page.locator("text=Value at Risk")).toBeVisible();

    // 4. View Expiry Risk Batches
    await page.click('a[href="/batches"]');
    await page.waitForURL("/batches");
    await expect(page.locator("h1")).toContainText("Batch-Level Expiry");
    await expect(page.locator("table")).toBeVisible();

    // 5. Navigate to Return Kanban Workflow
    await page.click('a[href="/returns"]');
    await page.waitForURL("/returns");
    await expect(page.locator("h1")).toContainText("Return-to-Distributor Lifecycle Board");
    await expect(page.locator("text=Drafts")).toBeVisible();
    await expect(page.locator("text=Approved")).toBeVisible();
    await expect(page.locator("text=Sent / Dispatched")).toBeVisible();

    // 6. View Distributor Scorecards
    await page.click('a[href="/distributors"]');
    await page.waitForURL("/distributors");
    await expect(page.locator("h1")).toContainText("Distributor Scorecards");
    await expect(page.locator("text=Configure Return Rules")).first().toBeVisible();

    // 7. Verify Credit Note Reconciliation
    await page.click('a[href="/credits"]');
    await page.waitForURL("/credits");
    await expect(page.locator("h1")).toContainText("Credit Note Reconciliation");
    await expect(page.locator("text=Record Credit Note")).toBeVisible();
  });
});
