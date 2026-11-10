(function(){
function $(s, r){ return (r || document).querySelector(s); }
function $$(s, r){ return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

/* Copy buttons */
$$('.copy').forEach(function(b){
  b.addEventListener('click', function(){
    var t = b.closest('.code').querySelector('code').innerText;
    var done = function(){ b.textContent = 'Copied'; setTimeout(function(){ b.textContent = 'Copy'; }, 1500); };
    var sel = function(){ var r = document.createRange(); r.selectNodeContents(b.closest('.code').querySelector('code'));
      var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = 'Press Ctrl+C'; };
    try { if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, sel); else sel(); } catch (e) { sel(); }
  });
});

/* Theme */
(function(){ var b = $('#theme-toggle'), r = document.documentElement, K = 'asd-theme', order = ['dark', 'light', 'system'];
  function cur(){ return r.getAttribute('data-theme') || 'system'; }
  function show(){ var c = cur(); b.textContent = 'Theme: ' + c; b.setAttribute('aria-label', 'Colour theme: ' + c + '. Select to change.'); }
  try { var t = localStorage.getItem(K); if (t === 'dark' || t === 'light') r.setAttribute('data-theme', t); } catch (e) {}
  b.addEventListener('click', function(){ var n = order[(order.indexOf(cur()) + 1) % 3];
    if (n === 'system') r.removeAttribute('data-theme'); else r.setAttribute('data-theme', n);
    try { localStorage.setItem(K, n); } catch (e) {} show(); });
  show(); })();

/* Scrollspy */
var links = $$('.side a'), tops = $$('header.site nav a');
if ('IntersectionObserver' in window) {
  var io = new IntersectionObserver(function(es){ es.forEach(function(e){ if (e.isIntersecting) {
    links.forEach(function(a){ a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id); });
    var on = $('.side a.on'), part = on ? on.getAttribute('data-part') : '';
    tops.forEach(function(t){ t.setAttribute('aria-current', t.getAttribute('data-part') === part ? 'true' : 'false'); }); } }); },
    {rootMargin: '-80px 0px -70% 0px'});
  $$('section[id]').forEach(function(s){ io.observe(s); });
}

/* Packet along a path */
var NS = 'http://www.w3.org/2000/svg', reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
function packet(svg, path){
  if (reduce || !path.getTotalLength) return;
  var m = (path.getAttribute('class') || '').match(/a-(\w+)/), c = document.createElementNS(NS, 'circle');
  c.setAttribute('r', '5'); c.setAttribute('class', 'pk pk-' + (m ? m[1] : 'n')); svg.appendChild(c);
  var L = path.getTotalLength(), t0 = null;
  function f(ts){ if (!t0) t0 = ts; var k = Math.min(1, (ts - t0) / 750), p = path.getPointAtLength(k * L);
    c.setAttribute('cx', p.x); c.setAttribute('cy', p.y); if (k < 1) requestAnimationFrame(f); else setTimeout(function(){ c.remove(); }, 150); }
  requestAnimationFrame(f);
}

/* Step-through */
var D = JSON.parse($('#guide-data').textContent);
$$('.stepbar').forEach(function(bar){
  var fid = bar.getAttribute('data-fig'), svg = document.getElementById(fid), data = D.steps[fid];
  var steps = $$('.st', svg), panel = $('.steppanel[data-fig="' + fid + '"]'), count = $('.scount', bar), cur = -1;
  function render(){
    steps.forEach(function(s, i){ s.classList.toggle('dim', cur >= 0 && i !== cur); s.classList.toggle('cur', i === cur); });
    if (cur < 0) { panel.hidden = true; count.textContent = 'All steps shown'; $('[data-act="next"]', bar).textContent = 'Step through'; return; }
    var d = data[cur]; panel.hidden = false;
    $('.sp-t', panel).textContent = (cur + 1) + '. ' + d.t; $('.sp-d', panel).textContent = d.d;
    var pre = $('.sp-c', panel); pre.hidden = !d.c; $('code', pre).textContent = d.c || '';
    count.textContent = 'Step ' + (cur + 1) + ' of ' + steps.length;
    $('[data-act="next"]', bar).textContent = cur === steps.length - 1 ? 'Start again' : 'Next';
    var p = steps[cur].querySelector('path'); if (p) packet(svg, p);
  }
  bar.addEventListener('click', function(e){ var b = e.target.closest('[data-act]'); if (!b) return; var a = b.getAttribute('data-act');
    if (a === 'next') cur = cur >= steps.length - 1 ? 0 : cur + 1;
    else if (a === 'prev') cur = cur <= 0 ? -1 : cur - 1; else cur = -1; render(); });
  steps.forEach(function(s, i){ s.addEventListener('click', function(){ cur = i; render(); }); });
  render();
});

/* Request builder */
(function(){ var rb = $('#rb'); if (!rb) return; var tab = 'curl';
  function v(id){ return $('#' + id).value.trim(); }
  function q(s){ return JSON.stringify(s); }
  function build(){
    var pid = v('rb-pid') || 'C9300-48P', cur = v('rb-cur') || '17.9.4', out = v('rb-out') || 'latest';
    var imgs = v('rb-img').split(',').map(function(s){ return s.trim(); }).filter(Boolean).slice(0, 5);
    var path = imgs.length ? '/metadata/pidimage' : '/metadata/pidrelease';
    var body = imgs.length ? {pid: pid, imageNames: imgs, pageIndex: '1', perPage: '25'}
      : {pid: pid, currentReleaseVersion: cur, outputReleaseVersion: out, pageIndex: '1', perPage: '25'};
    var dl = {pid: pid, mdfId: '<mdfId from metadata>', imageGuids: ['<imageGuid from metadata>'], metadataTransId: '<metadataTransId, under 60 min old>'};
    var B = 'https://apix.cisco.com/software/v4.0', s;
    if (tab === 'json') {
      s = '// POST ' + B + path + '\n' + JSON.stringify(body, null, 2) + '\n\n// POST ' + B + '/download/pidimage\n' + JSON.stringify(dl, null, 2);
    } else if (tab === 'py') {
      s = 'from asd_client import ASDClient\nimport os\n\nc = ASDClient(os.environ["CISCO_CLIENT_ID"], os.environ["CISCO_CLIENT_SECRET"])\n' +
        (imgs.length ? 'meta = c.metadata_by_image(' + q(pid) + ', ' + JSON.stringify(imgs) + ')\n'
                     : 'meta = c.metadata_by_release(' + q(pid) + ', ' + q(cur) + ', ' + q(out) + ')\n') +
        'rows = list(c.images(meta))\nfor r in rows:\n    print(r["release"], r["name"], r["exceptions"] or "ok")\n\n' +
        'pick = next(r for r in rows if not r["exceptions"])\n' +
        'd = c.download_urls(' + q(pid) + ', pick["mdfId"], [pick["guid"]], meta["metadataTransId"])\n' +
        'sha = c.fetch(d["downloads"][0], d["downloads"][0]["imageName"])\nassert sha == pick["sha512"].lower()';
    } else {
      s = '# 1. Token\nTOKEN=$(curl -s -X POST https://id.cisco.com/oauth2/default/v1/token \\\n' +
        '  --data-urlencode grant_type=client_credentials \\\n  --data-urlencode "client_id=$CISCO_CLIENT_ID" \\\n' +
        '  --data-urlencode "client_secret=$CISCO_CLIENT_SECRET" | jq -r .access_token)\n\n' +
        '# 2. Metadata (note metadataTransId, mdfId, imageGuid, sha512, exception)\n' +
        "curl -s -X POST " + B + path + " \\\n  -H \"Authorization: Bearer $TOKEN\" -H 'Content-Type: application/json' \\\n  -d '" + JSON.stringify(body) + "' | jq .\n\n" +
        '# 3. Download URL (within 60 minutes of step 2)\n' +
        "curl -s -X POST " + B + "/download/pidimage \\\n  -H \"Authorization: Bearer $TOKEN\" -H 'Content-Type: application/json' \\\n" +
        "  -d \"{\\\"pid\\\":" + q(pid).replace(/"/g, '\\"') + ",\\\"mdfId\\\":\\\"$MDF_ID\\\",\\\"imageGuids\\\":[\\\"$IMAGE_GUID\\\"],\\\"metadataTransId\\\":\\\"$TRANS_ID\\\"}\" | jq .downloads";
    }
    $('#rb-out-code').textContent = s;
    $('#rb-label').textContent = tab === 'py' ? 'Python · uses asd_client.py below' : (tab === 'json' ? 'JSON · request bodies' : 'Shell · generated (needs jq)');
  }
  $$('input', rb).forEach(function(i){ i.addEventListener('input', build); });
  $('#rb-tabs').addEventListener('click', function(e){ var b = e.target.closest('.chip'); if (!b) return; tab = b.getAttribute('data-t');
    $$('.chip', $('#rb-tabs')).forEach(function(x){ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }); build(); });
  build();
})();

/* Which path */
(function(){ var pk = $('#pick'); if (!pk) return;
  pk.addEventListener('click', function(e){ var b = e.target.closest('.chip'); if (!b) return; var d = D.pick[b.getAttribute('data-k')];
    $$('.chip', pk).forEach(function(x){ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    $('#pick-t').textContent = d[0]; $('#pick-d').textContent = d[1]; });
})();

/* Error lookup */
(function(){ var inp = $('#err-q'), rows = $$('#err-t tbody tr'), n = $('#err-n');
  function f(){ var q = inp.value.trim().toLowerCase(), k = 0;
    rows.forEach(function(r){ var s = !q || r.textContent.toLowerCase().indexOf(q) >= 0; r.hidden = !s; if (s) k++; });
    n.textContent = q ? k + ' of ' + rows.length + ' codes match' : rows.length + ' codes'; }
  inp.addEventListener('input', f); f();
})();
})();
