// Firebase's browser SDK is used here; no Firebase desktop Unity SDK is shipped.
const status=document.getElementById('status'), button=document.getElementById('login');
try {
  const config=await (await fetch('/v1/auth/config')).json();
  const challengeId=new URLSearchParams(location.search).get('challenge');
  if(config.unavailable||!challengeId)throw new Error('尚未設定遊戲專用登入服務，或登入連結無效。');
  const [{initializeApp},{getAuth,GoogleAuthProvider,signInWithPopup}]=await Promise.all([
    import('https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js'),
    import('https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js')]);
  const auth=getAuth(initializeApp(config));button.disabled=false;status.textContent='請確認正在登入你自己的遊戲帳號。';
  button.onclick=async()=>{button.disabled=true;try{const result=await signInWithPopup(auth,new GoogleAuthProvider());const firebaseToken=await result.user.getIdToken();const response=await fetch('/v1/auth/authorize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({challengeId,firebaseToken})});const value=await response.json();if(!response.ok)throw new Error(value.message);status.textContent='驗證完成，請回到遊戲。';}catch(error){status.textContent=error.message;button.disabled=false;}};
}catch(error){status.textContent=error.message;}
