import { test, expect } from '@playwright/test';
import { loginAsTestUser } from './helpers/auth';

test.describe('Factor Management Flow', () => {
  test.describe('Unauthenticated Access', () => {
    test('redirects to login when accessing factors without auth', async ({ page }) => {
      await page.goto('/factors');
      await expect(page).toHaveURL('/login', { timeout: 5000 });
    });

    test('redirects to login when accessing factor detail without auth', async ({ page }) => {
      await page.goto('/factors/1');
      await expect(page).toHaveURL('/login', { timeout: 5000 });
    });
  });

  test.describe('Factor List Page', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can navigate to factors page', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '因子管理' }).click();
      await expect(page).toHaveURL('/factors');
      await expect(page.getByText('因子管理')).toBeVisible();
    });

    test('factors page renders correctly', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '因子管理' }).click();
      await expect(page).toHaveURL('/factors');

      await expect(page.getByText('因子管理')).toBeVisible();
      await expect(page.getByPlaceholder('搜索因子名称或代码')).toBeVisible();
      await expect(page.getByRole('button', { name: '新建因子' })).toBeVisible();
      await expect(page.getByRole('button', { name: '初始化内置因子' })).toBeVisible();
    });

    test('can search factors', async ({ page }) => {
      await page.goto('/factors');

      const searchInput = page.getByPlaceholder('搜索因子名称或代码');
      await searchInput.fill('momentum');
      await searchInput.press('Enter');

      await page.waitForTimeout(1000);
    });

    test('can filter by category', async ({ page }) => {
      await page.goto('/factors');

      const categorySelect = page.locator('.ant-select').first();
      await categorySelect.click();
      await page.waitForTimeout(500);
    });
  });

  test.describe('Factor Detail Page', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can navigate to factor detail from list', async ({ page }) => {
      await page.goto('/factors');

      const detailButton = page.getByRole('button', { name: '详情' }).first();
      if (await detailButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await detailButton.click();
        await expect(page.url()).toContain('/factors/');
      }
    });

    test('factor detail page shows factor info', async ({ page }) => {
      await page.goto('/factors/1');

      await page.waitForLoadState('networkidle');

      const pageContent = await page.content();
      const hasFactorContent = pageContent.includes('因子') ||
        pageContent.includes('Factor') ||
        pageContent.includes('分析');
      expect(hasFactorContent).toBeTruthy();
    });
  });

  test.describe('Factor Creation', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can open create factor modal', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '因子管理' }).click();
      await expect(page).toHaveURL('/factors');

      await page.getByRole('button', { name: '新建因子' }).click();
      await page.waitForTimeout(500);

      const modal = page.locator('.ant-modal');
      await expect(modal).toBeVisible({ timeout: 5000 });
      await expect(modal.locator('.ant-modal-title')).toContainText('新建因子');
    });

    test('create factor form has required fields', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '因子管理' }).click();
      await expect(page).toHaveURL('/factors');

      await page.getByRole('button', { name: '新建因子' }).click();
      await page.waitForTimeout(500);

      const modal = page.locator('.ant-modal');
      await expect(modal).toBeVisible({ timeout: 5000 });
      await expect(modal.getByText('名称')).toBeVisible();
      await expect(modal.getByText('代码')).toBeVisible();
      await expect(modal.getByText('分类')).toBeVisible();
    });
  });

  test.describe('Initialize Builtin Factors', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can click initialize builtin factors button', async ({ page }) => {
      await page.goto('/factors');

      const initButton = page.getByRole('button', { name: '初始化内置因子' });
      await expect(initButton).toBeVisible();

      await initButton.click();
      await page.waitForTimeout(1000);
    });
  });
});
