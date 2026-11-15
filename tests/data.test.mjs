import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'
import ts from 'typescript'
const source=await fs.readFile('src/data.ts','utf8')
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText
const file=new URL('./.compiled-data.mjs',import.meta.url)
await fs.writeFile(file,compiled)
const {schemas,loadSiteData,DataError}=await import(file.href)
const embedded={}
async function files(dir){let result=[];for(const e of await fs.readdir(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory())result.push(...await files(p));else result.push(p)}return result}
for(const f of await files('public/data'))if(f.endsWith('.json')&&!f.includes('/raw/'))embedded[path.relative('public/data',f)]=JSON.parse(await fs.readFile(f,'utf8'))
const site='connecting-ridge-001/'
const actual=()=>structuredClone(embedded)
test('all shipped real JSON files satisfy their schemas',()=>{for(const name of ['sites','provenance','compare','validation'])assert.equal(schemas[name].safeParse(embedded[name+'.json']).success,true,name);for(const name of ['horizon','tracks','intervals','fragility'])assert.equal(schemas[name].safeParse(embedded[site+name+'.json']).success,true,name)})
test('typed loader uses the standalone data route and reports the real provenance',async()=>{global.window={__LUNA_DATA__:actual()};const data=await loadSiteData();assert.equal(data.synthetic,false);assert.equal(data.horizon.az_deg.length,2880);assert.equal(data.tracks.t_utc.length,337);assert.equal(data.intervals.totals.sun.min_h,null);assert.equal(data.compare.dominance.length,0)})
test('missing files produce typed errors rather than fallback numbers',async()=>{const data=actual();delete data[site+'tracks.json'];global.window={__LUNA_DATA__:data};await assert.rejects(loadSiteData(),e=>e instanceof DataError&&e.code==='MISSING')})
test('malformed/misaligned tracks are rejected',async()=>{const data=actual();data[site+'tracks.json'].earth.el_deg.pop();global.window={__LUNA_DATA__:data};await assert.rejects(loadSiteData(),e=>e.code==='MALFORMED')})
test('out-of-range disk fractions are rejected',()=>{const t=structuredClone(embedded[site+'tracks.json']);t.sun.disk_frac[0]=1.1;assert.equal(schemas.tracks.safeParse(t).success,false)})
test('any synthetic provenance forces the persistent banner flag',async()=>{const data=actual();data[site+'fragility.json'].provenance.is_synthetic=true;global.window={__LUNA_DATA__:data};assert.equal((await loadSiteData()).synthetic,true)})
test('the hero disagreement is a computed difference, not a fabricated visible state',()=>{const t=embedded[site+'tracks.json'];const i=t.disagreement_index;assert.notEqual(t.geometric_visible_earth[i],t.earth.disk_frac[i]>1e-6)})
test('all unknown continuous durations remain null',()=>{const intervals=embedded[site+'intervals.json'];for(const b of ['sun','earth']){assert.equal(intervals.totals[b].min_h,null);assert.equal(intervals.totals[b].max_h,null);assert.equal(intervals.longest_outage[b].min_h,null)}})
test('source checksum and observer settings survive export',()=>{const p=embedded['provenance.json'];assert.equal(p.datasets[0].checksum,'82030dcbdd7c4bb0c7d858e9b4b293b9f2cda5a543ba31ec0f42784bd6beee5a');assert.equal(embedded[site+'horizon.json'].site.mast_height_m,2)})
process.on('exit',()=>{import('node:fs').then(fs=>fs.unlinkSync(file)).catch(()=>{})})
