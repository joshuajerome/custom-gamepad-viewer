/* UI behavior script.

Fetches configuration (/api/config), applies changes via POST (/api/config),
reacts to storage events, and refreshes the preview iframe using returned URLs.
Designed to be framework-agnostic and easily portable to NiceGUI/Streamlit later.
*/

const selSkin   = document.getElementById('skin');
const selPlayer = document.getElementById('player');
const btnApply  = document.getElementById('apply');
const btnRefresh= document.getElementById('refresh');
const frame     = document.getElementById('gpv');
const link      = document.getElementById('link-gpv');
const statusEl  = document.getElementById('status');
const urlsEl    = document.getElementById('urls');

async function GET(url){ const r=await fetch(url,{cache:'no-store'}); if(!r.ok) throw new Error(r.status); return r.json(); }
async function POST(url, body){ const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); if(!r.ok) throw new Error(r.status); return r.json(); }

function setPreviewIfChanged(cfg){
  if (frame.src !== cfg.gpv_url) frame.src = cfg.gpv_url;
  link.href = cfg.gpv_url;
  urlsEl.textContent = `GPV: ${cfg.gpv_url} | CSS: ${cfg.css_url}`;
}

async function populateSkins(){
  const { themes } = await GET('/api/themes');
  selSkin.innerHTML = '';
  for (const t of themes) {
    const opt = document.createElement('option');
    opt.value = t.name;
    opt.textContent = t.name + (t.ok ? '' : ' (incomplete)');
    opt.disabled = !t.ok;
    selSkin.appendChild(opt);
  }
}

async function loadConfigOnce(){
  await populateSkins();
  const cfg = await GET('/api/config');
  selSkin.value   = cfg.skin;
  selPlayer.value = String(cfg.player);
  setPreviewIfChanged(cfg);
}

btnApply.addEventListener('click', async ()=>{
  statusEl.textContent = 'Applying…';
  try {
    const cfg = await POST('/api/config', { skin: selSkin.value, player: Number(selPlayer.value) });

    // Bust iframe cache (gpv caches editcss param aggressively)
    const url = cfg.gpv_url + (cfg.gpv_url.includes('#') ? `&a=${Date.now()}` : `#a=${Date.now()}`);
    frame.src = 'about:blank';
    setTimeout(()=>{ frame.src = url; }, 30);

    localStorage.setItem('lgv_skin', cfg.skin);
    localStorage.setItem('lgv_player', String(cfg.player));

    setPreviewIfChanged(cfg);
    statusEl.textContent = `Applied: theme=${cfg.skin}, player=p${cfg.player}`;
  } catch(e){
    statusEl.textContent = 'Failed to apply. ' + e;
  }
});

btnRefresh.addEventListener('click', async ()=>{
  statusEl.textContent = 'Refreshing preview…';
  try {
    const cfg = await GET('/api/config');
    const url = cfg.gpv_url + (cfg.gpv_url.includes('#') ? `&r=${Date.now()}` : `#r=${Date.now()}`);
    frame.src = 'about:blank';
    setTimeout(()=>{ frame.src = url; }, 30);
    setPreviewIfChanged(cfg);
    statusEl.textContent = 'Preview reloaded.';
  } catch(e){
    statusEl.textContent = 'Failed to refresh. ' + e;
  }
});

// Cross-tab sync: when Check Slot or another tab updates skin/player, reflect it
window.addEventListener('storage', async (e)=>{
  if (e.key === 'lgv_player' || e.key === 'lgv_skin') {
    try {
      const cfg = await GET('/api/config');
      selSkin.value   = cfg.skin;
      selPlayer.value = String(cfg.player);
      setPreviewIfChanged(cfg);
      statusEl.textContent = `Updated from external change → theme=${cfg.skin}, p${cfg.player}`;
    } catch {}
  }
});

loadConfigOnce().catch(err => { statusEl.textContent = 'Init failed: ' + err; });
