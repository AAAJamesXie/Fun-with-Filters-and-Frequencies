// Local browser verification using the already bundled Playwright runtime.
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
    if (images !== 13) throw new Error(`Expected 13 images, got ${images}`);
    await page.screenshot({ path: path.join(__dirname, 'qa/desktop.png'), fullPage: true });
    await page.locator('#results').screenshot({ path: path.join(__dirname, 'qa/filter-results.png') });
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 900 });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (overflow) throw new Error(`Page overflows at ${width}px`);
      if (width === 390) await page.screenshot({ path: path.join(__dirname, 'qa/mobile.png'), fullPage: true });
    }
    const links = await page.locator('a[href]').evaluateAll(anchors => anchors.map(a => a.getAttribute('href')));
    for (const href of links.filter(href => !href.startsWith('#'))) {
      if (!fs.existsSync(path.resolve(__dirname, decodeURIComponent(href)))) {
        throw new Error(`Missing linked file: ${href}`);
      }
    }
    if (errors.length) throw new Error(errors.join('\n'));
    await page.goto(pathToFileURL(path.join(__dirname, '../index.html')).href);
    await page.locator('.solid-link').click();
    if (!(await page.title()).includes('Convolutions from Scratch')) throw new Error('Landing link failed');
    console.log(JSON.stringify({ images, links: links.length, desktopWidth: 1440,
      mobileWidth: 390, pageErrors: errors, landingLink: 'OK' }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
