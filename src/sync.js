/* 端末間の同期。日本語版・英語版の両方の build.sh が part2.html の __SYNC__ の位置に差し込む。
   アプリの側で用意しておくもの：LS（保存キー。同期先の行の app にも使う）、defState の
   t / cnt / at / resetAt、save() から syncSoon() を呼ぶ、bump() で myCnt() も増やす、
   srs は setRec() で書き換える、起動時に syncMigrate()、vStats() に syncBox() と bindSync()、
   最後に sbInit()。関数宣言は巻き上げられるので、上のほうから呼んでかまわない。 */

/* 端末ごとの枚数。同じ日に iPhone で 20 枚、PC で 15 枚めくったら 35 枚にしたいので、
   合計を上書きし合うのではなく、端末ごとに持って足し合わせる。
   端末IDは記録とは別のキーに置く（書き出したファイルを別の端末で読んでも混ざらない）。 */
var DEV_;   // 初期値を書かない。起動直後の移行で先に呼ばれるため、あとでこの行を通っても消えないように
function devId(){
  if(DEV_) return DEV_;
  const k = LS + "/dev";
  try{ DEV_ = localStorage.getItem(k); }catch(e){}
  if(!DEV_){ DEV_ = Math.random().toString(36).slice(2,10) + Date.now().toString(36);
    try{ localStorage.setItem(k, DEV_); }catch(e){} }
  return DEV_; }
function myCnt(){ const id = devId();
  return st.cnt[id] || (st.cnt[id] = { log:{}, done:{}, qlog:{}, quiz:{n:0,ok:0}, at:0 }); }
/* 同期より前の記録は、この端末のぶんとして引き継ぐ。起動時に 1 回だけ呼ぶ */
function syncMigrate(){
  if(Object.keys(st.cnt).length) return;
  st.cnt[devId()] = { log:{...st.log}, done:{...st.done}, qlog:{...st.qlog}, quiz:{...st.quiz}, at:Date.now() };
  save(); }
function sumCnt(){
  const o = { log:{}, done:{}, qlog:{} }, q = { n:0, ok:0 };
  for(const id in st.cnt){ const c = st.cnt[id];
    for(const k in o) for(const d in c[k]||{}) o[k][d] = (o[k][d]||0) + c[k][d];
    q.n += (c.quiz&&c.quiz.n)|0; q.ok += (c.quiz&&c.quiz.ok)|0; }
  Object.assign(st, o); st.quiz = q;
  const v = Object.values(st.log); st.best = Math.max(st.best||0, ...v, 0);
}
/* srs を書き換えるときは必ずここを通す。時刻が新しいほうを同期で採る */
function setRec(k, r){ if(r) st.srs[k] = r; else delete st.srs[k]; st.t[k] = Date.now(); }

/* ============ 端末間の同期（Supabase） ============
   記録は 1 人・1 アプリ（app = LS）で 1 行、st をまるごと JSON で置く。書く前に必ず読んで混ぜるので、
   2 台がオフラインのまま進めても、あとで片方が消えることはない。
     srs            キーごとに、書き換えた時刻（st.t）が新しいほう
     枚数・小試験    端末ごとに持ち、新しいほうを採ってから足し合わせる（sumCnt）
     達成日・バッジ   和集合
     設定・しおり     最後に保存したほう（st.at）。配色と開いている画面は端末ごと
   URL と anon キーが空なら何もしない（いままでどおり端末内だけで動く）。
   anon キーは公開してよい鍵で、他人の行は RLS で読めない。 */
const SB_URL = "https://ildwcfbsuuiuhnkdknys.supabase.co";
const SB_KEY = "sb_publishable_PyFjmJo2xEDQJ7-PxvFysQ_DWmRaiZM";   // publishable キー（公開してよい）
const SB_LIB = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
const LOCAL_CFG = ["theme", "view"];
let sb = null, sbUser = null, sbMail = "";
let pushT = null, syncing = null, again = false, syncAt = 0, syncErr = "";

function writeLocal(){ try{ localStorage.setItem(LS, JSON.stringify(st)); }catch(e){} }
/* jsonb はキーの順を並べ替えて返すので、比べるときはキーを整列してから文字列にする */
const canon = v => JSON.stringify(v, (k,x)=> x && typeof x==="object" && !Array.isArray(x)
  ? Object.keys(x).sort().reduce((o,k)=>(o[k]=x[k],o),{}) : x);
