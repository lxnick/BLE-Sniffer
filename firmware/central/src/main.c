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

LOG_MODULE_REGISTER(golden_central, LOG_LEVEL_INF);

#define TARGET_NAME "BLE-SNIFFER-P"
#define BT_UUID_GOLDEN_SERVICE_VAL \
	BT_UUID_128_ENCODE(0x8d53dc1d, 0x1db7, 0x4cd3, 0x868b, 0x8a527460aa84)
#define BT_UUID_GOLDEN_DATA_VAL \
	BT_UUID_128_ENCODE(0xda2e7828, 0xfbce, 0x4e01, 0xae9e, 0x261174997c48)

static struct bt_uuid_128 golden_service_uuid = BT_UUID_INIT_128(BT_UUID_GOLDEN_SERVICE_VAL);
static struct bt_uuid_128 golden_data_uuid = BT_UUID_INIT_128(BT_UUID_GOLDEN_DATA_VAL);
static struct bt_conn *default_conn;
static struct bt_gatt_discover_params discover_params;
static struct bt_gatt_write_params write_params;
static struct bt_gatt_read_params read_params;
static struct bt_gatt_subscribe_params subscribe_params;
static uint16_t service_end_handle;
static uint16_t value_handle;
static uint8_t notification_count;
static const uint8_t write_payload[] = "central-write";
static struct k_work_delayable scan_work;

static int start_scan(void);

static bool name_matches(struct bt_data *data, void *user_data)
{
	bool *matched = user_data;

	if ((data->type == BT_DATA_NAME_COMPLETE || data->type == BT_DATA_NAME_SHORTENED) &&
	    data->data_len == strlen(TARGET_NAME) &&
	    memcmp(data->data, TARGET_NAME, data->data_len) == 0) {
		*matched = true;
		return false;
	}

	return true;
}

static void device_found(const bt_addr_le_t *addr, int8_t rssi, uint8_t type,
			 struct net_buf_simple *ad)
{
	bool matched = false;
	int err;

	if (default_conn != NULL ||
	    (type != BT_GAP_ADV_TYPE_ADV_IND &&
	     type != BT_GAP_ADV_TYPE_ADV_DIRECT_IND &&
	     type != BT_GAP_ADV_TYPE_SCAN_RSP)) {
		return;
	}

	bt_data_parse(ad, name_matches, &matched);
	if (!matched) {
		return;
	}

	LOG_INF("Target found (RSSI %d)", rssi);
	err = bt_le_scan_stop();
	if (err != 0) {
		LOG_ERR("Scan stop failed (%d)", err);
		return;
	}

	err = bt_conn_le_create(addr, BT_CONN_LE_CREATE_CONN,
				BT_LE_CONN_PARAM_DEFAULT, &default_conn);
	if (err != 0) {
		LOG_ERR("Connection create failed (%d)", err);
		default_conn = NULL;
		k_work_schedule(&scan_work, K_SECONDS(1));
	}
}

