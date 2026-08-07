# 架構設計

## 元件

```text
BLE radio traffic
      |
      v
nRF52840 Dongle
(Nordic sniffer firmware)
      |
      | USB / firmware transport
      v
Device adapter  ---> device/firmware diagnostics
      |
      v
Capture session ---> raw event normalization ---> PCAPNG writer
      |                                           |
      |                                           +--> Wireshark/tshark
      +--> extcap process                              |
                                                      v
                                               Offline analyzer
                                                      |
                                                      +--> JSON / console report
```

## 建議目錄

```text
firmware/                 # R1 自研研究線；MVP 可只放說明
host/
  src/ble_sniffer/
    cli.py                # CLI entry point
    devices.py            # stable device identity and discovery
    capture.py            # capture session lifecycle
    adapters/             # Nordic transport/tool adapter
    pcapng.py             # packet output boundary
    analyze.py            # offline event extraction
    diagnostics.py        # doctor/version checks
  tests/
extcap/                   # thin Wireshark adapter
captures/
  fixtures/               # 小型、去識別化 golden captures
docs/
scripts/                  # build/install/release helpers
```

## 邊界與資料模型

韌體 adapter 輸出正規化 `CapturedFrame`，至少包含：

- host monotonic timestamp 與 sniffer timestamp（若有）
- raw BLE PDU bytes
- channel/index、RSSI、PHY、CRC status（若 firmware 提供）
- direction、connection/event metadata（若可判定）
- source device ID 與 firmware version

缺少的 metadata 必須是 `unknown`，不可用猜測值填入。

`CaptureSession` 負責狀態機：

```text
disconnected -> opening -> ready -> capturing -> stopping -> closed
                    |          |          |
                    +--------> failed <---+
```

停止擷取必須 flush 並封閉 PCAPNG；Dongle 被拔除時保留已寫入資料並回報 partial capture。

## Wireshark 整合

extcap 維持薄層，只處理：

- `--extcap-interfaces`
- `--extcap-dlts`
- `--extcap-config`
- `--capture --fifo`
- Windows wrapper/安裝位置

實際擷取邏輯由 host package 共用，避免 CLI 與 extcap 出現兩套行為。

## RF 韌體研究線（R1）

若未來需要掌控 firmware source 或特殊 metadata，再另行驗證：

1. RADIO + TIMER + PPI/DPPI 的低延遲 timestamp/capture。
2. 三個 primary advertising channel 的排程與 device selection。
3. 由 CONNECT_IND/AUX_CONNECT_REQ 取得 access address、CRCInit、channel map、hop/SCA。
4. CSA #1/#2、connection event timing、PHY/channel map update。
5. USB buffering、flow control、丟包計數與 clock drift correction。
6. LE Coded/2M、extended/periodic advertising 的能力矩陣。

此工作量接近獨立協定分析器，不與 MVP 混在同一 critical path。

