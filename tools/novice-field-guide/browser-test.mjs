import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
const server=spawn(process.execPath,[path.join(dir,'server.mjs')],{env:{...process.env,PORT:'4318'},stdio:['ignore','pipe','pipe']});
let browser;
try{
 await once(server.stdout,'data');
 browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const errors=[],context=await browser.newContext({viewport:{width:1280,height:720}});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 await page.goto('http://127.0.0.1:4318');
 await page.locator('[data-place="board"]').click();await page.getByRole('button',{name:'關閉對話'}).click();
 for(const [id,choice] of [['inn','記下遠行的方向'],['training','留意引氣呼吸'],['creek','先觀察草葉']]){
  await page.locator('.map [data-place="'+id+'"]').click();await page.getByRole('button',{name:choice,exact:true}).click();
 }
 assert.equal(await page.locator('.entry').count(),3);assert.equal(await page.locator('#lore').isVisible(),true);
 await page.reload();assert.equal(await page.locator('.entry').count(),3);
 await page.locator('.map [data-place="training"]').click();await page.getByRole('button',{name:'記下身法的提示',exact:true}).click();
 assert.equal(await page.locator('.entry').count(),3);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await page.screenshot({path:path.join(dir,'previews/desktop-1280x720.png')});
 await page.locator('.map [data-place="board"]').click();assert.match(await page.locator('#options').innerText(),/記下身法/);
 await page.getByRole('button',{name:'關閉對話'}).click();
 const before=await page.evaluate(()=>JSON.parse(localStorage.getItem('qingxi-c-field-guide-v1')).player.x);await page.locator('#map').focus();await page.keyboard.press('ArrowRight');
 const after=await page.evaluate(()=>JSON.parse(localStorage.getItem('qingxi-c-field-guide-v1')).player.x);assert.ok(after>before);
 const mobile=await browser.newContext({viewport:{width:844,height:390},isMobile:true,hasTouch:true,deviceScaleFactor:1});const touch=await mobile.newPage();
 await touch.goto('http://127.0.0.1:4318');await touch.locator('.map [data-place="creek"]').tap();await touch.getByRole('button',{name:'記下安全的淺灘',exact:true}).tap();
 assert.equal(await touch.locator('.entry').count(),1);assert.equal(await touch.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await touch.screenshot({path:path.join(dir,'previews/mobile-844x390.png')});
 await touch.locator('.map [data-place="inn"]').tap();await touch.screenshot({path:path.join(dir,'previews/mobile-dialog.png')});await mobile.close();
 await page.evaluate(()=>navigator.serviceWorker.ready);await page.reload();await page.waitForFunction(()=>navigator.serviceWorker.controller!==null);
 await context.setOffline(true);await page.reload();assert.equal(await page.locator('.entry').count(),3);await page.locator('.map [data-place="creek"]').click();await page.getByRole('button',{name:'記下安全的淺灘',exact:true}).click();
 await context.setOffline(false);assert.deepEqual(errors,[]);
 await context.close();
 await writeFile(path.join(dir,'previews/browser-report.json'),JSON.stringify({pass:true,desktop:'1280x720',touch:'844x390 emulated Chrome, not physical phone',checks:['three events in arbitrary order','revisit updates without duplicates','reload restores','board summary','keyboard movement','touch choice','no horizontal overflow','offline reload and interaction'],errors},null,2));
 console.log('GUIDE_BROWSER_PASS');
}finally{await browser?.close();server.kill();}
