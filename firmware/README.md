# Golden connection test firmware

These two nRF52840 DK applications produce a deterministic BLE sequence for
sniffer validation:

```text
Advertising -> Connect -> Pair (Just Works) -> GATT Write -> GATT Read
            -> GATT Notify (5 times) -> Disconnect
```

The toolchain baseline is nRF Connect SDK v3.3.4 and the board target is
`nrf52840dk/nrf52840`.

## Fixed board roles

| Application | J-Link serial | Advertising name |
|---|---:|---|
| Peripheral | `1050244398` | `BLE-SNIFFER-P` |
| Central | `683519772` | n/a |

Never select a board by COM port; Windows can renumber it.

## Build

Run from the repository root in an nRF Connect SDK v3.3.4 toolchain
environment:

```powershell
west build -p always -b nrf52840dk/nrf52840 firmware/peripheral -d build/peripheral
west build -p always -b nrf52840dk/nrf52840 firmware/central -d build/central
```

## Flash

Flashing erases the current application on each DK. The commands deliberately
use the fixed J-Link serial numbers:

```powershell
west flash -d build/peripheral --dev-id 1050244398
west flash -d build/central --dev-id 683519772
```

> [!WARNING]
> These golden-capture test images enable the Bluetooth Core debug key via
> `CONFIG_BT_USE_DEBUG_KEYS=y`, so a passive sniffer can decrypt ATT traffic.
> Never use these images or this setting in a production device.

Start the sniffer before resetting the Central DK. Pairing is Just Works and no
bond is retained, so every reset produces a new pairing exchange.
