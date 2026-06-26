const { test, expect } = require('@playwright/test');

test('can add a todo item', async ({ page }) => {
  await page.goto('file:///submission/index.html');
  await page.fill('input', 'Buy milk');
  await page.click('button:has-text("Add")');
  await expect(page.locator('text=Buy milk')).toBeVisible();
});

test('can add multiple items', async ({ page }) => {
  await page.goto('file:///submission/index.html');
  await page.fill('input', 'Task one');
  await page.click('button:has-text("Add")');
  await page.fill('input', 'Task two');
  await page.click('button:has-text("Add")');
  await expect(page.locator('text=Task one')).toBeVisible();
  await expect(page.locator('text=Task two')).toBeVisible();
});

test('can delete a todo item', async ({ page }) => {
  await page.goto('file:///submission/index.html');
  await page.fill('input', 'Delete me');
  await page.click('button:has-text("Add")');
  await page.click('button:has-text("Delete")');
  await expect(page.locator('text=Delete me')).not.toBeVisible();
});
