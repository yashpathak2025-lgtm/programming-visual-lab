(()=>{
function q(s){return document.querySelector(s)}
function initInputBridge(){
  const right=q('.right');
  if(!right||q('#pvlInputPanel')) return;
  const panel=document.createElement('div');
  panel.id='pvlInputPanel';
  panel.className='panel card';
  panel.innerHTML='<div class="title">Interactive Program Input</div><textarea id="pvlStdin" aria-label="Program input" style="width:100%;min-height:90px;background:#07101a;color:#e8f0ff;border:1px solid #223553;border-radius:10px;padding:9px;font:12px/1.5 ui-monospace,monospace;resize:vertical" placeholder="Program input goes here. For multiple input() calls, put each value on a new line."></textarea><div style="display:flex;gap:7px;margin-top:7px"><button id="pvlSample" type="button">Sample Input</button><button id="pvlClear" type="button">Clear</button><span id="pvlInputStatus" class="muted" style="font-size:11px;align-self:center">stdin ready</span></div>';
  right.prepend(panel);
  q('#pvlSample').onclick=()=>{q('#pvlStdin').value='Yash\n20\n';q('#pvlInputStatus').textContent='Sample input loaded'};
  q('#pvlClear').onclick=()=>{q('#pvlStdin').value='';q('#pvlInputStatus').textContent='stdin cleared'};
  window.pvlGetStdin=()=>q('#pvlStdin')?.value||'';
}
function initShortcuts(){
  const b=q('#run'); if(!b||b.dataset.pvlInputShortcut) return;
  b.dataset.pvlInputShortcut='1';
  window.addEventListener('keydown',e=>{
    if((e.ctrlKey||e.metaKey)&&e.key==='Enter'&&!e.repeat){
      e.preventDefault(); b.click();
    }
  });
}
function boot(){initInputBridge();initShortcuts()}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();