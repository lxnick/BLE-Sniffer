# TODO

- [x] 準備可控制的 BLE Central 與 Peripheral 測試組合，並依 J-Link 序號固定角色。
- [ ] 擷取完整流程：Advertising → Connect → Pairing → GATT Read/Write/Notify → Disconnect。
- [ ] 將 capture 去識別化，建立 golden capture 與預期解析結果。
- [ ] 建立 Python package 骨架及鎖定依賴，所有操作使用專案 `.venv`。
- [ ] 實作 `devices`、`doctor`、`capture` CLI 指令。
- [ ] 實作穩定的裝置識別、timeout、Ctrl+C、熱插拔與錯誤處理。
- [ ] 將擷取結果保存為 PCAP/PCAPNG，並用 capinfos/tshark 自動驗證。
- [ ] 實作離線分析與 JSON 報告，優先重用 tshark dissector。
- [ ] 加入 fixture、單元測試、實機 smoke test 與長時間擷取測試。
- [ ] 完成 Windows 安裝、Wireshark extcap 與版本升級/回復流程。