/* 入力中に描き直すと打っている文字が消えるので、そのときは待つ */
function redraw(){ const a = document.activeElement;
  if(a && /INPUT|TEXTAREA/.test(a.tagName)) return; render(); }

function mergeIn(b){
  b = deepMerge(defState, b);
  if((st.resetAt||0) > (b.resetAt||0)) return;           // こちらで消した／読み込んだ → 手元が正
  if((b.resetAt||0) > (st.resetAt||0)){                  // 向こうで消した／読み込んだ → 向こうが正
    LOCAL_CFG.forEach(k=>{ b.cfg[k] = st.cfg[k]; });
    st = b; myCnt(); sumCnt(); return; }
  for(const k of new Set([...Object.keys(b.srs), ...Object.keys(b.t)])){
    const ta = st.t[k]||0, tb = b.t[k]||0, ra = st.srs[k], rb = b.srs[k];
    /* 時刻が無いのは同期より前の記録。両方にあるときは次の出題日が遅いほう（最近やったほう）に揃える。
       どちらの端末で混ぜても同じ結果になるよう、同じ日なら中身の大小で決める */
    const later = rb && (!ra || rb[1] > ra[1] || (rb[1] === ra[1] && String(rb) > String(ra)));
    if(tb > ta || (!ta && !tb && rb && later)){
      if(rb) st.srs[k] = rb; else delete st.srs[k];
      if(tb) st.t[k] = tb; }
  }
  for(const id in b.cnt)
    if(id !== devId() && (b.cnt[id].at||0) > ((st.cnt[id]||{}).at||0)) st.cnt[id] = b.cnt[id];
  st.best = Math.max(st.best||0, b.best||0);
  sumCnt();
  st.clear = Object.assign({}, b.clear, st.clear);
  for(const id in b.badges)                              // 獲得日は早いほう
    if(!st.badges[id] || b.badges[id] < st.badges[id]) st.badges[id] = b.badges[id];
  const am = st.miss, bm = b.miss;
  if(bm && (!am || bm.d > am.d)) st.miss = bm;
  else if(bm && am && bm.d === am.d) am.keys = [...new Set([...am.keys, ...bm.keys])].sort();
  st.kv = Math.max(st.kv|0, b.kv|0);
  /* 残り（設定・しおり・前回の続き など）は、最後に保存したほうをまるごと採る */
  if((b.at||0) > (st.at||0)){
    LOCAL_CFG.forEach(k=>{ b.cfg[k] = st.cfg[k]; });
    for(const k in st) if(!(k in b) && !MERGED.includes(k)) delete st[k];
    for(const k in b)  if(!MERGED.includes(k)) st[k] = b[k]; }
}
const MERGED = ["srs","t","cnt","log","done","qlog","quiz","best","clear","badges","miss","kv","resetAt"];

function sync(){
  if(!sb || !sbUser) return Promise.resolve();
  if(syncing){ again = true; return syncing; }
  clearTimeout(pushT); pushT = null;
  syncing = (async()=>{
    try{
      const { data, error } = await sb.from("progress").select("data")
        .eq("user_id", sbUser.id).eq("app", LS).maybeSingle();
      if(error) throw error;
      const remote = data && data.data ? canon(data.data) : "";
      if(remote){ const snap = canon(st); mergeIn(data.data);
        if(canon(st) !== snap){ writeLocal(); redraw(); } }
      if(canon(st) !== remote){
        const { error:e2 } = await sb.from("progress")
          .upsert({ user_id:sbUser.id, app:LS, data:st, updated_at:new Date().toISOString() },
                  { onConflict:"user_id,app" });
        if(e2) throw e2; }
      syncAt = Date.now(); syncErr = "";
    }catch(e){ syncErr = (e && e.message) || String(e); }
    syncing = null;
    if(st.cfg.view === "stats") redraw();
    if(again){ again = false; sync(); }
  })();
  return syncing;
}
function syncSoon(){ if(!sbUser) return; clearTimeout(pushT); pushT = setTimeout(sync, 3000); }
document.addEventListener("visibilitychange", ()=>sync());   // 閉じる前に書き、戻ったら読む
addEventListener("online", ()=>sync());

