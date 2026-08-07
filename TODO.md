# TODO

- [x] 準備可控制的 BLE Central 與 Peripheral 測試組合，並依 J-Link 序號固定角色。
- [x] 建置並驗證 Peripheral firmware，啟動後廣播名稱為 `BLE-SNIFFER-P`。
- [x] 將 Central firmware 燒錄至 J-Link `683519772`，並完成端到端 runtime 驗證。
- [x] 擷取完整流程：Advertising → Connect → Pairing → GATT Read/Write/Notify → Disconnect。
- [ ] 將 capture 去識別化，建立 golden capture 與預期解析結果。
- [x] 建立 Python package 骨架及鎖定依賴（目前零 runtime dependencies），所有操作使用專案 `.venv`。
- [ ] 實作 `devices`、`doctor`、`capture` CLI 指令。
- [ ] 實作穩定的裝置識別、timeout、Ctrl+C、熱插拔與錯誤處理。
- [ ] 將擷取結果保存為 PCAP/PCAPNG，並用 capinfos/tshark 自動驗證。
- [ ] 實作離線分析與 JSON 報告，優先重用 tshark dissector。
- [ ] 加入 fixture、單元測試、實機 smoke test 與長時間擷取測試。
- [ ] 完成 Windows 安裝、Wireshark extcap 與版本升級/回復流程。
