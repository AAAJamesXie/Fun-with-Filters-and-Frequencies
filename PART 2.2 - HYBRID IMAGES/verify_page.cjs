// Browser verification with the existing bundled Playwright runtime.
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
    if (images !== 40) throw new Error(`Expected 40 images, got ${images}`);
    if (await page.locator('.fft-grid img').count() !== 5) throw new Error('Five Fourier views are required');
    const text = await page.locator('body').innerText();
    for (const marker of ['Derek + Nutmeg', 'Obama + Trump', 'Chelsea + Owl', 'Mandatory extension']) {
      if (!text.includes(marker)) throw new Error(`Missing section: ${marker}`);
    }
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => window.scrollTo(0, 0));
      if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) {
        throw new Error(`Page overflows at ${width}px`);
      }
      await page.screenshot({ path: path.join(__dirname, `qa/${width === 1440 ? 'desktop' : 'mobile'}-top.png`) });
      if (width === 1440) {
        await page.locator('.fft-grid').screenshot({ path: path.join(__dirname, 'qa/frequency.png') });
        await page.locator('#color .four-grid').first().screenshot({ path: path.join(__dirname, 'qa/color-variants.png') });
        await page.locator('#gallery .triple').first().screenshot({ path: path.join(__dirname, 'qa/first-hybrid.png') });
      }
    }
    const links = await page.locator('a[href]').evaluateAll(anchors => anchors.map(a => a.getAttribute('href')));
    for (const href of links.filter(href => !href.startsWith('#') && !href.startsWith('https://'))) {
      if (!fs.existsSync(path.resolve(__dirname, decodeURIComponent(href)))) throw new Error(`Missing file: ${href}`);
    }
    for (const href of links.filter(href => href.startsWith('#'))) {
      if (await page.locator(href).count() !== 1) throw new Error(`Missing anchor: ${href}`);
    }
    const farWidths = await page.locator('.far-grid img').evaluateAll(images => images.map(image => ({ rendered: image.getBoundingClientRect().width, native: image.naturalWidth })));
    if (farWidths.some(value => value.rendered > value.native + 1)) throw new Error('Small views were enlarged');
    if (errors.length) throw new Error(errors.join('\n'));
    await page.goto(pathToFileURL(path.join(__dirname, '../index.html')).href);
    await page.getByRole('link', { name: /Part 2.2/ }).click();
    if (!(await page.title()).includes('Hybrid Images')) throw new Error('Landing link failed');
    console.log(JSON.stringify({ images, fftImages: 5, links: links.length, widths: [1440, 390],
      farWidths, pageErrors: errors, landingLink: 'OK' }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
