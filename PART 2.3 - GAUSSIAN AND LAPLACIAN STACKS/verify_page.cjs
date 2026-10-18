// End-to-end local browser checks using the bundled Playwright runtime.
const { chromium } = require(process.argv[2] || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true,
  });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    fs.mkdirSync(path.join(__dirname, 'qa'), { recursive: true });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(pathToFileURL(path.join(__dirname, 'index.html')).href);
    await page.locator('img').evaluateAll(images => Promise.all(images.map(image => {
      image.loading = 'eager'; return image.decode();
    })));
    const images = await page.locator('img').count();
    if (images !== 60) throw new Error(`Expected 60 images, got ${images}`);
    if (await page.locator('.figure-grid img').count() !== 12) throw new Error('Twelve figure panels required');
    if (await page.locator('.six-grid').count() !== 7) throw new Error('Six image stacks and one mask stack required');
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => window.scrollTo(0, 0));
      if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) throw new Error(`Overflow at ${width}px`);
      await page.screenshot({ path: path.join(__dirname, `qa/${width === 1440 ? 'desktop' : 'mobile'}-top.png`) });
      if (width === 1440) {
        await page.locator('.figure-grid').screenshot({ path: path.join(__dirname, 'qa/twelve-panels.png') });
        await page.locator('.six-grid').first().screenshot({ path: path.join(__dirname, 'qa/gaussian-levels.png') });
      }
    }
    const links = await page.locator('a[href]').evaluateAll(anchors => anchors.map(a => a.getAttribute('href')));
    for (const href of links.filter(href => !href.startsWith('#') && !href.startsWith('https://'))) {
      if (!fs.existsSync(path.resolve(__dirname, decodeURIComponent(href)))) throw new Error(`Missing linked file: ${href}`);
    }
    for (const href of links.filter(href => href.startsWith('#'))) {
      if (await page.locator(href).count() !== 1) throw new Error(`Missing anchor: ${href}`);
    }
    if (errors.length) throw new Error(errors.join('\n'));
    await page.goto(pathToFileURL(path.join(__dirname, '../index.html')).href);
    await page.getByRole('link', { name: /Part 2.3/ }).click();
    if (!(await page.title()).includes('Gaussian and Laplacian Stacks')) throw new Error('Landing link failed');
    console.log(JSON.stringify({ images, figurePanels: 12, stackRows: 7, links: links.length,
      widths: [1440, 390], pageErrors: errors, landingLink: 'OK' }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
