import { test, expect } from '@playwright/test';

test.describe('Stock Browsing Flow', () => {
  test('redirects to login when accessing stocks without auth', async ({ page }) => {
    await page.goto('/stocks');

    await expect(page).toHaveURL('/login', { timeout: 5000 });
  });

  test('redirects to login when accessing home without auth', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveURL('/login', { timeout: 5000 });
  });

  test('can access login page directly', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByText('EasyQuant')).toBeVisible();
    await expect(page).toHaveURL('/login');
  });
});
