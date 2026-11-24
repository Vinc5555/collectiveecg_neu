package com.polar.androidblesdk

import android.Manifest
import android.bluetooth.BluetoothGatt
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.Toast
import androidx.annotation.StringRes
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.graphics.drawable.DrawableCompat
import androidx.core.util.Pair
import com.google.android.material.snackbar.Snackbar
import com.polar.sdk.api.PolarBleApi
import com.polar.sdk.api.PolarBleApiCallback
import com.polar.sdk.api.PolarBleApiDefaultImpl
import com.polar.sdk.api.PolarH10OfflineExerciseApi
import com.polar.sdk.api.errors.PolarInvalidArgument
import com.polar.sdk.api.model.*
import io.reactivex.rxjava3.android.schedulers.AndroidSchedulers
import io.reactivex.rxjava3.core.Flowable
import io.reactivex.rxjava3.core.Single
import io.reactivex.rxjava3.disposables.Disposable
import java.util.*
import java.time.*
import kotlin.collections.HashMap
import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.roundToInt
import kotlin.time.*
class MainActivity : AppCompatActivity() {
    companion object {
        private const val TAG = "MainActivity"
        private const val API_LOGGER_TAG = "API LOGGER"
        private const val PERMISSION_REQUEST_CODE = 1
    }

    // ATTENTION! Replace with the device ID from your device.
    private var devID2sn = HashMap<String, String>()
    //init {
    //    devID2sn.put("A01", "E5695D2C")
    //}
    private val api: PolarBleApi by lazy {
        // Notice all features are enabled
        PolarBleApiDefaultImpl.defaultImplementation(
            applicationContext,
            setOf(
                PolarBleApi.PolarBleSdkFeature.FEATURE_HR,
                PolarBleApi.PolarBleSdkFeature.FEATURE_POLAR_SDK_MODE,
                PolarBleApi.PolarBleSdkFeature.FEATURE_BATTERY_INFO,
                PolarBleApi.PolarBleSdkFeature.FEATURE_POLAR_H10_EXERCISE_RECORDING,
                PolarBleApi.PolarBleSdkFeature.FEATURE_POLAR_OFFLINE_RECORDING,
                PolarBleApi.PolarBleSdkFeature.FEATURE_POLAR_ONLINE_STREAMING,
                PolarBleApi.PolarBleSdkFeature.FEATURE_POLAR_DEVICE_TIME_SETUP,
                PolarBleApi.PolarBleSdkFeature.FEATURE_DEVICE_INFO,
                PolarBleApi.PolarBleSdkFeature.FEATURE_POLAR_LED_ANIMATION
            )
        )
    }

    private lateinit var broadcastDisposable: Disposable
    private var deviceConnected = false
    private var bluetoothEnabled = false
    private var deviceId:String = ""

    private lateinit var deviceIdInput: EditText
    private lateinit var registerDevice: Button

    private lateinit var broadcastButton: Button
    private lateinit var connectButton: Button

