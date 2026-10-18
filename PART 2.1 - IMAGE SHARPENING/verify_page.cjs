// End-to-end local webpage checks using the existing bundled Playwright.
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
      image.loading = 'eager';
      return image.decode();
    })));
    const images = await page.locator('img').count();
    if (images !== 34) throw new Error(`Expected 34 images, got ${images}`);
    if ((await page.locator('body').innerText()).includes('Visual review pending')) throw new Error('Missing visual observations');
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => window.scrollTo(0, 0));
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (overflow) throw new Error(`Page overflows at ${width}px`);
      await page.screenshot({ path: path.join(__dirname, `qa/${width === 1440 ? 'desktop' : 'mobile'}-top.png`) });
      if (width === 1440) {
        await page.locator('#restore').screenshot({ path: path.join(__dirname, 'qa/restoration.png') });
        await page.locator('#examples .four-grid').first().screenshot({ path: path.join(__dirname, 'qa/taj-pipeline.png') });
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
    await page.getByRole('link', { name: /Part 2.1/ }).click();
    if (!(await page.title()).includes('Image Sharpening')) throw new Error('Landing link failed');
    console.log(JSON.stringify({ images, links: links.length, widths: [1440, 390], pageErrors: errors, landingLink: 'OK' }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