async function sbInit(){
  if(!SB_URL || !SB_KEY) return;
  try{
    const { createClient } = await import(SB_LIB);
    sb = createClient(SB_URL, SB_KEY, { auth:{ storageKey: LS + "/auth" } });
    sb.auth.onAuthStateChange((ev, s)=>{
      const u = (s && s.user) || null, was = sbUser && sbUser.id;
      sbUser = u;
      if(u && u.id !== was) setTimeout(sync, 0);   // コールバックの中で待つと固まるので外で呼ぶ
      if(st.cfg.view === "stats") redraw();
    });
  }catch(e){ syncErr = "同期の部品を読み込めませんでした。通信できるときに開き直してください。";
    if(st.cfg.view === "stats") redraw(); }
}

const hm = t => new Date(t).toTimeString().slice(0,5);
function syncBox(){
  if(!SB_URL) return "";
  const row = h => '<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:14px">'+h+'</div>';
  let h = '<div class="group-head">端末間の同期<span>'+(sbUser ? "ログイン中" : "未ログイン")+'</span></div>';
  if(!sb) h += row('<span class="note">'+(syncErr ? esc(syncErr) : "準備中…")+'</span>');
  else if(sbUser) h += row('<span class="note">'+esc(sbUser.email||"")+'</span>' +
      '<button class="chip" id="syncNow">今すぐ同期</button>' +
      '<button class="chip" id="sbOut" style="margin-left:auto">ログアウト</button>') +
    '<div class="note" style="margin-top:8px">' + (syncErr ? "同期できませんでした：" + esc(syncErr)
      : syncAt ? "最後に同期 " + hm(syncAt) : "同期中…") + '</div>';
  else h += row('<input class="field" id="sbMail" type="email" autocomplete="username" placeholder="メールアドレス" value="'+esc(sbMail)+'" style="width:16em;padding:4px 8px">' +
      '<input class="field" id="sbPass" type="password" autocomplete="current-password" placeholder="パスワード（8 文字以上）" style="width:13em;padding:4px 8px">' +
      '<button class="chip" id="sbIn">ログイン</button><button class="chip" id="sbUp">はじめて使う</button>') +
    '<div class="note" style="margin-top:8px">同じメールとパスワードでログインした端末どうしで、進捗を共有します。' +
    '最初の 1 台だけ「はじめて使う」で登録し、ほかの端末は「ログイン」してください。</div>';
  return h;
}
function bindSync(){
  const on = (id, fn) => { const e = document.getElementById(id); if(e) e.onclick = fn; };
  /* ログインはメールを送らない方式にしてある。無料枠の Supabase はメールの文面を変えられず、
     リンクで入る方式だと、ホーム画面に置いた PWA ではなく Safari の側がログインしてしまうため */
  const cred = () => {
    const email = ($("#sbMail").value||"").trim(), password = $("#sbPass").value||"";
    sbMail = email;
    if(!/^\S+@\S+\.\S+$/.test(email)){ banner("メールアドレスを確かめてください。", true); return null; }
    if(password.length < 8){ banner("パスワードは 8 文字以上にしてください。", true); return null; }
    return { email, password }; };
  on("sbIn", async ()=>{ const c = cred(); if(!c) return;
    const { error } = await sb.auth.signInWithPassword(c);
    if(error){ banner("ログインできませんでした：" + (/invalid/i.test(error.message) ? "メールかパスワードが違います。" : error.message), true); return; }
    banner("ログインしました。記録を同期します。"); });
  on("sbUp", async ()=>{ const c = cred(); if(!c) return;
    const { data, error } = await sb.auth.signUp(c);
    if(error){ banner("登録できませんでした：" + (/already/i.test(error.message) ? "このメールは登録済みです。「ログイン」を使ってください。" : error.message), true); return; }
    if(!data.session){ banner("登録しましたが、ログインできませんでした。もう一度「ログイン」を押してください。", true); return; }
    banner("登録しました。記録を同期します。"); });
  on("syncNow", async ()=>{ await sync();
    banner(syncErr ? "同期できませんでした：" + syncErr : "同期しました。", !!syncErr); });
  on("sbOut", async ()=>{
    if(!confirm("ログアウトします。この端末の記録はそのまま残ります。")) return;
    await sb.auth.signOut(); });
}

