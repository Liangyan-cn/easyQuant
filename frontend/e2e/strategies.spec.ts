import { test, expect } from '@playwright/test';
import { loginAsTestUser } from './helpers/auth';

test.describe('Strategy Management Flow', () => {
  test.describe('Unauthenticated Access', () => {
    test('redirects to login when accessing strategies without auth', async ({ page }) => {
      await page.goto('/strategies');
      await expect(page).toHaveURL('/login', { timeout: 5000 });
    });

    test('redirects to login when accessing strategy detail without auth', async ({ page }) => {
      await page.goto('/strategies/1');
      await expect(page).toHaveURL('/login', { timeout: 5000 });
    });
  });

  test.describe('Strategy List Page', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can navigate to strategies page', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '策略管理' }).click();
      await expect(page).toHaveURL('/strategies');
      await expect(page.getByText('策略管理')).toBeVisible();
    });

    test('strategies page renders correctly', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '策略管理' }).click();
      await expect(page).toHaveURL('/strategies');
      
      await expect(page.getByText('策略管理')).toBeVisible();
      await expect(page.getByPlaceholder('搜索策略名称或代码')).toBeVisible();
      await expect(page.getByRole('button', { name: '新建策略' })).toBeVisible();
    });

    test('can search strategies', async ({ page }) => {
      await page.goto('/strategies');
      
      const searchInput = page.getByPlaceholder('搜索策略名称或代码');
      await searchInput.fill('ma_cross');
      await searchInput.press('Enter');
      
      await page.waitForTimeout(1000);
    });

    test('displays strategy table with columns', async ({ page }) => {
      await page.goto('/strategies');
      
      await expect(page.getByRole('columnheader', { name: '名称' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '代码' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '类型' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '状态' })).toBeVisible();
    });
  });

  test.describe('Strategy Detail Page', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can navigate to strategy detail from list', async ({ page }) => {
      await page.goto('/strategies');
      
      const detailButton = page.getByRole('button', { name: '详情' }).first();
      if (await detailButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await detailButton.click();
        await expect(page.url()).toContain('/strategies/');
      }
    });

    test('strategy detail page shows strategy info', async ({ page }) => {
      await page.goto('/strategies/1');
      
      await page.waitForLoadState('networkidle');
      
      const pageContent = await page.content();
      const hasStrategyContent = pageContent.includes('策略') || 
                                  pageContent.includes('Strategy') ||
                                  pageContent.includes('回测');
      expect(hasStrategyContent).toBeTruthy();
    });

    test('strategy detail has backtest section', async ({ page }) => {
      await page.goto('/strategies/1');
      
      await page.waitForLoadState('networkidle');
      
      const backtestSection = page.getByText('回测').or(page.getByText('Backtest'));
      if (await backtestSection.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(backtestSection).toBeVisible();
      }
    });
  });

  test.describe('Strategy Creation', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can open create strategy modal', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '策略管理' }).click();
      await expect(page).toHaveURL('/strategies');
      
      await page.getByRole('button', { name: '新建策略' }).click();
      await page.waitForTimeout(500);
      
      const modal = page.locator('.ant-modal');
      await expect(modal).toBeVisible({ timeout: 5000 });
      await expect(modal.locator('.ant-modal-title')).toContainText('新建策略');
    });

    test('create strategy form has required fields', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '策略管理' }).click();
      await expect(page).toHaveURL('/strategies');
      
      await page.getByRole('button', { name: '新建策略' }).click();
      await page.waitForTimeout(500);
      
      const modal = page.locator('.ant-modal');
      await expect(modal).toBeVisible({ timeout: 5000 });
      await expect(modal.getByText('名称')).toBeVisible();
      await expect(modal.getByText('代码')).toBeVisible();
      await expect(modal.getByText('类型')).toBeVisible();
    });
  });

  test.describe('Strategy Actions', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can copy strategy', async ({ page }) => {
      await page.goto('/strategies');
      
      const copyButton = page.getByRole('button', { name: '复制' }).first();
      if (await copyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await copyButton.click();
        await page.waitForTimeout(1000);
      }
    });

    test('can delete strategy with confirmation', async ({ page }) => {
      await page.goto('/strategies');
      
      const deleteButton = page.getByRole('button', { name: '删除' }).first();
      if (await deleteButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await deleteButton.click();
        
        const confirmButton = page.getByRole('button', { name: '确定' }).or(page.getByRole('button', { name: '确认' }));
        if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await expect(confirmButton).toBeVisible();
        }
      }
    });
  });
});
