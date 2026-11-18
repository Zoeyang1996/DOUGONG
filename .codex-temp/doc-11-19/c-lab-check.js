
const $=s=>document.querySelector(s);let latest='',recognition,busy=false;
function state(s){$('#state').textContent=s}
async function ask(){if(busy)return;busy=true;state('思考');$('#answer').textContent='';
 try{const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:$('#question').value})});const d=await r.json();if(!r.ok)throw Error(d.error);latest=d.answer;$('#answer').textContent=latest;$('#refs').textContent=JSON.stringify(d.refs,null,2);$('#mode').textContent=d.mode}
 catch(e){latest='';$('#answer').textContent=e.message;$('#refs').textContent='';$('#mode').textContent='请求未完成'}finally{busy=false;state('待机')}}
$('#ask').onclick=ask;
$('#speak').onclick=()=>{if(!latest)return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(latest);u.lang='zh-CN';u.onstart=()=>state('朗读');u.onend=u.onerror=()=>state('待机');speechSynthesis.speak(u)};
$('#cancel').onclick=()=>{speechSynthesis.cancel();state('待机')};
async function initVoice(){const cfg=await fetch('config.json').then(r=>r.json());if(!cfg.voiceEnabled){$('#mode').textContent='录音未接通：完成训练步骤后启用';return}
 const R=window.SpeechRecognition||window.webkitSpeechRecognition;
 if(!R){$('#mode').textContent='此浏览器无可用语音识别接口；请改用文字测试，并记录语音未通过';return}
 recognition=new R();recognition.lang='zh-CN';recognition.interimResults=false;
 recognition.onstart=()=>state('聆听');recognition.onerror=e=>{$('#mode').textContent='识别失败：'+e.error;state('待机')};recognition.onend=()=>{if(!busy)state('待机')};
 recognition.onresult=e=>{$('#question').value=e.results[0][0].transcript; /* TRAIN_C: 在这里调用问答函数 */};
 $('#record').disabled=false;$('#record').onclick=()=>{if(!busy)try{recognition.start()}catch(e){$('#mode').textContent=e.message}};
 $('#stop').onclick=()=>recognition.stop();}
initVoice().catch(e=>$('#mode').textContent=e.message);