static uint8_t notify_callback(struct bt_conn *conn,
			       struct bt_gatt_subscribe_params *params,
			       const void *data, uint16_t length)
{
	if (data == NULL) {
		LOG_INF("Notifications stopped");
		params->value_handle = 0;
		return BT_GATT_ITER_STOP;
	}

	notification_count++;
	LOG_HEXDUMP_INF(data, length, "Notification");
	if (notification_count >= 5) {
		LOG_INF("Golden sequence complete; disconnecting");
		bt_conn_disconnect(conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
		return BT_GATT_ITER_CONTINUE;
	}

	return BT_GATT_ITER_CONTINUE;
}

static uint8_t discover_ccc(struct bt_conn *conn,
			    const struct bt_gatt_attr *attr,
			    struct bt_gatt_discover_params *params)
{
	int err;

	if (attr == NULL) {
		LOG_ERR("CCC descriptor not found");
		memset(params, 0, sizeof(*params));
		return BT_GATT_ITER_STOP;
	}
	if (bt_uuid_cmp(attr->uuid, BT_UUID_GATT_CCC) != 0) {
		return BT_GATT_ITER_CONTINUE;
	}

	subscribe_params.notify = notify_callback;
	subscribe_params.value = BT_GATT_CCC_NOTIFY;
	subscribe_params.value_handle = value_handle;
	subscribe_params.ccc_handle = attr->handle;
	atomic_set_bit(subscribe_params.flags, BT_GATT_SUBSCRIBE_FLAG_VOLATILE);

	err = bt_gatt_subscribe(conn, &subscribe_params);
	if (err != 0 && err != -EALREADY) {
		LOG_ERR("Subscribe failed (%d)", err);
	} else {
		LOG_INF("Subscribed for notifications");
	}

	memset(params, 0, sizeof(*params));
	return BT_GATT_ITER_STOP;
}

static uint8_t read_callback(struct bt_conn *conn, uint8_t err,
			     struct bt_gatt_read_params *params,
			     const void *data, uint16_t length)
{
	if (err != 0) {
		LOG_ERR("GATT read failed (0x%02x)", err);
		return BT_GATT_ITER_STOP;
	}

	if (data != NULL) {
		LOG_HEXDUMP_INF(data, length, "GATT read");
		return BT_GATT_ITER_CONTINUE;
	}

	memset(&discover_params, 0, sizeof(discover_params));
	discover_params.uuid = NULL;
	discover_params.func = discover_ccc;
	discover_params.start_handle = value_handle + 1;
	discover_params.end_handle = service_end_handle;
	discover_params.type = BT_GATT_DISCOVER_DESCRIPTOR;
	if (bt_gatt_discover(conn, &discover_params) != 0) {
		LOG_ERR("CCC discovery start failed");
	}

	return BT_GATT_ITER_STOP;
}

static void write_callback(struct bt_conn *conn, uint8_t err,
			   struct bt_gatt_write_params *params)
{
	ARG_UNUSED(params);

	if (err != 0) {
		LOG_ERR("GATT write failed (0x%02x)", err);
		return;
	}

	LOG_INF("GATT write complete");
	memset(&read_params, 0, sizeof(read_params));
	read_params.func = read_callback;
	read_params.handle_count = 1;
	read_params.single.handle = value_handle;
	read_params.single.offset = 0;
	if (bt_gatt_read(conn, &read_params) != 0) {
		LOG_ERR("GATT read start failed");
	}
}

static uint8_t discover_characteristic(struct bt_conn *conn,
				       const struct bt_gatt_attr *attr,
				       struct bt_gatt_discover_params *params)
{
	const struct bt_gatt_chrc *chrc;

	if (attr == NULL) {
		LOG_ERR("Golden characteristic not found");
		memset(params, 0, sizeof(*params));
		return BT_GATT_ITER_STOP;
	}

	chrc = attr->user_data;
	value_handle = chrc->value_handle;
	memset(params, 0, sizeof(*params));

	write_params.handle = value_handle;
	write_params.offset = 0;
	write_params.data = write_payload;
	write_params.length = sizeof(write_payload) - 1;
	write_params.func = write_callback;
	if (bt_gatt_write(conn, &write_params) != 0) {
		LOG_ERR("GATT write start failed");
	}

	return BT_GATT_ITER_STOP;
}

static uint8_t discover_service(struct bt_conn *conn,
				const struct bt_gatt_attr *attr,
				struct bt_gatt_discover_params *params)
{
	const struct bt_gatt_service_val *service;

	if (attr == NULL) {
		LOG_ERR("Golden service not found");
		memset(params, 0, sizeof(*params));
		return BT_GATT_ITER_STOP;
	}

	service = attr->user_data;
	service_end_handle = service->end_handle;
	memset(params, 0, sizeof(*params));
	params->uuid = &golden_data_uuid.uuid;
	params->func = discover_characteristic;
	params->start_handle = attr->handle + 1;
	params->end_handle = service_end_handle;
	params->type = BT_GATT_DISCOVER_CHARACTERISTIC;
	if (bt_gatt_discover(conn, params) != 0) {
		LOG_ERR("Characteristic discovery start failed");
	}

	return BT_GATT_ITER_STOP;
}

static void start_discovery(struct bt_conn *conn)
{
	memset(&discover_params, 0, sizeof(discover_params));
	discover_params.uuid = &golden_service_uuid.uuid;
	discover_params.func = discover_service;
	discover_params.start_handle = BT_ATT_FIRST_ATTRIBUTE_HANDLE;
	discover_params.end_handle = BT_ATT_LAST_ATTRIBUTE_HANDLE;
	discover_params.type = BT_GATT_DISCOVER_PRIMARY;
	if (bt_gatt_discover(conn, &discover_params) != 0) {
		LOG_ERR("Service discovery start failed");
	}
}

static void connected(struct bt_conn *conn, uint8_t err)
{
	if (err != 0) {
		LOG_ERR("Connection failed (0x%02x)", err);
		bt_conn_unref(default_conn);
		default_conn = NULL;
		k_work_schedule(&scan_work, K_SECONDS(1));
		return;
	}

	LOG_INF("Connected; requesting security level 2");
	err = bt_conn_set_security(conn, BT_SECURITY_L2);
	if (err != 0) {
		LOG_ERR("Security request failed (%d)", err);
		bt_conn_disconnect(conn, BT_HCI_ERR_AUTH_FAIL);
	}
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
	LOG_INF("Disconnected (0x%02x)", reason);
	if (default_conn != NULL) {
		bt_conn_unref(default_conn);
		default_conn = NULL;
	}
	notification_count = 0;
	memset(&subscribe_params, 0, sizeof(subscribe_params));
	k_work_schedule(&scan_work, K_SECONDS(2));
}

static void security_changed(struct bt_conn *conn, bt_security_t level,
			     enum bt_security_err err)
{
	if (err != BT_SECURITY_ERR_SUCCESS) {
		LOG_ERR("Security failed (%d)", err);
		bt_conn_disconnect(conn, BT_HCI_ERR_AUTH_FAIL);
		return;
	}

	LOG_INF("Security level %u; discovering service", level);
	start_discovery(conn);
}

BT_CONN_CB_DEFINE(connection_callbacks) = {
	.connected = connected,
	.disconnected = disconnected,
	.security_changed = security_changed,
};

static void scan_work_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	start_scan();
}

static int start_scan(void)
{
	int err = bt_le_scan_start(BT_LE_SCAN_ACTIVE, device_found);

	if (err != 0) {
		LOG_ERR("Scan start failed (%d)", err);
		return err;
	}

	LOG_INF("Scanning for %s", TARGET_NAME);
	return 0;
}

int main(void)
{
	int err;

	k_work_init_delayable(&scan_work, scan_work_handler);
	err = bt_enable(NULL);
	if (err != 0) {
		LOG_ERR("Bluetooth init failed (%d)", err);
		return 0;
	}

	start_scan();
	return 0;
}
