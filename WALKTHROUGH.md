# AI Asset Factory + Model Router V0.1 Walkthrough

## 專案目的
本專案為一個 AI 創作與路由中樞 MVP，目的在於接收使用者的簡單創作需求 (Brief)，自動生成針對不同目標 (圖像、UI、影片) 的結構化提示詞與素材包 (Asset Pack)；同時，它能根據需求的預算、品質與速度等屬性，自動評估並推薦最合適的 AI 供應商模型 (Model Router)。

## 資料流 (Data Flow)
1. **輸入 (Input)**: 讀取包含專案細節的 JSON 檔案 (`ProjectBrief`)。
2. **路由評估 (Routing)**: `ModelRouter` 根據 Brief 的品質、預算、速度、風格，計算各 `Provider` 的權重得分，挑選出最佳推薦模型 (`RoutingPlan`)。
3. **產包 (Factory Generation)**: `PromptBuilder` 根據 Brief 的內容，將其展開成多份文字資料 (包含 Markdown 提示詞包、結構化圖片提示詞、UI 指南、分鏡表草稿等)。
4. **輸出 (Output)**: `AssetPackWriter` 將所有資料與路由計畫打包寫入指定的 output 目錄中，形成完整的 `Asset Pack`。

## Asset Factory 如何產包
Factory 模組 (`prompt_builder.py`) 主要負責依據任務類型進行字串與樣板組裝。
- **通用產出**: `prompt_pack.md`, `image_prompts.json`。
- **條件產出**: 若 `task_type == "ui"`，則會生成詳細的 `ui_style_guide.md`；若為 `video`，則生成詳細的 `storyboard.md`。若不符合，也會生成對應的 N/A 佔位檔案保持結構一致性。

## Router 如何評分
Router 採用一套基於權重的積分系統 (`scoring.py`)：
1. **先決條件**: 若任務類型 (task_type) 不在 Provider 的 `supported_tasks` 內，直接淘汰 (給予 -1 分)。
2. **屬性評分**: 根據 Brief 要求的 quality/speed/budget，給予 1, 3, 5 等級的權重，並與 Provider 的基礎屬性相乘。例如：使用者要求 high budget，則便宜的模型不一定會獲得高分；反之若要求 low budget，則 cost_level 低的模型會獲得高加權。
3. **風格加分 (Bonus)**: 若風格關鍵字 (如 game, ui) 命中 Provider 的 strengths，則額外加上 10 分。
最終加總排序，第一名為 `recommended_provider`，第二名為 `fallback_provider`。

## Provider 如何擴充
本系統在 `providers/base.py` 中定義了嚴謹的 `BaseProvider` 抽象類別。
要新增 Provider (例如 Midjourney 或 Luma)：
1. 建立一個繼承 `BaseProvider` 的類別，設定 `name`, `supported_tasks`, `strengths`, `weaknesses`。
2. 設定其基礎能力值 (1-5)：`cost_level`, `speed_level`, `quality_level`。
3. 實作 `generate_mock_result()` 方法。
4. 在 `providers/__init__.py` 的 `AVAILABLE_PROVIDERS` 陣列中註冊即可生效。

## V0.1 使用限制
1. 完全處於 Mock 狀態，未接上任何真實的外部 API 服務。
2. Prompt 生成基於靜態的字串組合 (Template Replacement)，尚不支援使用 LLM 進行語意擴寫。
3. 無非同步機制，若未來串接真實耗時任務 (如影片生成)，將會阻塞主執行緒。

## V0.2 前置條件
- 在正式串接真實 API 前，必須設定 `pyproject.toml`，以標準化專案安裝與執行。
- 需要確認是否引入 `requests` 或各家官方 SDK (如 `openai` package)。
- 建立更安全的 Secrets 管理機制 (例如確實讀取 `.env`)。
