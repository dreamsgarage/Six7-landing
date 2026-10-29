const themeButtons=[...document.querySelectorAll('[data-theme-choice]')];
function syncThemeButtons(){themeButtons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.themeChoice===document.documentElement.dataset.theme)))}
syncThemeButtons();
themeButtons.forEach(button=>button.addEventListener('click',()=>{const theme=button.dataset.themeChoice;document.documentElement.dataset.theme=theme;try{localStorage.setItem('six7-theme',theme)}catch(e){}syncThemeButtons();const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content=theme==='light'?'#f4f2eb':'#242527'}));
window.addEventListener('storage',event=>{if(event.key==='six7-theme'&&(event.newValue==='light'||event.newValue==='dark')){document.documentElement.dataset.theme=event.newValue;syncThemeButtons()}});
