import { test, expect } from '@playwright/test';

test.describe('网站简化诊断', () => {
  test('检查控制台错误和网络请求', async ({ page }) => {
    const consoleErrors: string[] = [];
    const networkErrors: string[] = [];
    const apiCalls: string[] = [];
    
    // 监听控制台消息
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(`[${msg.type()}] ${msg.text()}`);
      }
      if (msg.type() === 'warning') {
        console.log(`[WARN] ${msg.text()}`);
      }
    });
    
    // 监听网络请求
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiCalls.push(`${request.method()} ${request.url()}`);
      }
    });
    
    page.on('response', response => {
      if (!response.ok() && response.status() >= 400) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    // 访问首页并等待加载完成
    await page.goto('/', { waitUntil: 'networkidle' });
    
    // 等待一些时间让所有异步操作完成
    await page.waitForTimeout(3000);
    
    // 输出诊断信息
    console.log('\n=== 诊断结果 ===');
    console.log(`控制台错误数量: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      console.log('控制台错误:');
      consoleErrors.forEach(error => console.log(`  - ${error}`));
    }
    
    console.log(`网络错误数量: ${networkErrors.length}`);
    if (networkErrors.length > 0) {
      console.log('网络错误:');
      networkErrors.forEach(error => console.log(`  - ${error}`));
    }
    
    console.log(`API调用数量: ${apiCalls.length}`);
    if (apiCalls.length > 0) {
      console.log('API调用:');
      apiCalls.forEach(call => console.log(`  - ${call}`));
    }
    
    // 检查页面基本元素
    const title = await page.title();
    console.log(`页面标题: ${title}`);
    
    const hasHeader = await page.locator('header').count() > 0;
    console.log(`头部存在: ${hasHeader}`);
    
    const hasMainContent = await page.locator('main').count() > 0;
    console.log(`主内容存在: ${hasMainContent}`);
    
    // 检查数据卡片
    const dataCards = await page.locator('[class*="grid"] [class*="card"]').count();
    console.log(`数据卡片数量: ${dataCards}`);
    
    // 截图保存
    await page.screenshot({ path: 'tests/screenshots/diagnosis.png', fullPage: true });
    console.log('诊断截图已保存到 tests/screenshots/diagnosis.png');
    
    // 基本断言 - 页面应该能正常加载
    expect(title).toContain('GEO Monitor');
  });
});
