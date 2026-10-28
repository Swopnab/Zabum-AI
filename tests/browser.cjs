// Fictional local fixtures only. See docs/BROWSER_CHECKS.md before running.
const {chromium}=require(process.env.PLAYWRIGHT_PATH || 'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const out=process.env.REVIEW_OUTPUT||path.join(__dirname,'screenshots');
const reports=[];
async function check(name,run){if(process.env.CHECK_FILTER&&!name.match(process.env.CHECK_FILTER))return;await run();reports.push({name,result:'passed'});console.log('PASS',name);}
async function shot(page,name){await fs.mkdir(out,{recursive:true});await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});}
async function noOverflow(page){
 const state=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,outside:[...document.querySelectorAll('body *')].map(e=>({tag:e.tagName,cls:String(e.className),right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).filter(e=>e.right>innerWidth+1&&e.width>0).slice(0,8)}));
 assert.ok(state.scroll<=state.width+1,`page must fit viewport: ${JSON.stringify(state)}`);
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 const ctx=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const errors=[];ctx.on('page',p=>p.on('pageerror',e=>errors.push(e.message)));
 const z=await ctx.newPage();
 await check('Zabum browser upload, evidence, source inspection and reload',async()=>{
  assert.equal((await (await ctx.request.get('http://127.0.0.1:5091/api/status')).json()).review_fixture,true,'Refusing to clear a non-fixture Zabum server');
  for(const [key,url] of [['documents','documents'],['memories','memories'],['conversations','conversations']]) {const data=await(await ctx.request.get('http://127.0.0.1:5091/api/'+url)).json();for(const item of data[key])await ctx.request.delete('http://127.0.0.1:5091/api/'+url+'/'+item.id);}
  await ctx.request.put('http://127.0.0.1:5091/api/preferences',{data:{memory_enabled:true}});
  await z.goto('http://127.0.0.1:5091/app');
  await z.locator('#chatFileInput').setInputFiles({name:'fictional-mission.txt',mimeType:'text/plain',buffer:Buffer.from('Fictional Venus mission fuel budget is 37 units. This is synthetic test data.')});
  await z.locator('#documentReadiness').filter({hasText:'ready to search'}).waitFor();
  await z.locator('#chatInput').fill('Venus fuel budget');await z.locator('#sendBtn').click();
  await z.getByText('Document passages · quoted evidence',{exact:true}).waitFor();
  await z.locator('.sources-accordion summary').last().click();
  await z.locator('.source-link').last().click();
  await z.locator('.selected-passage').waitFor();
  await z.locator('[data-modal="chunkModal"]').first().click();
  await z.reload();await z.locator('#conversationList .conv-item').first().click();
  await z.getByText('Document passages · quoted evidence',{exact:true}).waitFor();
  await noOverflow(z);await shot(z,'zabum-desktop');
 });
 await check('Zabum memory approval and persistent disable through UI',async()=>{
  await z.locator('#answerMode').selectOption('general');await z.locator('#chatInput').fill('Remember that I prefer Python');await z.locator('#sendBtn').click();
  await z.getByRole('button',{name:'Approve',exact:true}).waitFor();
  assert.equal((await (await ctx.request.get('http://127.0.0.1:5091/api/memories')).json()).count,0);
  await z.getByRole('button',{name:'Approve',exact:true}).click();
  await z.locator('#memorySuggestions').filter({hasText:'Remember this?'}).waitFor({state:'hidden'});
  await z.locator('#memoryEnabled').uncheck();
  await z.waitForFunction(()=>!document.getElementById('memoryEnabled').disabled);
  await z.reload();await z.waitForFunction(()=>!document.getElementById('memoryEnabled').checked);
 });
 await check('Zabum failed memory saves keep the dialog open',async()=>{
  await z.setViewportSize({width:1440,height:1000});await z.locator('#tabMemoryBtn').click();await z.locator('#openAddMemoryBtn').click();
  await z.locator('#memoryContentInput').fill('Fictional failed-save test');
  await z.route('**/api/memories',route=>route.request().method()==='POST'?route.fulfill({status:500,contentType:'application/json',body:'{"error":"synthetic failure"}'}):route.continue());
  await z.locator('#saveMemoryBtn').click();await z.getByRole('alert').filter({hasText:'Failed to save memory'}).waitFor();
  assert.ok(await z.getByRole('dialog').isVisible());await z.keyboard.press('Escape');await z.unroute('**/api/memories');
 });
 for(const [name,url] of [['Zabum', 'http://127.0.0.1:5091/app']]) {
  await check(`${name} desktop, tablet and phone layouts`,async()=>{
   // Fresh contexts avoid leaking the timer's emulated clock or focus between visual cases.
   for(const [w,h] of [[390,844],[768,1024],[1440,1000]]){
    const layout=await browser.newContext({viewport:{width:w,height:h},reducedMotion:'reduce'});layout.on('page',p=>p.on('pageerror',e=>errors.push(e.message)));const page=await layout.newPage();
    await page.goto(url);await page.waitForLoadState('networkidle');await noOverflow(page);await page.evaluate(()=>document.activeElement?.blur());await shot(page,`${name.toLowerCase()}-${w}`);await layout.close();
   }
  });
 }
 await check('Zabum keyboard navigation and mobile chat controls',async()=>{
  await z.setViewportSize({width:390,height:844});await z.goto('http://127.0.0.1:5091/app');
  assert.ok(await z.locator('#sidebar').evaluate(el=>el.inert));
  await z.locator('#toggleSidebarBtn').click();assert.equal(await z.locator('#sidebar').evaluate(el=>el.inert),false);
  await z.locator('#tabMemoryBtn').click();await z.locator('#openAddMemoryBtn').focus();await z.keyboard.press('Enter');
  await z.getByRole('dialog').waitFor();await z.keyboard.press('Tab');assert.ok(await z.getByRole('dialog').evaluate(el=>el.contains(document.activeElement)));
  await z.keyboard.press('Escape');assert.equal(await z.getByRole('dialog').count(),0);
 });
 assert.deepEqual(errors,[],`Browser errors: ${errors.join('; ')}`);
 await fs.writeFile(path.join(out,'results.json'),JSON.stringify({fixture:'Fictional temporary documents; mock provider; Chromium viewport emulation',checks:reports,unhandledPageErrors:errors},null,2));
 await browser.close();console.log(JSON.stringify(reports));
})().catch(e=>{console.error(e);process.exit(1);});
