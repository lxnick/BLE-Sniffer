# 開發流程

## Phase 0：需求與硬體基準（1–2 天）

- 確認 Dongle 型號為 PCA10059、數量與硬體版本。
- 建立可控制的 BLE peripheral/central 測試組合。
- 以官方 nRF Util BLE Sniffer + Wireshark 完成一次廣播及一次連線 capture。
- 保存版本清單、操作紀錄、golden PCAPNG 與已知限制。

出口條件：能重複燒錄、Wireshark 看得到 ATT traffic，並知道是否需提供 LTK/配對資訊。

## Phase 1：Repository 與契約（2–3 天）

- 建立 Python package、lint/type/test 與 lockfile。
- 定義 `DeviceInfo`、`CapturedFrame`、`CaptureSession`。
- 用錄製的 transport bytes 建立 adapter fixture。
- 寫 PCAPNG 最小 round-trip 測試。

出口條件：沒有實體 Dongle 也能跑 parser/writer tests。

## Phase 2：CLI 擷取（3–5 天）

- `devices`、`doctor`、`capture` 指令。
- Ctrl+C、duration、Dongle 拔除、port busy、磁碟錯誤處理。
- structured logging 與穩定結束碼。
- 實機 soak test 30–60 分鐘並記錄 dropped-frame 指標。

出口條件：命令列可穩定產生 Wireshark 可讀檔案。

## Phase 3：extcap（2–4 天）

- 實作 extcap discovery、DLT、config、FIFO capture。
- Windows 安裝/移除腳本。
- Wireshark GUI 啟停、重啟、多 Dongle 列舉測試。

出口條件：使用者不需手動選 COM port 即可從 Wireshark 擷取。

## Phase 4：分析與報告（4–7 天）

- 優先呼叫 tshark 的成熟 dissector 輸出欄位，不重寫 ATT/SMP dissector。
- 建立連線 timeline、GATT 操作、錯誤 response、重傳/間隔異常摘要。
- JSON schema 與 golden-file regression tests。

出口條件：同一 capture 產生 deterministic report，並能用規則讓 CI pass/fail。

## Phase 5：封裝與相容性（3–5 天）

- Windows standalone packaging 與簽章策略。
- Linux udev/permission 文件與 smoke test。
- 建立 toolchain compatibility matrix、升級與 rollback 程序。

## 每次變更的驗證層級

1. 單元測試：frame decoder、狀態機、PCAPNG blocks、report rules。
2. Fixture 測試：錄製 transport stream 與 golden PCAPNG。
3. 工具整合：`capinfos`/`tshark` 可讀性。
4. 實機 smoke：廣播、建立連線、GATT read/write/notify、disconnect。
5. 長時間測試：丟包、記憶體、USB reset、Dongle 熱插拔。

## Definition of Done

- 功能、錯誤路徑與文件同步完成。
- 新的 packet/metadata 行為有 fixture。
- 不提交含敏感 address、LTK 或產品資料的 capture。
- 輸出格式變更有 schema/version 說明。
- 已在鎖定工具鏈及至少一支實體 PCA10059 驗證。

