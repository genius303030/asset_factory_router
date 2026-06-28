# VERSION_LOCK

- **封版狀態**: V0.2_LOCKED (Engineering Core)
- **封版日期**: 2026-06-28
- **核心功能**:
  - `asset-factory` 全局指令與 `pip install -e .`。
  - Provider Registry 與 Profiles。
  - 外部化 router weights 設定。
  - 包含 10 個核心檔案的 Asset Pack。
  - 15 支以上的單元測試與 Brief Validation。
- **不可破壞原則**:
  - 請維持 Provider Registry 模式。
  - 請維持 Router 評分維度架構。
  - V0.3 的新功能（如 API 串接）必須透過實作 BaseProvider 來擴充，不可改動 `main.py` 與 `router.py` 的主流程。
