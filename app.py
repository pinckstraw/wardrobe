import streamlit as st
# from rembg import remove, new_session   # 改成延遲載入
from PIL import Image
import cv2
import numpy as np
import os, shutil, json, base64, time
from datetime import datetime
from io import BytesIO
from google import genai

# ═══════════════════════════════════════════════════════
# 頁面設定
# ═══════════════════════════════════════════════════════
st.set_page_config(page_title="🎀 數位衣櫥", page_icon="", layout="centered")

HOT   = "#FE81D4"
MID   = "#FAACBF"
BLUSH = "#FBC3C1"
CREAM = "#FFEABB"
TEXT  = "#5C2D4A"
SOFT  = "#FFF5F9"

SEASONS   = ["四季皆宜", "春夏", "秋冬"]
OCCASIONS = ["日常", "旅遊", "約會", "朋友聚會"]
COLORS    = ["白", "黑", "灰", "米", "粉", "紅", "藍", "黃", "紫", "咖", "碎花"] # 🌟 新增基礎顏色清單
COLUMNS   = ["左欄（主要衣物）", "右欄（配件）"]
LEVELS    = ["上層", "中層", "下層"]
COL_KEY   = {"左欄（主要衣物）": "L", "右欄（配件）": "R"}
LVL_KEY   = {"上層": 1, "中層": 2, "下層": 3}

# ═══════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

