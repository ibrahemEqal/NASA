import {useEffect,useId,useRef,useState} from 'react'
import type {BodyName, SiteData} from '../data'
import {fmt,utc} from '../data'
import {tr,type Lang} from '../i18n'
const colors={sun:'var(--amber)',earth:'var(--earth)'}
export function state(frac:number){return frac<=0?'blocked':frac>=1?'visible':'partial'}
function line(points:[number,number][]){return points.map(([x,y],i)=>`${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ')}
// Match the viewBox to the rendered width: SVG labels retain their screen size
// instead of shrinking along with a fixed desktop coordinate system on phones.
function usePlotWidth(initial=500){
 const ref=useRef<SVGSVGElement>(null),[width,setWidth]=useState(initial)
 useEffect(()=>{const element=ref.current;if(!element)return;const resize=new ResizeObserver(([entry])=>{if(entry.contentRect.width>0)setWidth(entry.contentRect.width)});resize.observe(element);return()=>resize.disconnect()},[])
 return{ref,width}
}
export function HeroScene({data,index,terrain,lang,onEvidence}:{data:SiteData;index:number;terrain:boolean;lang:Lang;onEvidence:()=>void}){
 const {ref,width:w}=usePlotWidth(600),id=useId().replace(/:/g,'');const h=data.horizon,t=data.tracks
 const left=52,right=w-22,bottom=235,top=30,pw=Math.max(right-left,1)
 const ys=[...h.h_nominal_deg,t.sun.el_deg[index]+t.sun.radius_deg[index],t.earth.el_deg[index]-t.earth.radius_deg[index]]
 const min=Math.floor(Math.min(...ys)-.7),max=Math.ceil(Math.max(...ys)+.7),px=(a:number)=>left+a/360*pw,py=(e:number)=>bottom-(e-min)/(max-min)*(bottom-top)
 const points=h.az_deg.filter((_,i)=>i%4===0).map(a=>{const i=h.az_deg.indexOf(a);return[px(a),py(terrain?h.h_nominal_deg[i]:t.smooth_horizon_deg)] as [number,number]})
 const path=line(points)
 return <div className="hero-plot" style={{direction:'ltr'}}><svg ref={ref} viewBox={`0 0 ${w} 305`} style={{height:305}} role="img" aria-label={tr(lang,'skyQuestion')}>
 <defs><linearGradient id={id} x1="0" x2="0" y1="0" y2="1"><stop stopColor="#a6abb4" stopOpacity=".25"/><stop offset="1" stopColor="#5f6774" stopOpacity=".03"/></linearGradient><clipPath id={`${id}-sky`}><path d={`${path}L${right} 10L${left} 10Z`}/></clipPath><pattern id={`${id}h`} width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6L6 0" stroke="currentColor" opacity=".08"/></pattern></defs>
 {[0,1,2,3,4].map(i=>{const e=min+(max-min)*i/4;return <g key={i}><line x1={left} x2={right} y1={py(e)} y2={py(e)} className="svg-grid"/><text x={left-10} y={py(e)+4} textAnchor="end" className="svg-tick">{fmt(e,1)}°</text></g>})}
 {[0,90,180,270,360].map((a,i)=><text key={a} x={px(a)} y="264" textAnchor={i===0?'start':i===4?'end':'middle'} className="svg-tick">{a}°</text>)}
 <path d={`${path}L${right} ${bottom+8}L${left} ${bottom+8}Z`} fill={`url(#${id})`}/><path d={`${path}L${right} ${bottom+8}L${left} ${bottom+8}Z`} fill={`url(#${id}h)`}/><path d={path} fill="none" className="terrain-stroke" strokeWidth="1.7" strokeDasharray={terrain?undefined:'5 5'}/>
 {(['sun','earth'] as BodyName[]).map(b=>{const body=t[b],x=px(body.az_deg[index]),y=py(body.el_deg[index]),fraction=terrain?body.disk_frac[index]:body.geometric_disk_frac[index];const rr=body.radius_deg[index]*(bottom-top)/(max-min),rx=body.radius_deg[index]*pw/360/Math.cos(body.el_deg[index]*Math.PI/180),nearRight=x>w-125,tx=nearRight?x-16:x+16;return <g key={b} tabIndex={0} role="button" onClick={onEvidence} onKeyDown={e=>e.key==='Enter'&&onEvidence()} aria-label={`${tr(lang,b)} ${fmt(fraction*100,1)}%`}>
 <line x1={x} x2={x} y1={y+14} y2={bottom+8} stroke={colors[b]} opacity=".28" strokeDasharray="2 5"/>
 <ellipse cx={x} cy={y} rx={rx} ry={rr} fill={colors[b]} opacity=".16" stroke={colors[b]} strokeWidth=".6"/><ellipse cx={x} cy={y} rx={rx} ry={rr} fill={colors[b]} clipPath={`url(#${id}-sky)`}/>
 <circle cx={x} cy={y} r={rr+7} fill="none" stroke={colors[b]} opacity=".12"/>
 <text x={tx} y={y-12} textAnchor={nearRight?'end':'start'} fill={colors[b]} className="svg-label">{b==='sun'?'SUN':'EARTH'}</text><text x={tx} y={y+10} textAnchor={nearRight?'end':'start'} className="svg-tick">{tr(lang,state(fraction))}</text>
 <title>{tr(lang,b)} · {fmt(body.az_deg[index])}° / {fmt(body.el_deg[index])}° · {fmt(fraction*100,1)}%</title>
 </g>})}
 <text x={(left+right)/2} y="295" textAnchor="middle" className="svg-micro">AZIMUTH (°)</text>
 </svg></div>
}
export function SkyPlot({data,index,terrain,lang,onEvidence,highlight}:{data:SiteData;index:number;terrain:boolean;lang:Lang;onEvidence:()=>void;highlight?:number}){
 const {ref,width:w}=usePlotWidth(460),center=w/2,radius=Math.max((w-80)/2,1)
 const h=data.horizon,t=data.tracks;const all=[...h.h_nominal_deg,...t.sun.el_deg,...t.earth.el_deg];const low=Math.floor(Math.min(...all)-2),high=Math.ceil(Math.max(...all)+2);const radial=(e:number)=>radius*(high-e)/(high-low)
 const pos=(a:number,e:number):[number,number]=>[center+radial(e)*Math.sin(a*Math.PI/180),center-radial(e)*Math.cos(a*Math.PI/180)]
 const hp=h.az_deg.map((a,i)=>pos(a,terrain?h.h_nominal_deg[i]:t.smooth_horizon_deg));const horizonPath=line(hp)+'Z',id=useId().replace(/:/g,'')
 return <svg ref={ref} className="sky-svg" viewBox={`0 0 ${w} ${w}`} role="img" aria-label={`${tr(lang,'skyTitle')} ${data.site.name}`} style={{direction:'ltr',height:w}}>
 <defs><mask id={id}><rect width={w} height={w} fill="white"/><path d={horizonPath} fill="black"/></mask><pattern id={`${id}-pattern`} width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(40)"><line x1="0" x2="0" y2="7" stroke="currentColor" strokeWidth="1" opacity=".11"/></pattern></defs>
 <circle cx={center} cy={center} r={radius} fill="currentColor" opacity=".035" mask={`url(#${id})`}/><circle cx={center} cy={center} r={radius} fill={`url(#${id}-pattern)`} mask={`url(#${id})`}/>
 {[.25,.5,.75,1].map(r=><g key={r}><circle cx={center} cy={center} r={radius*r} fill="none" className="svg-grid"/>{r<1&&<text x={center+5} y={center-radius*r-5} className="svg-tick">{fmt(high-r*(high-low),1)}°</text>}</g>)}
 {[0,45,90,135,180,225,270,315].map(a=>{const p=pos(a,low);return <line key={a} x1={center} y1={center} x2={p[0]} y2={p[1]} className="svg-grid"/>})}
 <path d={horizonPath} fill="none" className="terrain-stroke" strokeWidth="1.5" strokeDasharray={terrain?undefined:'5 4'}/>
 {highlight!==undefined&&<path d={line([[center,center],pos(highlight,low)])} stroke="var(--amber)" strokeWidth="1.5" strokeDasharray="3 3"/>}
 {(['sun','earth'] as BodyName[]).map(b=>{const body=t[b],track=body.az_deg.map((a,i)=>pos(a,body.el_deg[i])),[x,y]=pos(body.az_deg[index],body.el_deg[index]),rr=body.radius_deg[index]*radius/(high-low),tangential=radial(body.el_deg[index])*body.radius_deg[index]*Math.PI/180/Math.cos(body.el_deg[index]*Math.PI/180),f=terrain?body.disk_frac[index]:body.geometric_disk_frac[index],angle=body.az_deg[index],nearRight=x>w-95;return <g key={b}>
 <path d={line(track)} fill="none" stroke={colors[b]} strokeWidth="1.6" opacity=".65" strokeDasharray={b==='earth'?'4 3':undefined}/>
 <ellipse cx={x} cy={y} rx={tangential} ry={rr} transform={`rotate(${angle} ${x} ${y})`} fill={colors[b]} opacity={f<=0?.35:1} stroke={colors[b]} strokeWidth="1"/>
 <circle cx={x} cy={y} r={rr+8} fill="transparent" stroke={colors[b]} strokeWidth=".7" opacity=".5" tabIndex={0} role="button" aria-label={`${tr(lang,b)} ${tr(lang,state(f))}`} onClick={onEvidence} onKeyDown={e=>e.key==='Enter'&&onEvidence()}/>
 <text x={nearRight?x-rr-13:x+rr+13} y={y+4} textAnchor={nearRight?'end':'start'} fill={colors[b]} className="svg-label">{b==='sun'?'SUN':'EARTH'}</text>
 <title>{utc(t.t_utc[index])} · {tr(lang,b)} · {fmt(body.az_deg[index])}° / {fmt(body.el_deg[index])}°</title>
 </g>})}
 <text x={center} y="22" textAnchor="middle" className="compass">N</text><text x={w-15} y={center+5} textAnchor="middle" className="compass">E</text><text x={center} y={w-8} textAnchor="middle" className="compass">S</text><text x="15" y={center+5} textAnchor="middle" className="compass">W</text><circle cx={center} cy={center} r="2" className="terrain-dot"/>
 </svg>
}
export function Timeline({data,index,range,onIndex,onRange,lang,terrain,threshold}:{data:SiteData;index:number;range:[number,number];onIndex:(i:number)=>void;onRange:(r:[number,number])=>void;lang:Lang;terrain:boolean;threshold:number}){
 const {ref,width:w}=usePlotWidth(1000),left=78,right=w-52,pw=Math.max(right-left,1)
 const [lo,hi]=range,[brush,setBrush]=useState<[number,number]|null>(null);const t=data.tracks,x=(i:number)=>left+(i-lo)/Math.max(hi-lo,1)*pw,y=(v:number,row:number)=>82+row*112-v*54,id=useId().replace(/:/g,'')
 const pick=(clientX:number,element:SVGSVGElement)=>{const bounds=element.getBoundingClientRect();return Math.max(lo,Math.min(hi,Math.round(lo+(clientX-bounds.left-left)/pw*(hi-lo))))}
 const tickCount=w<600?3:5
 return <svg ref={ref} className="timeline-svg" viewBox={`0 0 ${w} 300`} role="img" aria-label={tr(lang,'timelineTitle')} style={{direction:'ltr',height:300}} onPointerDown={e=>{const i=pick(e.clientX,e.currentTarget);setBrush([i,i]);onIndex(i);e.currentTarget.setPointerCapture(e.pointerId)}} onPointerMove={e=>{if(brush)setBrush([brush[0],pick(e.clientX,e.currentTarget)])}} onPointerUp={()=>{if(brush&&Math.abs(brush[1]-brush[0])>1)onRange([Math.min(...brush),Math.max(...brush)]);setBrush(null)}} onPointerCancel={()=>setBrush(null)}>
 {brush&&<rect x={x(Math.min(...brush))} y="15" width={Math.abs(x(brush[1])-x(brush[0]))} height="210" fill="var(--earth)" opacity=".12"/>}
 <defs><pattern id={id} width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6L6 0" stroke="currentColor" opacity=".3"/></pattern></defs>
 {(['sun','earth'] as BodyName[]).map((body,row)=>{const f=terrain?t[body].disk_frac:t[body].geometric_disk_frac,points=f.slice(lo,hi+1).map((v,j)=>[x(lo+j),y(v,row)] as [number,number]),area=`${line(points)}L${x(hi)} ${y(0,row)}L${x(lo)} ${y(0,row)}Z`;const runs:{a:number;b:number;status:'visible'|'blocked'|'indeterminate'}[]=[];for(let i=lo;i<=hi;i++){const low=terrain?t[body].disk_frac_low[i]:f[i],high=terrain?t[body].disk_frac_high[i]:f[i],status=low>threshold?'visible':high<=threshold?'blocked':'indeterminate',last=runs.at(-1);if(last&&last.status===status)last.b=i;else runs.push({a:i,b:i,status})}return <g key={body}>
 <text x="8" y={54+row*112} fill={colors[body]} className="svg-label">{body.toUpperCase()}</text>
 <line x1={left} x2={right} y1={y(0,row)} y2={y(0,row)} className="svg-grid"/><line x1={left} x2={right} y1={y(1,row)} y2={y(1,row)} className="svg-grid"/>
 <text x={w-5} y={y(1,row)+4} textAnchor="end" className="svg-tick">100%</text><text x={w-5} y={y(0,row)+4} textAnchor="end" className="svg-tick">0%</text>
 <path d={area} fill={colors[body]} opacity=".1"/><path d={line(points)} fill="none" stroke={colors[body]} strokeWidth="2"/>
 {terrain&&<path d={`${line(t[body].disk_frac_high.slice(lo,hi+1).map((v,j)=>[x(lo+j),y(v,row)]))}${t[body].disk_frac_low.slice(lo,hi+1).map((v,j)=>[x(lo+j),y(v,row)] as [number,number]).reverse().map(p=>`L${p[0]},${p[1]}`).join('')}Z`} fill={colors[body]} opacity=".25"/>}
 <line x1={left} x2={right} y1={y(threshold,row)} y2={y(threshold,row)} stroke="var(--earth)" opacity=".5" strokeDasharray="2 4"/>
 {runs.map((run,i)=><g key={i}><rect x={x(run.a)} y={94+row*112} width={Math.max(1,x(run.b)-x(run.a))} height="12" rx="2" fill={run.status==='visible'?colors[body]:`url(#${id})`} opacity={run.status==='visible'?.45:run.status==='indeterminate'?.2:.7}/>{run.a===lo&&<path d={`M${x(run.a)+8} ${94+row*112}l-6 12`} stroke="currentColor"/>}{run.b===hi&&<path d={`M${x(run.b)-8} ${94+row*112}l6 12`} stroke="currentColor"/>}<title>{tr(lang,run.status)} · {utc(t.t_utc[run.a])} — {utc(t.t_utc[run.b])} · {run.a===lo||run.b===hi?tr(lang,'censored'):'sampled run'}</title></g>)}
 </g>})}
 {Array.from({length:tickCount},(_,j)=>{const i=Math.round(lo+(hi-lo)*j/(tickCount-1));return <text key={j} x={x(i)} y="250" textAnchor={j===0?'start':j===tickCount-1?'end':'middle'} className="svg-tick">{utc(t.t_utc[i],true)}</text>})}
 <line x1={x(index)} x2={x(index)} y1="17" y2="225" stroke="currentColor" opacity=".55" strokeDasharray="3 3"/><circle cx={x(index)} cy="19" r="3" fill="currentColor"/>
 <text x={(left+right)/2} y="284" textAnchor="middle" className="svg-micro">UTC</text>
 </svg>
}
export function ResponseCurve({x,y,flip,lang,onEvidence}:{x:number[];y:number[];flip:number|null;lang:Lang;onEvidence:()=>void}){
 const {ref,width:w}=usePlotWidth(600),left=78,right=w-22,top=52,bottom=232
 const minX=Math.min(...x),maxX=Math.max(...x),minY=Math.min(...y),maxY=Math.max(...y),px=(v:number)=>left+(v-minX)/(maxX-minX||1)*(right-left),py=(v:number)=>bottom-(v-minY)/(maxY-minY||1)*(bottom-top),tickCount=w<500?3:5
 return <svg ref={ref} className="response-svg" viewBox={`0 0 ${w} 315`} role="img" aria-label={tr(lang,'response')} style={{direction:'ltr',height:315}}>
 {[0,1,2,3,4].map(i=>{const v=minY+(maxY-minY)*i/4;return <g key={i}><line x1={left} x2={right} y1={py(v)} y2={py(v)} className="svg-grid"/><text x={left-10} y={py(v)+4} textAnchor="end" className="svg-tick">{fmt(v,2)}°</text></g>})}
 <line x1={left} x2={right} y1={py(0)} y2={py(0)} stroke="currentColor" opacity=".35" strokeDasharray="3 4"/>
 <path d={line(x.map((v,i)=>[px(v),py(y[i])]))} fill="none" stroke="var(--amber)" strokeWidth="2.4"/>
 <line x1={px(0)} x2={px(0)} y1={top} y2={bottom} stroke="currentColor" opacity=".2" strokeDasharray="4 4"/>
 {flip!==null&&<g onClick={onEvidence} role="button" tabIndex={0} onKeyDown={e=>e.key==='Enter'&&onEvidence()} aria-label={tr(lang,'flip')}><line x1={px(flip)} x2={px(flip)} y1="35" y2={bottom} stroke="var(--amber)" opacity=".5" strokeDasharray="3 4"/><circle cx={px(flip)} cy={py(0)} r="5" fill="var(--amber)"/><text x={Math.max(60,Math.min(w-60,px(flip)))} y="25" textAnchor="middle" fill="var(--amber)" className="svg-label">{fmt(flip,1)} m</text></g>}
 {Array.from({length:tickCount},(_,i)=>{const v=minX+(maxX-minX)*i/(tickCount-1);return <text key={i} x={px(v)} y="260" textAnchor={i===0?'start':i===tickCount-1?'end':'middle'} className="svg-tick">{fmt(v,0)} m</text>})}
 <text x={(left+right)/2} y={w<380?285:300} textAnchor="middle" className="svg-micro">{w<380?<>{tr(lang,'perturbation').split(' ').slice(0,Math.ceil(tr(lang,'perturbation').split(' ').length/2)).join(' ')}<tspan x={(left+right)/2} dy="21">{tr(lang,'perturbation').split(' ').slice(Math.ceil(tr(lang,'perturbation').split(' ').length/2)).join(' ')}</tspan></>:tr(lang,'perturbation')}</text>
 </svg>
}
