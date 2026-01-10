# Huali Edu 椤圭洰

## 绠€浠?
鏈」鐩负鍗庣珛鏁欒偛鎴愮哗绠＄悊涓庢壒閲忚瘎鍒嗙郴缁燂紝鍩轰簬Django寮€鍙戯紝鏀寔澶氱彮绾с€佸浣滀笟鑷姩鐧昏鎴愮哗銆?

## 鐩綍缁撴瀯
- grading/         涓诲簲鐢紝鍖呭惈瑙嗗浘銆佹ā鏉裤€侀潤鎬佽祫婧?
- huali_edu/       鏍稿績涓氬姟閫昏緫涓庡伐鍏?
- hualiEdu/        Django椤圭洰閰嶇疆
- tests/           鑷姩鍖栨祴璇曠敤渚?
- static/          闈欐€佽祫婧愶紙JS/CSS/鍥剧墖锛?
- staticfiles/     Django鏀堕泦鐨勯潤鎬佹枃浠?
- media/           杩愯鏃朵笂浼?鐢熸垚鏂囦欢
- scripts/         鑷姩鍖栬剼鏈?
- docs/            椤圭洰鏂囨。

## 蹇€熷紑濮?

### 1. 鐜鍙橀噺閰嶇疆
鏈」鐩娇鐢ㄧ幆澧冨彉閲忎繚鎶ゆ晱鎰熶俊鎭紝璇峰厛閰嶇疆鐜鍙橀噺锛?

```bash
# 鏂规硶1锛氫娇鐢ㄨ嚜鍔ㄨ缃剼鏈?uv run python scripts/setup_env.py

# 鏂规硶2锛氭墜鍔ㄥ鍒跺苟缂栬緫
cp env.example .env
# PowerShell
Copy-Item env.example .env
# 鐒跺悗缂栬緫 .env 鏂囦欢锛屽～鍏ュ疄闄呯殑閰嶇疆鍊?```

**閲嶈閰嶇疆椤癸細**
- `SECRET_KEY`: Django 瀵嗛挜
- `VOLCENGINE_API_KEY`: 鐏北寮曟搸 AI API 瀵嗛挜
- `DEBUG`: 璋冭瘯妯″紡 (True/False)

### 2. 楠岃瘉閰嶇疆
```bash
uv run python scripts/verify_env.py
```

### 3. 瀹夎渚濊禆
```bash
uv sync
```

### 4. 鍒濆鍖栨暟鎹簱
```bash
uv run python manage.py migrate
```

### 5. 鍒涘缓绠＄悊鍛樿处鍙?
```bash
uv run python manage.py createsuperuser
```

### 6. 鍚姩寮€鍙戞湇鍔″櫒
```bash
uv run python manage.py runserver

### Makefile (recommended)
Windows without make:
```powershell
.\scripts\dev.ps1 runserver
```
This will start Podman services (MySQL/Redis) and run Django.
```bash
make runserver
```

```

### 7. 璁块棶搴旂敤
璁块棶 http://localhost:8000/

**鏂囨。绱㈠紩涓庣幆澧冭鏄庤鏌ョ湅 `docs/`锛?*
- 鏂囨。绱㈠紩: `docs/README.md`
- 鐜涓庨厤缃? `docs/environment.md`
- AI 瀵嗛挜鎺掓煡: `docs/ai-key.md`
- 浼樺寲涓庢妧鏈敼杩? `docs/optimization.md`

## 娴嬭瘯
- 鎵€鏈夋祴璇曠敤渚嬩綅浜?`tests/` 鐩綍
- 杩愯鍏ㄩ儴娴嬭瘯锛?  ```bash
  uv run python -m unittest discover tests
  ```

## 寮€鍙戣鑼?

- 浠ｇ爜鏍煎紡鍖栦笌妫€鏌ワ細浣跨敤 black + isort + flake8锛屽苟閫氳繃 pre-commit 鑷姩鏍￠獙銆?
- 瀹夎寮€鍙戜緷璧栦笌瀹夎閽╁瓙锛?
  ```bash
  uv sync --dev
  pre-commit install
  # 棣栨鍙鍏ㄥ簱鎵ц涓€閬?  pre-commit run --all-files
  ```

## 閮ㄧ讲
- 鎺ㄨ崘浣跨敤 Docker 閮ㄧ讲锛岃 `Dockerfile` 鍜?`docker-compose.yml`
- 鐢熶骇鐜璇烽厤缃幆澧冨彉閲忥紝鍒嗙鏁忔劅淇℃伅

## 甯歌闂
- **闈欐€佹枃浠舵湭鍔犺浇锛?*
  - 璇疯繍琛?`python manage.py collectstatic` 骞剁‘淇?`STATIC_ROOT` 閰嶇疆姝ｇ‘
- **鏁版嵁搴撹縼绉诲け璐ワ紵**
  - 妫€鏌?`migrations/` 鐩綍锛屽皾璇?`python manage.py makemigrations` 鍚庡啀 migrate
- **鎴愮哗鏈啓鍏xcel锛?*
  - 妫€鏌ユ棩蹇楄緭鍑恒€佹枃浠舵潈闄愩€佸鐢熷悕涓嶦xcel涓€鑷存€?

## 璐＄尞
- 娆㈣繋鎻愪氦PR鍜孖ssue锛屽缓璁厛闃呰 `docs/project_rules.md`

## 鍏跺畠
- 鏃ュ織鏂囦欢榛樿杈撳嚭鍒?logs/ 鐩綍
- 鎵€鏈変緷璧栬鐢?`pip freeze > requirements.txt` 瀹氭湡鏇存柊


## ?????
?????????????????? API?Django?????? React?

?????
- ???`uv run python manage.py runserver`??? 8000?
- ???`cd frontend` -> `npm install` -> `npm run dev`??? 5173?

?????
- ???`http://localhost:5173/`
- ???????`http://localhost:8000/`

?? API ????`frontend/.env` ? `VITE_API_BASE_URL`?

????? `docs/frontend.md`?