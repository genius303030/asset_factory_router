# PROJECT_INDEX

- **專案名稱**: AI Asset Factory + Model Router
- **目前版本**: V0.2_DEV
- **專案用途**: 將創作需求轉譯成可發包給各 AI 模型的規格書與提示詞，並負責智能評分路由最合適的模型。
- **核心模組**:
  - `brief_loader.py` & `brief_schema.py` & `validator.py`: 讀取並驗證需求規格
  - `router.py` & `scoring.py`: 依據外部組態檔 (router_weights) 計算 8 大維度評分
  - `prompt_engine.py`: 渲染 7 種樣板，產生 11 個段落的 prompt_pack
  - `providers/registry.py`: 提供 Provider 能力矩陣註冊與讀取
  - `asset_pack_writer.py` & `inspector.py`: 輸出 10 份最終資產並負責完整性驗證
- **如何執行**: `pip install -e .` 後執行 `asset-factory demo`
- **如何驗收**: `python -m unittest discover tests`
- **目前限制**: 尚未串接真實 API。
- **下一版方向**: 真實 API 串接與前端 UI。
- **封版日期欄位**: 待定。
