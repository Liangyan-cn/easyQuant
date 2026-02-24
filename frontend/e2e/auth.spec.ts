import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('can navigate between login and register', async ({ page }) => {
    await page.goto('/login');
    await page.getByText('立即注册').click();
    await expect(page).toHaveURL('/register');

    await page.getByText('立即登录').click();
    await expect(page).toHaveURL('/login');
  });

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByText('EasyQuant')).toBeVisible();
    await expect(page.getByText('登录您的账户')).toBeVisible();
    await expect(page.getByPlaceholder('邮箱')).toBeVisible();
    await expect(page.getByPlaceholder('密码')).toBeVisible();
    await expect(page.getByRole('button', { name: /登\s*录/ })).toBeVisible();
  });

  test('register page renders correctly', async ({ page }) => {
    await page.goto('/register');

    await expect(page.getByText('EasyQuant')).toBeVisible();
    await expect(page.getByText('创建新账户')).toBeVisible();
    await expect(page.getByPlaceholder('用户名')).toBeVisible();
    await expect(page.getByPlaceholder('邮箱')).toBeVisible();
    await expect(page.getByRole('button', { name: /注\s*册/ })).toBeVisible();
  });

  test('shows validation error for empty login form', async ({ page }) => {
    await page.goto('/login');

    await page.getByRole('button', { name: /登\s*录/ }).click();

    await expect(page.getByText('请输入邮箱')).toBeVisible({ timeout: 5000 });
  });
});
