const $=s=>document.querySelector(s);const $$=s=>document.querySelectorAll(s);let authMode='login';
async function api(url,opts={}){const r=await fetch(url,{...opts,headers:{'Content-Type':'application/json',...(opts.headers||{})}});let d={};try{d=await r.json()}catch{}if(!r.ok)throw Error(d.error||'Something went wrong.');return d}
function esc(v=''){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function cropIcon(c){const s=c.toLowerCase();if(/tomato/.test(s))return'🍅';if(/onion/.test(s))return'🧅';if(/potato/.test(s))return'🥔';if(/rice|paddy/.test(s))return'🌾';if(/mango/.test(s))return'🥭';if(/banana/.test(s))return'🍌';if(/corn|maize/.test(s))return'🌽';if(/chilli|pepper/.test(s))return'🌶️';if(/cabbage/.test(s))return'🥬';return'🌱'}
async function loadStats(){try{const s=await api('/api/stats');$('#farmers').textContent=s.farmers;$('#listingCount').textContent=s.listings;$('#buyers').textContent=s.buyers;$('#cropCount').textContent=s.crops}catch{}}
async function loadListings(){const q=$('#searchInput').value.trim();try{const d=await api('/api/listings?q='+encodeURIComponent(q));const grid=$('#listingGrid');if(!d.listings.length){grid.innerHTML='<div class="empty">No crop listings yet. Join as a farmer to publish the first harvest.</div>';return}grid.innerHTML=d.listings.map(x=>`<article class="crop-card"><div class="crop-top"><div class="crop-icon">${cropIcon(x.crop)}</div><span class="crop-badge">AVAILABLE</span></div><h3>${esc(x.crop)}</h3><div class="location">⌖ ${esc(x.location)}</div><div class="crop-bottom"><div class="price">₹${Number(x.price_per_kg).toLocaleString('en-IN',{maximumFractionDigits:2})}<small> / kg</small></div><div class="quantity">${Number(x.quantity_kg).toLocaleString('en-IN')} kg</div></div><div class="farmer-name">Listed by ${esc(x.farmer_name)}</div></article>`).join('')}catch{$('#listingGrid').innerHTML='<div class="empty">Could not load listings. Please refresh.</div>'}}
async function refreshUser(){try{const d=await api('/api/me');const u=d.user;$('#userStatus').textContent=u?`Signed in as ${u.name} · ${u.role}`:'You\'re browsing as a guest.';$('#accountBtn').textContent=u?'Sign out':'Sign in / Join';$('#portalAccount').textContent=u?'Sign out ↗':'Create your account ↗';$$('#farmerForm input,#farmerForm textarea,#buyerForm input').forEach(el=>{if(u&&u.location&&el.name==='location'&&!el.value)el.value=u.location});return u}catch{return null}}
function showAuth(){if($('#accountBtn').textContent==='Sign out'){api('/api/logout',{method:'POST'}).then(async()=>{await refreshUser();await loadStats();$('#portalMessage').textContent='You have signed out.'}).catch(e=>alert(e.message));return}$('#authModal').classList.remove('hidden')}
$('#accountBtn').addEventListener('click',showAuth);$('#portalAccount').addEventListener('click',showAuth);$('#closeModal').addEventListener('click',()=>$('#authModal').classList.add('hidden'));$('#authModal').addEventListener('click',e=>{if(e.target.id==='authModal')$('#authModal').classList.add('hidden')});
$$('[data-auth]').forEach(b=>b.addEventListener('click',()=>{authMode=b.dataset.auth;$$('[data-auth]').forEach(x=>x.classList.toggle('active',x===b));$('#nameWrap').classList.toggle('hidden',authMode!=='register');$('#extraFields').classList.toggle('hidden',authMode!=='register');$('#authSubmit').textContent=authMode==='login'?'Sign in ↗':'Create account ↗';$('#authMessage').textContent=''}));
$('#authForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),data=Object.fromEntries(f.entries());try{const d=await api('/api/'+(authMode==='login'?'login':'register'),{method:'POST',body:JSON.stringify(data)});$('#authMessage').textContent=`Welcome, ${d.user.name}!`;setTimeout(()=>$('#authModal').classList.add('hidden'),500);await refreshUser();await loadStats()}catch(err){$('#authMessage').textContent=err.message}});
$$('.portal-panel [data-tab]').forEach(b=>b.addEventListener('click',()=>{$$('.portal-panel [data-tab]').forEach(x=>x.classList.toggle('active',x===b));$('#farmerForm').classList.toggle('hidden',b.dataset.tab!=='farmerForm');$('#buyerForm').classList.toggle('hidden',b.dataset.tab!=='buyerForm');$('#portalMessage').textContent='';$('#matchResults').innerHTML=''}));
$('#farmerForm').addEventListener('submit',async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target).entries());try{await api('/api/listings',{method:'POST',body:JSON.stringify(data)});$('#portalMessage').textContent='Your crop listing has been published.';e.target.reset();await loadListings();await loadStats();await refreshUser()}catch(err){$('#portalMessage').textContent=err.message}});
$('#buyerForm').addEventListener('submit',async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target).entries());try{const d=await api('/api/requirements',{method:'POST',body:JSON.stringify(data)});$('#portalMessage').textContent=`Found ${d.matches.length} matching listing(s). Transport costs remain pending until a real quote is provided.`;$('#matchResults').innerHTML=d.matches.length?d.matches.map(m=>`<div class="match"><div><strong>${esc(m.crop)} · ${esc(m.farmer_name)}</strong><small>${Number(m.quantity_kg).toLocaleString()} kg available · ${esc(m.location)}<br>Match score: ${Number(m.match_score||0)}% · ${esc(m.match_reason||'Crop and quantity match')}<br>Transport: Quote pending</small></div><b>₹${Number(m.produce_total).toLocaleString('en-IN',{maximumFractionDigits:2})}<small> produce total</small></b></div>`).join(''):'<div class="empty">No exact crop-and-quantity match yet. Try a smaller quantity or check back later.</div>'}catch(err){$('#portalMessage').textContent=err.message;$('#matchResults').innerHTML=''}});
$('#searchBtn').addEventListener('click',loadListings);$('#searchInput').addEventListener('keydown',e=>{if(e.key==='Enter')loadListings()});
loadStats();loadListings();refreshUser();


