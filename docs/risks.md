# 風險與對策

| 風險 | 影響 | 對策 |
|---|---|---|
| 把 HCI controller 當被動 sniffer | 架構無法追蹤空中連線 | M0 使用 Nordic sniffer firmware；HCI sample 僅作 BLE adapter，不列入方案 |
| 官方 firmware/host 協定非穩定 API | 升級後 adapter 失效 | 鎖版本、保存 firmware hash、adapter contract tests、升級矩陣 |
| 單 radio 漏掉廣播或連線起始 | 無法追蹤後續 data channel | sniffer 靠近 DUT、固定目標、記錄 dropped/CRC 指標；必要時多 Dongle |
| 已加密連線且未捕捉配對/無金鑰 | payload 無法解碼 | 從配對前開始擷取，允許安全輸入 LTK；報告中明示 encrypted/unknown |
| Extended/Coded/Periodic feature 支援差異 | 宣稱能力與實際不符 | M0 建立 firmware capability matrix，未驗證項目不列為支援 |
| Dongle 沒有板載 debugger | 韌體失敗時救援較麻煩 | 保留 Nordic DFU bootloader；研究線使用獨立 DK/J-Link，不在唯一 Dongle 冒險 |
| Windows COM port/driver 變動 | 裝置選錯或消失 | 以 USB identity + serial number 建 stable ID，不保存 COM 名稱為永久 identity |
| extcap FIFO 或程序終止造成損壞 | capture 遺失 | incremental blocks、flush、partial-capture 標記、kill/restart tests |
| PCAPNG metadata mapping 錯誤 | Wireshark 顯示誤導 | 以官方 capture 作差異比較，未知欄位保留 unknown |
| Capture 內含產品或金鑰資訊 | 資安/隱私問題 | fixtures 去識別化、金鑰不進 log、輸出目錄與 retention 規則文件化 |

