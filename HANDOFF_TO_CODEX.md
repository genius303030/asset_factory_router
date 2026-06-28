# HANDOFF TO CODEX

**專案摘要**: 
這是一個將創意需求轉換為「AI 素材包」的系統。V0.2 階段已完成了核心引擎的工程化重構，包括 Provider Registry, 組態化 Router，以及完整的 Schema Validator。

**已完成內容**: 
- `asset-factory` 全局 CLI。
- 15 項自動化單元測試。
- 10 檔案的 Asset Pack 輸出。

**不要動的部分**: 
- 原有的 V0.1.1 業務邏輯精神與整體資料流方向不可改變。
- 測試框架基底。

**可以改的部分**: 
- Router 的分數權重與計算細節可以微調。
- Provider 的 profiles 可以擴充。

**V0.3 建議任務**: 
- 把 MockProvider 替換成真實的 API Client。
- 加入 Async 並發請求機制。

**驗收標準**: 
- 所有指令與測試皆能穩定運行 `python -m unittest discover tests`。
