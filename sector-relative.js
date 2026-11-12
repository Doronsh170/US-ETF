/* Sector performance versus SPY/QQQ using ETF Explorer snapshot return fields. */
(function(){
 'use strict';
 const root=document.getElementById('relativePerformance');
 if(!root || typeof RAW==='undefined')return;
 const lookup=new Map(RAW.map(f=>[String(f.Symbol||'').toUpperCase(),f]));
 const symbols=[
 ['XLK','טכנולוגיה','core'],['XLF','פיננסים','core'],['XLV','בריאות','core'],
 ['XLY','צריכה מחזורית','core'],['XLP','צריכה בסיסית','core'],['XLE','אנרגיה','core'],
 ['XLI','תעשייה','core'],['XLB','חומרי גלם','core'],['XLU','שירותים ציבוריים','core'],
 ['XLRE','נדל״ן','core'],['XLC','שירותי תקשורת','core'],
 ['SMH','מוליכים למחצה','themes'],['CIBR','סייבר','themes'],['SKYY','ענן','themes'],
 ['ITA','תעופה וביטחון','themes'],['BOTZ','רובוטיקה ובינה מלאכותית','themes']
 ];
 const periods={ytd:['YTDPct','מתחילת השנה'],one:['Return1YPct','שנה'],three:['Return3YAnnPct','3 שנים, ממוצע שנתי']};
 let period='ytd',benchmark='SPY',scope='core';
 const el=id=>document.getElementById(id);
 const num=x=>x!==null&&x!==''&&Number.isFinite(Number(x))?Number(x):null;
 const pct=x=>x===null?'לא זמין':(x>0?'+':'')+x.toFixed(2)+'%';
 const pp=x=>x===null?'לא זמין':(x>0?'+':'')+x.toFixed(2)+' נ״א';
 function render(){
  const field=periods[period][0],base=num(lookup.get(benchmark)?.[field]);
  const rows=symbols.filter(g=>scope==='all'||g[2]===scope).map(g=>{
   const val=num(lookup.get(g[0])?.[field]);
   return {symbol:g[0],name:g[1],val:val,diff:val===null||base===null?null:val-base};
  }).sort((a,b)=>(b.diff??-Infinity)-(a.diff??-Infinity));
  for(const btn of root.querySelectorAll('[data-rel-period]'))btn.setAttribute('aria-pressed',String(btn.dataset.relPeriod===period));
  for(const btn of root.querySelectorAll('[data-rel-base]'))btn.setAttribute('aria-pressed',String(btn.dataset.relBase===benchmark));
  for(const btn of root.querySelectorAll('[data-rel-scope]'))btn.setAttribute('aria-pressed',String(btn.dataset.relScope===scope));
  el('relHeading').textContent='תשואת יתר / חסר מול '+benchmark+' · '+periods[period][1];
  el('relBaseValue').textContent=pct(base);
  el('relSectorCount').textContent=String(rows.filter(r=>r.diff!==null).length);
  const max=Math.max(1,...rows.map(r=>Math.abs(r.diff||0)));
  el('relRows').innerHTML=rows.map(r=>{
   const up=r.diff!==null&&r.diff>=0,pos=r.diff===null?0:Math.abs(r.diff)/max*48;
   const left=up?50:50-pos;
   const bar=r.diff===null?'':'<span class="rel-diff-bar '+(up?'rel-positive':'rel-negative')+'" style="left:'+left.toFixed(2)+'%;width:'+pos.toFixed(2)+'%"></span>';
   return '<div class="rel-entry"><div class="rel-sector"><strong>'+r.name+'</strong><small dir="ltr">'+r.symbol+'</small></div><div class="rel-visual" role="img" aria-label="'+r.name+', פער '+pp(r.diff)+' מול '+benchmark+'"><span class="rel-zero"></span>'+bar+'</div><div class="rel-value '+(r.diff===null?'':up?'rel-up':'rel-down')+'" dir="ltr"><strong>'+pp(r.diff)+'</strong><small>'+pct(r.val)+' · '+r.symbol+'</small></div></div>';
  }).join('')||'<p>אין נתונים להצגה.</p>';
  el('relFootnote').textContent='כל שורה מייצגת ETF סקטוריאלי או תמטי אחד, ולא תשואה משוקללת של כל הקרנות בתחום. פער התשואה מחושב בנקודות אחוז מול '+benchmark+'. תשואת 3 שנים מוצגת בשיעור שנתי, כפי שהיא מופיעה במקור. מקור: ETF Explorer, תאריך המידע מוצג בראש האתר. נתוני המקור אינם מכילים סדרה היסטורית יומית לכל תאריך.';
 }
 root.addEventListener('click',e=>{
  const b=e.target.closest('button');
  if(!b)return;
  if(b.hasAttribute('data-rel-period'))period=b.dataset.relPeriod;
  else if(b.hasAttribute('data-rel-base'))benchmark=b.dataset.relBase;
  else if(b.hasAttribute('data-rel-scope'))scope=b.dataset.relScope;
  else return;
  render();
 });
 el('relToggle').addEventListener('click',()=>{
  const opened=root.classList.toggle('etf-closed')===false;
  el('relToggle').setAttribute('aria-expanded',String(opened));
 });
 render();
})();