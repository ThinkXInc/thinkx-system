// 切り抜き編集の区間ロジックだけを取り出して検証する（DOM 非依存。CLIP_PLAN C-3）
// main.py の CLIP_JS 内 markStart / markEnd / joinGap / normalizeClips と同じ規則。
const EPS=0.01, MINW=0.05;
function clipAt(clips,t){ for(let i=0;i<clips.length;i++){ if(clips[i][0]<=t&&t<clips[i][1]) return i; } return -1; }
function normalize(clips){
  clips.sort((a,b)=>a[0]-b[0]);
  const out=[];
  clips.forEach(c=>{
    if(out.length&&c[0]<=out[out.length-1][1]+EPS){
      out[out.length-1][1]=Math.max(out[out.length-1][1],c[1]);
    }else out.push([c[0],c[1]]);
  });
  return out;
}
function markStart(st,t){
  const ci=clipAt(st.clips,t);
  if(ci>=0){
    const c=st.clips[ci];
    if(t-c[0]<MINW||c[1]-t<MINW) return 'too_close';
    st.clips.splice(ci,1,[c[0],t],[t,c[1]]); return 'split';
  }
  st.pending=t; return 'pending';
}
function markEnd(st,t){
  if(st.pending!=null){
    if(t<=st.pending+MINW) return 'bad_order';
    st.clips.push([st.pending,t]); st.pending=null;
    st.clips=normalize(st.clips); return 'clip';
  }
  const ci=clipAt(st.clips,t);
  if(ci>=0){
    if(t-st.clips[ci][0]<MINW) return 'bad_order';
    st.clips[ci][1]=t; return 'trim';
  }
  return 'no_start';
}
function joinGap(st,t){
  if(clipAt(st.clips,t)>=0) return 'inside';
  let prev=null,next=null;
  st.clips.forEach((c,i)=>{
    if(c[1]<=t&&(prev===null||c[1]>st.clips[prev][1])) prev=i;
    if(c[0]>=t&&(next===null||c[0]<st.clips[next][0])) next=i;
  });
  if(prev===null||next===null) return 'no_pair';
  const a=st.clips[prev][0], b=st.clips[next][1];
  st.clips=st.clips.filter((c,i)=>i!==prev&&i!==next);
  st.clips.push([a,b]); st.pending=null;
  st.clips=normalize(st.clips); return 'joined';
}
let ok=0,ng=0;
function eq(name,got,want){
  const g=JSON.stringify(got),w=JSON.stringify(want);
  if(g===w){ok++;console.log('  OK  ',name);} else {ng++;console.log('  NG  ',name,'\n     得:',g,'\n     期:',w);}
}
console.log('== S → E で切り抜きが1本できる ==');
let st={clips:[],pending:null};
eq('空白で S は保留', markStart(st,10), 'pending');
eq('E で確定', markEnd(st,25), 'clip');
eq('区間', st.clips, [[10,25]]);
eq('保留は消える', st.pending, null);
console.log('== 開始と終了の順序 ==');
st={clips:[],pending:30};
eq('終了が開始より前なら拒否', markEnd(st,20), 'bad_order');
console.log('== 切り抜きの中で S ＝ 分割（原文 L17） ==');
st={clips:[[10,25]],pending:null};
eq('分割できる', markStart(st,18), 'split');
eq('2本になる', st.clips, [[10,18],[18,25]]);
eq('端では分割しない', markStart(st,10.01), 'too_close');
console.log('== E 単独 ＝ 終了の指定（後ろが空白になる） ==');
st={clips:[[10,25]],pending:null};
eq('終了を動かす', markEnd(st,20), 'trim');
eq('区間', st.clips, [[10,20]]);
console.log('== 空白右クリック「この間を詰める」＝前後を結合（原文 L23） ==');
st={clips:[[10,18],[20,25]],pending:null};
eq('結合できる', joinGap(st,19), 'joined');
eq('1本になる（間も含む）', st.clips, [[10,25]]);
st={clips:[[10,18]],pending:null};
eq('片側だけなら拒否', joinGap(st,19), 'no_pair');
st={clips:[[10,18],[20,25]],pending:null};
eq('切り抜きの中では効かない', joinGap(st,15), 'inside');
console.log('== E で新規が既存と重なったら1本に統合 ==');
st={clips:[[10,18]],pending:15};
eq('確定できる', markEnd(st,22), 'clip');
eq('統合される', st.clips, [[10,22]]);
console.log(`\n合計 OK=${ok} NG=${ng}`);
process.exit(ng?1:0);
