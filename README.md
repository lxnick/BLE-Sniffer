# nRF52840 BLE Sniffer Tool

以 Nordic nRF52840 Dongle（PCA10059）為擷取硬體的 BLE 封包擷取、分析與自動化工具專案。

## 專案方向

第一版不重寫 BLE 空中封包追蹤韌體，而是使用 Nordic 官方 nRF Sniffer for Bluetooth LE 韌體，專注開發可維護的主機端工具：

- 探測與管理 sniffer dongle
- 啟停擷取並輸出 PCAPNG
- 以 CLI 重現擷取工作流程
- 整合 Wireshark extcap
- 提取連線、ATT/GATT、配對與異常事件摘要
- 為自動化測試產生 JSON 報告與明確的結束碼

這個切法可先取得可靠的跳頻、連線追蹤與 Wireshark 解碼能力。一般 HCI USB controller 不是被動 sniffer，不能取代空中封包擷取韌體。

## 建議環境

- nRF52840 Dongle（PCA10059），至少 1 支
- Windows 10/11（第一個支援平台）
- Wireshark 4.x
- Python 3.11+（主機端原型）
- Nordic nRF Util 與 `ble-sniffer` command/plugin
- nRF Connect for Desktop Programmer（救援與人工燒錄）

## 里程碑

1. `M0`：官方工具基準驗證，可在 Wireshark 擷取廣播及單一 BLE 連線。
2. `M1`：CLI 可列舉裝置、開始/停止擷取、寫出有效 PCAPNG。
3. `M2`：Wireshark extcap 整合與裝置/廣播頻道/目標選擇。
4. `M3`：離線分析與 JSON 報告，涵蓋連線、ATT、SMP 和封包遺失指標。
5. `M4`：測試自動化、安裝包、Windows/Linux 相容性。
6. `R1`：評估自研 RF 韌體；不阻塞 M0–M4。

詳細內容見 [project.md](project.md)、[架構](docs/architecture.md)、[開發流程](docs/development-process.md) 與 [風險清單](docs/risks.md)。

目前工作站與 Dongle 的點檢結果見 [2026-07-16 環境點檢](docs/environment-check-2026-07-16.md)。可重跑：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_prerequisites.ps1
```

## 近期工作

- [x] 安裝並鎖定 nRF Util、BLE Sniffer、Wireshark 版本
- [x] 將 Dongle 進入 DFU，燒錄官方 sniffer firmware
- [x] 建立兩台 BLE 測試裝置並依 J-Link 序號分配 Central/Peripheral 角色
- [x] 建置並燒錄 Peripheral 測試 firmware（`1050244398`）
- [x] 建置、燒錄並驗證 Central 測試 firmware（`683519772`）
- [x] 實機驗證 Pairing、GATT Write/Read、5 次 Notify 與 Disconnect 測試序列
- [x] 保存第一份完整連線 golden capture（private，含 SMP、ATT 與 5 次 notification）
- [x] 記錄 Dongle USB/COM 識別資訊與 advertising smoke capture 結果
- [x] 確認 smoke capture 的 link type、metadata 與 Wireshark 解碼結果

## Host package 開發

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s host\tests -v
.\.venv\Scripts\ble-sniffer.exe --version
.\.venv\Scripts\ble-sniffer.exe devices
.\.venv\Scripts\ble-sniffer.exe devices --all --json
.\.venv\Scripts\ble-sniffer.exe doctor
.\.venv\Scripts\ble-sniffer.exe doctor --json
```

目前 Phase 1 已建立正規化資料模型、capture lifecycle 狀態機，以及可由
Wireshark/tshark 讀取的 Nordic BLE PCAPNG writer。`devices` 預設只列出相容
sniffer；`--all` 可顯示本專案相關的 Nordic EVK，但排除其他廠牌的序列裝置。`doctor` 任一必要檢查
失敗時回傳 exit code 1；裝置列舉錯誤為 2，找不到 sniffer 為 3。

## 原則

- 原始封包永遠可保存；分析結果不可取代 PCAPNG。
- 韌體傳輸與分析層解耦，避免綁死特定 firmware 版本。
- 每個里程碑都用可重播 capture 測試，不以肉眼操作為唯一驗證。
- 未取得 LTK/STK 或配對過程時，不宣稱能解密既有加密連線。
