// Render screenshots of REAL local helper outputs, never simulated ChatGPT UI.
const {execFileSync} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '..');
const state = fs.mkdtempSync(path.join(os.tmpdir(), 'ccb-share-demo-'));
const run = (thread, intent, phase) => JSON.parse(execFileSync('python3', [path.join(root,'scripts/session.py'), '--state',state,'--thread',thread,'--intent',intent,'--phase',phase], {encoding:'utf8'}));
const first = [
 ['New conversation / 默认', run('demo-a','inherit','routine')],
 ['CCB · Analyze architecture / 方案分析', run('demo-a','enable','analysis')],
 ['Run tests / 运行测试', run('demo-a','inherit','routine')],
 ['Ask GPT this time / 本次指定 GPT', run('demo-a','require-gpt','routine')]
];
const second = [
 ['A · Handle locally once / 本次自己做', run('demo-a','local-once','decision')],
 ['B · New conversation / 新会话', run('demo-b','inherit','analysis')],
 ['A · Independent review / 独立复核', run('demo-a','inherit','review')],
 ['A · Exit CCB / 退出', run('demo-a','disable','routine')]
];
const escape = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
(async()=>{
 const browser = await chromium.launch({headless:true});
 try {
  for (const [name,title,subtitle,rows] of [
   ['01-selective-collaboration','ChatGPT when it helps.','重要分析按需协作 · 日常执行保持直接',first],
   ['02-session-isolation','One conversation. One switch.','跨轮继承 · 单次覆盖 · 会话隔离',second]]) {
   const page = await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
   await page.setContent(`<html><meta charset="utf-8"><style>body{margin:0;padding:64px;background:#101827;color:#eef3fb;font:24px -apple-system,BlinkMacSystemFont,sans-serif} .tag{color:#68ddc5;font-size:20px;letter-spacing:3px}h1{font-size:56px;margin:24px 0 12px}p{color:#acbdd2;margin:0 0 28px}.row{background:#1b2940;border:1px solid #34455e;border-radius:16px;padding:24px;margin:14px 0;display:flex;justify-content:space-between;align-items:center}.meta{font:18px monospace;color:#a9bbd1;margin-top:10px}.who{font-size:30px;color:#68ddc5}footer{font-size:18px;color:#a9bbd1;margin-top:28px;line-height:1.6}</style><div class="tag">CCB / LOCAL CLI DEMONSTRATION</div><h1>${title}</h1><p>${subtitle}</p>${rows.map(([label,r])=>`<div class="row"><div>${escape(label)}<div class="meta">enabled=${r.enabled} · phase=${r.phase} · dispatched=${r.dispatched}</div></div><div class="who">${r.participant==='chatgpt'?'ChatGPT':'Codex'}</div></div>`).join('')}<footer>Actual session.py outputs · Isolated fictional sessions · No GPT messages sent<br>真实本地执行结果；不是 ChatGPT 对话截图，也不是 Full 连通证明。</footer></html>`);
   await page.screenshot({path:path.join(root,'marketing',name+'.png'),fullPage:true});
   await page.close();
  }
 } finally { await browser.close(); fs.rmSync(state,{recursive:true}); }
 console.log('Two screenshots generated from actual isolated CLI runs. No personal runtime used.');
})().catch(e=>{console.error(e.message);process.exitCode=1});
