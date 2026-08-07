# 專案規格

## 1. 目標

建立一套以 nRF52840 Dongle 為 RF 前端、能在 PC 上擷取與分析 BLE 流量的工程工具。工具應同時支援互動除錯與 CI/產線式的非互動操作。

## 2. 第一版範圍

### 必須完成

- 掃描並辨識一支或多支 nRF52840 sniffer
- 擷取 Legacy/Extended Advertising（以官方韌體實際能力為準）
- 從 CONNECT_IND/AUX_CONNECT_REQ 開始追蹤單一連線
- 保存 PCAPNG，供 Wireshark/tshark 開啟
- CLI timeout、目標篩選、輸出路徑及結束碼
- 顯示 firmware、host tool、Wireshark 等版本資訊
- 從 capture 產生機器可讀 JSON 摘要
- Windows 優先，核心模組不得依賴 Windows GUI

### 暫不納入

- 同一支 Dongle 同時完整追蹤多條連線
- 保證捕獲所有三個廣播頻道上的每個封包
- 在未取得金鑰的情況破解 BLE 加密
- BLE direction finding/IQ sampling
- 取代 Wireshark 的完整 dissector GUI
- 第一階段自研 BLE link-layer sniffer firmware

## 3. 使用情境

```text
ble-sniffer devices
ble-sniffer capture --device <id> --target <addr-or-name> --duration 30s --output run.pcapng
ble-sniffer analyze run.pcapng --json run.json
ble-sniffer doctor
```

Wireshark 使用者則從 capture interface 選擇 Dongle，設定目標裝置與選配金鑰後開始擷取。

## 4. 成功標準

| 項目 | 驗收方式 |
|---|---|
| 裝置辨識 | 插拔、兩支 Dongle、COM port 改號仍可穩定識別 |
| 廣播擷取 | 60 秒測試可看到測試 peripheral 的廣播與 RSSI |
| 連線追蹤 | 從連線建立到斷線皆有封包，ATT 操作可由 Wireshark 解碼 |
| 檔案相容性 | `capinfos`、Wireshark、tshark 均能開啟輸出 |
| 可重現性 | 同一 golden PCAPNG 的 JSON 結果固定 |
| 異常處理 | Dongle 拔除、busy、timeout、輸出失敗都有非零結束碼與清楚訊息 |

## 5. 技術決策

### 主機端語言：Python 3.11+

原型階段選 Python，因為 extcap、serial/USB、PCAPNG 與測試生態成熟，且 Nordic 既有工具鏈也易整合。效能敏感的 frame parser 保留日後改成 Rust library 的邊界，但不預先最佳化。

### 擷取核心：官方 firmware 優先

M0–M4 使用 Nordic 官方 nRF Sniffer for Bluetooth LE firmware / nRF Util 流程。若官方 host API 不穩定，adapter 僅包住 command/serial 邊界，不讓其資料模型滲入分析層。

### 檔案格式：PCAPNG 為真實來源

擷取結果保存為 PCAPNG；JSON 是衍生報告。封包 timestamp、channel、RSSI、direction、PHY、event counter 等 metadata 能保留多少，須在 M0 實測並形成相容性表。

## 6. 版本策略

在 `toolchain.lock`（M0 建立）記錄：

- nRF Util 與 ble-sniffer plugin 版本
- Dongle firmware 版本及 SHA-256
- Wireshark/tshark 版本
- Python 與依賴 lockfile
- 作業系統版本

先鎖定已驗證組合，再安排升級測試，不追逐未驗證的最新版。

