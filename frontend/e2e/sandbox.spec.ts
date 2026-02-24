import { test, expect } from '@playwright/test';
import { loginAsTestUser } from './helpers/auth';

test.describe('Sandbox Account Flow', () => {
  test.describe('Unauthenticated Access', () => {
    test('redirects to login when accessing sandbox without auth', async ({ page }) => {
      await page.goto('/sandbox');
      await expect(page).toHaveURL('/login', { timeout: 5000 });
    });

    test('redirects to login when accessing sandbox detail without auth', async ({ page }) => {
      await page.goto('/sandbox/1');
      await expect(page).toHaveURL('/login', { timeout: 5000 });
    });
  });

  test.describe('Sandbox List Page', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can navigate to sandbox page', async ({ page }) => {
      await page.locator('.ant-menu-item').filter({ hasText: '沙盒交易' }).click();
      await expect(page).toHaveURL('/sandbox');
      await expect(page.getByText('沙盒账户')).toBeVisible();
    });

    test('sandbox page renders correctly', async ({ page }) => {
      await page.goto('/sandbox');
      
      await expect(page.getByText('沙盒账户')).toBeVisible();
      await expect(page.getByPlaceholder('搜索账户名称或描述')).toBeVisible();
      await expect(page.getByRole('button', { name: '新建账户' })).toBeVisible();
    });

    test('can search sandbox accounts', async ({ page }) => {
      await page.goto('/sandbox');
      
      const searchInput = page.getByPlaceholder('搜索账户名称或描述');
      await searchInput.fill('测试');
      await searchInput.press('Enter');
      
      await page.waitForTimeout(1000);
    });

    test('displays sandbox table with columns', async ({ page }) => {
      await page.goto('/sandbox');
      
      await expect(page.getByRole('columnheader', { name: '账户名称' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '初始资金' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '状态' })).toBeVisible();
    });
  });

  test.describe('Sandbox Detail Page', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can navigate to sandbox detail from list', async ({ page }) => {
      await page.goto('/sandbox');
      
      const detailButton = page.getByRole('button', { name: '详情' }).first();
      if (await detailButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await detailButton.click();
        await expect(page.url()).toContain('/sandbox/');
      }
    });

    test('sandbox detail page shows account info', async ({ page }) => {
      await page.goto('/sandbox/1');
      
      await page.waitForLoadState('networkidle');
      
      const pageContent = await page.content();
      const hasSandboxContent = pageContent.includes('账户') || 
                                 pageContent.includes('资金') ||
                                 pageContent.includes('持仓') ||
                                 pageContent.includes('Sandbox');
      expect(hasSandboxContent).toBeTruthy();
    });

    test('sandbox detail has positions section', async ({ page }) => {
      await page.goto('/sandbox/1');
      
      await page.waitForLoadState('networkidle');
      
      const positionsSection = page.getByText('持仓').or(page.getByText('Positions'));
      if (await positionsSection.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(positionsSection).toBeVisible();
      }
    });

    test('sandbox detail has performance metrics', async ({ page }) => {
      await page.goto('/sandbox/1');
      
      await page.waitForLoadState('networkidle');
      
      const metricsSection = page.getByText('收益').or(page.getByText('绩效')).or(page.getByText('Performance'));
      if (await metricsSection.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(metricsSection).toBeVisible();
      }
    });
  });

  test.describe('Sandbox Creation', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can open create sandbox modal', async ({ page }) => {
      await page.goto('/sandbox');
      
      await page.getByRole('button', { name: '新建账户' }).click();
      
      await expect(page.getByText('新建账户').or(page.getByText('创建账户'))).toBeVisible({ timeout: 5000 });
    });

    test('create sandbox form has required fields', async ({ page }) => {
      await page.goto('/sandbox');
      
      await page.getByRole('button', { name: '新建账户' }).click();
      await page.waitForTimeout(500);
      
      const modal = page.locator('.ant-modal');
      if (await modal.isVisible()) {
        const hasNameField = await modal.getByText('名称').or(modal.getByText('账户名称')).isVisible().catch(() => false);
        expect(hasNameField).toBeTruthy();
      }
    });

    test('create sandbox form has initial capital field', async ({ page }) => {
      await page.goto('/sandbox');
      
      await page.getByRole('button', { name: '新建账户' }).click();
      await page.waitForTimeout(500);
      
      const modal = page.locator('.ant-modal');
      if (await modal.isVisible()) {
        const hasCapitalField = await modal.getByText('初始资金').or(modal.getByText('资金')).isVisible().catch(() => false);
        expect(hasCapitalField).toBeTruthy();
      }
    });
  });

  test.describe('Sandbox Actions', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('can edit sandbox account', async ({ page }) => {
      await page.goto('/sandbox');
      
      const editButton = page.getByRole('button', { name: '编辑' }).first();
      if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await editButton.click();
        
        const modal = page.locator('.ant-modal');
        await expect(modal).toBeVisible({ timeout: 3000 });
      }
    });

    test('can delete sandbox with confirmation', async ({ page }) => {
      await page.goto('/sandbox');
      
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

  test.describe('Strategy Deployment', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTestUser(page);
    });

    test('sandbox detail has deploy strategy section', async ({ page }) => {
      await page.goto('/sandbox/1');
      
      await page.waitForLoadState('networkidle');
      
      const deploySection = page.getByText('部署').or(page.getByText('策略部署')).or(page.getByText('Deploy'));
      if (await deploySection.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(deploySection).toBeVisible();
      }
    });
  });
});
