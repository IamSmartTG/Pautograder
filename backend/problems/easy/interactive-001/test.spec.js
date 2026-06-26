const { test, expect } = require('@playwright/test');
const path = require('path');

test('click counter works correctly', async ({ page }) => {
  // Student must submit an index.html in their zip
  await page.goto('file:///submission/index.html');

  // Counter starts at 0
  const counter = page.locator('[data-testid="counter"], #counter, .counter');
  await expect(counter).toHaveText('0');

  // Click increments counter
  await page.click('button:has-text("Click me")');
  await expect(counter).toHaveText('1');

  await page.click('button:has-text("Click me")');
  await expect(counter).toHaveText('2');

  // Screenshot comparison
  await expect(page).toHaveScreenshot('baseline.png', { threshold: 0.05 });
});
