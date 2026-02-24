import { Page } from '@playwright/test';

const TEST_USER = {
  username: 'e2e_test_user',
  email: 'e2e_test@example.com',
  password: 'Test123456',
};

export async function ensureTestUserExists(page: Page) {
  await page.goto('/register');
  await page.getByPlaceholder('用户名').fill(TEST_USER.username);
  await page.getByPlaceholder('邮箱').fill(TEST_USER.email);
  const passwordFields = page.getByPlaceholder(/密码/);
  await passwordFields.first().fill(TEST_USER.password);
  if (await passwordFields.count() > 1) {
    await passwordFields.nth(1).fill(TEST_USER.password);
  }
  await page.getByRole('button', { name: /注\s*册/ }).click();
  await page.waitForTimeout(2000);
}

export async function loginAsTestUser(page: Page) {
  await page.goto('/login');
  await page.getByPlaceholder('邮箱').fill(TEST_USER.email);
  await page.getByPlaceholder('密码').fill(TEST_USER.password);
  await page.getByRole('button', { name: /登\s*录/ }).click();
  
  try {
    await page.waitForURL('/', { timeout: 5000 });
  } catch {
    await ensureTestUserExists(page);
    await page.goto('/login');
    await page.getByPlaceholder('邮箱').fill(TEST_USER.email);
    await page.getByPlaceholder('密码').fill(TEST_USER.password);
    await page.getByRole('button', { name: /登\s*录/ }).click();
    await page.waitForURL('/', { timeout: 10000 });
  }
}

export { TEST_USER };