// Local AI-style prototype tools (no paid service or network API).
$('#cropAiForm').addEventListener('submit', async e => {
  e.preventDefault();
  const result=$('#cropAiResult'); result.textContent='Analysing conditions…';
  const data=Object.fromEntries(new FormData(e.target).entries());
  try {
    const d=await api('/api/ai/crop-recommendation',{method:'POST',body:JSON.stringify(data)});
    result.innerHTML='<h4>Top recommendations</h4>'+d.recommendations.map((x,i)=>`<div class="ai-output"><strong>${i+1}. ${esc(x.crop)} <span>${x.suitability}% fit</span></strong><p>${esc(x.reason)}</p></div>`).join('')+`<small>${esc(d.notice)}</small>`;
  } catch(err) { result.textContent=err.message; }
});

$('#priceAiForm').addEventListener('submit', async e => {
  e.preventDefault();
  const result=$('#priceAiResult'); result.textContent='Calculating indicative range…';
  const data=Object.fromEntries(new FormData(e.target).entries());
  try {
    const d=await api('/api/ai/price-prediction?crop='+encodeURIComponent(data.crop)+'&location='+encodeURIComponent(data.location||''));
    result.innerHTML=`<div class="price-estimate"><small>INDICATIVE ESTIMATE · INR / KG</small><strong>₹${Number(d.estimated_price).toFixed(2)}</strong><span>Possible range: ₹${Number(d.low).toFixed(2)} – ₹${Number(d.high).toFixed(2)}</span></div><p>Source: ${esc(d.source)} · Data points: ${d.data_points} · Confidence: ${esc(d.confidence)}</p><small>${esc(d.notice)}</small>`;
  } catch(err) { result.textContent=err.message; }
});

function addChat(text,who){const node=document.createElement('div');node.className='chat-bubble '+who;node.textContent=text;$('#chatLog').appendChild(node);$('#chatLog').scrollTop=$('#chatLog').scrollHeight;}
$('#chatForm').addEventListener('submit',async e=>{
  e.preventDefault(); const input=$('#chatMessage'); const message=input.value.trim(); if(!message)return;
  addChat(message,'user'); input.value='';
  try {const d=await api('/api/ai/chatbot',{method:'POST',body:JSON.stringify({message})});addChat(d.reply,'bot');}
  catch(err){addChat(err.message,'bot');}
});
