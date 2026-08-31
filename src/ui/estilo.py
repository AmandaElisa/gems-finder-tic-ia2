"""Folha de estilo do Gems Finder — visual "sticker" do protótipo HTML.

Cards brancos com borda preta de 2px, cantos arredondados, sombra sólida
deslocada, fontes Fredoka (títulos) e Figtree (corpo).
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&family=Fredoka:wght@500;600;700&display=swap');

:root{
  --lima:#CFF25E; --rosa:#F79BD8; --peri:#B3BCF7; --azul:#3B45D9;
  --verde:#1DB954; --verde-esc:#0E7A36; --creme:#FAF6EC; --tinta:#141414; --mute:#6E6A63;
  --f:"Figtree",ui-sans-serif,system-ui,sans-serif;
  --d:"Fredoka",var(--f);
}

/* ---------- base ---------- */
html, body, .stApp, .stMarkdown, p, li, label, input, button, textarea{font-family:var(--f);}
.stApp{
  background-color:var(--creme); color:var(--tinta);
  background-image:radial-gradient(520px 380px at 92% 2%, rgba(179,188,247,.35), transparent 60%),
                   radial-gradient(460px 340px at 2% 96%, rgba(247,155,216,.28), transparent 60%);
  background-attachment:fixed;
}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1180px;padding-top:2rem;padding-bottom:5rem;}
h1,h2,h3,h4{font-family:var(--d);letter-spacing:-.01em;color:var(--tinta);}
:focus-visible{outline:3px solid var(--azul);outline-offset:3px;border-radius:8px;}
hr{border-color:rgba(20,20,20,.15);}
/* o streamlit põe margin-bottom:-16px no markdown pra engolir a margem do último
   <p>; nos blocos de HTML cru (que terminam em div/ul) isso corta 16px do
   conteúdo e faz os cards transbordarem — neutraliza só nesses casos */
[data-testid="stMarkdownContainer"]:has(> :last-child:not(p)){margin-bottom:0 !important;}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:var(--creme);border-right:2px solid var(--tinta);}
[data-testid="stSidebar"] [role="radiogroup"]{gap:8px;}
[data-testid="stSidebar"] [role="radiogroup"] label{
  background:#fff;border:2px solid var(--tinta);border-radius:14px;padding:9px 12px;
  box-shadow:3px 3px 0 var(--tinta);font-weight:700;transition:.14s;width:100%;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{transform:translate(-1px,-1px);}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:var(--lima);}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-family:var(--f) !important;
  font-weight:700 !important;font-size:14.5px !important;}
.gf-brand{display:flex;align-items:center;gap:11px;margin-bottom:6px;}
.gf-logo{flex:none;display:block;}
/* o streamlit aplica padding:20px 0 16px nos h1; zerar junta o subtítulo ao título */
.gf-brand h1{font-family:var(--d);font-size:21px;font-weight:700;margin:0;padding:0;
  line-height:1.18;}
.gf-brand small{display:block;font-size:11.5px;color:var(--mute);font-weight:600;}
/* o seletor [data-testid="stMarkdownContainer"] p do streamlit vence .gf-nav-label
   na especificidade e forçava 16px aqui; daí o !important no tamanho */
[data-testid="stSidebar"] .gf-nav-label{font-size:12px !important;letter-spacing:.12em;
  text-transform:uppercase;color:var(--mute);font-weight:800;margin:14px 0 6px;}
.gf-rail-foot{font-size:12px;color:var(--mute);line-height:1.7;
  border-top:2px dashed rgba(20,20,20,.2);padding-top:14px;margin-top:22px;}
.gf-rail-foot b{color:var(--tinta);}
[data-testid="stSidebar"] .gf-rail-foot a{color:var(--mute);text-decoration:underline;
  text-decoration-thickness:1px;text-underline-offset:2px;transition:.14s;}
[data-testid="stSidebar"] .gf-rail-foot a:hover{color:var(--tinta);}

/* ---------- cartões sticker ---------- */
[class*="st-key-cartao-"]{
  background:#fff;border:2px solid var(--tinta);border-radius:22px;
  padding:20px 24px;box-shadow:5px 5px 0 var(--tinta);margin-bottom:6px;
}
/* respiro entre os elementos dentro dos cartões (o padrão vinha grudado) */
[class*="st-key-cartao-"] > div[data-testid="stVerticalBlock"]{gap:16px;}
[class*="st-key-gema-"]{
  background:#fff;border:2px solid var(--tinta);border-radius:20px;
  padding:14px 18px 4px;box-shadow:4px 4px 0 var(--tinta);margin-bottom:0;
}
.gf-card{background:#fff;border:2px solid var(--tinta);border-radius:22px;padding:22px 24px;
  box-shadow:5px 5px 0 var(--tinta);margin-bottom:6px;}

/* ---------- hero ---------- */
.gf-hero{display:flex;align-items:center;gap:22px;flex-wrap:wrap;margin-bottom:8px;}
.gf-title{font-family:var(--d);font-size:40px;font-weight:700;letter-spacing:-.02em;
  margin:0;line-height:1.08;}
.gf-lede{color:var(--mute);margin:8px 0 0;max-width:56ch;font-size:15.5px;}
.gf-bubble{background:#fff;border:2px solid var(--tinta);border-radius:22px 22px 22px 6px;
  padding:12px 18px;font-family:var(--d);font-size:16px;box-shadow:4px 4px 0 var(--tinta);
  animation:gfFloat 3.6s ease-in-out infinite;}
@keyframes gfFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}

/* ---------- passos ---------- */
.gf-step{display:flex;align-items:center;gap:10px;margin-bottom:4px;}
/* flex:none + nowrap pra o selo não ser comprimido pelo título e quebrar
   "PASSO 2" em duas linhas nas telas estreitas */
.gf-step b{font-size:11px;font-weight:800;letter-spacing:.08em;background:var(--lima);
  border:2px solid var(--tinta);border-radius:99px;padding:2px 10px;
  flex:none;white-space:nowrap;}
.gf-step h3{font-family:var(--d);font-size:19px;font-weight:600;margin:0;}
.gf-help{color:var(--mute);font-size:13.5px;margin:0 0 16px;}
.gf-help b{color:var(--tinta);}
.gf-status{font-size:13.5px;color:var(--mute);margin:0 0 16px;}
.gf-status b{color:var(--tinta);font-weight:800;}

/* ---------- vibes (o card inteiro é o botão) ---------- */
.gf-vibe{border:2px solid var(--tinta);border-radius:20px;padding:16px 14px 14px;
  text-align:center;box-shadow:4px 4px 0 var(--tinta);transition:.16s;background:#fff;}
.gf-vibe strong{display:block;font-family:var(--d) !important;font-size:17px;
  font-weight:600;margin-top:8px;}
.gf-vibe span{display:block;font-size:12.5px;color:var(--mute);line-height:1.35;margin-top:2px;}
.gf-vibe.on{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--tinta);}
.gf-vibe .gf-mascote{margin:0 auto;}
[class*="st-key-vibecard-"]{position:relative;}
[class*="st-key-vibecard-"]:hover .gf-vibe{transform:translate(-2px,-2px);
  box-shadow:6px 6px 0 var(--tinta);}
[class*="st-key-vibecard-"] [data-testid="stElementContainer"]:has(.stButton){
  position:absolute;inset:0;z-index:2;margin:0;}
[class*="st-key-vibecard-"] .stButton, [class*="st-key-vibecard-"] .stButton > button{
  width:100%;height:100%;}
[class*="st-key-vibecard-"] .stButton > button{opacity:0;cursor:pointer;border-radius:20px;
  box-shadow:none;}

/* ---------- chips de gênero e artista (st.buttons em linha com quebra) ---------- */
[class*="st-key-chips-"]{flex-direction:row !important;flex-wrap:wrap;gap:10px;}
[class*="st-key-chips-"] [data-testid="stElementContainer"]{width:auto !important;flex:0 0 auto;}
[class*="st-key-chips-"] .stButton > button{font-family:var(--f) !important;font-weight:700;
  padding:8px 16px;box-shadow:3px 3px 0 var(--tinta);}
[class*="st-key-chips-"] .stButton > button:hover{transform:translate(-1px,-1px);
  box-shadow:4px 4px 0 var(--tinta);}
[class*="st-key-chips-"] .stButton > button p{font-family:var(--f) !important;
  font-size:14px !important;font-weight:700 !important;}
[class*="st-key-chips-"] .stButton > button[kind="primary"],
[class*="st-key-chips-"] .stButton > button[data-testid="stBaseButton-primary"]{
  background:var(--lima) !important;color:var(--tinta) !important;}

/* ---------- profundidade ---------- */
.gf-num{font-family:var(--d);font-size:44px;font-weight:700;line-height:1;}
.gf-num span{font-size:15px;color:var(--mute);font-family:var(--f);font-weight:700;}
.gf-strata{display:flex;align-items:flex-end;gap:3px;height:48px;}
.gf-strata i{flex:1;background:#EAE4D6;border:1px solid rgba(20,20,20,.15);border-bottom:0;
  border-radius:4px 4px 0 0;transition:.22s;}
.gf-strata i.dig{background:var(--lima);border-color:var(--tinta);}
.gf-axis{display:flex;justify-content:space-between;font-size:11.5px;color:var(--mute);
  margin-top:7px;font-weight:600;}

/* ---------- métricas ---------- */
.gf-sec{display:flex;align-items:center;gap:12px;margin:30px 0 12px;flex-wrap:wrap;}
.gf-sec h3{font-family:var(--d);font-size:24px;font-weight:600;margin:0;}
.gf-sec p{margin:0;font-size:13.5px;color:var(--mute);}
.gf-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px;}
.gf-met{background:#fff;border:2px solid var(--tinta);border-radius:18px;padding:14px 18px;
  box-shadow:4px 4px 0 var(--tinta);}
.gf-met.a{background:var(--lima);} .gf-met.b{background:var(--peri);}
.gf-met p{margin:0;font-size:12px;font-weight:800;}
.gf-met strong{display:block;font-family:var(--d);font-size:34px;font-weight:700;
  letter-spacing:-.02em;margin:2px 0 3px;}
.gf-met small{font-size:11.5px;line-height:1.4;display:block;color:var(--mute);}
.gf-met.modelo strong{color:var(--verde-esc);}
.gf-met.modelo p:after{content:"MODELO";font-size:9px;letter-spacing:.08em;background:var(--tinta);
  color:#fff;border-radius:99px;padding:2px 7px;margin-left:7px;vertical-align:2px;}

/* ---------- faixas ---------- */
.gf-gtop{display:flex;align-items:center;gap:13px;}
.gf-gtop .txt{flex:1;min-width:0;}
.gf-gtop b{display:block;font-family:var(--d);font-size:17px;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gf-gtop i{display:block;font-style:normal;font-size:13px;color:var(--mute);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gf-gtop .mt{text-align:right;flex:none;}
.gf-gtop .mt strong{display:block;font-family:var(--d);font-size:23px;font-weight:700;line-height:1.05;}
.gf-gtop .mt small{font-size:10.5px;color:var(--mute);font-weight:700;}
.gf-meta{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px;}
.gf-badge{border:2px solid var(--tinta);border-radius:99px;padding:2px 10px;font-weight:700;
  font-size:11.5px;background:#fff;}
.gf-attr{display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--mute);margin-bottom:8px;}
.gf-attr span{width:118px;flex:none;color:var(--tinta);font-weight:700;}
.gf-attr i{flex:1;height:9px;background:#fff;border:2px solid var(--tinta);border-radius:99px;
  display:block;overflow:hidden;}
.gf-attr i b{display:block;height:100%;background:var(--rosa);}
.gf-attr em{font-style:normal;width:30px;text-align:right;flex:none;font-weight:700;color:var(--tinta);}
.gf-why{font-size:12.5px;color:var(--mute);margin:10px 0 0;}
.gf-empty{text-align:center;padding:34px;}
.gf-empty p{margin:0;font-family:var(--d);font-size:20px;}

/* ---------- conta ---------- */
.gf-who{display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
.gf-avatar{width:54px;height:54px;border-radius:50%;background:var(--rosa);
  border:2px solid var(--tinta);display:grid;place-items:center;font-family:var(--d);
  font-size:22px;font-weight:700;}
.gf-who strong{display:block;font-family:var(--d);font-size:20px;font-weight:600;}
.gf-who span{font-size:13px;color:var(--mute);}
.gf-pill{margin-left:auto;background:var(--lima);border:2px solid var(--tinta);border-radius:99px;
  padding:6px 15px;font-size:12px;font-weight:800;}
.gf-tops{display:flex;gap:9px;flex-wrap:wrap;margin-top:10px;}
.gf-top{background:#fff;border:2px solid var(--tinta);border-radius:99px;padding:7px 15px;
  font-size:13px;font-weight:700;}
.gf-top s{text-decoration:none;color:var(--mute);font-weight:500;}
.gf-perm{margin:14px 0 4px;padding:0;list-style:none;}
.gf-perm li{font-size:13.5px;color:var(--mute);padding-left:24px;position:relative;margin-bottom:5px;}
.gf-perm li:before{content:"✓";position:absolute;left:0;color:var(--verde-esc);font-weight:800;}

/* ---------- widgets do streamlit ---------- */
.stButton > button{
  border:2px solid var(--tinta) !important;border-radius:99px;background:#fff;color:var(--tinta);
  font-family:var(--d);font-weight:600;font-size:15px;padding:9px 24px;
  box-shadow:4px 4px 0 var(--tinta);transition:.14s;
}
.stButton > button:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--tinta);
  color:var(--tinta);background:#fff;}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"]{
  background:var(--verde) !important;color:#fff !important;}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover{
  background:var(--verde) !important;color:#fff !important;}
.stLinkButton > a{border:2px solid var(--tinta) !important;border-radius:99px;
  background:#fff;color:var(--tinta);font-family:var(--d) !important;font-weight:600;
  font-size:15px;padding:9px 24px;box-shadow:4px 4px 0 var(--tinta);transition:.14s;
  text-decoration:none !important;}
.stLinkButton > a:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--tinta);}
.stLinkButton > a[kind="primary"], .stLinkButton > a[data-testid="stBaseLinkButton-primary"]{
  background:var(--verde) !important;color:#fff !important;}
.stLinkButton > a p{font-family:var(--d) !important;color:inherit !important;}
[data-baseweb="input"], [data-baseweb="base-input"]{background:#fff !important;}
[data-testid="stTextInput"] [data-baseweb="input"]{border:2px solid var(--tinta) !important;
  border-radius:99px;padding:2px 8px;}
[data-testid="stTextInputRootElement"]{border:2px solid var(--tinta) !important;
  border-radius:99px;background:#fff !important;padding:2px 10px;}
[data-testid="stTextInputField"]{background:transparent !important;}
[data-baseweb="select"] > div{border:2px solid var(--tinta) !important;border-radius:14px;
  background:#fff !important;}
[data-baseweb="tag"]{background:var(--lima) !important;color:var(--tinta) !important;
  border:2px solid var(--tinta) !important;border-radius:99px !important;font-weight:700;}
[data-baseweb="tag"] span{color:var(--tinta) !important;}
/* segmented control com o visual .seg do protótipo: pílula branca, item ativo preto */
[data-testid="stButtonGroup"]{display:inline-flex;background:#fff;border:2px solid var(--tinta);
  border-radius:99px;padding:4px;gap:4px;box-shadow:3px 3px 0 var(--tinta);flex-wrap:wrap;
  width:auto;margin:2px 0 4px;}
[data-testid="stButtonGroup"] button{border:0 !important;background:transparent !important;
  border-radius:99px !important;padding:7px 20px !important;box-shadow:none !important;
  color:var(--mute) !important;transition:.14s;}
[data-testid="stButtonGroup"] button:hover{color:var(--tinta) !important;transform:none;}
[data-testid="stButtonGroup"] button p{font-weight:700 !important;font-size:14px !important;
  color:inherit !important;}
[data-testid="stButtonGroup"] button[aria-checked="true"],
[data-testid="stButtonGroup"] button[data-selected="true"],
[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"]{
  background:var(--tinta) !important;}
[data-testid="stButtonGroup"] button[aria-checked="true"] p,
[data-testid="stButtonGroup"] button[data-selected="true"] p,
[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"] p{
  color:#fff !important;}
[data-testid="stSlider"] [role="slider"]{background:var(--rosa) !important;
  border:2px solid var(--tinta) !important;box-shadow:none !important;}
[data-testid="stExpander"]{border:none !important;background:transparent !important;}
[data-testid="stExpander"] details, [data-testid="stExpander"] > div:first-child{
  border:none !important;background:transparent !important;box-shadow:none !important;}
[data-testid="stExpander"] summary{border-top:2px dashed rgba(20,20,20,.18);
  padding:8px 0 4px !important;font-weight:700;font-size:12.5px;color:var(--mute);}
[data-testid="stExpander"] summary:hover{color:var(--tinta);}
[data-testid="stAlert"], [data-testid="stNotification"]{border:2px solid var(--tinta);
  border-radius:16px;box-shadow:3px 3px 0 var(--tinta);}
[data-testid="stStatusWidget"], [data-testid="stExpanderDetails"]{background:transparent;}
.stCode, pre{border-radius:14px !important;}
[data-testid="stCaptionContainer"]{color:var(--mute);}

/* ---------- mascote ---------- */
.gf-mascote{display:block;}
.gf-mascote .eye{animation:gfBlink 5s infinite;}
.gf-mascote .eye.b{animation-delay:.15s;}
@keyframes gfBlink{0%,94%,100%{transform:scaleY(1)}97%{transform:scaleY(.1)}}

/* corpo em Figtree também nos textos internos dos widgets (radio, select, slider…) */
.stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea,
[data-baseweb="select"] div, [data-baseweb="tag"] span,
[data-testid="stSlider"] div{font-family:var(--f) !important;}

/* fontes por cima do CSS interno do streamlit (especificidade + !important) */
.gf-title,.gf-step h3,.gf-sec h3,.gf-bubble,.gf-num,.gf-met strong,
.gf-gtop b,.gf-gtop .mt strong,.gf-empty p,.gf-who strong,.gf-avatar,
.stButton > button,.stButton > button p{font-family:var(--d) !important;}
.gf-lede,.gf-help,.gf-status,.gf-vibe span,.gf-attr,.gf-why,.gf-meta,.gf-badge,
.gf-axis,.gf-tops,.gf-rail-foot,.gf-perm li,.gf-who span,.gf-num span{
  font-family:var(--f) !important;}

@media (max-width:1000px){
  .gf-title{font-size:29px;}
  .gf-metrics{grid-template-columns:1fr 1fr;}
}
/* em tela estreita os três modos não cabem na linha e o flex-wrap partia a
   pílula no meio; mantém a cara de tabs comprimindo fonte e padding, e deixa
   correr no eixo x (sem barra visível) se ainda faltar espaço */
@media (max-width:640px){
  /* Tabs roláveis no padrão do Material 3: uma linha só, e o que não couber se
     alcança arrastando. O flex que envolve os botões é um div INTERNO do
     stButtonGroup, não ele mesmo — o nowrap e o overflow vão nele. */
  [data-testid="stButtonGroup"]{max-width:100%;}
  [data-testid="stButtonGroup"] > div{
    flex-wrap:nowrap !important;overflow-x:auto;max-width:100%;
    -webkit-overflow-scrolling:touch;scroll-behavior:smooth;
    scroll-snap-type:x proximity;scrollbar-width:none;-ms-overflow-style:none;}
  [data-testid="stButtonGroup"] > div::-webkit-scrollbar{display:none;}
  [data-testid="stButtonGroup"] button{flex:none;padding:6px 10px !important;
    scroll-snap-align:center;}
  [data-testid="stButtonGroup"] button p{font-size:11.5px !important;letter-spacing:0;}
  .gf-metrics{grid-template-columns:1fr;}
}
/* No touch o swipe basta e a barra fica escondida. Com mouse não há como
   arrastar a tira, então expõe uma barra fininha — é a afordância que o
   Material cobre com as setas laterais no desktop. */
@media (max-width:640px) and (pointer:fine){
  [data-testid="stButtonGroup"]{padding-bottom:2px;}
  [data-testid="stButtonGroup"] > div{scrollbar-width:thin;
    scrollbar-color:rgba(20,20,20,.4) transparent;padding-bottom:5px;}
  [data-testid="stButtonGroup"] > div::-webkit-scrollbar{display:block;height:5px;}
  [data-testid="stButtonGroup"] > div::-webkit-scrollbar-track{background:transparent;}
  [data-testid="stButtonGroup"] > div::-webkit-scrollbar-thumb{
    background:rgba(20,20,20,.4);border-radius:99px;}
  [data-testid="stButtonGroup"] > div::-webkit-scrollbar-thumb:hover{
    background:rgba(20,20,20,.65);}
}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}}
</style>
"""
