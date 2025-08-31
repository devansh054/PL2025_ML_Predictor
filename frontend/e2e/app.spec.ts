import { test, expect } from '@playwright/test';

test.describe('Premier League Predictor E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('has title', async ({ page }) => {
    await expect(page).toHaveTitle(/Premier League Predictor/);
  });

  test('navigation works correctly', async ({ page }) => {
    // Test Stats navigation
    await page.click('text=Stats');
    await expect(page.locator('text=Model Performance')).toBeVisible();
    
    // Test Teams navigation
    await page.click('text=Teams');
    await expect(page.locator('text=Premier League Teams')).toBeVisible();
    
    // Test About navigation
    await page.click('text=About');
    await expect(page.locator('text=About Premier League Predictor')).toBeVisible();
    
    // Test back to Predictions
    await page.click('text=Predictions');
    await expect(page.locator('text=Home Team')).toBeVisible();
  });

  test('prediction flow works', async ({ page }) => {
    // Select home team
    await page.selectOption('select[data-testid="home-team-select"]', 'Arsenal');
    
    // Select away team
    await page.selectOption('select[data-testid="away-team-select"]', 'Chelsea');
    
    // Click predict button
    await page.click('text=Predict Match');
    
    // Wait for prediction result
    await expect(page.locator('[data-testid="prediction-result"]')).toBeVisible({ timeout: 10000 });
  });

  test('responsive design works on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check if navigation is still accessible
    await expect(page.locator('text=PL Predictor')).toBeVisible();
    await expect(page.locator('text=Predictions')).toBeVisible();
    
    // Check if team selection is visible
    await expect(page.locator('text=Home Team')).toBeVisible();
    await expect(page.locator('text=Away Team')).toBeVisible();
  });

  test('3D background loads without errors', async ({ page }) => {
    // Check if canvas element is present
    await expect(page.locator('canvas')).toBeVisible();
    
    // Check for any console errors related to WebGL
    const logs = [];
    page.on('console', msg => logs.push(msg.text()));
    
    await page.waitForTimeout(2000); // Wait for 3D scene to load
    
    const webglErrors = logs.filter(log => 
      log.includes('WebGL') && log.includes('error')
    );
    expect(webglErrors).toHaveLength(0);
  });

  test('performance metrics', async ({ page }) => {
    // Measure page load performance
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
    
    // Check for layout shifts
    const cls = await page.evaluate(() => {
      return new Promise((resolve) => {
        let clsValue = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          }
          resolve(clsValue);
        }).observe({ type: 'layout-shift', buffered: true });
        
        setTimeout(() => resolve(clsValue), 3000);
      });
    });
    
    // CLS should be less than 0.1 (good score)
    expect(cls).toBeLessThan(0.1);
  });
});
