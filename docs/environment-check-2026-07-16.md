# 環境點檢紀錄 — 2026-07-16

## 結論

nRF52840 Dongle 的 USB 與 Nordic DFU bootloader 正常，可以作為本專案的 BLE sniffer 硬體。它目前停在 DFU bootloader，必須先燒錄 BLE Sniffer firmware，之後才會成為可擷取介面。

## 實測結果

| 檢查項目 | 結果 | 實測資訊/後續工作 |
|---|---|---|
| Nordic USB device | PASS | `VID_1915`, `PID_521F` |
| Windows device status | PASS | `Status=OK`, `ConfigManagerErrorCode=0` |
| DFU serial interface | PASS | 燒錄前為 `COM14` |
| Dongle DFU identity | PASS | 燒錄前為 `D32D7EF97D16` |
| DFU bootloader | PASS | Nordic Open DFU Bootloader 可正常列舉 |
| Sniffer application firmware | PASS | Nordic BLE Sniffer 4.1.1；燒錄後 `PID_522A`, `COM15` |
| Sniffer application identity | PASS | `C6C01676D0F97A4E`；nRF Util 顯示 `nRF Sniffer for Bluetooth LE` |
| System Python | PASS | Python 3.11.0 |
| Project `.venv` | PASS | `.venv\Scripts\python.exe`, Python 3.11.0 |
| pip in `.venv` | PASS | pip 22.3；目前未升級，以免未經鎖版引入變動 |
| nRF Util | PASS | 8.2.0，透過 winget 安裝 |
| nRF Util `device` command | PASS | 2.19.4；已辨識 PCA10059、序號與 DFU traits |
| nRF Util `ble-sniffer` command | PASS | 0.20.0；內含 PCA10059 firmware 4.1.1 |
| Wireshark | PASS | 4.6.7，安裝於 `C:\Program Files\Wireshark` |
| tshark/capinfos | PASS | 可讀取 Nordic BLE encapsulation 186 |
| Wireshark extcap | PASS | bootstrap 成功，COM15 可由 extcap 列舉 |
| Advertising smoke capture | PASS | 9.823 秒、552 packets、43,185 bytes、channels 37/38/39 |
| Golden connection capture | PENDING | Peripheral/Central EVK 已分配角色（見下方章節）；尚待燒錄 firmware 並實際擷取 |

## 判讀

`PID_521F` 是本次系統讀到的 Nordic DFU composite device。DFU 正常代表可透過支援的 Nordic 工具寫入應用程式，但它不等於 sniffer firmware 已經在執行。

燒錄後 VID/PID、COM port 或介面型態可能改變，因此工具不得把 `COM14` 當永久裝置 ID；應優先使用 USB serial identity。

## Golden connection capture 測試裝置（2026-08-07 追加）

兩塊 nRF52840 EVK（PCA10056）已接上並以 J-Link 序號分配角色。角色分配以序號為準，COM port 會隨系統重新列舉而改變：

| 角色 | J-Link 序號 | VCOM Port | 備註 |
|---|---|---|---|
| Peripheral（被連線方） | `001050244398` | COM8 / COM16 | 有 Mass Storage，可拖拉燒錄；2026-08-07 重新列舉後實測 |
| Central（發起連線方） | `000683519772` | COM17 | 無 Mass Storage（較舊款 J-Link OB 韌體）；2026-08-07 重新列舉後實測 |

實體板子已依序號後四碼貼標籤（`P-4398` / `C-9772`），供日後拔插核對。

## 待完成操作

1. ~~準備一組可控制的 BLE peripheral/central。~~（已完成，見上方角色分配）
2. ~~建置 Peripheral/Central EVK 對應 firmware。~~（已完成；NCS v3.3.4）
3. ~~燒錄並驗證 Peripheral firmware。~~（已完成；`BLE-SNIFFER-P` 正常廣播）
4. ~~將 Central firmware 燒錄至 J-Link `000683519772`。~~（已完成）
5. 從配對或建立連線前開始擷取，取得完整 connection capture。
6. 將去識別化的 capture 納入 regression fixture。

## Golden test firmware（2026-08-07）

| 角色 | 狀態 | 映像 SHA-256 |
|---|---|---|
| Peripheral `1050244398` | 已建置、燒錄、verify；UART 確認 `Advertising as BLE-SNIFFER-P` | `7a7fe31fd214092b732e420460938c3604369bdc10c9983af5e699ed4157d2dc` |
| Central `683519772` | 已建置、燒錄、verify；端到端序列通過 | `3b4567fdcaefe26bdd0aed3b97a897f951b92ac655166d39b13663c7bf4565a2` |

預期自動測試序列：Advertising → Connect → Just Works Pairing → GATT Write → GATT Read → 5 次 Notify → Disconnect。

2026-08-07 實機 UART 驗證已完整觀察到上述序列；斷線原因為 Central 主動終止（`0x16`），之後 Central 會重新開始掃描。

## 已解除的阻塞

- 關閉占用 COM14 的工具後，官方 firmware 已成功寫入。
- Wireshark 背景安裝完成後，點檢可找到 Wireshark、tshark 與 capinfos。

## Smoke capture 證據

- 檔案：`captures/private/smoke.pcap`（已由 `.gitignore` 排除）
- PCAP encapsulation：`nRF Sniffer for Bluetooth LE (186 - nordic_ble)`
- 封包數：552
- 擷取長度：9.823396 秒
- SHA-256：`7811f14fbd9c637e88ba508bb7f2af9ff2decff3e491a3893b406beb9f35af21`
- tshark 已解碼 `nordic_ble.channel` 與 `nordic_ble.rssi`；前幾筆涵蓋 channels 37、38、39。

## 重跑點檢

從專案根目錄執行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_prerequisites.ps1
```
