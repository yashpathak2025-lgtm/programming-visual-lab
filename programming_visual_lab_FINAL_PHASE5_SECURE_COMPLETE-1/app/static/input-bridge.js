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
  const runWithInput=async(e)=>{e.preventDefault();e.stopImmediatePropagation();
    if(typeof stopPlay==='function') stopPlay();
    q('#runState').textContent='Running…';
    state.events=[];state.step=-1;
    if(typeof renderTimeline==='function') renderTimeline();
    try{
      const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:q('#code').value,language:q('#language').value,timeout_ms:5000,stdin:q('#pvlStdin')?.value||''})});
      const res=await r.json();state.result=res;state.events=res.events||[];
      if(typeof renderOutput==='function') renderOutput(res);
      q('#eventCount').textContent=state.events.length+' events';
      if(res.ok){
        q('#runState').textContent='Execution ready';
        if(state.current){state.completed.add(state.current.group+':'+state.current.name);if(typeof persistProgress==='function')persistProgress();if(typeof renderLessons==='function')renderLessons();}
        if(state.current&&typeof nextStep==='function') nextStep();
      }else{
        q('#runState').textContent='Execution error';
        q('#explain').innerHTML='<b>Error:</b> '+esc(res.error||'Unknown error')+'<br><br>'+esc(res.traceback||'');
        if(typeof drawMessage==='function') drawMessage('Execution stopped',res.error||'Unknown error');
      }
    }catch(err){
      q('#runState').textContent='Network error';
      if(typeof drawMessage==='function') drawMessage('Server error',err.message);
    }
  };
  b.addEventListener('click',runWithInput,true);
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();e.stopImmediatePropagation();runWithInput(e)}},true);
}
function boot(){initInputBridge();patchRun()}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();