html,body,[class*="css"],.stApp{{
  font-family:'Nunito','Noto Sans TC',sans-serif!important;
  -webkit-text-size-adjust:100%;
}}
.stApp{{background:linear-gradient(150deg,{SOFT} 0%,#fff8fb 50%,#fffbf0 100%)}}
#MainMenu,footer,header{{visibility:hidden}}
.block-container{{padding:0.8rem 0.8rem 5rem!important;max-width:420px}}

/* ── 按鈕 ── */
.stButton>button{{
  font-family:'Nunito',sans-serif!important;font-weight:800!important;
  border-radius:14px!important;border:none!important;
  padding:11px 14px!important;font-size:14px!important;
  transition:all 0.18s!important;
  background:linear-gradient(135deg,{HOT},{MID})!important;
  color:white!important;box-shadow:0 3px 12px {HOT}40!important;
  min-height:44px;line-height:1.3;
}}
.stButton>button:active{{transform:scale(0.96)!important}}

/* ── Input / Select ── */
.stSelectbox>div>div,
.stTextInput>div>div>input{{
  background:white!important;border:2px solid {MID}90!important;
  border-radius:12px!important;color:{TEXT}!important;
  font-weight:700!important;font-family:'Nunito',sans-serif!important;
  font-size:15px!important;min-height:44px!important;
}}

/* ── Multiselect ── */
.stMultiSelect>div>div{{
  background:white!important;border:2px solid {MID}90!important;
  border-radius:12px!important;min-height:44px!important;
}}
.stMultiSelect span[data-baseweb="tag"]{{
  background:linear-gradient(135deg,{HOT},{MID})!important;
  border-radius:8px!important;color:white!important;
  font-weight:700!important;font-size:11px!important;
}}

/* ── Slider ── */
.stSlider>div>div>div{{background:linear-gradient(90deg,{HOT},{MID})!important}}
.stSlider label{{font-weight:700!important;color:{TEXT}!important}}

/* ── File uploader：偽裝成大框框（採用偽元素方式）── */
[data-testid="stFileUploaderDropzone"] {{
  background:linear-gradient(135deg,{HOT}08,{CREAM}20)!important;
  border:3px dashed {HOT}!important;
  border-radius:20px!important;
  padding:50px 20px!important;
  display:flex!important;
  flex-direction:column!important;
  align-items:center!important;
  justify-content:center!important;
  cursor:pointer!important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
  border-color:{HOT}!important;
  background:linear-gradient(135deg,{HOT}15,{CREAM}35)!important;
}}
/* 徹底隱藏原本的 Upload 按鈕與內建文字 */
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploaderDropzone"] > div {{
  display:none!important;
}}
/* 變出相機圖示 */
[data-testid="stFileUploaderDropzone"]::before {{
  content:"📸";
  font-size:46px;
  display:block;
  margin-bottom:8px;
}}
/* 變出中文說明文字 */
[data-testid="stFileUploaderDropzone"]::after {{
  content:"點選或拖曳上傳衣服照片";
  color:{TEXT};
  font-weight:800;
  font-size:16px;
  display:block;
}}

/* ── Toast ── */
[data-testid="stToast"]{{
  background:linear-gradient(135deg,{HOT},{MID})!important;
  color:white!important;border-radius:14px!important;
  font-weight:800!important;border:none!important;font-size:13px!important;
}}

/* ── 移除各頁面多餘白框 ── */
/* text_input 上方空白框 */
div[data-testid="stTextInput"] > label{{
  display:none!important;
}}
div[data-testid="stTextInput"] > div{{
  margin-top:0!important;
}}
/* selectbox 上方空白框 */
div[data-testid="stSelectbox"] > label{{
  display:none!important;
}}
/* multiselect 上方空白框 */
div[data-testid="stMultiSelect"] > label{{
  display:none!important;
}}
/* slider 多餘空間 */
div[data-testid="stSlider"] > label{{
  display:none!important;
}}
/* file uploader label */
div[data-testid="stFileUploader"] > label{{
  display:none!important;
}}
div[data-baseweb="input"]{{
  border-radius:12px!important;
}}

/* ── Expander ── */
.stExpander{{
  background:rgba(255,255,255,0.85)!important;
  border:2px solid {BLUSH}60!important;border-radius:14px!important;overflow:hidden;
}}

/* ── 卡片 ── */
.wcard{{
  background:rgba(255,255,255,0.92);backdrop-filter:blur(8px);
  border-radius:18px;padding:14px;
  border:2px solid {BLUSH}50;box-shadow:0 3px 16px {HOT}12;margin-bottom:10px;
}}

/* ── 標題 ── */
.title-box{{text-align:center;padding:6px 0 10px}}
.title-eyebrow{{font-size:10px;font-weight:800;letter-spacing:3.5px;color:{MID};margin-bottom:4px}}
.title-main{{
  font-size:26px;font-weight:900;line-height:1.1;
  background:linear-gradient(135deg,{HOT} 0%,{MID} 50%,{BLUSH} 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}}
.title-sub{{color:{MID};font-size:12px;font-weight:600;margin-top:4px}}

/* ── 導覽 ── */
.nav-active{{
  text-align:center;
  background:linear-gradient(135deg,{HOT},{MID});
  color:white;border-radius:14px;padding:9px 4px;font-weight:800;
  font-size:12px;box-shadow:0 3px 12px {HOT}40;
  min-height:44px;display:flex;align-items:center;
  justify-content:center;flex-direction:column;gap:1px;
}}

/* ── 區塊標題 ── */
.sec-title{{
  font-size:11px;font-weight:800;letter-spacing:1.8px;
  color:{MID};margin:6px 0 10px;text-transform:uppercase;
}}

/* ── Badge ── */
.badge{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:10px;font-weight:800;margin:1px 2px}}
.b-hot{{background:{HOT}25;color:{HOT};border:1.5px solid {HOT}40}}
.b-mid{{background:{MID}25;color:{MID};border:1.5px solid {MID}40}}
.b-cream{{background:{CREAM}90;color:#8B6914;border:1.5px solid {CREAM}}}
.b-blush{{background:{BLUSH}50;color:{TEXT};border:1.5px solid {BLUSH}}}

/* ── 已選衣物 chip ── */
.sel-chip{{
  display:flex;align-items:center;gap:10px;
  background:linear-gradient(135deg,{HOT}15,{CREAM}20);
  border:2px solid {HOT}40;border-radius:14px;padding:10px 12px;
  margin-bottom:8px;
}}
.sel-chip img{{
  width:48px;height:48px;object-fit:contain;
  background:white;border-radius:10px;padding:3px;
  box-shadow:0 2px 6px {HOT}20;flex-shrink:0;
}}
.sel-chip .info .name{{font-weight:800;color:{TEXT};font-size:13px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.sel-chip .info .tags{{margin-top:3px}}

/* ── 瀏覽貼紙（大） ── */
.browse-sticker{{
  background:{CREAM}!important; /* 🌟 換成能凸顯白邊的可愛奶黃底色 */
  border-radius:16px;
  padding:10px 8px;
  text-align:center;
  border:2.5px solid {CREAM};
  box-shadow:0 4px 12px {HOT}15;
  margin-bottom:8px;
  height:160px; /* 🌟 統一所有卡片的高度，絕不凌亂 */
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:space-between;
}}
.browse-sticker img{{
  width:100%;
  height:105px; /* 🌟 限制圖片的最大顯示空間 */
  object-fit:contain; /* 保證圖片等比例縮放，絕對不變形 */
  filter:drop-shadow(0 4px 6px {HOT}25); /* 偷偷加上貼紙的立體陰影 */
}}
.browse-sticker .name{{
  font-size:11.5px;font-weight:800;color:{TEXT};
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  width:100%;margin-bottom:2px;
}}
.browse-sticker-sel{{
  border-color:{HOT}!important;
  box-shadow:0 0 0 2.5px {HOT}55,0 6px 16px {HOT}30!important;
}}

/* ── 畫布 ── */
.canvas-box{{
  background: {CREAM} !important; /* 🌟 直接使用你設定的 #FFEABB 完美奶黃色 */
  border-radius:20px;
  border:2.5px solid #F5D38A !important; /* 邊框稍微加深一點點，讓畫布更有立體感 */
  box-shadow:0 5px 24px {HOT}14,inset 0 1px 0 rgba(255,255,255,0.5);
  padding:12px 10px;
}}

/* 強制讓畫布裡的衣服底色變透明，白邊才會在黃底上跑出來 */
.canvas-box [data-testid="stVerticalBlock"],
.canvas-box [data-testid="stHorizontalBlock"],
.canvas-box [data-testid="column"] {{
  background: transparent !important;
}}
.canvas-title{{
  text-align:center;font-size:10px;font-weight:800;
  letter-spacing:2.5px;color:{MID};margin-bottom:8px;text-transform:uppercase;
}}
.canvas-col-label{{
  font-size:9.5px;font-weight:800;letter-spacing:1.2px;
  color:{BLUSH};text-align:center;margin-bottom:5px;text-transform:uppercase;
}}

/* ── 畫布貼紙（小） ── */
.mini-sticker{{
  background:transparent;border-radius:11px;border:2.5px solid transparent;
  padding:4px;text-align:center;margin-bottom:6px;
  aspect-ratio:1;display:flex;align-items:center;justify-content:center;
}}
.mini-sticker img{{
  width:100%;height:100%;object-fit:contain;border-radius:7px;display:block;
  filter:drop-shadow(0 4px 8px {HOT}30); /* 偷偷幫你的貼紙加上一點點粉色立體陰影，會更像實體貼紙喔！ */
}}
.mini-sticker-sel{{
  border-color:{HOT}!important;
  background:{HOT}15; /* 被選中時，給它一點點淡淡的粉紅底色方便辨識 */
  box-shadow:0 0 0 2.5px {HOT}55,0 4px 12px {HOT}35!important;
}}

/* ── Popover 按鈕透明 ── */
[data-testid="stPopover"]>button{{
  background:transparent!important;box-shadow:none!important;
  padding:0!important;min-height:0!important;
  width:100%!important;border-radius:11px!important;
}}

/* ── 即時預覽區 ── */
.preview-box{{
  background:linear-gradient(135deg,{CREAM} 0%,#FFE9A0 100%);
  border-radius:18px;border:2px solid {CREAM};
  padding:16px;text-align:center;margin-bottom:12px;
}}
.preview-label{{
  font-size:10px;font-weight:800;letter-spacing:1.5px;
  color:{MID};margin-bottom:10px;text-transform:uppercase;
}}
.preview-compare{{
  display:flex;gap:12px;align-items:flex-start;justify-content:center;
}}
.preview-item{{text-align:center;flex:1}}
.preview-item img{{
  width:100%;max-width:120px;border-radius:12px;
  box-shadow:0 4px 14px {HOT}20;display:block;margin:0 auto;
}}
.preview-item .plabel{{
  font-size:10px;font-weight:700;color:{MID};margin-top:5px;
}}

/* ── Cream 提示 ── */
.cream-box{{
  background:linear-gradient(135deg,{CREAM}70,{CREAM}30);
  border-radius:14px;padding:11px 14px;border:1.5px solid {CREAM};margin-bottom:10px;
}}

/* ── Empty ── */
.empty{{text-align:center;padding:36px 14px;color:{MID}}}

hr{{border-color:{BLUSH}40!important;margin:12px 0!important}}
div[data-testid="column"]{{padding:0 3px!important}}
::-webkit-scrollbar{{width:4px}}
::-webkit-scrollbar-thumb{{background:{MID};border-radius:10px}}

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# ☁️ 資料管理 (Google Drive 雲端引擎)
# ═══════════════════════════════════════════════════════
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from io import BytesIO

BASE = "my_wardrobe"
os.makedirs(BASE, exist_ok=True)
FOLDER_ID = "18DMJqPraV58GdQs-b75D0I1tL03e69RM"

@st.cache_resource
def get_drive_service():
    import json
    info = st.secrets["google_credentials"]
    
    # 🌟 翻譯魔法：加上 strict=False 讓翻譯機忽略那些隱形的排版符號！
    if isinstance(info, str):
        # 如果一般的寬容模式還是會報錯，我們就在解析前先幫它過濾掉不合法的換行
        try:
            info = json.loads(info, strict=False)
        except json.decoder.JSONDecodeError:
            # 備用清除魔法：處理複製貼上時多出來的實體換行
            clean_info = info.replace('\r\n', '\\n').replace('\n', '\\n')
            info = json.loads(clean_info, strict=False)
            
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

drive_service = get_drive_service()

def get_drive_file_id(name):
    # 🌟 修改點：加入 supportsAllDrives=True
    q = f"'{FOLDER_ID}' in parents and name='{name}' and trashed=false"
    res = drive_service.files().list(
        q=q, fields="files(id)", 
        supportsAllDrives=True, 
        includeItemsFromAllDrives=True
    ).execute()
    files = res.get('files', [])
    return files[0]['id'] if files else None

def load_json(name, default):
    fid = get_drive_file_id(name)
    if not fid: return default
    req = drive_service.files().get_media(fileId=fid)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done: _, done = downloader.next_chunk()
    try: return json.loads(fh.getvalue().decode('utf-8'))
    except: return default

def save_json(name, data):
    fid = get_drive_file_id(name)
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    media = MediaIoBaseUpload(BytesIO(json_bytes), mimetype='application/json', resumable=True)
    if fid:
        # 🌟 修改點：update 加入 supportsAllDrives
        drive_service.files().update(
            fileId=fid, media_body=media, supportsAllDrives=True
        ).execute()
    else:
        meta = {'name': name, 'parents': [FOLDER_ID]}
        # 🌟 修改點：create 加入 supportsAllDrives
        drive_service.files().create(
            body=meta, media_body=media, supportsAllDrives=True
        ).execute()

# 🌟 雲端快取機制：確保網頁秒速重載，不會一直呼叫雲端導致卡頓
def load_meta():
    if "meta_cache" not in st.session_state:
        st.session_state.meta_cache = load_json("metadata.json", {})
    return st.session_state.meta_cache

def save_meta(d):
    st.session_state.meta_cache = d
    save_json("metadata.json", d)

def load_cats():
    if "cats_cache" not in st.session_state:
        st.session_state.cats_cache = load_json("categories.json", {})
    return st.session_state.cats_cache

def save_cats(d):
    st.session_state.cats_cache = d
    save_json("categories.json", d)

def load_settings():  return {"gemini_key": st.secrets.get("gemini_key", "")}
def save_settings(d): pass # API Key 改放 Secrets，不需要存檔了

@st.cache_resource
def get_rembg_session():
    import urllib.request
    import ssl
    import shutil
    from rembg import new_session
    
    model_path = os.path.join(os.getcwd(), "isnet-general-use.onnx")
    
    if not os.path.exists(model_path):
        url = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx"
        try:
            # 🌟 破解 SSL 阻擋魔法：強制建立一個「不嚴格檢查安全憑證」的連線通道
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(url, context=ctx) as response, open(model_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            print(f"去背模型下載失敗: {e}")
            
    # 告訴 rembg 直接在這裡找模型，不要去網路抓！
    os.environ["U2NET_HOME"] = os.getcwd() 
    return new_session("isnet-general-use")

# ═══════════════════════════════════════════════════════
# 安全改名（修正 Windows 檔案鎖問題）
# ═══════════════════════════════════════════════════════
def safe_rename_folder(src: str, dst: str) -> tuple:
    if not os.path.exists(src): return False, "原始資料夾不存在"
    if os.path.exists(dst):     return False, "目標名稱已存在"
    # 先嘗試直接 rename（快速）
    for i in range(5):
        try:
            os.rename(src, dst)
            return True, ""
        except (PermissionError, OSError):
            time.sleep(0.4 * (i + 1))
    # 備用方案：複製 + 刪除
    try:
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(src):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        try: shutil.rmtree(src)
        except: pass
        return True, ""
    except Exception as e:
        return False, f"改名失敗：{e}"

# ═══════════════════════════════════════════════════════
# 圖片處理
# ═══════════════════════════════════════════════════════
def apply_border(rgba_arr: np.ndarray, ratio: int) -> Image.Image:
    """只做邊框，不重跑去背（快速）"""
    alpha = rgba_arr[:, :, 3]
    h, w  = alpha.shape
    t = max(2, int(max(h, w) * (ratio / 100.0)))
    if t > 0:
        sm = cv2.GaussianBlur(alpha, (5, 5), 0)
        r  = t; ky, kx = np.ogrid[-r:r+1, -r:r+1]
        k  = (kx**2 + ky**2 <= r**2).astype(np.uint8)
        d  = cv2.dilate(sm, k, iterations=1)
        d  = cv2.GaussianBlur(d, (3, 3), 0)
        d  = np.clip(d.astype(np.int32) * 2, 0, 255).astype(np.uint8)
    else:
        d = alpha
    bg = np.zeros_like(rgba_arr)
    bg[:, :, 0:3] = 255; bg[:, :, 3] = d
    bg[alpha > 0] = rgba_arr[alpha > 0]
    return Image.fromarray(bg.astype(np.uint8))

def fix_orientation(img: Image.Image) -> Image.Image:
    """根據 EXIF 修正照片方向"""
    try:
        exif = img._getexif()
        if exif:
            orientation = exif.get(274)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img

def remove_bg(img: Image.Image) -> np.ndarray:
    """去背，回傳 RGBA numpy array。注意：呼叫前要先 fix_orientation"""
    from rembg import remove   # 延遲載入
    session = get_rembg_session() 
    no_bg = remove(img, session=session)
    return np.array(no_bg.convert("RGBA"))

def shrink_for_speed(img: Image.Image, max_side: int = 1024) -> Image.Image:
    """如果圖片過大則等比例縮小，加速去背處理"""
    w, h = img.size
    if max(w, h) <= max_side:
        return img
    if w >= h:
        new_w = max_side
        new_h = int(h * max_side / w)
    else:
        new_h = max_side
        new_w = int(w * max_side / h)
    return img.resize((new_w, new_h), Image.LANCZOS)

def to_b64(img: Image.Image, size: int = None) -> str:
    # 🌟 智能縮圖魔法：如果有指定尺寸，就先縮小再轉碼，大幅減少瀏覽器負擔！
    if size:
        img.thumbnail((size, size), Image.LANCZOS)
    buf = BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# 🌟 雲端圖片引擎：從 Google Drive 讀取、上傳與刪除
def load_img_b64(fname: str, size: int = 300) -> str:
    fname = os.path.basename(fname) # 防呆：如果傳進來的是路徑，只取檔名
    if "img_cache" not in st.session_state: st.session_state.img_cache = {}
    if fname in st.session_state.img_cache: return st.session_state.img_cache[fname]
    
    fid = get_drive_file_id(fname)
    if not fid: return ""
    
    req = drive_service.files().get_media(fileId=fid)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done: _, done = downloader.next_chunk()
    
    try:
        img = Image.open(fh)
        b64 = to_b64(img, size)
        st.session_state.img_cache[fname] = b64
        return b64
    except: return ""

def upload_img_to_drive(img: Image.Image, fname: str):
    buf = BytesIO()
    img.save(buf, format="PNG")
    media = MediaIoBaseUpload(BytesIO(buf.getvalue()), mimetype='image/png', resumable=True)
    meta = {'name': fname, 'parents': [FOLDER_ID]}
    # 🌟 修改點：create 加入 supportsAllDrives
    drive_service.files().create(
        body=meta, media_body=media, supportsAllDrives=True
    ).execute()
    if "img_cache" not in st.session_state: st.session_state.img_cache = {}
    st.session_state.img_cache[fname] = to_b64(img, 300)

def delete_img_from_drive(fname: str):
    fid = get_drive_file_id(fname)
    if fid: 
        # 🌟 修改點：update 加入 supportsAllDrives
        drive_service.files().update(
            fileId=fid, body={'trashed': True}, supportsAllDrives=True
        ).execute()
    if "img_cache" in st.session_state and fname in st.session_state.img_cache:
        del st.session_state.img_cache[fname]

# ═══════════════════════════════════════════════════════
# Gemini AI 推薦
# ═══════════════════════════════════════════════════════
def get_gemini_recommendation(api_key, selected_item, wardrobe_items, season, occasions):
    try:
        # 🌟 核心修正：將版本改回 v1beta，這是目前 1.5 免費版最穩定的通道
        client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1beta'}
        )
        
        if not wardrobe_items:
            return {"_error": "衣櫃裡目前沒有符合條件的衣物，請先上傳衣服喔！"}

        occ_str = "、".join(occasions) if occasions else "不限"
        items_desc = "".join(f"- {it['category']}: {it['name']} ({it['fname']})\n" for it in wardrobe_items)
        
        prompt = f"妳是專業造型師，請從以下衣櫥清單推薦搭配：{items_desc}。只回傳 JSON。"

        # 🌟 核心修正：使用 gemini-1.5-flash
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=prompt
        )
        
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return {"_error": f"AI 通訊失敗 (v2026)：{str(e)}"}

# ═══════════════════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════════════════
for k, v in [
    ("page",          "wardrobe"),
    ("sel_item",      None),
    ("sel_cat", "✨ 全部衣物"),
    ("recs",          {}),
    ("editing_cat",   None),
    ("filter_season", "四季皆宜"),
    ("filter_occ",    []),
    ("filter_color",  "全部顏色"),
    ("browse_open",   True),
    # 製作貼紙相關
    ("nobg_arr",      None),   # 去背後的 numpy array（快取）
    ("border_ratio",  3),      # 預設推薦值 3
    ("upload_step",   "upload"), # upload → preview → done
]:
    if k not in st.session_state:
        st.session_state[k] = v

if "toast_msg" in st.session_state:
    st.toast(st.session_state.pop("toast_msg"), icon="🎀")

# ═══════════════════════════════════════════════════════
# 標題 + 導覽列
# ═══════════════════════════════════════════════════════
# 🌟 終極排版魔法：強制解除手機版堆疊，並加入「完美比例防爆框」設定！
NAV = [("👗","wardrobe","衣櫃"), ("✨","upload","製作"),
       ("📦","closet","管理"),   ("⚙️","settings","設定")]

# 🌟 切換頁面時清除暫存 state，避免殘影 + 加速
def switch_page(new_pid):
    """切換頁面"""
    st.session_state.page = new_pid
    st.session_state.editing_cat = None
    st.session_state.editing_item = None

# 2x2 排版
row1_cols = st.columns(2)
row2_cols = st.columns(2)
all_cols = row1_cols + row2_cols
for col, (icon, pid, label) in zip(all_cols, NAV):
    with col:
        if st.session_state.page == pid:
            st.markdown(f'<div class="nav-active" style="margin-bottom:12px">{icon}<br>{label}</div>', unsafe_allow_html=True)
        else:
            # 🌟 絲滑切換魔法：使用 on_click 讓程式在背景瞬間切換好，不再需要強制 st.rerun()！
            st.button(f"{icon}\n{label}", key=f"nav_{pid}", use_container_width=True, on_click=switch_page, args=(pid,))

st.markdown(f"""<div style="height:4px;
  background:linear-gradient(90deg,{HOT} 0%,{MID} 33%,{BLUSH} 66%,{CREAM} 100%);
  border-radius:3px;margin:2px 0 14px"></div>""", unsafe_allow_html=True)
page = st.session_state.page

# ═══════════════════════════════════════════════════════
# PAGE 1 ── 衣櫃瀏覽 + 穿搭畫布
# ═══════════════════════════════════════════════════════
if page == "wardrobe":
    cats      = load_cats()
    meta      = load_meta()
    cat_names = sorted(cats.keys())

    if not cat_names:
        st.markdown(f"""<div class="empty">
          <div style="font-size:44px">👗</div>
          <div style="font-weight:800;font-size:16px;color:{TEXT};margin-top:10px">衣櫥是空的！</div>
          <div style="color:{MID};margin-top:6px;font-size:12px">
            先到「設定」新增類別，再去「製作」上傳衣服 🌸
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        # 🌟 修正防呆機制：把「✨ 全部衣物」加入合法清單中，如果不合法就預設回「全部衣物」
        if st.session_state.sel_cat not in ["✨ 全部衣物"] + cat_names:
            st.session_state.sel_cat = "✨ 全部衣物"

        sel = st.session_state.sel_item

        # ── 篩選條件（摺疊） ──────────────────────────
        # 🌟 邏輯：如果 sel 為 None (沒選衣服)，expanded 就為 True (展開)；反之則自動摺疊。
        with st.expander("🔍 篩選條件（季節／場合／顏色）", expanded=(sel is None)):
            # ⛅ 季節篩選
            st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:0 0 4px">⛅ 季節</div>', unsafe_allow_html=True)
            # 🌟 修正：直接使用 SEASONS，不再額外加上 ["四季皆宜"] 以免重複
            fs = st.selectbox("季節", SEASONS, key="fs",
                index=SEASONS.index(st.session_state.filter_season)
                if st.session_state.filter_season in SEASONS else 0,
                label_visibility="collapsed")
            st.session_state.filter_season = fs

            # 🎨 顏色篩選 (支援多選模式)
            st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:8px 0 4px">🎨 顏色</div>', unsafe_allow_html=True)
            m_temp = load_meta()
            used_colors = sorted(list(set(v.get("color") for v in m_temp.values() if v.get("color"))))
            
            # 🌟 防呆魔法：如果舊的設定還是文字（例如"全部顏色"），先把它轉換成空的列表
            if not isinstance(st.session_state.filter_color, list):
                st.session_state.filter_color = []
                
            fc = st.multiselect("顏色", used_colors, key="fc",
                default=[c for c in st.session_state.filter_color if c in used_colors],
                placeholder="選擇顏色（不選代表全部）",
                label_visibility="collapsed")
            st.session_state.filter_color = fc

            # 📍 場合篩選
            st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:8px 0 4px">📍 場合</div>', unsafe_allow_html=True)
            fo = st.multiselect("場合", OCCASIONS, default=st.session_state.filter_occ,
                placeholder="選擇場合（不選代表全部）", label_visibility="collapsed")
            st.session_state.filter_occ = fo

        # ── 穿搭畫布 ──────────────────────────────────
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        
        # 🌟 建立專屬容器，把畫布的元素打包在一起，就不會跟上面的瀏覽區混在一起了！
        with st.container():
            st.markdown('<span id="my-canvas-box"></span>', unsafe_allow_html=True)
            st.markdown(f"""<style>
              /* 1. 精準鎖定包含標記的畫布容器，塗上奶黃色 */
              div[data-testid="stVerticalBlock"]:has(> div.element-container #my-canvas-box) {{
                background: {CREAM} !important;
                border-radius:20px!important;
                border:2.5px solid #F5D38A !important;
                box-shadow:0 5px 24px {HOT}14!important;
                padding:22px 14px 14px 14px!important;
              }}
              /* 2. 強制讓畫布裡面的粉色背景變透明！ */
              div[data-testid="stVerticalBlock"]:has(> div.element-container #my-canvas-box) [data-testid="stVerticalBlock"],
              div[data-testid="stVerticalBlock"]:has(> div.element-container #my-canvas-box) [data-testid="stHorizontalBlock"],
              div[data-testid="stVerticalBlock"]:has(> div.element-container #my-canvas-box) [data-testid="column"] {{
                background: transparent !important;
                box-shadow: none !important;
                border: none !important;
              }}
            </style>""", unsafe_allow_html=True)
            
            st.markdown(f'<div style="text-align:center;font-size:10px;font-weight:800;letter-spacing:2.5px;color:{MID};margin:0 0 8px;text-transform:uppercase">✦ 今日穿搭畫布 ✦</div>', unsafe_allow_html=True)
            
            # 預先載入 settings 和 has_key（不管有沒有選衣服都需要）
            settings = load_settings()
            has_key  = bool(settings.get("gemini_key", "").strip())

            # 如果有選衣服，先取出 s_cat / s_fname / s_info
            if sel is not None:
                s_cat, s_fname = sel
                s_info = meta.get(s_fname, {})
            else:
                s_cat, s_fname, s_info = None, None, {}

            # AI 推薦按鈕（🌟 修正：按鈕解封印！現在隨時都會出現囉！）
            if not st.session_state.recs:
                if has_key:
                    # 先準備好必要的變數
                    has_season = st.session_state.filter_season != "四季皆宜"
                    has_occ    = bool(st.session_state.filter_occ)
                    sel_exists = (sel is not None)

                    # 🌟 這裡直接放按鈕，不再攔截它！
                    if st.button("✨ AI 幫我搭配整套造型！", key="do_rec", use_container_width=True):
                        wlist = []
                        exclude_cat = s_cat if sel_exists else None
                        for cat_n in cat_names:
                            if cat_n == exclude_cat: continue
                            cp = os.path.join(BASE, cat_n)
                            if not os.path.exists(cp):
                                continue
                            
                            for fn in os.listdir(cp):
                                if not fn.endswith(".png"): continue
                                m = meta.get(fn, {})
                                
                                # ⛅ 季節篩選
                                if st.session_state.filter_season != "四季皆宜":
                                    if m.get("season","") not in (st.session_state.filter_season,"四季皆宜"):
                                        continue
                                        
                                # 📍 場合篩選
                                if st.session_state.filter_occ:
                                    if not any(o in m.get("occasions",[]) for o in st.session_state.filter_occ):
                                        continue
                                        
                                # 🎨 顏色篩選 (支援多選)
                                if st.session_state.filter_color:
                                    if m.get("color", "") not in st.session_state.filter_color:
                                        continue
                                        
                                # 📦 打包裝箱給 AI
                                wlist.append({
                                    "fname": fn,
                                    "category": cat_n,
                                    "name": m.get("name", fn),
                                    "season": m.get("season", ""),
                                    "occasions": m.get("occasions", []),
                                    "color": m.get("color", "") 
                                })

                        # 🌟 核心防呆：如果經過上面的篩選後衣櫃是空的，就在這裡攔截！
                        if not wlist:
                            st.warning("🧐 哎呀！衣櫃裡目前沒有符合條件的衣物，AI 沒辦法幫你搭配喔！")
                        else:
                            if sel_exists:
                                selected_for_ai = {**s_info, "category": s_cat}
                            else:
                                selected_for_ai = {"name": "（未指定，請完整推薦）", "category": "未指定",
                                                   "season": st.session_state.filter_season,
                                                   "occasions": st.session_state.filter_occ,
                                                   "color": st.session_state.filter_color}

                            with st.spinner("✨ AI 分析搭配中..."):
                                result = get_gemini_recommendation(
                                    settings["gemini_key"],
                                    selected_for_ai,
                                    wlist,
                                    st.session_state.filter_season,
                                    st.session_state.filter_occ)
                            if "_error" in result:
                                st.error(f"AI 推薦失敗：{result['_error']}")
                            else:
                                st.session_state.recs = result
                                st.rerun()
                else:
                    st.markdown(f"""<div class="cream-box">
                      <div style="font-size:12px;font-weight:800;color:#8B6914">⚠️ 尚未設定 Gemini API Key</div>
                      <div style="font-size:11px;color:#8B6914;margin-top:3px">請到「設定」頁面填入 API Key</div>
                    </div>""", unsafe_allow_html=True)

            # ── 🌟 核心修復：顯示畫布內容或提示 ──
            if sel is None and not st.session_state.recs:
                # 情況 A：沒選衣服也沒 AI 推薦 -> 顯示引導手勢
                st.markdown(f"""<div class="empty" style="padding:38px 14px">
                  <div style="font-size:38px">👆</div>
                  <div style="font-weight:800;color:{TEXT};font-size:14px;margin-top:10px">請先選一件衣服或選擇季節/場合</div>
                  <div style="color:{MID};font-size:11px;margin-top:4px">讓 AI 幫你搭配完整造型！</div>
                </div>""", unsafe_allow_html=True)
            
            elif st.session_state.recs == {} and sel is None:
                # 情況 B：AI 跑完了但沒找到任何適合的衣服
                st.warning("🧐 AI 努力找過了，但目前衣櫃裡沒有適合當前條件的搭配。")
            
            else:
                # 情況 C：有選衣服或有 AI 推薦 -> 建立畫布資料
                left_rows  = {1:[], 2:[], 3:[]}
                right_rows = {1:[], 2:[], 3:[]}

                # 1. 放入妳親自選的那件衣服
                if sel is not None:
                    s_cat, s_fname = sel
                    s_info = meta.get(s_fname, {})
                    s_col = cats.get(s_cat, {}).get("col", "L")
                    s_lvl = cats.get(s_cat, {}).get("level", 2)
                    s_b64 = load_img_b64(os.path.join(BASE, s_cat, s_fname))
                    if s_b64:
                        entry = {"fname":s_fname, "name":s_info.get("name",s_fname[:12]),
                                 "reason":"","b64":s_b64, "is_selected":True, "cat":s_cat}
                        (left_rows if s_col=="L" else right_rows)[s_lvl].append(entry)

                # 2. 處理 AI 推薦的衣服（加強解析邏輯）
                if st.session_state.recs and "_error" not in st.session_state.recs:
                    for cat_n, rec_data in st.session_state.recs.items():
                        # 🌟 核心修正：自動偵測並取出正確的字典格式
                        rec = None
                        if isinstance(rec_data, list) and len(rec_data) > 0:
                            rec = rec_data[0]
                        elif isinstance(rec_data, dict):
                            rec = rec_data
                        
                        if not rec or not isinstance(rec, dict):
                            continue

                        fn = rec.get("fname", "")
                        # 🌟 核心修正：如果 AI 回傳的檔名不含 .png，幫它補上
                        if fn and not fn.lower().endswith(".png"):
                            fn += ".png"
                            
                        fp = os.path.join(BASE, cat_n, fn)
                        
                        # 檢查檔案是否存在，並載入
                        if os.path.exists(fp):
                            b64 = load_img_b64(fp)
                            if b64:
                                col_ = cats.get(cat_n,{}).get("col","L")
                                lvl_ = cats.get(cat_n,{}).get("level",2)
                                e = {"fname":fn, "name":meta.get(fn,{}).get("name",fn[:12]),
                                     "reason":rec.get("reason",""), "b64":b64,
                                     "is_selected":False, "cat":cat_n}
                                (left_rows if col_=="L" else right_rows)[lvl_].append(e)

                # 3. 渲染兩欄畫布 UI
                # 🌟 核心修正：先檢查是否有衣服可以顯示
                has_any_left = any(left_rows.values())
                has_any_right = any(right_rows.values())

                if not has_any_left and not has_any_right:
                    # 情況 A：真的沒衣服可以顯示
                    st.info("✨ AI 已經看過你的衣櫃了，但目前的篩選條件下（季節/場合）沒有建議的搭配。可以試試將篩選條件調鬆一點喔！")
                else:
                    # 情況 B：有衣服，這時才定義 lc, rc 並開始畫畫
                    lc, rc = st.columns(2, gap="small")
                    for col_obj, rows_dict, col_label in [
                        (lc, left_rows, "👗 主要衣物"), 
                        (rc, right_rows, "👒 配件")
                    ]:
                        with col_obj:
                            st.markdown(f'<div class="canvas-col-label">{col_label}</div>', unsafe_allow_html=True)
                            for lvl in [1, 2, 3]:
                                items = rows_dict[lvl]
                                if not items: continue
                                
                                # 🌟 修正後的畫布渲染部分
                                sub_cols = st.columns(len(items))
                                for sc, e in zip(sub_cols, items):
                                    with sc:
                                        # 🌟 加入智能縮放邏輯
                                        check_str = e['cat'] + e['name']
                                        if any(k in check_str for k in ["洋裝", "連身", "長褲", "西裝褲", "褲", "大衣", "全身", "長裙"]):
                                            img_scale = "100%" # 衣服類佔滿
                                        elif any(k in check_str for k in ["帽", "鞋", "包", "飾", "配件", "襪", "項鍊", "耳環", "貝雷帽"]):
                                            img_scale = "50%"  # 配件類縮小到 50%
                                        else:
                                            img_scale = "80%"  # 其他中間比例

                                        with st.popover("", use_container_width=True):
                                            st.markdown(f"**{e['name']}**")
                                            # ... 原本的內容保持不變 ...
                                        
                                        sel_border = f"border:2.5px solid {HOT};" if e['is_selected'] else ""
                                        # 🌟 在 img 標籤加入 max-height 與 width 限制
                                        st.markdown(f"""
                                        <div class="mini-sticker" style="{sel_border}">
                                          <img src="data:image/png;base64,{e['b64']}" 
                                               style="width:{img_scale}; height:auto; margin:auto;"/>
                                        </div>""", unsafe_allow_html=True)

                # 重新推薦按鈕
                if st.session_state.recs and "_error" not in st.session_state.recs:
                    if st.button("🔄 重新推薦", key="redo_rec", use_container_width=True):
                        st.session_state.recs = {}
                        st.rerun()
                        
        # ── 瀏覽區 ──────────────────────────────────
        if sel is not None and not st.session_state.browse_open:
            # 已選衣物→顯示小 chip + 更換按鈕
            s_cat, s_fname = sel
            s_info = meta.get(s_fname, {})
            s_b64  = load_img_b64(os.path.join(BASE, s_cat, s_fname))
            ca, cb = st.columns([3, 1])
            with ca:
                st.markdown(f"""
                <div class="sel-chip">
                  <img src="data:image/png;base64,{s_b64}"/>
                  <div class="info">
                    <div class="name">✓ {s_info.get('name', s_fname[:14])}</div>
                    <div class="tags">
                      <span class="badge b-hot">{s_info.get('season','')}</span>
                      <span class="badge b-mid">{s_cat}</span>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
            with cb:
                if st.button("🔄\n更換", key="change_item", use_container_width=True):
                    st.session_state.browse_open = True
                    st.session_state.sel_item    = None
                    st.session_state.recs        = {}
                    st.rerun()
        else:
            # 展開瀏覽區
            st.markdown('<div class="sec-title">🚪 選擇一件衣服</div>', unsafe_allow_html=True)
            
            # 🌟 1. 建立包含「全部」的選單列表，並將「全部」放在第一個
            display_cats = ["✨ 全部衣物"] + cat_names
            
            # 如果是剛啟動或找不到類別，預設選「全部衣物」
            if st.session_state.sel_cat not in display_cats:
                st.session_state.sel_cat = "✨ 全部衣物"

            st.session_state.sel_cat = st.selectbox(
                "類別", display_cats,
                index=display_cats.index(st.session_state.sel_cat),
                key="cat_picker", label_visibility="collapsed")

            act_cat = st.session_state.sel_cat

            # 🌟 2. 獲取檔案清單（優化：建立 (類別, 檔名) 的配對清單）
            files_to_show = []
            if act_cat == "✨ 全部衣物":
                # 選全部時，掃描所有分類資料夾
                for c in cat_names:
                    c_path = os.path.join(BASE, c)
                    if os.path.exists(c_path):
                        for f in os.listdir(c_path):
                            if f.endswith(".png"):
                                files_to_show.append((c, f))
            else:
                # 選單一分類時，只掃描該資料夾
                c_path = os.path.join(BASE, act_cat)
                if os.path.exists(c_path):
                    for f in os.listdir(c_path):
                        if f.endswith(".png"):
                            files_to_show.append((act_cat, f))
            
            # 按檔案名稱排序（新產生的 item_... 檔名會排在前面）
            files_to_show.sort(key=lambda x: x[1], reverse=True)

            if not files_to_show:
                st.markdown(f"""<div class="empty" style="padding:20px 10px">
                  <div style="font-size:30px">🌸</div>
                  <div style="font-weight:800;color:{MID};font-size:13px;margin-top:5px">目前沒有任何衣物</div>
                </div>""", unsafe_allow_html=True)
            else:
                # 🌟 3. 渲染圖片
                rows = [files_to_show[i:i+2] for i in range(0, len(files_to_show), 2)]
                for row in rows:
                    c1, c2 = st.columns(2)
                    for col_obj, (f_cat, fname) in zip([c1, c2], row):
                        fp    = os.path.join(BASE, f_cat, fname)
                        info  = meta.get(fname, {})
                        is_sel= sel == (f_cat, fname)
                        
                        # 🌟 終極版縮放魔法：同時檢查「分類名稱」與「衣服名稱」，確保長褲跟帽子比例完美！
                        check_str = f_cat + info.get('name', '') 
                        if any(k in check_str for k in ["洋裝", "連身", "長褲", "西裝褲", "褲", "大衣", "全身", "長裙"]):
                            img_scale = "105px"
                        elif any(k in check_str for k in ["帽", "鞋", "包", "飾", "配件", "襪", "項鍊", "耳環", "貝雷帽"]):
                            img_scale = "40px"
                        else:
                            img_scale = "80px"

                        with col_obj:
                            b64 = load_img_b64(fp)
                            st.markdown(f"""
                            <div class="browse-sticker {'browse-sticker-sel' if is_sel else ''}">
                              <img src="data:image/png;base64,{b64}" style="max-height:{img_scale}; height:100%; margin:auto 0;"/>
                              <div class="name">{info.get('name', fname[:14])}</div>
                            </div>""", unsafe_allow_html=True)
                            if st.button("✓ 已選" if is_sel else "選這件 🎀",
                                         key=f"pk_{f_cat}_{fname}", use_container_width=True):
                                if is_sel:
                                    st.session_state.sel_item    = None
                                    st.session_state.recs        = {}
                                    st.session_state.browse_open = True
                                else:
                                    st.session_state.sel_item    = (f_cat, fname)
                                    st.session_state.recs        = {}
                                    st.session_state.browse_open = False
                                st.rerun()        
                        
# ═══════════════════════════════════════════════════════
# PAGE 2 ── 製作貼紙（簡化版：上傳 → 去背 → 填資訊 → 儲存）
# ═══════════════════════════════════════════════════════
elif page == "upload":
    cats      = load_cats()
    cat_names = sorted(cats.keys())

    if not cat_names:
        st.warning("請先到「設定」新增類別！")
    else:
        step = st.session_state.upload_step

        # ── STEP 1：上傳照片 → 裁切 → 去背 ──
        if step == "upload":
            st.markdown('<div class="sec-title">📸 上傳衣服照片</div>', unsafe_allow_html=True)

            # 如果有上傳的照片暫存，就不顯示上傳框
            uploaded = None
            if "saved_img_id" not in st.session_state:
                uploaded = st.file_uploader("上傳衣服照片", type=["jpg","jpeg","png"], label_visibility="collapsed", key="up_file")
            
            # 處理新上傳
            if uploaded is not None:
                from PIL import ImageOps
                # 🌟 核心修復：強制把圖片先讀進獨立的記憶體，防止 Streamlit 過河拆橋！
                bytes_data = uploaded.getvalue()
                img = Image.open(BytesIO(bytes_data))
                img.load() # 強制解碼，徹底斷開與上傳元件的連結
            
                raw_img = ImageOps.exif_transpose(img)
                st.session_state.orig_img = raw_img
                st.session_state.crop_input = shrink_for_speed(raw_img, 500)
                st.session_state.saved_img_id = uploaded.file_id
                st.session_state["crop_pts"] = []
                st.rerun()
            
            # 如果有暫存照片，顯示裁切介面
            if "saved_img_id" in st.session_state:
                from PIL import ImageDraw
                from streamlit_image_coordinates import streamlit_image_coordinates
                
                orig_img   = st.session_state.orig_img
                crop_input = st.session_state.crop_input
                
                # 重新上傳按鈕（放最上面）
                if st.button("🔄 重新上傳照片", key="reupload", use_container_width=True):
                    for k in ["saved_img_id", "orig_img", "crop_input", "crop_pts"]:
                        if k in st.session_state: del st.session_state[k]
                    st.rerun()
                
                use_crop = st.checkbox("✂️ 使用裁切框", value=True, key="use_crop")
                
                if use_crop:
                    st.markdown(f'<div style="color:{MID};font-size:13px;font-weight:900;margin:4px 0 6px">✂️ 在照片上點兩下：第一下=左上角，第二下=右下角</div>', unsafe_allow_html=True)
                    
                    if "crop_pts" not in st.session_state:
                        st.session_state["crop_pts"] = []
                    pts = st.session_state["crop_pts"]
                    
                    # 畫已點的標記和矩形
                    preview = crop_input.copy()
                    draw = ImageDraw.Draw(preview)
                    for p in pts:
                        x, y = p['x'], p['y']
                        draw.ellipse([x-8, y-8, x+8, y+8], outline='#FE81D4', width=3)
                        draw.line([x-12, y, x+12, y], fill='#FE81D4', width=2)
                        draw.line([x, y-12, x, y+12], fill='#FE81D4', width=2)
                    if len(pts) == 2:
                        x1, y1 = pts[0]['x'], pts[0]['y']
                        x2, y2 = pts[1]['x'], pts[1]['y']
                        l, t = min(x1, x2), min(y1, y2)
                        r, b = max(x1, x2), max(y1, y2)
                        draw.rectangle([l, t, r, b], outline='#FE81D4', width=4)
                    
                    # 顯示可點擊的圖片（固定寬度避免座標誤差）
                    DISPLAY_W = 380
                    iw, ih = preview.size
                    DISPLAY_H = int(ih * DISPLAY_W / iw)
                    
                    coords = streamlit_image_coordinates(
                        preview,
                        key="img_coords_main",
                        width=DISPLAY_W,
                        height=DISPLAY_H,
                    )
                    
                    if coords is not None:
                        scale_x = iw / DISPLAY_W
                        scale_y = ih / DISPLAY_H
                        new_pt = {'x': int(coords['x'] * scale_x), 'y': int(coords['y'] * scale_y)}
                        if not pts or pts[-1] != new_pt:
                            if len(pts) >= 2:
                                st.session_state["crop_pts"] = [new_pt]
                            else:
                                st.session_state["crop_pts"].append(new_pt)
                            st.rerun()
                    
                    # 狀態提示 + 重設按鈕
                    if len(pts) == 0:
                        st.info("👆 請點第 1 下：標記裁切框的**左上角**")
                        final_img = crop_input
                    elif len(pts) == 1:
                        st.info("👆 請點第 2 下：標記裁切框的**右下角**")
                        final_img = crop_input
                    else:
                        col_a, col_b = st.columns([2, 1])
                        with col_a:
                            st.success(f"✅ 已選範圍 {abs(pts[1]['x']-pts[0]['x'])}×{abs(pts[1]['y']-pts[0]['y'])}")
                        with col_b:
                            if st.button("🔄 重新選", key="reset_crop", use_container_width=True):
                                st.session_state["crop_pts"] = []
                                st.rerun()
                        x1, y1 = pts[0]['x'], pts[0]['y']
                        x2, y2 = pts[1]['x'], pts[1]['y']
                        l, t = min(x1, x2), min(y1, y2)
                        r, b = max(x1, x2), max(y1, y2)
                        final_img = crop_input.crop((l, t, r, b))
                else:
                    st.image(orig_img, use_container_width=True)
                    final_img = orig_img
                
                if st.button("✨ 確定並執行 AI 去背！", use_container_width=True):
                    with st.spinner("✨ AI 魔法去背中，請稍候..."):
                        small_img = shrink_for_speed(final_img, 1024)
                        arr = remove_bg(small_img)
                        sticker = apply_border(arr, 3)
                    buf = BytesIO()
                    sticker.save(buf, format="PNG")
                    st.session_state.sticker_bytes = buf.getvalue()
                    st.session_state.upload_step   = "info"
                    # 清掉裁切相關暫存
                    for k in ["saved_img_id", "orig_img", "crop_input", "crop_pts"]:
                        if k in st.session_state: del st.session_state[k]
                    st.rerun()

        # ── STEP 2：填寫衣物資訊 ──
        elif step == "info":
            sticker_bytes = st.session_state.get("sticker_bytes", None)
            if not sticker_bytes:
                st.warning("⚠️ 找不到貼紙資料，請重新上傳")
                if st.button("← 重新上傳", key="back_upload", use_container_width=True):
                    st.session_state.upload_step = "upload"
                    st.rerun()
            else:
                # 顯示去背後的貼紙（黃色底）
                sticker_img = Image.open(BytesIO(sticker_bytes))
                bg = Image.new("RGBA", sticker_img.size, (255, 234, 187, 255))
                bg.paste(sticker_img, mask=sticker_img.split()[3])
                preview_b64 = to_b64(bg.convert("RGB"))

                st.markdown('<div class="sec-title">✨ 去背完成！填寫衣物資訊</div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{CREAM},{CREAM}90);
                            border-radius:18px;border:2px solid {CREAM};
                            padding:18px;text-align:center;margin-bottom:14px">
                  <img src="data:image/png;base64,{preview_b64}"
                    style="max-width:180px;width:100%;border-radius:14px;
                           box-shadow:0 4px 14px rgba(0,0,0,0.1);display:block;margin:0 auto"/>
                  <div style="font-size:11px;font-weight:800;color:#8B6914;margin-top:8px">
                    🎉 你的貼紙
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # 🌟 動態獲取已經存過的自訂顏色，讓選單自動變聰明！
                m_temp = load_meta()
                custom_colors = []
                for k, v in m_temp.items():
                    c = v.get("color")
                    if c and c not in COLORS and c not in custom_colors:
                        custom_colors.append(c)
                all_colors = COLORS + custom_colors + ["➕ 自訂新顏色..."]

                # 🌟 表單：標籤位置優化版（說明文字移到上方）
                
                # 👗 衣物名稱
                st.markdown(f'<div style="font-size:11px;font-weight:700;color:{MID};margin:10px 0 4px">👗 衣物名稱</div>', unsafe_allow_html=True)
                item_name = st.text_input("衣物名稱", placeholder="例如：粉色針織衫", label_visibility="collapsed")

                # 📁 分類
                st.markdown(f'<div style="font-size:11px;font-weight:700;color:{MID};margin:10px 0 4px">📁 分類</div>', unsafe_allow_html=True)
                sel_cat = st.selectbox("分類", cat_names, label_visibility="collapsed")

                # ⛅ 季節
                st.markdown(f'<div style="font-size:11px;font-weight:700;color:{MID};margin:10px 0 4px">⛅ 季節</div>', unsafe_allow_html=True)
                sel_season = st.selectbox("季節", SEASONS, label_visibility="collapsed")

                # 🎨 顏色
                st.markdown(f'<div style="font-size:11px;font-weight:700;color:{MID};margin:10px 0 4px">🎨 顏色</div>', unsafe_allow_html=True)
                sel_color_choice = st.selectbox("顏色", all_colors, label_visibility="collapsed")
                
                # 如果選擇自訂顏色
                if sel_color_choice == "➕ 自訂新顏色...":
                    st.markdown(f'<div style="font-size:11px;font-weight:800;color:{HOT};margin:8px 0 4px">✨ 請輸入新顏色（儲存後會永久記住！）</div>', unsafe_allow_html=True)
                    sel_color = st.text_input("輸入新顏色", placeholder="例如：酒紅色、莫蘭迪藍...", label_visibility="collapsed")
                else:
                    sel_color = sel_color_choice

                # 📍 場合
                st.markdown(f'<div style="font-size:11px;font-weight:700;color:{MID};margin:10px 0 4px">📍 場合</div>', unsafe_allow_html=True)
                sel_occs = st.multiselect("場合", OCCASIONS,
                                          placeholder="選擇場合（不選代表全部）", # 🌟 貼心提示改為不選代表全部
                                          label_visibility="collapsed")

                col_back, col_save = st.columns([1, 2])
                with col_back:
                    if st.button("← 重新上傳", key="back_to_upload", use_container_width=True):
                        st.session_state.upload_step = "upload"
                        st.session_state.sticker_bytes = None
                        st.rerun()
                with col_save:
                    if st.button("🎀 儲存到衣櫥！", key="save_sticker", use_container_width=True):
                        if not item_name:
                            st.error("請填寫衣物名稱！")
                        elif not sel_color: # 🌟 防呆：確保有選顏色或輸入自訂顏色
                            st.error("請選擇或輸入衣物顏色！")
                        # 🌟 這裡移除了原本「請至少選擇一個場合」的錯誤警告！
                        else:
                            # 🌟 魔法判定：如果 sel_occs 是空的，就直接幫它填入所有 OCCASIONS！
                            final_occs = sel_occs if sel_occs else OCCASIONS
                            
                            fname = f"item_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            fpath = os.path.join(BASE, sel_cat, fname)
                            
                            # 🌟 雲端魔法：直接上傳到 Google Drive
                            upload_img_to_drive(sticker_img, fname)
                            m = load_meta()
                            # 🌟 寫入 metadata
                            m[fname] = {
                                "name": item_name, 
                                "category": sel_cat,
                                "season": sel_season, 
                                "color": sel_color, 
                                "occasions": final_occs # 🌟 存入我們剛剛判定好的場合
                            }
                            save_meta(m)
                            st.session_state.upload_step    = "done"
                            st.session_state.last_saved_b64 = preview_b64
                            st.session_state.last_saved_cat = sel_cat
                            st.rerun()

        # ── STEP 3：完成 ──
        elif step == "done":
            b64_done = st.session_state.get("last_saved_b64", "")
            cat_done = st.session_state.get("last_saved_cat", "")
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{HOT}15,{CREAM}30);
                        border-radius:20px;padding:24px 16px;text-align:center;
                        border:2px solid {HOT}30;margin-bottom:14px">
              <div style="font-size:32px">🎉</div>
              <div style="font-weight:900;color:{TEXT};font-size:16px;margin-top:8px">貼紙製作完成！</div>
              <div style="color:{MID};font-size:12px;margin-top:4px">已存入「{cat_done}」</div>
              {f'<img src="data:image/png;base64,{b64_done}" style="max-width:160px;width:60%;border-radius:14px;margin-top:14px;box-shadow:0 4px 14px rgba(0,0,0,0.1)"/>' if b64_done else ''}
            </div>
            """, unsafe_allow_html=True)
            if st.button("✨ 繼續製作下一件", use_container_width=True):
                st.session_state.upload_step    = "upload"
                st.session_state.sticker_bytes  = None
                st.session_state.last_saved_b64 = ""
                st.rerun()

# PAGE 3 ── 衣物管理
# ═══════════════════════════════════════════════════════
elif page == "closet":
    cats      = load_cats()
    cat_names = sorted(cats.keys())

    # 初始化編輯狀態
    if "editing_item" not in st.session_state:
        st.session_state.editing_item = None  # 目前編輯中的 fname

    if not cat_names:
        st.info("還沒有類別，先到「設定」新增！")
    else:
        meta = load_meta()
        
        # 🌟 1. 加入「全部衣物」選項並設定預設
        display_cats = ["✨ 全部衣物"] + cat_names
        view_cat = st.selectbox("選擇類別", display_cats, key="vc", label_visibility="collapsed")
        
        # 🌟 2. 獲取檔案清單（修正縮排與變數名稱）
        files_to_show = []
        meta = load_meta() 
        
        # 準備篩選條件
        f_season = st.session_state.filter_season
        f_color  = st.session_state.filter_color
        f_occs   = st.session_state.filter_occ

        # 取得原始清單
        raw_files = []
        if view_cat == "✨ 全部衣物":
            for c in cat_names:
                c_path = os.path.join(BASE, c)
                if os.path.exists(c_path):
                    for f in os.listdir(c_path):
                        if f.endswith(".png"): raw_files.append((c, f))
        else:
            c_path = os.path.join(BASE, view_cat)
            if os.path.exists(c_path):
                for f in os.listdir(c_path):
                    if f.endswith(".png"): raw_files.append((view_cat, f))

        # 進行深度過濾
        for f_cat, fname in raw_files:
            info = meta.get(fname, {})
            
            # ⛅ 季節過濾
            if f_season != "四季皆宜":
                if info.get("season", "") not in [f_season, "四季皆宜"]:
                    continue
            
            # 🎨 顏色過濾 (支援多選)
            if f_color: # 如果清單不是空的（代表有選顏色）
                item_color = info.get("color", "")
                if item_color not in f_color:
                    continue
            
            # 📍 場合過濾
            if f_occs:
                if not any(o in info.get("occasions", []) for o in f_occs):
                    continue
            
            # 通過重重考驗，這件衣服可以顯示！
            files_to_show.append((f_cat, fname))
                    
        # 排序
        files_to_show.sort(key=lambda x: x[1], reverse=True)

        st.markdown(f'<div style="color:{MID};font-size:12px;font-weight:700;margin-bottom:8px">共 {len(files_to_show)} 件</div>', unsafe_allow_html=True)

        if not files_to_show:
            st.markdown(f"""<div class="empty">
              <div style="font-size:36px">🌸</div>
              <div style="font-weight:800;color:{MID};margin-top:8px">這個類別還是空的</div>
            </div>""", unsafe_allow_html=True)
        else:
            for f_cat, fname in files_to_show:
                fpath = os.path.join(BASE, f_cat, fname)
                info  = meta.get(fname, {})
                occs  = info.get("occasions", [])
                is_editing = st.session_state.editing_item == fname

                # ── 編輯模式 ──
                if is_editing:
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,{HOT}10,{CREAM}20);
                      border-radius:16px;padding:14px;border:2px solid {HOT}40;margin-bottom:10px">
                      <div style="font-size:11px;font-weight:800;color:{HOT};margin-bottom:10px">
                        ✏️ 編輯衣物資訊
                      </div>
                    </div>""", unsafe_allow_html=True)

                    img_col, form_col = st.columns([1, 2])
                    with img_col:
                        try: st.image(Image.open(fpath), use_container_width=True)
                        except: pass

                    with form_col:
                        # 🌟 3. 改用衣服專屬的分類 (f_cat) 來尋找原始資料
                        cur_cat_for_item = info.get("category", f_cat)
                        cur_col_key = cats.get(cur_cat_for_item, {}).get("col", "L")
                        cur_lvl_key = cats.get(cur_cat_for_item, {}).get("level", 2)

                        e_name   = st.text_input("名稱", value=info.get("name",""),
                                                  key=f"e_name_{fname}", label_visibility="collapsed",
                                                  placeholder="衣物名稱")
                        st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:-6px 0 4px">👗 名稱</div>', unsafe_allow_html=True)

                        e_cat    = st.selectbox("分類", cat_names,
                                                 index=cat_names.index(cur_cat_for_item)
                                                 if cur_cat_for_item in cat_names else 0,
                                                 key=f"e_cat_{fname}", label_visibility="collapsed")
                        st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:-6px 0 4px">📁 分類</div>', unsafe_allow_html=True)

                        e_season = st.selectbox("季節", SEASONS,
                                                 index=SEASONS.index(info.get("season", SEASONS[0]))
                                                 if info.get("season") in SEASONS else 0,
                                                 key=f"e_season_{fname}", label_visibility="collapsed")
                        st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:-6px 0 4px">⛅ 季節</div>', unsafe_allow_html=True)

                        e_occs   = st.multiselect("場合", OCCASIONS,
                                                   default=[o for o in occs if o in OCCASIONS],
                                                   key=f"e_occs_{fname}", label_visibility="collapsed")
                        st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:-6px 0 4px">📍 場合</div>', unsafe_allow_html=True)

                        # 版位設定
                        COL_VALS = list(COL_KEY.keys())
                        LVL_VALS = list(LVL_KEY.keys())
                        col_idx  = next((i for i,k in enumerate(COL_VALS) if COL_KEY[k]==cur_col_key), 0)
                        lvl_idx  = next((i for i,k in enumerate(LVL_VALS) if LVL_KEY[k]==cur_lvl_key), 1)
                        e_col    = st.selectbox("欄位", COL_VALS, index=col_idx,
                                                 key=f"e_col_{fname}", label_visibility="collapsed")
                        st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:-6px 0 4px">👈👉 欄位位置</div>', unsafe_allow_html=True)
                        e_lvl    = st.selectbox("層級", LVL_VALS, index=lvl_idx,
                                                 key=f"e_lvl_{fname}", label_visibility="collapsed")
                        st.markdown(f'<div style="font-size:10px;color:{MID};font-weight:700;margin:-6px 0 8px">⬆️⬇️ 上中下層</div>', unsafe_allow_html=True)

                    sv_col, ca_col = st.columns(2)
                    with sv_col:
                        if st.button("💾 儲存修改", key=f"save_edit_{fname}", use_container_width=True):
                            # 更新 metadata
                            meta[fname]["name"]     = e_name
                            meta[fname]["category"] = e_cat
                            meta[fname]["season"]   = e_season
                            meta[fname]["occasions"]= e_occs
                            save_meta(meta)
                            # 🌟 雲端版：所有照片都在同一個大倉庫，所以改分類不用搬檔案了！只要 metadata 有更新就好。
                            # 更新類別的欄位/層級設定
                            cats_data = load_cats()
                            cats_data[e_cat]["col"]   = COL_KEY[e_col]
                            cats_data[e_cat]["level"] = LVL_KEY[e_lvl]
                            save_cats(cats_data)
                            st.session_state.editing_item = None
                            st.session_state.toast_msg = "✅ 已儲存修改！"
                            st.rerun()
                    with ca_col:
                        if st.button("✕ 取消", key=f"cancel_edit_{fname}", use_container_width=True):
                            st.session_state.editing_item = None
                            st.rerun()

                # ── 一般顯示模式 ──
                else:
                    c1, c2, c3, c4 = st.columns([1.2, 2.2, 0.7, 0.7])
                    with c1:
                        # 🌟 升級版縮放魔法：同時檢查「分類名稱」與「衣服名稱」，確保「粉色西裝褲」絕對不會漏抓！
                        check_str = f_cat + info.get('name', '') 
                        if any(k in check_str for k in ["洋裝", "連身", "長褲", "西裝褲", "褲", "大衣", "全身", "長裙"]):
                            img_scale = "105px"  # 100% 最大比例 (給洋裝、褲子)
                        elif any(k in check_str for k in ["帽", "鞋", "包", "飾", "配件", "襪", "項鍊", "耳環", "貝雷帽"]):
                            img_scale = "40px"   # 縮小到 40px，解決帽子太大的問題！
                        else:
                            img_scale = "80px"   # 中等比例 (上衣等)

                        try: 
                            b64 = load_img_b64(fpath)
                            st.markdown(f"""
                            <div style="background:{CREAM}; border-radius:14px; height:110px; display:flex; align-items:center; justify-content:center; box-shadow:0 3px 10px {HOT}15; border:2px solid {CREAM};">
                              <img src="data:image/png;base64,{b64}" style="max-height:{img_scale}; width:auto; max-width:100%; object-fit:contain; filter:drop-shadow(0 4px 6px {HOT}25);"/>
                            </div>
                            """, unsafe_allow_html=True)
                        except: pass
                    with c2:
                        occ_badges = "".join(f'<span class="badge b-mid">{o}</span>' for o in occs)
                        # 🌟 4. 同樣確保全部視角下讀到正確分類
                        cur_cat_info = cats.get(info.get("category", f_cat), {})
                        col_label = "左欄" if cur_cat_info.get("col","L")=="L" else "右欄"
                        lvl_map   = {1:"上層", 2:"中層", 3:"下層"}
                        lvl_label = lvl_map.get(cur_cat_info.get("level",2), "中層")
                        st.markdown(f"""
                        <div style="padding-top:4px">
                          <div style="font-weight:800;color:{TEXT};font-size:13px;margin-bottom:5px">
                            {info.get('name', fname[:16])}
                          </div>
                          <span class="badge b-hot">⛅ {info.get('season','-')}</span>
                          <span class="badge b-blush">{col_label} {lvl_label}</span>
                          <br/>{occ_badges}
                        </div>""", unsafe_allow_html=True)
                    with c3:
                        if st.button("✏️", key=f"edit_{fname}", use_container_width=True):
                            st.session_state.editing_item = fname
                            st.rerun()
                    with c4:
                        if st.button("🗑️", key=f"del_{fname}", use_container_width=True):
                            delete_img_from_drive(fname)
                            if fname in meta:
                                del meta[fname]; save_meta(meta)
                            st.session_state.toast_msg = "已移除 🌸"
                            st.rerun()

            st.markdown(f'<div style="height:1px;background:{BLUSH}40;margin:6px 0"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# PAGE 4 ── 設定（API Key + 類別管理）
# ═══════════════════════════════════════════════════════
elif page == "settings":
    settings = load_settings()

    # ── Gemini API Key ──────────────────────────────
    st.markdown('<div class="sec-title">🤖 Gemini AI 設定</div>', unsafe_allow_html=True)
    key_input = st.text_input("Gemini API Key", value=settings.get("gemini_key",""),
                               type="password", placeholder="貼上你的 Gemini API Key...")
    if st.button("💾 儲存 API Key", use_container_width=True):
        settings["gemini_key"] = key_input.strip()
        save_settings(settings)
        st.session_state.toast_msg = "✅ API Key 已儲存！"
        st.rerun()
    st.markdown(f"""<div style="font-size:11px;color:{MID};margin-top:6px">
      👉 沒有 Key？前往
      <a href="https://aistudio.google.com" target="_blank" style="color:{HOT};font-weight:800">
      aistudio.google.com</a> 免費取得
    </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

    # ── 新增類別 ────────────────────────────────────
    st.markdown('<div class="sec-title">📁 新增類別</div>', unsafe_allow_html=True)
    new_cat_name = st.text_input("", placeholder="類別名稱，例如：上衣、帽子", label_visibility="collapsed")
    nc1, nc2 = st.columns(2)
    with nc1:
        new_col_sel = st.selectbox("欄位", COLUMNS, label_visibility="collapsed")
    with nc2:
        new_lvl_sel = st.selectbox("層級", LEVELS, label_visibility="collapsed")
    if st.button("➕ 新增類別", use_container_width=True):
        if new_cat_name:
            # 防止使用會破壞檔案系統的字元
            forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            if any(c in new_cat_name for c in forbidden_chars):
                st.error("類別名稱不能包含這些字元：/ \\ : * ? \" < > |")
            else:
                cats = load_cats()
                if new_cat_name not in cats:
                    os.makedirs(os.path.join(BASE, new_cat_name), exist_ok=True)
                    cats[new_cat_name] = {"col": COL_KEY[new_col_sel], "level": LVL_KEY[new_lvl_sel]}
                    save_cats(cats)
                    st.session_state.toast_msg = f"✨ 已建立「{new_cat_name}」！"
                    st.rerun()
                else:
                    st.error("此類別已存在！")
        st.markdown(f"""<div class="cream-box" style="margin-top:10px">
          <div style="font-size:11px;font-weight:800;color:#8B6914">💡 版位說明</div>
          <div style="font-size:11px;color:#8B6914;margin-top:3px;line-height:1.6">
            左欄：上衣、外套、裙子、褲子、洋裝<br>
            右欄：帽子、鞋子、包包、項鍊、配件<br>
            上層 → 中層 → 下層：由上到下排列
          </div>
        </div>""", unsafe_allow_html=True)

    # ── 現有類別 ────────────────────────────────────
    cats      = load_cats()
    cat_names = sorted(cats.keys())
    if cat_names:
        st.markdown('<div class="sec-title" style="margin-top:12px">🗂️ 現有類別</div>', unsafe_allow_html=True)
        COL_VALS = list(COL_KEY.keys())
        LVL_VALS = list(LVL_KEY.keys())

        for cat in cat_names:
            info    = cats.get(cat, {})
            cur_col = info.get("col", "L")
            cur_lvl = info.get("level", 2)

            if st.session_state.editing_cat == cat:
                e1, e2, e3 = st.columns([2, 1, 1])
                with e1:
                    rn = st.text_input("", value=cat, key=f"rn_{cat}", label_visibility="collapsed")
                with e2:
                    if st.button("💾", key=f"sv_{cat}", use_container_width=True):
                        rn = rn.strip()
                        if rn and rn != cat:
                            ok, err = safe_rename_folder(os.path.join(BASE, cat), os.path.join(BASE, rn))
                            if ok:
                                cats[rn] = cats.pop(cat)
                                save_cats(cats)
                                # 更新 metadata 的 category 欄位
                                m = load_meta()
                                for fn, finfo in m.items():
                                    if finfo.get("category") == cat:
                                        finfo["category"] = rn
                                save_meta(m)
                                st.session_state.toast_msg = f"✅ 已改名為「{rn}」"
                            else:
                                st.error(err)
                        st.session_state.editing_cat = None
                        st.rerun()
                with e3:
                    if st.button("✕", key=f"ca_{cat}", use_container_width=True):
                        st.session_state.editing_cat = None
                        st.rerun()
            else:
                c1, c2, c3, c4, c5 = st.columns([1.6, 1.6, 1.2, 0.6, 0.6])
                with c1:
                    st.markdown(f'<div style="padding-top:10px;font-weight:800;color:{TEXT};font-size:13px">👚 {cat}</div>', unsafe_allow_html=True)
                with c2:
                    col_idx = next((i for i,k in enumerate(COL_VALS) if COL_KEY[k]==cur_col), 0)
                    new_col = st.selectbox("", COL_VALS, index=col_idx, key=f"col_{cat}", label_visibility="collapsed")
                    if COL_KEY[new_col] != cur_col:
                        cats[cat]["col"] = COL_KEY[new_col]; save_cats(cats); st.rerun()
                with c3:
                    lvl_idx = next((i for i,k in enumerate(LVL_VALS) if LVL_KEY[k]==cur_lvl), 1)
                    new_lvl = st.selectbox("", LVL_VALS, index=lvl_idx, key=f"lvl_{cat}", label_visibility="collapsed")
                    if LVL_KEY[new_lvl] != cur_lvl:
                        cats[cat]["level"] = LVL_KEY[new_lvl]; save_cats(cats); st.rerun()
                with c4:
                    if st.button("✏️", key=f"ed_{cat}", use_container_width=True):
                        st.session_state.editing_cat = cat; st.rerun()
                with c5:
                    if st.button("🗑️", key=f"dc_{cat}", use_container_width=True):
                        try: shutil.rmtree(os.path.join(BASE, cat))
                        except: pass
                        del cats[cat]; save_cats(cats); st.rerun()
    else:
        st.markdown(f"""<div class="empty">
          <div style="font-size:34px">📁</div>
          <div style="font-weight:800;color:{MID};margin-top:8px">還沒有類別</div>
        </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:24px 0 14px;
  color:{MID};font-size:10px;font-weight:800;letter-spacing:2.5px">
  ✦ made with love 🎀 ✦
</div>""", unsafe_allow_html=True)
