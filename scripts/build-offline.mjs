import fs from 'node:fs/promises'
import path from 'node:path'
import crypto from 'node:crypto'
const dist=path.resolve('dist')
async function files(dir){let result=[];for(const entry of await fs.readdir(dir,{withFileTypes:true})){const p=path.join(dir,entry.name);if(entry.isDirectory())result.push(...await files(p));else result.push(p)}return result}
const dataFiles=(await files(path.join(dist,'data'))).filter(f=>f.endsWith('.json')&&!f.includes('/raw/'))
const data={};for(const file of dataFiles)data[path.relative(path.join(dist,'data'),file).replaceAll(path.sep,'/')]=JSON.parse(await fs.readFile(file,'utf8'))
const html=await fs.readFile(path.join(dist,'index.html'),'utf8')
const jsPath=html.match(/<script type="module"[^>]*src="([^"]+)"[^>]*><\/script>/)?.[1]
const cssPath=html.match(/<link rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/)?.[1]
if(!jsPath||!cssPath)throw Error('Expected a single Vite entry and stylesheet')
const js=await fs.readFile(path.join(dist,jsPath),'utf8'),css=await fs.readFile(path.join(dist,cssPath),'utf8')
const injected=JSON.stringify(data).replaceAll('<','\\u003c')
const standalone=html.replace(/<script type="module"[^>]*src="[^"]+"[^>]*><\/script>/,()=>`<script>window.__LUNA_DATA__=${injected};<\/script><script type="module">${js.replaceAll('</script','<\\/script')}<\/script>`).replace(/<link rel="stylesheet"[^>]*href="[^"]+"[^>]*>/,()=>`<style>${css}</style>`)
if (/<script[^>]+src=["'][^"']*assets\//i.test(standalone)) throw Error('Offline edition still references an external bundle')
await fs.writeFile(path.join(dist,'offline.html'),standalone)
const paths=(await files(dist)).filter(p=>!p.endsWith('.map')&&!p.endsWith('sw.js')).map(p=>'./'+path.relative(dist,p).replaceAll(path.sep,'/'))
const key=crypto.createHash('sha256').update(js+css+injected+standalone).digest('hex').slice(0,12)
await fs.writeFile(path.join(dist,'sw.js'),`const CACHE='luna-${key}';const FILES=${JSON.stringify(['./',...paths])};self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting())));self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('luna-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));self.addEventListener('fetch',e=>{if(e.request.method!=='GET'||new URL(e.request.url).origin!==self.location.origin)return;e.respondWith(fetch(e.request).then(r=>{if(r.ok){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy))}return r}).catch(()=>caches.match(e.request).then(r=>r||(e.request.mode==='navigate'?caches.match('./index.html'):Response.error()))))});`)
console.log('Built self-contained dist/offline.html and offline service worker. Data files:',dataFiles.length)
