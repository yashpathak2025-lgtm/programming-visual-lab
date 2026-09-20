(()=>{ 
function q(s){return document.querySelector(s)}
function initInputBridge(){
  const right=q('.right');
  if(!right||q('#pvlInputPanel')) return;
  const panel=document.createElement('div');
  panel.id='pvlInputPanel';
  panel.className='panel card';
  panel.innerHTML='<div class="title">Interactive Program Input</div><textarea id="pvlStdin" style="width:100%;min-height:90px;background:#07101a;color:#e8f0ff;border:1px solid #223553;border-radius:10px;padding:9px;font:12px/1.5 ui-monospace,monospace;resize:vertical" placeholder="Program input goes here. For multiple input() calls, put each value on a new line."></textarea><div style="display:flex;gap:7px;margin-top:7px"><button id="pvlSample">Sample Input</button><button id="pvlClear">Clear</button><span id="pvlInputStatus" class="muted" style="font-size:11px;align-self:center">stdin ready</span></div>';
  right.prepend(panel);
  q('#pvlSample').onclick=()=>{q('#pvlStdin').value='Yash\n20\n';q('#pvlInputStatus').textContent='Sample input loaded'};
  q('#pvlClear').onclick=()=>{q('#pvlStdin').value='';q('#pvlInputStatus').textContent='stdin cleared'};
}
function patchRun(){
  const b=q('#run');
  if(!b||b.dataset.pvlInputBridge) return;
  b.dataset.pvlInputBridge='1';

  // The main application owns execution. This bridge only exposes stdin and
  // supplies it to the existing runCode() function, avoiding a second /api/run
  // request and eliminating the previous competing capture-phase listener.
  const original=window.runCode;
  if(typeof original!=='function') return;
  window.runCode=async function(){
    const input=q('#pvlStdin');
    if(input){
      window.pvlPendingStdin=input.value||'';
      q('#pvlInputStatus').textContent='Input ready';
    }
    return original.apply(this,arguments);
  };
  window.addEventListener('keydown',e=>{
    if((e.ctrlKey||e.metaKey)&&e.key==='Enter'&&document.activeElement!==b){
      e.preventDefault();
      b.click();
    }
  });
}
function boot(){initInputBridge();patchRun()}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();