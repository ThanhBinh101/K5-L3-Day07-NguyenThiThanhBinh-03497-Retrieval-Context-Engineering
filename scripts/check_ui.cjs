const fs=require('fs');const path=require('path');
let pw;try{pw=require('playwright');}catch{pw=require(process.env.PLAYWRIGHT_MODULE||'/Users/eroheta/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');}
const assert=require('assert');
(async()=>{
 const browser=await pw.chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8707');
 for(let i=0;i<90;i++){const s=await (await page.request.get('http://127.0.0.1:8707/api/status')).json();if(s.error)throw new Error(s.error);if(s.ready)break;await page.waitForTimeout(1000);if(i===89)throw new Error('Index not ready');}
 await page.screenshot({path:'results/private/ui-desktop-empty.png',fullPage:true});
 async function alpha(v){await page.locator('#alpha').evaluate((el,v)=>{el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));},v);}
 await alpha('0');assert((await page.locator('#alpha-description').textContent()).includes('100% BM25'));
 await alpha('.1');const desc=await page.locator('#alpha-description').textContent();assert(desc.includes('90% BM25')&&desc.includes('10% dense'));
 await alpha('1');assert((await page.locator('#alpha-description').textContent()).includes('100% dense'));
 await alpha('.5');await page.locator('#query').fill('trần nhà');await page.locator('#search-button').click();await page.locator('#results .result-card').first().waitFor();
 assert((await page.locator('#results').textContent()).includes('天井'));
 await page.screenshot({path:'results/private/ui-desktop-search.png',fullPage:true});
 await page.locator('#results [data-page]').first().click();await page.locator('#page-image').evaluate(img=>img.complete&&img.naturalWidth?null:new Promise(r=>img.onload=r));assert(await page.locator('#page-dialog').isVisible());await page.locator('#close-dialog').click();
 await page.locator('#sweep-button').click();await page.locator('#sweep-results tbody tr').last().waitFor();assert.equal(await page.locator('#sweep-results tbody tr').count(),11);await page.locator('[data-alpha="0.2"]').click();assert((await page.locator('#alpha-value').textContent()).includes('0.2'));
 await alpha('.5');await page.locator('#query').fill('免許 đọc thế nào và nghĩa là gì?');await page.locator('#ask-button').click();await page.waitForFunction(()=>document.querySelector('#ask-button').disabled===false,{timeout:120000});assert((await page.locator('#answer').textContent()).includes('めんきょ'));assert((await page.locator('#answer').textContent()).includes('giấy phép'));
 await page.locator('[data-tab="draw"]').click();
 const data=JSON.parse(fs.readFileSync('data/private/templates.json','utf8'));const ref=data.characters.find(x=>x.kanji==='井');const box=await page.locator('#canvas').boundingBox();
 for(const stroke of ref.strokes){for(let i=0;i<stroke.length;i++){const [x,y]=stroke[i];await page.mouse.move(box.x+x/256*box.width,box.y+y/256*box.height);if(i===0)await page.mouse.down();}await page.mouse.up();}
 await page.locator('#recognize').click();await page.locator('[data-candidate="0"]').waitFor();assert.equal((await page.locator('[data-candidate="0"]').textContent()).trim(),'井');assert(await page.locator('#kanji-detail img').count());await page.screenshot({path:'results/private/ui-handwriting.png',fullPage:true});
 await page.locator('[data-tab="search"]').click();await page.setViewportSize({width:390,height:900});await page.screenshot({path:'results/private/ui-mobile.png',fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
 await page.locator('#corpus').selectOption('report');assert(await page.locator('#lesson').isDisabled());await page.locator('#query').fill('Graph 1-1-2 1993');await page.locator('#search-button').click();await page.locator('#results .result-card').first().waitFor();assert((await page.locator('#results').textContent()).includes('15'));
 const bad=await page.request.post('http://127.0.0.1:8707/api/search',{data:{query:'test',alpha:2}});assert.equal(bad.status(),400);
 const foreign=await page.request.post('http://127.0.0.1:8707/api/search',{headers:{Origin:'https://example.com'},data:{query:'test',alpha:0}});assert.equal(foreign.status(),403);
 const hidden=await page.request.get('http://127.0.0.1:8707/.env');assert.equal(hidden.status(),404);
 assert.deepEqual(errors,[]);
 fs.writeFileSync('results/ui_checks.json',JSON.stringify({passed:true,checks:['alpha endpoints and 0.1 description','one search input','Kanji search and vocabulary','source page dialog','11 alpha levels and row selection','real API answer with citation','synthetic KanjiVG handwriting top-1 and illustration','390px viewport no horizontal overflow','report search and lesson control','invalid alpha rejection','foreign Origin rejection','secret route inaccessible','no browser errors'],handwriting_limit:'Synthetic template check, not a real-user handwriting benchmark.',screenshots:['results/private/ui-desktop-empty.png','results/private/ui-desktop-search.png','results/private/ui-handwriting.png','results/private/ui-mobile.png'],timestamp:new Date().toISOString()},null,2));
 await browser.close();console.log('UI checks passed');
})().catch(e=>{console.error(e);process.exit(1)});