    private val entryCache: MutableMap<String, MutableList<PolarOfflineRecordingEntry>> = mutableMapOf()



    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        Log.d(TAG, "version: " + PolarBleApiDefaultImpl.versionInfo())
        deviceIdInput = findViewById(R.id.device_id_input)
        registerDevice = findViewById(R.id.register_device_id)
        broadcastButton = findViewById(R.id.broadcast_button)
        connectButton = findViewById(R.id.connect_button)
        devID2sn["A03"] = "01AB0134"
        devID2sn["A04"] = "01AB0437"
        devID2sn["A05"] = "02F1F63C"
        devID2sn["A06"] = "02F2BD38"
        devID2sn["A08"] = "02EF0C30"
        devID2sn["A09"] = "02EF143B"
        devID2sn["A10"] = "02F1F93F"
        devID2sn["A11"] = "02F1FA30"
        devID2sn["B03"] = "02F2C735"
        devID2sn["B04"] = "02F2DE3F"
        devID2sn["B05"] = "0230C33B"
        devID2sn["B06"] = "0230B338"
        devID2sn["B08"] = "02301239"
        devID2sn["B09"] = "0230D43F"
        devID2sn["B10"] = "022F783D"
        devID2sn["B11"] = "0230CA32"
        devID2sn["C03"] = "02305A3D"
        devID2sn["C04"] = "02306238"
        devID2sn["C05"] = "0230C139"
        devID2sn["C06"] = "0230BE33"
        devID2sn["C08"] = "02EB423E"
        devID2sn["C09"] = "02E92034"
        devID2sn["C10"] = "02EB5D3C"
        devID2sn["C11"] = "02F20630"
        devID2sn["D03"] = "02F2C230"
        devID2sn["D04"] = "02EB6F31"
        devID2sn["D05"] = "02EBC83C"
        devID2sn["D06"] = "02EB7136"
        devID2sn["D08"] = "02EBAF3D"
        devID2sn["D09"] = "02F2CC3A"
        devID2sn["D10"] = "01AA9633"
        devID2sn["D11"] = "02EB6537"
        devID2sn["S01"] = "01AAF130"
        devID2sn["S02"] = "01AAF635"
        devID2sn["S03"] = "01AAE33F"
        devID2sn["S04"] = "01AA5D3E"
        devID2sn["T01"] = "E44F832A"
        devID2sn["T02"] = "E5695D2C"
        devID2sn["T03"] = "EB4CAC2D"
        devID2sn["T04"] = "01AB073A"
        devID2sn["T05"] = "01AA9A37"
        devID2sn["T06"] = "01AADD36"

        api.setPolarFilter(false)

        // If there is need to log what is happening inside the SDK, it can be enabled like this:
        val enableSdkLogs = false
        if(enableSdkLogs) {
            api.setApiLogger { s: String -> Log.d(API_LOGGER_TAG, s) }
        }

        api.setApiCallback(object : PolarBleApiCallback() {
            override fun blePowerStateChanged(powered: Boolean) {
                Log.d(TAG, "BLE power: $powered")
                bluetoothEnabled = powered
                if (powered) {
                    enableAllButtons()
                    showToast("Phone Bluetooth on")
                } else {
                    disableAllButtons()
                    showToast("Phone Bluetooth off")
                }
            }

            override fun deviceConnected(polarDeviceInfo: PolarDeviceInfo) {
                Log.d(TAG, "CONNECTED: ${polarDeviceInfo.deviceId}")
                deviceId = polarDeviceInfo.deviceId
                deviceConnected = true
                val buttonText = getString(R.string.disconnect_from_device, deviceId)
                toggleButtonDown(connectButton, buttonText)
                //showToast("device is connected to " + polarDeviceInfo.deviceId)
                //showToast("device is connected to juju " + deviceId)
                showToast("Successfully connected")

                // Wait 7500 ms for service discovery
                Thread.sleep(7500)


                // Wait until close to a round second
                var curr_time_now = Instant.now()

                val curr_time_milli = curr_time_now.toEpochMilli()


                var curr_time = curr_time_milli.toFloat() * 0.001

                var curr_time_ceil = ceil(Instant.now().toEpochMilli().toFloat() * 0.001)
                var time_to_sleep = ((curr_time_ceil * 1000 - Instant.now().toEpochMilli().toFloat()).toLong())
                showToast("sleeping for " + time_to_sleep.toString())
                //showToast("waiting for " + ((curr_time_ceil * 1000 - Instant.now().toEpochMilli().toFloat()).toLong()).toString())
                // Thread.sleep(( (1000* curr_time_ceil - Instant.now().toEpochMilli().toFloat()).toLong()))
                Thread.sleep(time_to_sleep)
                //var rounded_time = curr_time.roundToInt().toFloat()
                //showToast("rounded time" + rounded_time)
                //val tol = 0.001
                //showToast("Entering Whiled territory")
                //while (kotlin.math.abs(curr_time - rounded_time) > tol) {
                //    // keep looping until close to perfect second
                //        curr_time_now = Instant.now()
                //        curr_time = curr_time_now.toEpochMilli().toFloat()* 0.001
                //        rounded_time = curr_time.roundToInt().toFloat()
                //    Log.d(TAG,"new value is $curr_time_now $rounded_time  " + kotlin.math.abs(curr_time - rounded_time).toString())
                //    }

                // When perfect second, push time to polar device
                val calendar = Calendar.getInstance()
                curr_time_now = Instant.now()
                calendar.time = Date.from(curr_time_now)
                api.setLocalTime(deviceId, calendar)
                    .observeOn(AndroidSchedulers.mainThread())
                    .subscribe(
                        {
                            val timeSetString = "time ${calendar.time}, set to device"
                            Log.d(TAG, timeSetString)
                            showToast(timeSetString)
                        },
                        { error: Throwable -> Log.e(TAG, "set time failed: $error") }
                    )
                var curr_time_milli_2 = curr_time_now.toEpochMilli()


                var curr_time_2 = curr_time_milli_2.toFloat()
                showToast("set time as " + curr_time_2.toString())
            }

            override fun deviceConnecting(polarDeviceInfo: PolarDeviceInfo) {
                Log.d(TAG, "CONNECTING: ${polarDeviceInfo.deviceId}")
            }

            override fun deviceDisconnected(polarDeviceInfo: PolarDeviceInfo) {
                Log.d(TAG, "DISCONNECTED: ${polarDeviceInfo.deviceId}")
                deviceConnected = false
                val buttonText = getString(R.string.connect_to_device, deviceId)
                toggleButtonUp(connectButton, buttonText)
                //toggleButtonUp(toggleSdkModeButton, R.string.enable_sdk_mode)
            }

            override fun disInformationReceived(identifier: String, uuid: UUID, value: String) {
                Log.d(TAG, "DIS INFO uuid: $uuid value: $value")
            }

            override fun batteryLevelReceived(identifier: String, level: Int) {
                Log.d(TAG, "BATTERY LEVEL: $level")
            }

        })
    
