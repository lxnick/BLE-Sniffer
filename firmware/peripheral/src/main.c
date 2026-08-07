#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/byteorder.h>

LOG_MODULE_REGISTER(golden_peripheral, LOG_LEVEL_INF);

/* 8d53dc1d-1db7-4cd3-868b-8a527460aa84 */
#define BT_UUID_GOLDEN_SERVICE_VAL \
	BT_UUID_128_ENCODE(0x8d53dc1d, 0x1db7, 0x4cd3, 0x868b, 0x8a527460aa84)
/* da2e7828-fbce-4e01-ae9e-261174997c48 */
#define BT_UUID_GOLDEN_DATA_VAL \
	BT_UUID_128_ENCODE(0xda2e7828, 0xfbce, 0x4e01, 0xae9e, 0x261174997c48)

static struct bt_uuid_128 golden_service_uuid = BT_UUID_INIT_128(BT_UUID_GOLDEN_SERVICE_VAL);
static struct bt_uuid_128 golden_data_uuid = BT_UUID_INIT_128(BT_UUID_GOLDEN_DATA_VAL);

static uint8_t value[20] = "peripheral-ready";
static uint8_t value_len = sizeof("peripheral-ready") - 1;
static bool notify_enabled;
static uint32_t notify_counter;

static ssize_t read_value(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			  void *buf, uint16_t len, uint16_t offset)
{
	return bt_gatt_attr_read(conn, attr, buf, len, offset, value, value_len);
}

static ssize_t write_value(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			   const void *buf, uint16_t len, uint16_t offset,
			   uint8_t flags)
{
	ARG_UNUSED(conn);
	ARG_UNUSED(attr);
	ARG_UNUSED(flags);

	if (offset != 0 || len == 0 || len > sizeof(value)) {
		return BT_GATT_ERR(BT_ATT_ERR_INVALID_OFFSET);
	}

	memcpy(value, buf, len);
	value_len = len;
	LOG_HEXDUMP_INF(value, value_len, "GATT write");
	return len;
}

static void ccc_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
	ARG_UNUSED(attr);
	notify_enabled = (value == BT_GATT_CCC_NOTIFY);
	notify_counter = 0;
	LOG_INF("Notifications %s", notify_enabled ? "enabled" : "disabled");
}

BT_GATT_SERVICE_DEFINE(golden_service,
	BT_GATT_PRIMARY_SERVICE(&golden_service_uuid),
	BT_GATT_CHARACTERISTIC(&golden_data_uuid.uuid,
		BT_GATT_CHRC_READ | BT_GATT_CHRC_WRITE | BT_GATT_CHRC_NOTIFY,
		BT_GATT_PERM_READ_ENCRYPT | BT_GATT_PERM_WRITE_ENCRYPT,
		read_value, write_value, value),
	BT_GATT_CCC(ccc_changed, BT_GATT_PERM_READ_ENCRYPT | BT_GATT_PERM_WRITE_ENCRYPT));

static const struct bt_data advertising_data[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
	BT_DATA(BT_DATA_UUID128_ALL, golden_service_uuid.val, sizeof(golden_service_uuid.val)),
};

static const struct bt_data scan_response[] = {
	BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME,
		sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

static void connected(struct bt_conn *conn, uint8_t err)
{
	if (err != 0) {
		LOG_ERR("Connection failed (0x%02x)", err);
		return;
	}

	LOG_INF("Central connected");
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
	ARG_UNUSED(conn);
	notify_enabled = false;
	LOG_INF("Disconnected (0x%02x)", reason);
}

static void security_changed(struct bt_conn *conn, bt_security_t level,
			     enum bt_security_err err)
{
	ARG_UNUSED(conn);
	LOG_INF("Security level %u, error %d", level, err);
}

BT_CONN_CB_DEFINE(connection_callbacks) = {
	.connected = connected,
	.disconnected = disconnected,
	.security_changed = security_changed,
};

int main(void)
{
	int err = bt_enable(NULL);

	if (err != 0) {
		LOG_ERR("Bluetooth init failed (%d)", err);
		return 0;
	}

	err = bt_le_adv_start(BT_LE_ADV_CONN_FAST_1, advertising_data,
			      ARRAY_SIZE(advertising_data), scan_response,
			      ARRAY_SIZE(scan_response));
	if (err != 0) {
		LOG_ERR("Advertising failed (%d)", err);
		return 0;
	}

	LOG_INF("Advertising as %s", CONFIG_BT_DEVICE_NAME);

	for (;;) {
		if (notify_enabled) {
			uint8_t notification[8];
			uint32_t count = ++notify_counter;

			memcpy(notification, "NTFY", 4);
			sys_put_le32(count, &notification[4]);
			err = bt_gatt_notify(NULL, &golden_service.attrs[2],
					     notification, sizeof(notification));
			if (err != 0 && err != -ENOTCONN) {
				LOG_WRN("Notify failed (%d)", err);
			}
		}

		k_sleep(K_SECONDS(1));
	}
}
