import { test, expect } from '@playwright/test';

test.describe('GEO Monitor 网站诊断', () => {
  test('检查页面基本加载和渲染', async ({ page }) => {
    // 监听控制台错误
    const consoleErrors: string[] = [];
    const networkErrors: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    page.on('response', response => {
      if (!response.ok() && response.status() >= 400) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    // 访问首页
    await page.goto('/', { waitUntil: 'networkidle' });
    
    // 检查页面标题
    await expect(page).toHaveTitle(/GEO Monitor/);
    
    // 检查主要元素是否存在
    await expect(page.locator('text=GEO Monitor')).toBeVisible();
    
    // 检查是否有控制台错误
    if (consoleErrors.length > 0) {
      console.log('控制台错误:', consoleErrors);
    }
    
    // 检查是否有网络错误
    if (networkErrors.length > 0) {
      console.log('网络错误:', networkErrors);
    }
    
    // 截图保存当前状态
    await page.screenshot({ path: 'tests/screenshots/homepage.png', fullPage: true });
  });

  test('检查CSS样式加载', async ({ page }) => {
    await page.goto('/');
    
    // 检查Tailwind CSS是否正确加载
    const bodyStyles = await page.locator('body').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
        fontFamily: styles.fontFamily,
        color: styles.color
      };
    });
    
    console.log('Body样式:', bodyStyles);
    
    // 检查关键组件是否有正确的样式
    const headerElement = page.locator('header');
    if (await headerElement.count() > 0) {
      const headerStyles = await headerElement.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          backgroundColor: styles.backgroundColor,
          borderBottom: styles.borderBottom,
          position: styles.position
        };
      });
      console.log('Header样式:', headerStyles);
    }
  });

  test('检查数据显示和组件渲染', async ({ page }) => {
    await page.goto('/');
    
    // 等待页面完全加载
    await page.waitForTimeout(2000);
    
    // 检查关键数据卡片是否显示
    const dataCards = [
      '总任务数',
      '运行中任务', 
      '平均准确率',
      '待处理告警'
    ];
    
    for (const cardText of dataCards) {
      const card = page.locator(`text=${cardText}`);
      const isVisible = await card.isVisible();
      console.log(`${cardText} 卡片可见性:`, isVisible);
      
      if (isVisible) {
        // 检查数据是否显示
        const cardContainer = card.locator('..').locator('..');
        const hasData = await cardContainer.locator('text=/\\d+/').count() > 0;
        console.log(`${cardText} 有数据:`, hasData);
      }
    }
    
    // 检查图表区域
    const chartArea = page.locator('text=声量占有率趋势');
    const chartVisible = await chartArea.isVisible();
    console.log('图表区域可见性:', chartVisible);
    
    // 检查任务列表
    const taskList = page.locator('text=最近任务');
    const taskListVisible = await taskList.isVisible();
    console.log('任务列表可见性:', taskListVisible);
  });

  test('检查交互功能', async ({ page }) => {
    await page.goto('/');
    
    // 检查刷新按钮
    const refreshButton = page.locator('button:has-text("刷新")');
    if (await refreshButton.count() > 0) {
      await refreshButton.click();
      console.log('刷新按钮可点击');
    }
    
    // 检查时间选择器
    const timeSelector = page.locator('select, [role="combobox"]').first();
    if (await timeSelector.count() > 0) {
      await timeSelector.click();
      console.log('时间选择器可点击');
    }
    
    // 检查侧边栏菜单（移动端）
    const menuButton = page.locator('button:has([data-testid="menu-icon"], svg)');
    if (await menuButton.count() > 0) {
      await menuButton.click();
      console.log('菜单按钮可点击');
    }
  });

  test('检查响应式设计', async ({ page }) => {
    // 桌面视图
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/');
    await page.screenshot({ path: 'tests/screenshots/desktop.png' });
    
    // 平板视图
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();
    await page.screenshot({ path: 'tests/screenshots/tablet.png' });
    
    // 移动端视图
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.screenshot({ path: 'tests/screenshots/mobile.png' });
    
    console.log('响应式截图已保存');
  });

  test('检查API调用和数据获取', async ({ page }) => {
    const apiCalls: string[] = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiCalls.push(request.url());
      }
    });
    
    await page.goto('/');
    await page.waitForTimeout(3000);
    
    console.log('API调用:', apiCalls);
    
    // 检查是否有失败的API调用
    const failedRequests: string[] = [];
    page.on('response', response => {
      if (response.url().includes('/api/') && !response.ok()) {
        failedRequests.push(`${response.status()} ${response.url()}`);
      }
    });
    
    if (failedRequests.length > 0) {
      console.log('失败的API请求:', failedRequests);
    }
  });
});
