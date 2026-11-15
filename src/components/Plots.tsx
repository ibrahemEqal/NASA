import {useId,useState} from 'react'
import type {BodyName, SiteData} from '../data'
import {fmt,utc} from '../data'
import {tr,type Lang} from '../i18n'
const colors={sun:'var(--amber)',earth:'var(--earth)'}
export function state(frac:number){return frac<=0?'blocked':frac>=1?'visible':'partial'}
function line(points:[number,number][]){return points.map(([x,y],i)=>`${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ')}
export function HeroScene({data,index,terrain,lang,onEvidence}:{data:SiteData;index:number;terrain:boolean;lang:Lang;onEvidence:()=>void}){
 const id=useId().replace(/:/g,'');const h=data.horizon,t=data.tracks
 const ys=[...h.h_nominal_deg,t.sun.el_deg[index]+t.sun.radius_deg[index],t.earth.el_deg[index]-t.earth.radius_deg[index]]
 const min=Math.floor(Math.min(...ys)-.7),max=Math.ceil(Math.max(...ys)+.7),px=(a:number)=>38+a/360*600,py=(e:number)=>230-(e-min)/(max-min)*180
 const points=h.az_deg.filter((_,i)=>i%4===0).map(a=>{const i=h.az_deg.indexOf(a);return[px(a),py(terrain?h.h_nominal_deg[i]:t.smooth_horizon_deg)] as [number,number]})
 const path=line(points)
 return <div className="hero-plot" style={{direction:"ltr"}}><svg viewBox="0 0 680 300" role="img" aria-label={tr(lang,'skyQuestion')}>
 <defs><linearGradient id={id} x1="0" x2="0" y1="0" y2="1"><stop stopColor="#a6abb4" stopOpacity=".25"/><stop offset="1" stopColor="#5f6774" stopOpacity=".03"/></linearGradient><clipPath id={`${id}-sky`}><path d={`${path}L638 25L38 25Z`}/></clipPath><pattern id={`${id}h`} width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6L6 0" stroke="currentColor" opacity=".08"/></pattern></defs>
 {[0,1,2,3,4].map(i=>{const e=min+(max-min)*i/4;return <g key={i}><line x1="38" x2="638" y1={py(e)} y2={py(e)} className="svg-grid"/><text x="17" y={py(e)+3} className="svg-tick">{fmt(e,1)}°</text></g>})}
 {[0,90,180,270,360].map(a=><text key={a} x={px(a)} y="259" textAnchor="middle" className="svg-tick">{a}°</text>)}
 <path d={`${path}L638 239L38 239Z`} fill={`url(#${id})`}/><path d={`${path}L638 239L38 239Z`} fill={`url(#${id}h)`}/><path d={path} fill="none" className="terrain-stroke" strokeWidth="1.7" strokeDasharray={terrain?undefined:'5 5'}/>
 {(['sun','earth'] as BodyName[]).map(b=>{const body=t[b],x=px(body.az_deg[index]),y=py(body.el_deg[index]),fraction=terrain?body.disk_frac[index]:body.geometric_disk_frac[index];const rr=body.radius_deg[index]*180/(max-min);const rx=body.radius_deg[index]*600/360/Math.cos(body.el_deg[index]*Math.PI/180);return <g key={b} tabIndex={0} role="button" onClick={onEvidence} onKeyDown={e=>e.key==='Enter'&&onEvidence()} aria-label={`${tr(lang,b)} ${fmt(fraction*100,1)}%`}>
 <line x1={x} x2={x} y1={y+14} y2="242" stroke={colors[b]} opacity=".28" strokeDasharray="2 5"/>
 <ellipse cx={x} cy={y} rx={rx} ry={rr} fill={colors[b]} opacity=".16" stroke={colors[b]} strokeWidth=".6"/><ellipse cx={x} cy={y} rx={rx} ry={rr} fill={colors[b]} clipPath={`url(#${id}-sky)`}/>
 <circle cx={x} cy={y} r={rr+7} fill="none" stroke={colors[b]} opacity=".12"/>
 <text x={x+18} y={y-7} fill={colors[b]} className="svg-label">{b==='sun'?'SUN':'EARTH'}</text><text x={x+18} y={y+10} className="svg-tick">{tr(lang,state(fraction))}</text>
 <title>{tr(lang,b)} · {fmt(body.az_deg[index])}° / {fmt(body.el_deg[index])}° · {fmt(fraction*100,1)}%</title>
 </g>})}
 <text x="338" y="289" textAnchor="middle" className="svg-micro">AZIMUTH / LOCAL NORTH → CLOCKWISE</text>
 </svg></div>
}
export function SkyPlot({data,index,terrain,lang,onEvidence,highlight}:{data:SiteData;index:number;terrain:boolean;lang:Lang;onEvidence:()=>void;highlight?:number}){
 const h=data.horizon,t=data.tracks;const all=[...h.h_nominal_deg,...t.sun.el_deg,...t.earth.el_deg];const low=Math.floor(Math.min(...all)-2),high=Math.ceil(Math.max(...all)+2);const radial=(e:number)=>190*(high-e)/(high-low)
 const pos=(a:number,e:number):[number,number]=>[240+radial(e)*Math.sin(a*Math.PI/180),240-radial(e)*Math.cos(a*Math.PI/180)]
 const hp=h.az_deg.map((a,i)=>pos(a,terrain?h.h_nominal_deg[i]:t.smooth_horizon_deg));const horizonPath=line(hp)+'Z';const id=useId().replace(/:/g,'')
 return <svg className="sky-svg" viewBox="0 0 480 480" role="img" aria-label={`${tr(lang,'skyTitle')} ${data.site.name}`} style={{direction:"ltr"}}>
 <defs><mask id={id}><rect width="480" height="480" fill="white"/><path d={horizonPath} fill="black"/></mask><pattern id={`${id}-pattern`} width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(40)"><line x1="0" x2="0" y2="7" stroke="currentColor" strokeWidth="1" opacity=".11"/></pattern></defs>
 <circle cx="240" cy="240" r="190" fill="currentColor" opacity=".035" mask={`url(#${id})`}/><circle cx="240" cy="240" r="190" fill={`url(#${id}-pattern)`} mask={`url(#${id})`}/>
 {[.25,.5,.75,1].map(r=><g key={r}><circle cx="240" cy="240" r={190*r} fill="none" className="svg-grid"/><text x="245" y={240-190*r-4} className="svg-tick">{fmt(high-r*(high-low),1)}°</text></g>)}
 {[0,45,90,135,180,225,270,315].map(a=>{const p=pos(a,low);return <line key={a} x1="240" y1="240" x2={p[0]} y2={p[1]} className="svg-grid"/>})}
 <path d={horizonPath} fill="none" className="terrain-stroke" strokeWidth="1.5" strokeDasharray={terrain?undefined:'5 4'}/>
 {highlight!==undefined&&<path d={line([[240,240],pos(highlight,low)])} stroke="var(--amber)" strokeWidth="1.5" strokeDasharray="3 3"/>}
 {(['sun','earth'] as BodyName[]).map(b=>{const body=t[b];const track=body.az_deg.map((a,i)=>pos(a,body.el_deg[i]));const [x,y]=pos(body.az_deg[index],body.el_deg[index]);const rr=body.radius_deg[index]*190/(high-low);const tangential=radial(body.el_deg[index])*body.radius_deg[index]*Math.PI/180/Math.cos(body.el_deg[index]*Math.PI/180);const f=terrain?body.disk_frac[index]:body.geometric_disk_frac[index];const angle=body.az_deg[index];return <g key={b}>
 <path d={line(track)} fill="none" stroke={colors[b]} strokeWidth="1.6" opacity=".65" strokeDasharray={b==='earth'?'4 3':undefined}/>
 <ellipse cx={x} cy={y} rx={tangential} ry={rr} transform={`rotate(${angle} ${x} ${y})`} fill={colors[b]} opacity={f<=0?.35:1} stroke={colors[b]} strokeWidth="1"/>
 <circle cx={x} cy={y} r={rr+8} fill="transparent" stroke={colors[b]} strokeWidth=".7" opacity=".5" tabIndex={0} role="button" aria-label={`${tr(lang,b)} ${tr(lang,state(f))}`} onClick={onEvidence} onKeyDown={e=>e.key==='Enter'&&onEvidence()}/>
 <text x={x+rr+13} y={y+4} fill={colors[b]} className="svg-label">{b==='sun'?'SUN':'EARTH'}</text>
 <title>{utc(t.t_utc[index])} · {tr(lang,b)} · {fmt(body.az_deg[index])}° / {fmt(body.el_deg[index])}°</title>
 </g>})}
 <text x="240" y="28" textAnchor="middle" className="compass">N</text><text x="457" y="244" textAnchor="middle" className="compass">E</text><text x="240" y="464" textAnchor="middle" className="compass">S</text><text x="23" y="244" textAnchor="middle" className="compass">W</text><circle cx="240" cy="240" r="2" className="terrain-dot"/>
 </svg>
}
export function Timeline({data,index,range,onIndex,onRange,lang,terrain,threshold}:{data:SiteData;index:number;range:[number,number];onIndex:(i:number)=>void;onRange:(r:[number,number])=>void;lang:Lang;terrain:boolean;threshold:number}){
 const [lo,hi]=range;const [brush,setBrush]=useState<[number,number]|null>(null);const t=data.tracks;const x=(i:number)=>100+(i-lo)/Math.max(hi-lo,1)*850;const y=(v:number,row:number)=>74+row*112-v*54;const id=useId().replace(/:/g,'')
 return <svg className="timeline-svg" viewBox="0 0 1000 292" role="img" aria-label={tr(lang,'timelineTitle')} style={{direction:"ltr"}} onPointerDown={e=>{const b=e.currentTarget.getBoundingClientRect();const xx=(e.clientX-b.left)/b.width*1000;const i=Math.max(lo,Math.min(hi,Math.round(lo+(xx-100)/850*(hi-lo))));setBrush([i,i]);onIndex(i);e.currentTarget.setPointerCapture(e.pointerId)}} onPointerMove={e=>{if(!brush)return;const b=e.currentTarget.getBoundingClientRect();const xx=(e.clientX-b.left)/b.width*1000;setBrush([brush[0],Math.max(lo,Math.min(hi,Math.round(lo+(xx-100)/850*(hi-lo))))])}} onPointerUp={()=>{if(brush&&Math.abs(brush[1]-brush[0])>1)onRange([Math.min(...brush),Math.max(...brush)]);setBrush(null)}} onPointerCancel={()=>setBrush(null)}>
 {brush&&<rect x={x(Math.min(...brush))} y="8" width={Math.abs(x(brush[1])-x(brush[0]))} height="210" fill="var(--earth)" opacity=".12"/>}
 <defs><pattern id={id} width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6L6 0" stroke="currentColor" opacity=".3"/></pattern></defs>
 {(['sun','earth'] as BodyName[]).map((body,row)=>{const f=terrain?t[body].disk_frac:t[body].geometric_disk_frac;const points=f.slice(lo,hi+1).map((v,j)=>[x(lo+j),y(v,row)] as [number,number]);const area=`${line(points)}L${x(hi)} ${y(0,row)}L${x(lo)} ${y(0,row)}Z`;const runs:{a:number;b:number;status:'visible'|'blocked'|'indeterminate'}[]=[];for(let i=lo;i<=hi;i++){const low=terrain?t[body].disk_frac_low[i]:f[i],high=terrain?t[body].disk_frac_high[i]:f[i];const status=low>threshold?'visible':high<=threshold?'blocked':'indeterminate';const last=runs.at(-1);if(last&&last.status===status)last.b=i;else runs.push({a:i,b:i,status})}return <g key={body}>
 <text x="15" y={43+row*112} fill={colors[body]} className="svg-label">{body.toUpperCase()}</text><text x="15" y={61+row*112} className="svg-tick">DISK AREA</text>
 <line x1="100" x2="950" y1={y(0,row)} y2={y(0,row)} className="svg-grid"/><line x1="100" x2="950" y1={y(1,row)} y2={y(1,row)} className="svg-grid"/>
 <text x="974" y={y(1,row)+3} textAnchor="end" className="svg-tick">100%</text><text x="974" y={y(0,row)+3} textAnchor="end" className="svg-tick">0%</text>
 <path d={area} fill={colors[body]} opacity=".1"/><path d={line(points)} fill="none" stroke={colors[body]} strokeWidth="2"/>
 {terrain&&<path d={`${line(t[body].disk_frac_high.slice(lo,hi+1).map((v,j)=>[x(lo+j),y(v,row)]))}${t[body].disk_frac_low.slice(lo,hi+1).map((v,j)=>[x(lo+j),y(v,row)] as [number,number]).reverse().map(p=>`L${p[0]},${p[1]}`).join('')}Z`} fill={colors[body]} opacity=".25"/>}
 <line x1="100" x2="950" y1={y(threshold,row)} y2={y(threshold,row)} stroke="#6a9dce" opacity=".5" strokeDasharray="2 4"/>
 {runs.map((run,i)=><g key={i}><rect x={x(run.a)} y={85+row*112} width={Math.max(1,x(run.b)-x(run.a))} height="9" rx="2" fill={run.status==='visible'?colors[body]:`url(#${id})`} opacity={run.status==='visible'?.45:run.status==='indeterminate'?.2:.7}/>{run.a===lo&&<path d={`M${x(run.a)+8} ${85+row*112}l-6 9`} stroke="currentColor"/>}{run.b===hi&&<path d={`M${x(run.b)-8} ${85+row*112}l6 9`} stroke="currentColor"/>}<title>{tr(lang,run.status)} · {utc(t.t_utc[run.a])} — {utc(t.t_utc[run.b])} · {run.a===lo||run.b===hi?tr(lang,'censored'):'sampled run'}</title></g>)}
 </g>})}
 {[0,1,2,3,4].map(j=>{const i=Math.round(lo+(hi-lo)*j/4);return <text key={j} x={x(i)} y="244" textAnchor="middle" className="svg-tick">{utc(t.t_utc[i],true)}</text>})}
 <line x1={x(index)} x2={x(index)} y1="9" y2="218" stroke="currentColor" opacity=".55" strokeDasharray="3 3"/><circle cx={x(index)} cy="11" r="3" fill="currentColor"/>
 <text x="525" y="278" textAnchor="middle" className="svg-micro">UTC · {tr(lang,'zoom')}</text>
 </svg>
}
export function ResponseCurve({x,y,flip,lang,onEvidence}:{x:number[];y:number[];flip:number|null;lang:Lang;onEvidence:()=>void}){
 const minX=Math.min(...x),maxX=Math.max(...x),minY=Math.min(...y),maxY=Math.max(...y);const px=(v:number)=>64+(v-minX)/(maxX-minX||1)*530,py=(v:number)=>212-(v-minY)/(maxY-minY||1)*164
 return <svg className="response-svg" viewBox="0 0 650 284" role="img" aria-label={tr(lang,'response')} style={{direction:"ltr"}}>
 {[0,1,2,3,4].map(i=>{const v=minY+(maxY-minY)*i/4;return <g key={i}><line x1="64" x2="594" y1={py(v)} y2={py(v)} className="svg-grid"/><text x="51" y={py(v)+4} textAnchor="end" className="svg-tick">{fmt(v,2)}°</text></g>})}
 <line x1="64" x2="594" y1={py(0)} y2={py(0)} stroke="currentColor" opacity=".35" strokeDasharray="3 4"/>
 <path d={line(x.map((v,i)=>[px(v),py(y[i])]))} fill="none" stroke="var(--amber)" strokeWidth="2.4"/>
 <line x1={px(0)} x2={px(0)} y1="40" y2="218" stroke="currentColor" opacity=".2" strokeDasharray="4 4"/>
 {flip!==null&&<g onClick={onEvidence} role="button" tabIndex={0} onKeyDown={e=>e.key==='Enter'&&onEvidence()} aria-label={tr(lang,'flip')}><line x1={px(flip)} x2={px(flip)} y1="33" y2="218" stroke="var(--amber)" opacity=".5" strokeDasharray="3 4"/><circle cx={px(flip)} cy={py(0)} r="5" fill="var(--amber)"/><text x={px(flip)-10} y="24" textAnchor="end" fill="var(--amber)" className="svg-label">{fmt(flip,1)} m · {tr(lang,'flip')}</text></g>}
 {[0,1,2,3,4].map(i=>{const v=minX+(maxX-minX)*i/4;return <text key={i} x={px(v)} y="238" textAnchor="middle" className="svg-tick">{fmt(v,0)} m</text>})}
 <text x="325" y="272" textAnchor="middle" className="svg-micro">{tr(lang,'perturbation')}</text>
 </svg>
}