        registerDevice.setOnClickListener {
            val userInput = deviceIdInput.text.toString()

            showToast("using device id " + userInput + " " + devID2sn[userInput] + " " + devID2sn[userInput].toString())
            // get device id from user input
            //deviceId = devID2sn[userInput.toString()]
            //var chosenDevice:String =
            deviceId = devID2sn[userInput].toString()
            // update connect button text
            connectButton.text = getString(R.string.connect_to_device, deviceId)
        }

        broadcastButton.setOnClickListener {
            if (!this::broadcastDisposable.isInitialized || broadcastDisposable.isDisposed) {
                toggleButtonDown(broadcastButton, R.string.listening_broadcast)
                broadcastDisposable = api.startListenForPolarHrBroadcasts(null)
                    .subscribe(
                        { polarBroadcastData: PolarHrBroadcastData ->
                            showToast("HR BROADCAST ${polarBroadcastData.polarDeviceInfo.deviceId} HR: ${polarBroadcastData.hr} batt: ${polarBroadcastData.batteryStatus}")
                        },
                        { error: Throwable ->
                            toggleButtonUp(broadcastButton, R.string.listen_broadcast)
                            Log.e(TAG, "Broadcast listener failed. Reason $error")
                        },
                        { Log.d(TAG, "complete") }
                    )
            } else {
                toggleButtonUp(broadcastButton, R.string.listen_broadcast)
                broadcastDisposable.dispose()
            }
        }

