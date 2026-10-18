// Real browser checks against generated local artifacts; no mock network.
const { chromium } = require(process.argv[2] || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
(async () => {
  const browser = await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e=>errors.push(e.message));
    fs.mkdirSync(path.join(__dirname,'qa'),{recursive:true});
    await page.goto(pathToFileURL(path.join(__dirname,'index.html')).href);
    await page.locator('img').evaluateAll(images=>Promise.all(images.map(im=>{im.loading='eager';return im.decode();})));
    const count = await page.locator('img').count();
    if(count!==61) throw new Error(`Expected 61 images, got ${count}`);
    if(await page.locator('.case').count()!==3) throw new Error('Three cases required');
    if(await page.locator('.color-study img').count()!==12) throw new Error('Four color modes per case required');
    if(await page.locator('.figure-grid img').count()!==12) throw new Error('Twelve contribution panels required');
    if(await page.locator('.six-grid img').count()!==6) throw new Error('Six mask levels required');
    for (const width of [1440,390]) {
      await page.setViewportSize({width,height:1000});
      for(const open of [false,true]) {
        await page.locator('details').evaluateAll((nodes,value)=>nodes.forEach(n=>n.open=value),open);
        if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth)) throw new Error(`Overflow: ${width}px, details=${open}`);
      }
      await page.locator('details').evaluateAll(nodes=>nodes.forEach(n=>n.open=false));
      await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:path.join(__dirname,`qa/${width===1440?'desktop':'mobile'}-top.png`)});
      if(width===1440) {
        await page.locator('#cat-owl .methods').screenshot({path:path.join(__dirname,'qa/cat-owl-methods.png')});
        await page.locator('#cat-owl .color-study').screenshot({path:path.join(__dirname,'qa/cat-owl-color.png')});
        await page.locator('.figure-grid').screenshot({path:path.join(__dirname,'qa/contributions.png')});
      }
    }
    const links = await page.locator('a[href]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
    for(const href of links) {
      if(href.startsWith('https://')) continue;
      if(href.startsWith('#')) {
        if(await page.locator(href).count()!==1) throw new Error(`Bad anchor ${href}`);
      } else if(!fs.existsSync(path.resolve(__dirname,decodeURIComponent(href)))) throw new Error(`Missing file ${href}`);
    }
    await page.goto(pathToFileURL(path.join(__dirname,'../index.html')).href);
    await page.getByRole('link',{name:/Part 2.4/}).click();
    if(!(await page.title()).includes('Multiresolution Blending')) throw new Error('Homepage entry failed');
    if(errors.length) throw new Error(errors.join('\n'));
    console.log(JSON.stringify({images:count,cases:3,colorVariants:12,processPanels:12,maskLevels:6,links:links.length,widths:[1440,390],detailsOpenAndClosed:'OK',homepageEntry:'OK',pageErrors:errors}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
