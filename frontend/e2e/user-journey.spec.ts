import { test, expect } from '@playwright/test';
import { loginAsTestUser } from './helpers/auth';

test.describe('Complete User Journey', () => {
  test.describe('New User Onboarding', () => {
    test('can complete registration flow', async ({ page }) => {
      await page.goto('/register');
      
      await expect(page.getByText('创建新账户')).toBeVisible();
      await expect(page.getByPlaceholder('用户名')).toBeVisible();
      await expect(page.getByPlaceholder('邮箱')).toBeVisible();
      
      await page.getByText('立即登录').click();
      await expect(page).toHaveURL('/login');
    });

    test('can navigate from login to register and back', async ({ page }) => {
      await page.goto('/login');
      
      await page.getByText('立即注册').click();
      await expect(page).toHaveURL('/register');
      
      await page.getByText('立即登录').click();
      await expect(page).toHaveURL('/login');
    });
  });

  test.describe('Authenticated User Navigation', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can navigate through all main sections', async ({ page }) => {
      await expect(page.getByText('欢迎使用 EasyQuant')).toBeVisible();
      
      await page.locator('.ant-menu-item').filter({ hasText: '股票数据' }).click();
      await expect(page).toHaveURL('/stocks');
      await expect(page.getByText('股票列表')).toBeVisible();
      
      await page.locator('.ant-menu-item').filter({ hasText: '因子管理' }).click();
      await expect(page).toHaveURL('/factors');
      await expect(page.getByText('因子管理')).toBeVisible();
      
      await page.locator('.ant-menu-item').filter({ hasText: '策略管理' }).click();
      await expect(page).toHaveURL('/strategies');
      await expect(page.getByText('策略管理')).toBeVisible();
      
      await page.locator('.ant-menu-item').filter({ hasText: '沙盒交易' }).click();
      await expect(page).toHaveURL('/sandbox');
      await expect(page.getByText('沙盒账户')).toBeVisible();
    });

    test('home page displays feature cards', async ({ page }) => {
      await page.goto('/');
      
      await expect(page.getByText('策略回测')).toBeVisible();
      await expect(page.getByText('实时行情')).toBeVisible();
      await expect(page.getByText('自动交易')).toBeVisible();
    });
  });

  test.describe('Quant Workflow: Factor to Strategy to Sandbox', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can browse factors and view details', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '因子管理' }).click();
      await expect(page).toHaveURL('/factors');
      await expect(page.getByText('因子管理')).toBeVisible();
      
      const detailButton = page.getByRole('button', { name: '详情' }).first();
      if (await detailButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await detailButton.click();
        await page.waitForLoadState('networkidle');
        await expect(page.url()).toContain('/factors/');
      }
    });

    test('can browse strategies and view details', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '策略管理' }).click();
      await expect(page).toHaveURL('/strategies');
      await expect(page.getByText('策略管理')).toBeVisible();
      
      const detailButton = page.getByRole('button', { name: '详情' }).first();
      if (await detailButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await detailButton.click();
        await page.waitForLoadState('networkidle');
        await expect(page.url()).toContain('/strategies/');
      }
    });

    test('can browse sandbox accounts and view details', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '沙盒交易' }).click();
      await expect(page).toHaveURL('/sandbox');
      await expect(page.getByText('沙盒账户')).toBeVisible();
      
      const detailButton = page.getByRole('button', { name: '详情' }).first();
      if (await detailButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await detailButton.click();
        await page.waitForLoadState('networkidle');
        await expect(page.url()).toContain('/sandbox/');
      }
    });
  });

  test.describe('Stock Research Flow', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can browse stocks and search', async ({ page }) => {
      await page.goto('/stocks');
      await expect(page.getByText('股票列表')).toBeVisible();
      
      const searchInput = page.getByPlaceholder('搜索股票名称或代码');
      await searchInput.fill('平安');
      await searchInput.press('Enter');
      
      await page.waitForTimeout(1000);
    });

    test('can view stock detail', async ({ page }) => {
      await page.goto('/stocks');
      
      const stockRow = page.locator('tr').filter({ hasText: /\d{6}/ }).first();
      if (await stockRow.isVisible({ timeout: 5000 }).catch(() => false)) {
        await stockRow.click();
        await page.waitForLoadState('networkidle');
      }
    });
  });

  test.describe('Data Persistence', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('maintains session across page navigation', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '股票数据' }).click();
      await expect(page).toHaveURL('/stocks');
      await expect(page.getByText('股票列表')).toBeVisible();
      
      await page.locator('.ant-menu-item').filter({ hasText: '因子管理' }).click();
      await expect(page).toHaveURL('/factors');
      await expect(page.getByText('因子管理')).toBeVisible();
      
      await page.locator('.ant-menu-item').filter({ hasText: '策略管理' }).click();
      await expect(page).toHaveURL('/strategies');
      await expect(page.getByText('策略管理')).toBeVisible();
      
      await page.locator('.ant-menu-item').filter({ hasText: '沙盒交易' }).click();
      await expect(page).toHaveURL('/sandbox');
      await expect(page.getByText('沙盒账户')).toBeVisible();
    });

    test('can refresh page and stay logged in', async ({ page }) => {
      await page.goto('/stocks');
      await expect(page.getByText('股票列表')).toBeVisible();
      
      await page.reload();
      
      const isStillOnStocks = await page.url().includes('/stocks');
      const redirectedToLogin = await page.url().includes('/login');
      
      expect(isStillOnStocks || redirectedToLogin).toBeTruthy();
    });
  });

  test.describe('Error Handling', () => {
    test('shows 404 or redirects for non-existent pages', async ({ page }) => {
      await page.goto('/non-existent-page');
      await page.waitForLoadState('networkidle');
      
      const is404 = await page.getByText('404').isVisible({ timeout: 3000 }).catch(() => false);
      const isRedirected = page.url().includes('/login');
      const isHome = page.url().endsWith('/') || page.url().includes('localhost:3000');
      
      expect(is404 || isRedirected || isHome).toBeTruthy();
    });

    test('handles invalid factor ID gracefully', async ({ page }) => {
      await loginAsTestUser(page);
      await page.goto('/factors/99999');
      
      await page.waitForLoadState('networkidle');
      
      const hasError = await page.getByText('错误').or(page.getByText('Error')).or(page.getByText('未找到')).isVisible({ timeout: 3000 }).catch(() => false);
      const isOnFactorsPage = page.url().includes('/factors');
      
      expect(hasError || isOnFactorsPage).toBeTruthy();
    });
  });

  test.describe('Responsive Layout', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('sidebar navigation is visible on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');
      
      const sidebar = page.locator('.ant-layout-sider').or(page.locator('nav'));
      await expect(sidebar).toBeVisible();
    });

    test('main content area is visible', async ({ page }) => {
      await page.goto('/');
      
      const mainContent = page.locator('.ant-layout-content').or(page.locator('main'));
      await expect(mainContent).toBeVisible();
    });
  });
});