        connectButton.text = getString(R.string.connect_to_device, deviceId)
        connectButton.setOnClickListener {
            if (deviceId=="") {
                showToast("Please Enter Device Id First")
            } else {
                try {
                    showToast("Trying Connection with " + deviceId)
                    if (deviceConnected) {
                        api.disconnectFromDevice(deviceId)
                    } else {
                        // Attempt connection
                        api.connectToDevice(deviceId)

                        showToast("connecting to " + deviceId)
                    }
                } catch (polarInvalidArgument: PolarInvalidArgument) {
                    val attempt = if (deviceConnected) {
                        "disconnect"
                    } else {
                        "connect"
                    }
                    Log.e(TAG, "Failed to $attempt. Reason $polarInvalidArgument ")
                }
            }
        }


        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                requestPermissions(arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT), PERMISSION_REQUEST_CODE)
            } else {
                requestPermissions(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION), PERMISSION_REQUEST_CODE)
            }
        } else {
            requestPermissions(arrayOf(Manifest.permission.ACCESS_COARSE_LOCATION), PERMISSION_REQUEST_CODE)
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            for (index in 0..grantResults.lastIndex) {
                if (grantResults[index] == PackageManager.PERMISSION_DENIED) {
                    disableAllButtons()
                    Log.w(TAG, "No sufficient permissions")
                    showToast("No sufficient permissions")
                    return
                }
            }
            Log.d(TAG, "Needed permissions are granted")
            enableAllButtons()
        }
    }

    public override fun onPause() {
        super.onPause()
    }

    public override fun onResume() {
        super.onResume()
        api.foregroundEntered()
    }

    public override fun onDestroy() {
        super.onDestroy()
        api.shutDown()
    }

    private fun toggleButtonDown(button: Button, text: String? = null) {
        toggleButton(button, true, text)
    }

    private fun toggleButtonDown(button: Button, @StringRes resourceId: Int) {
        toggleButton(button, true, getString(resourceId))
    }

    private fun toggleButtonUp(button: Button, text: String? = null) {
        toggleButton(button, false, text)
    }

    private fun toggleButtonUp(button: Button, @StringRes resourceId: Int) {
        toggleButton(button, false, getString(resourceId))
    }

    private fun toggleButton(button: Button, isDown: Boolean, text: String? = null) {
        if (text != null) button.text = text

        var buttonDrawable = button.background
        buttonDrawable = DrawableCompat.wrap(buttonDrawable!!)
        if (isDown) {
            DrawableCompat.setTint(buttonDrawable, resources.getColor(R.color.primaryDarkColor))
        } else {
            DrawableCompat.setTint(buttonDrawable, resources.getColor(R.color.primaryColor))
        }
        button.background = buttonDrawable
    }

    private fun requestStreamSettings(identifier: String, feature: PolarBleApi.PolarDeviceDataType): Flowable<PolarSensorSetting> {
        val availableSettings = api.requestStreamSettings(identifier, feature)
        val allSettings = api.requestFullStreamSettings(identifier, feature)
            .onErrorReturn { error: Throwable ->
                Log.w(TAG, "Full stream settings are not available for feature $feature. REASON: $error")
                PolarSensorSetting(emptyMap())
            }
        return Single.zip(availableSettings, allSettings) { available: PolarSensorSetting, all: PolarSensorSetting ->
            if (available.settings.isEmpty()) {
                throw Throwable("Settings are not available")
            } else {
                Log.d(TAG, "Feature " + feature + " available settings " + available.settings)
                Log.d(TAG, "Feature " + feature + " all settings " + all.settings)
                return@zip android.util.Pair(available, all)
            }
        }
            .observeOn(AndroidSchedulers.mainThread())
            .toFlowable()
            .flatMap { sensorSettings: android.util.Pair<PolarSensorSetting, PolarSensorSetting> ->
                DialogUtility.showAllSettingsDialog(
                    this@MainActivity,
                    sensorSettings.first.settings,
                    sensorSettings.second.settings
                ).toFlowable()
            }
    }

    private fun showToast(message: String) {
        val toast = Toast.makeText(applicationContext, message, Toast.LENGTH_LONG)
        toast.show()
    }

    private fun showSnackbar(message: String) {
        val contextView = findViewById<View>(R.id.buttons_container)
        Snackbar.make(contextView, message, Snackbar.LENGTH_LONG)
            .show()
    }

    private fun showDialog(title: String, message: String) {
        AlertDialog.Builder(this)
            .setTitle(title)
            .setMessage(message)
            .setPositiveButton("OK") { _, _ ->
                // Respond to positive button press
            }
            .show()
    }

    private fun disableAllButtons() {

        connectButton.isEnabled = false
        broadcastButton.isEnabled = false
    }

    private fun enableAllButtons() {

        connectButton.isEnabled = true
        broadcastButton.isEnabled = true

    }

    private fun disposeAllStreams() {
    }
}
