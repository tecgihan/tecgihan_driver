from threading import Thread

import time

import serial
import serial.tools.list_ports


class DPA06BDriver:
    """Driver I/O class for DPA-06B amplifier.

    No UART parameters (baudrate, parity, etc.) are required.
    """

    def _open(self, port='/dev/ttyUSB0', timeout=1.0):
        """Open a port for DPA-06B.

        No baudrate or UART parameters are set.

        Args:
            port (str, optional): The device port. Defaults to '/dev/ttyUSB0'.
            timeout (float, optional): Set a read timeout value in seconds. Defaults to 1.0.
        """
        self._ser = serial.Serial(port=port,
                                  timeout=timeout,
                                  write_timeout=timeout * 2.0)
        if self._is_connected():
            print('Port Opened: {}'.format(self._ser.name))
        else:
            print('Port Open Error: {}'.format(self._ser.name))

    def _close(self):
        """Close the serial port."""
        self._reset_input_buffer()
        self._ser.close()
        if not self._is_connected():
            print('Port Disconnected: {}'.format(self._ser.name))

    def _print_info(self):
        """Print the serial port informations."""
        print(' port: {}'.format(self._ser.name))
        for k, v in self._ser.get_settings().items():
            print(' {}: {}'.format(k, v))

    def _is_connected(self):
        """Return the serial port is connected or not.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._ser and self._ser.is_open

    def _send_command(self, command_string):
        """Send command to the serial port write buffer with the command string.

        Args:
            command_string (str): The command to write.

        Returns:
            int: Number of bytes written.
        """
        command_bytes = command_string.encode('utf-8')
        if getattr(self, '_debug', False):
            print('Command Bytes: {}'.format(command_bytes))
        result = self._ser.write(command_bytes)
        if getattr(self, '_debug', False):
            print('Write Data Result (Command Length): {}'.format(result))
        return result

    def _recv_command(self, terminator=b'\n'):
        r"""Read the serial port input buffer until the terminator.

        Args:
            terminator (bytes, optional):
                The terminator to end reading. Defaults to b'\n'.

        Returns:
            str: The received and UTF-8 decoded data.
        """
        result = b''
        try:
            result = self._ser.read_until(terminator)
            # remove tailing \n
            if len(result) >= len(terminator) and result.endswith(terminator):
                result = result[:-len(terminator)]
        except serial.SerialException as e:
            print('Serial Error: {}'.format(e))
        except serial.SerialTimeoutException:
            print('Command Timeout')
        except Exception:
            print('Can Not Receive Command')
        return result.decode('utf-8')

    def _reset_input_buffer(self):
        """Reset the serial port input buffer."""
        self._ser.reset_input_buffer()

    def _find_port_by_id(self, vendor_id, product_id):
        """Find a serial port by a vendor ID and a product ID.

        Args:
            vendor_id (int): The device vendor ID.
            product_id (int): The device product ID.

        Returns:
            Union[str, None]:
                - str: The port device string like '/dev/ttyUSB0'.
                - None: VID or PID did not match the actual device connected.
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == vendor_id and port.pid == product_id:
                return port.device
        return None

    def _find_port_by_name(self, product_name, serial_number=None, location=None):
        """Find a serial port by a device name and optionally by a device location.

        Args:
            product_name (str): The product name of the amplifier.
            serial_number (str, optional): The device serial number. Defaults to None.
            location (str, optional): The device location like '1-2'. Defaults to None.

        Returns:
            Union[dict, None]:
                - dict: {'port': str, 'product': str}
                - None: The args did not match the actual device connected.
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.product and product_name in port.product:
                if serial_number:
                    if port.serial_number and serial_number in port.serial_number:
                        print(
                            'Device Serial No. Specified: {}'.format(port.serial_number))
                        return {
                            'port': port.device,
                            'product': port.product
                        }
                elif location:
                    if port.location and location in port.location:
                        print(
                            'Device Location Specified: {}'.format(port.location))
                        return {
                            'port': port.device,
                            'product': port.product
                        }
                else:
                    print(
                        'Device Location or Serial No. - NOT Specified'
                        'and 1st Device Chosen')
                    return {
                        'port': port.device,
                        'product': port.product
                    }
        return None


class DPA06BDriverForRobot(DPA06BDriver):
    """Command I/O class for DPA-06B amplifier.

    DPA-06B supports two sensor configurations selectable by sensor_mode:
        '3axis' : 3-axis sensor x 2 (default)
                  - ITF: 3x3=9 values x 2 sets
                         (one set for 3-axis sensor1, one set for 3-axis sensor2)
                  - FS : 6 values [ch1,ch2,ch3,ch4,ch5,ch6]
        '6axis' : 6-axis sensor x 1
                  - ITF: 6x6=36 values x 1 set
                  - FS : 6 values [ch1,ch2,ch3,ch4,ch5,ch6]
    """

    # Number of channels
    CH_COUNT = 6
    # Number of hex characters per channel (16bit = 4 hex chars)
    CHR_PER_CH = 4
    # ITF matrix dimension for 3axis mode (3x3)
    ITF_COUNT_3AXIS = 9
    # ITF matrix dimension for 6axis mode (6x6)
    ITF_COUNT_6AXIS = 36
    # ITF element index map for 3axis sensor1 (3x3 block at rows 0-2, cols 0-2 of 6x6)
    ITF_MAP_3AXIS_SENSOR_1 = [0, 1, 2, 6, 7, 8, 12, 13, 14]
    # ITF element index map for 3axis sensor2 (3x3 block at rows 3-5, cols 3-5 of 6x6)
    ITF_MAP_3AXIS_SENSOR_2 = [21, 22, 23, 27, 28, 29, 33, 34, 35]
    # ITF element index map for 6axis mode (full 6x6 matrix, items 0-35)
    ITF_MAP_6AXIS = list(range(36))

    def __init__(self,
                 debug=False,
                 frequency=1000,
                 init_zero=False,
                 timeout=1.0,
                 serial_number=None,
                 location=None,
                 sensor_mode='3axis'):
        """Construct DPA06BDriverForRobot class instance.

        Args:
            debug (bool, optional): True is for Debug mode, False is not.
                                    Defaults to False.
            frequency (int, optional): Sensing frequency.
                                        Defaults to 1000.
            init_zero (bool, optional): True to initialize as Zero forces.
                                        Defaults to False.
            timeout (float, optional): The max time [sec] to wait data
                                        during read operation. Defaults to 1.0.
            serial_number (str, optional): The device serial number
                                            to distinguish between multiple amplifiers.
                                            Defaults to None.
            location (str, optional): The device location like '1-2'
                                            to distinguish between multiple amplifiers.
                                            Defaults to None.
            sensor_mode (str, optional): Sensor configuration mode.
                                          '3axis': 3-axis sensor x 2 (ITF: 3x3 x 2).
                                          '6axis': 6-axis sensor x 1 (ITF: 6x6 x 1).
                                          Defaults to '3axis'.
        """
        print('Tec Gihan DPA-06B Driver: Starting ...')

        if sensor_mode not in ('3axis', '6axis'):
            print("Warning: Unknown sensor_mode '{}', using '3axis'".format(sensor_mode))
            sensor_mode = '3axis'
        self._sensor_mode = sensor_mode
        print('Sensor Mode: {}'.format(self._sensor_mode))

        search_name = 'DPA-06'
        port = '/dev/ttyUSB0'
        product_name = 'DPA-06'
        info = self._find_port_by_name(
            product_name=search_name, serial_number=serial_number, location=location)
        if info is None:
            print('DPA-06 not found.')
            self._ser = None
            return
        port = info['port']
        product_name = info['product']
        self._open(port, timeout=timeout)
        time.sleep(1)

        if self._is_connected():
            print('Connected: {}'.format(product_name))
            self._print_info()
        else:
            print('Not Connected: {}'.format(product_name))
            return

        self._debug = debug
        self.stop()

        # Ensure robot mode is enabled
        self.set_for_robot()

        if init_zero:
            self.set_zero()

        # frequency
        current_frequency = self.get_frequency()
        if current_frequency != frequency:
            if self.set_frequency(frequency):
                self._frequency = frequency
                print('DPA-06B: SET Frequency: {}Hz -> {}Hz'.format(
                    current_frequency, frequency))
            else:
                self._frequency = (
                    current_frequency if current_frequency is not None else frequency)
                print('DPA-06B: set_frequency failed, keeping frequency: {}'.format(
                    self._frequency))
        else:
            self._frequency = frequency
            print('DPA-06B: Device Frequency ({}Hz) already matches target, skipping SET'.format(
                current_frequency))

        # FS for all 6 channels
        fs_list = self.get_fs()
        if fs_list:
            (self._fs_ch1, self._fs_ch2, self._fs_ch3,
             self._fs_ch4, self._fs_ch5, self._fs_ch6) = fs_list
        else:
            (self._fs_ch1, self._fs_ch2, self._fs_ch3,
             self._fs_ch4, self._fs_ch5, self._fs_ch6) = (1000,) * 6
            print('FS read failed, using default values (1000 x 6)')

        # ITF depends on sensor_mode
        if self._sensor_mode == '3axis':
            self.get_itf_3axis_sensor1()  # sensor 1 (ch1-3): 3x3=9
            self.get_itf_3axis_sensor2()  # sensor 2 (ch4-6): 3x3=9
        else:
            self.get_itf_6axis()    # 6-axis sensor: 6x6=36

        self._assigning = False
        self._eng1 = 0.0
        self._eng2 = 0.0
        self._eng3 = 0.0
        self._eng4 = 0.0
        self._eng5 = 0.0
        self._eng6 = 0.0
        self._data_time = time.time()

        self._convert_data = False
        self._thr = Thread(target=self._data_conversion)
        self._thr.start()

    def __del__(self):
        """Destructor of this class instance."""
        self.close()

    def _data_conversion(self):
        """Aquire and convert sensing data with thread."""
        data_length = self.CH_COUNT * self.CHR_PER_CH  # 6 * 4 = 24
        while self._is_connected():
            # Skip if self._convert_data is False
            if not self._convert_data:
                if self._debug:
                    print('Convert waiting...')
                time.sleep(0.1)
                continue
            buffer = self._recv_command()
            last_time = self._data_time
            self._data_time = time.time()
            diff_time = self._data_time - last_time
            if len(buffer) == data_length:
                data = int('0x' + buffer, 0)
                ch1 = (data >> (5 * 16)) & 0xffff
                ch2 = (data >> (4 * 16)) & 0xffff
                ch3 = (data >> (3 * 16)) & 0xffff
                ch4 = (data >> (2 * 16)) & 0xffff
                ch5 = (data >> (1 * 16)) & 0xffff
                ch6 = data & 0xffff
                ad1 = self._to_signedint(ch1)
                ad2 = self._to_signedint(ch2)
                ad3 = self._to_signedint(ch3)
                ad4 = self._to_signedint(ch4)
                ad5 = self._to_signedint(ch5)
                ad6 = self._to_signedint(ch6)
                self._assigning = True
                if self._sensor_mode == '3axis':
                    # Sensor 1 (ch1-3) and Sensor 2 (ch4-6) calculated separately
                    self._eng1, self._eng2, self._eng3 = self._calculate_eng_data(
                        ad1, ad2, ad3,
                        self._fs_ch1, self._fs_ch2, self._fs_ch3)
                    self._eng4, self._eng5, self._eng6 = self._calculate_eng_data(
                        ad4, ad5, ad6,
                        self._fs_ch4, self._fs_ch5, self._fs_ch6)
                else:
                    # 6-axis sensor: all 6 channels calculated together
                    (self._eng1, self._eng2, self._eng3,
                     self._eng4, self._eng5, self._eng6) = self._calculate_eng_data(
                        ad1, ad2, ad3, ad4, ad5, ad6,
                        self._fs_ch1, self._fs_ch2, self._fs_ch3,
                        self._fs_ch4, self._fs_ch5, self._fs_ch6)
                self._assigning = False
                if self._debug:
                    print('Time: {} (Diff: {} )'.format(
                        self._data_time, diff_time))
                    print('Buffer: {}'.format(buffer))
                    print('Hex: ( 0x{:04x}, 0x{:04x}, 0x{:04x},'
                          ' 0x{:04x}, 0x{:04x}, 0x{:04x} )'.format(
                              ch1, ch2, ch3, ch4, ch5, ch6))
                    print('Int: ( {:10d}, {:10d}, {:10d},'
                          ' {:10d}, {:10d}, {:10d} )'.format(
                              ad1, ad2, ad3, ad4, ad5, ad6))
                    print('Eng: ( {:10.5f}, {:10.5f}, {:10.5f},'
                          ' {:10.5f}, {:10.5f}, {:10.5f} )'.format(
                              self._eng1, self._eng2, self._eng3,
                              self._eng4, self._eng5, self._eng6))
                self._ros_publish()
            else:
                if self._debug:
                    print('NOT DATA [{}]'.format(buffer))
            time.sleep(0.6 / self._frequency)

    def _ros_publish(self):
        """Be overrided in a ROS node.

        An empty function to override in a ROS node
        to publish a ROS topic after the data conversion.

        Returns:
            bool: False
        """
        return False

    def _calculate_eng_data(self, ad1, ad2, ad3,
                            fs1, fs2, fs3,
                            ad4=None, ad5=None, ad6=None,
                            fs4=None, fs5=None, fs6=None):
        """Calculate the engineering data from signed int data with FS values.

        For '3axis' mode: call with 3 channels (ad1-3, fs1-3).
        For '6axis' mode: call with 6 channels (ad1-6, fs1-6).

        Args:
            ad1 (int): Channel 1 integer value.
            ad2 (int): Channel 2 integer value.
            ad3 (int): Channel 3 integer value.
            fs1 (int): Full Scale value for channel 1.
            fs2 (int): Full Scale value for channel 2.
            fs3 (int): Full Scale value for channel 3.
            ad4 (int, optional): Channel 4 integer value. For '6axis' mode.
            ad5 (int, optional): Channel 5 integer value. For '6axis' mode.
            ad6 (int, optional): Channel 6 integer value. For '6axis' mode.
            fs4 (int, optional): Full Scale value for channel 4. For '6axis' mode.
            fs5 (int, optional): Full Scale value for channel 5. For '6axis' mode.
            fs6 (int, optional): Full Scale value for channel 6. For '6axis' mode.

        Returns:
            Tuple[float, ...]:
                3 floats for '3axis' mode, 6 floats for '6axis' mode.
        """
        eng1 = ad1 * fs1 / 32000
        eng2 = ad2 * fs2 / 32000
        eng3 = ad3 * fs3 / 32000
        if ad4 is not None:
            eng4 = ad4 * fs4 / 32000
            eng5 = ad5 * fs5 / 32000
            eng6 = ad6 * fs6 / 32000
            return eng1, eng2, eng3, eng4, eng5, eng6
        return eng1, eng2, eng3

    def _to_signedint(self, value: int, bits=16):
        """Convert an unsigned int to a signed int.

        Converts an unsigned integer to its signed integer representation
        using two's complement.

        Args:
            value (int): The unsigned integer to convert.
            bits (int, optional): The bit width to interpret the value with.
                                    Defaults to 16.

        Returns:
            int: The signed integer representation of the input value.
        """
        if value & (1 << (bits - 1)):
            value -= 1 << bits
        return value

    def _get_reply(self, command_string: str):
        """Send a command to the amplifier and get a reply for it.

        Args:
            command_string (str): Command to send.

        Returns:
            str: Reply for the command.
        """
        data_length = self.CH_COUNT * self.CHR_PER_CH  # 24
        self._convert_data = False
        time.sleep(0.2)
        self._send_command(command_string)
        time.sleep(0.5)
        reply = 'x' * data_length  # dummy to enter loop
        while len(reply) == data_length:  # skip data
            reply = self._recv_command()
        if getattr(self, '_debug', False):
            print('Get reply: {}'.format(reply))
        return reply

    def start(self):
        """Send START command to the amplifier and start the data conversion.

        Returns:
            str: Reply for the command.
        """
        reply = self._get_reply('START\n')
        self._convert_data = True
        return reply

    def stop(self):
        """Send STOP command to the amplifier and stop the data conversion.

        Unlike other commands handled via _get_reply(), STOP is sent while
        the data acquisition thread may still be mid-stream. _get_reply()
        only skips replies whose length exactly matches a full data packet
        (data_length chars), so a truncated/partial data packet received
        right after STOP can slip through as if it were the STOP reply.
        To avoid that, explicitly wait for a line containing STOP_OK or
        STOP_NG (max 2 seconds), discarding anything else in between.

        Returns:
            str: 'STOP_OK' or 'STOP_NG' on a valid reply,
                 '' if no reply was received within the timeout.
        """
        self._convert_data = False
        self._send_command('STOP\n')

        reply = ''
        deadline = time.time() + 2.0
        while time.time() < deadline:
            line = self._recv_command()
            if 'STOP_OK' in line:
                reply = 'STOP_OK'
                break
            if 'STOP_NG' in line:
                reply = 'STOP_NG'
                break
        print('Get reply: {}'.format(
            reply if reply else 'STOP timeout (no STOP_OK/STOP_NG received)'))

        self._reset_input_buffer()
        return reply

    def close(self):
        """Close the serial port.

        Close the serial port
        after stopping the amplifier and the data conversion process.
        """
        self._convert_data = False
        if self._is_connected():
            self.stop()
            self._close()
        if hasattr(self, '_thr') and isinstance(self._thr, Thread):
            self._thr.join()

    def is_connected(self):
        """Return the serial port is connected or not.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._is_connected()

    def set_zero(self):
        """Start zero force adjustment and store them.

        Returns:
            str: Reply for the command.

        Note:
            - The adjustment takes around 2 seconds after sending the command.
            - The adjustment data are stored in non-volatile memory in the amplifier.
        """
        restart = self._convert_data
        self._reset_input_buffer()
        reply = self.stop()
        if reply == 'STOP_OK':
            wait_ = 3.0
            print('Send ZERO command and wait {} seconds ...'.format(wait_))
            self._send_command('ZERO\n')
            time.sleep(wait_)  # Wait more than 2.0 seconds
            reply = 'Set ZERO: '
            reply += self._recv_command()
            self.stop()
            if restart:
                reply += ' and Restart: '
                reply += self.start()
        else:
            reply += ' and ZERO command: Not Sent'
        print(reply)
        return reply

    def get_for_robot(self):
        """Get the amplifier has functions for robot usage or not.

        Returns:
            Tuple[str, bool]:
                - str:  Reply for the command.
                - bool: True if for Robot, False if not for robot.
        """
        reply = self._get_reply('GET_FOR_ROBOT\n')
        success = False
        if reply == 'FOR_ROBOT_0' or reply == 'FOR_ROBOT_1':
            success = True
        return reply, success

    def set_for_robot(self):
        """Set the amplifier to robot mode if available or to non-robot mode.

        Returns:
            str: Reply for the command or error message if failure.
        """
        self._convert_data = False
        reply, success = self.get_for_robot()
        print('Get For Robot: Reply={}, Success={}'.format(reply, success))
        self._convert_data = False
        time.sleep(0.1)
        set_reply = 'Set for Robot: Error'
        if success and reply == 'FOR_ROBOT_0':
            set_reply = self._get_reply('SET_FOR_ROBOT_1\n')
            print('Set For Robot 1: Reply={}'.format(set_reply))
        else:
            print('Set For Robot 1: Skipped (Reply={}, Success={})'.format(reply, success))
        return set_reply

    def get_fs(self):
        """Get a list of 6 int data of FS (Full Scale) from the amplifier.

        Returns:
            List[int]: List of 6 int FS [ch1,ch2,ch3,ch4,ch5,ch6] data.
        """
        reply = self._get_reply('GET_FS\n')

        if reply.startswith('FS_'):
            reply = reply.replace('FS_', '')
        else:
            return None
        reply = reply.split(',')

        if len(reply) != self.CH_COUNT:
            print('FS Dimension Error: {}/{}'.format(len(reply), self.CH_COUNT))
            return None
        fs = [int(v) for v in reply]
        print('Get FS (from device): ({})'.format(','.join(str(v) for v in fs)))
        return fs

    def set_fs(self, val_list: list[int]):
        """Set 6 int data of FS (Full Scale) to the amplifier.

        Args:
            val_list (list[int]): List of 6 int FS [ch1,ch2,ch3,ch4,ch5,ch6].

        Returns:
            bool: True on success, False on failure.

        Note:
            The set data are stored in non-volatile memory in the amplifier.
        """
        if len(val_list) != self.CH_COUNT:
            print('Set FS Dimension Error: {}/{}'.format(len(val_list), self.CH_COUNT))
            return False

        for i in range(self.CH_COUNT):
            command_string = 'SET_FS_' + str(i) + '_' + str(val_list[i]) + '\n'
            self._get_reply(command_string)

        # Check for each
        overall_result = True
        get_list = self.get_fs()
        if get_list is None:
            print('Set FS Check Error: Could not read back FS values')
            return False
        for i in range(self.CH_COUNT):
            result = True
            if val_list[i] != get_list[i]:
                overall_result = result = False
            if self._debug:
                print('Check Value: No.{} Set:{:5} Get:{:5} Check: {}'.format(
                    i, val_list[i], get_list[i], result))
        if overall_result:
            (self._fs_ch1, self._fs_ch2, self._fs_ch3,
             self._fs_ch4, self._fs_ch5, self._fs_ch6) = get_list
        return overall_result

    # -------------------------------------------------------------------------
    # ITF for 3axis mode: 3x3=9 values x 2 sets
    # (one set for 3-axis sensor1, one set for 3-axis sensor2)
    #
    # The amplifier exposes only ONE ITF command pair for the whole 6x6
    # (actually addressed as "6x12", items 0-71, but only 0-35 are used)
    # interference correction matrix:
    #     GET_ITF_6X12_xx        -> reply: ITF_6X12_<value>
    #     SET_ITF_6X12_xx_<value> -> reply: SET_ITF_6X12_OK / SET_ITF_6X12_NG
    # There is no per-sensor / bulk ITF command on the device side, so the
    # 3-axis sensor1/sensor2 ITF and the 6-axis ITF are all built on top of
    # these single element get/set commands, using ITF_MAP_3AXIS_SENSOR_1/2
    # and ITF_MAP_6AXIS to pick out which of the 36 elements belong to which
    # sensor/set.
    # -------------------------------------------------------------------------

    def get_itf_3axis_sensor1(self):
        """Get a list of 3x3 float ITF data for 3-axis sensor1 from the amplifier.

        For '3axis' mode only.
        This is the interference correction matrix for 3-axis sensor1 (ch1-3).

        Returns:
            list[float]: List of 9 float ITF data for 3-axis sensor1, or None on failure.
        """
        return self._get_itf(self.ITF_MAP_3AXIS_SENSOR_1, label='3axis sensor1')

    def get_itf_3axis_sensor2(self):
        """Get a list of 3x3 float ITF data for 3-axis sensor2 from the amplifier.

        For '3axis' mode only.
        This is the interference correction matrix for 3-axis sensor2 (ch4-6).

        Returns:
            list[float]: List of 9 float ITF data for 3-axis sensor2, or None on failure.
        """
        return self._get_itf(self.ITF_MAP_3AXIS_SENSOR_2, label='3axis sensor2')

    def set_itf_3axis_sensor1(self, val_list: list[float]):
        """Set 3x3 float ITF data for 3-axis sensor1 to the amplifier.

        For '3axis' mode only.
        This is the interference correction matrix for 3-axis sensor1 (ch1-3).

        Args:
            val_list (list[float]): List of 9 float ITF values for 3-axis sensor1.

        Returns:
            bool: True on success, False on failure.

        Note:
            The set data are stored in non-volatile memory in the amplifier.
        """
        return self._set_itf(val_list, self.ITF_MAP_3AXIS_SENSOR_1,
                             self.get_itf_3axis_sensor1, self.ITF_COUNT_3AXIS)

    def set_itf_3axis_sensor2(self, val_list: list[float]):
        """Set 3x3 float ITF data for 3-axis sensor2 to the amplifier.

        For '3axis' mode only.
        This is the interference correction matrix for 3-axis sensor2 (ch4-6).

        Args:
            val_list (list[float]): List of 9 float ITF values for 3-axis sensor2.

        Returns:
            bool: True on success, False on failure.

        Note:
            The set data are stored in non-volatile memory in the amplifier.
        """
        return self._set_itf(val_list, self.ITF_MAP_3AXIS_SENSOR_2,
                             self.get_itf_3axis_sensor2, self.ITF_COUNT_3AXIS)

    # -------------------------------------------------------------------------
    # ITF for 6axis mode: 6x6=36 values x 1 set
    # -------------------------------------------------------------------------

    def get_itf_6axis(self):
        """Get a list of 6x6 float data of ITF from the amplifier.

        For '6axis' mode only.
        ITF is the interference correction matrix for the 6-axis sensor.

        Returns:
            list[float]: List of 36 float ITF data, or None on failure.
        """
        return self._get_itf(self.ITF_MAP_6AXIS, label='6axis')

    def set_itf_6axis(self, val_list: list[float]):
        """Set 6x6 float data for ITF to the amplifier.

        For '6axis' mode only.
        ITF is the interference correction matrix for the 6-axis sensor.

        Args:
            val_list (list[float]): List of 36 float ITF values.

        Returns:
            bool: True on success, False on failure.

        Note:
            The set data are stored in non-volatile memory in the amplifier.
        """
        return self._set_itf(val_list, self.ITF_MAP_6AXIS,
                             self.get_itf_6axis, self.ITF_COUNT_6AXIS)

    # -------------------------------------------------------------------------
    # ITF common private methods
    # -------------------------------------------------------------------------

    def _get_itf_from_device(self, item: int):
        """Get a single ITF coefficient from the amplifier.

        Args:
            item (int): ITF element index (0-71 on the device side;
                only 0-35 are actually used, see class docstring).

        Returns:
            float: The ITF coefficient value, or None on failure.
        """
        prefix = 'ITF_6X12_'
        reply = self._get_reply('GET_ITF_6X12_{:02d}\n'.format(item))
        if not reply.startswith(prefix):
            print('Get ITF Reply Error: No.{:02d} Reply:{}'.format(item, reply))
            return None
        try:
            return float(reply[len(prefix):])
        except ValueError:
            print('Get ITF ValueError: No.{:02d} Reply:{}'.format(item, reply))
            return None

    def _set_itf_to_device(self, item: int, value: float):
        """Set a single ITF coefficient to the amplifier.

        Args:
            item (int): ITF element index (0-71 on the device side;
                only 0-35 are actually used, see class docstring).
            value (float): The ITF coefficient value to set.

        Returns:
            bool: True on success ('SET_ITF_6X12_OK'), False otherwise.
        """
        command_string = 'SET_ITF_6X12_{:02d}_{}\n'.format(item, value)
        reply = self._get_reply(command_string)
        return reply == 'SET_ITF_6X12_OK'

    def _get_itf(self, index_map: list[int], label: str = ''):
        """Get an ITF matrix from the amplifier.

        Reads each ITF element individually via GET_ITF_6X12_xx, since the
        amplifier exposes only a single per-element ITF command, not a bulk
        per-sensor / per-mode ITF command.

        Args:
            index_map (list[int]): Device-side element indices (0-71) to
                read, in the order they should appear in the result.
            label (str, optional): Human-readable label (e.g. '3axis sensor1')
                used only for the summary log line. Defaults to ''.

        Returns:
            list[float]: List of float ITF data, or None on failure.
        """
        itf_list = []
        for item in index_map:
            value = self._get_itf_from_device(item)
            if value is None:
                return None
            itf_list.append(value)
        print('Get ITF{} (from device): {}'.format(
            ' ({})'.format(label) if label else '', itf_list))
        return itf_list

    def _set_itf(self, val_list: list[float], index_map: list[int],
                 get_func, expected_dim: int):
        """Set an ITF matrix to the amplifier.

        Writes each ITF element individually via SET_ITF_6X12_xx_<value>,
        since the amplifier exposes only a single per-element ITF command,
        not a bulk per-sensor / per-mode ITF command.

        Args:
            val_list (list[float]): List of float ITF values.
            index_map (list[int]): Device-side element indices (0-71),
                in the same order as val_list.
            get_func (callable): Corresponding getter to verify written values.
            expected_dim (int): Expected number of ITF values (9 or 36).

        Returns:
            bool: True on success, False on failure.
        """
        if len(val_list) != expected_dim:
            print('Set ITF Dimension Error: {}/{}'.format(len(val_list), expected_dim))
            return False

        overall_result = True
        for i, item in enumerate(index_map):
            result = self._set_itf_to_device(item, val_list[i])
            if not result:
                overall_result = False
            if self._debug or not result:
                print('Set ITF: No.{:02d} Value:{:9.5f} Result: {}'.format(
                    item, val_list[i], result))

        # Check for each
        get_list = get_func()
        if get_list is None:
            print('Set ITF Check Error: Could not read back ITF values')
            return False
        for i in range(expected_dim):
            result = True
            if val_list[i] != get_list[i]:
                overall_result = result = False
            if self._debug or not result:
                print('Check Value: No.{:02d} Set:{:9.5f} Get:{:9.5f} Check: {}'.format(
                    i, val_list[i], get_list[i], result))
        print('Set ITF: {}'.format('OK' if overall_result else 'NG (see above)'))
        return overall_result

    def set_frequency(self, frequency: int):
        """Set sensing frequency to the amplifier.

        Args:
            frequency (int): Frequency [Hz] of the amplifier sensing.

        Returns:
            bool: True on success, False on failure.

        Note:
            The set data are stored in non-volatile memory in the amplifier.
        """
        success = False

        if frequency <= 100:
            command = 'SET_FREQUENCY_100\n'
        elif 100 < frequency < 1000:
            command = 'SET_FREQUENCY_500\n'
        elif 1000 <= frequency:
            command = 'SET_FREQUENCY_1000\n'
        else:
            return success

        reply = self._get_reply(command)
        if reply == 'SET_FREQUENCY_OK':
            success = True
        return success

    def get_frequency(self):
        """Get current sensing frequency from the amplifier.

        Returns:
            int or None: Frequency [Hz] on success, None on failure.
        """
        reply = self._get_reply('GET_FREQUENCY\n')
        if reply.startswith('FREQUENCY_'):
            try:
                value = int(reply.replace('FREQUENCY_', ''))
                print('Get Frequency (from device): {}Hz'.format(value))
                return value
            except ValueError:
                pass
        return None

    def get_data_3axis_sensor1(self):
        """Get engineering data for sensor 1 (ch1-3).

        For '3axis' mode.

        Returns:
            Tuple[float, float, float, float]:
                - float: Time of reading data from the serial port.
                - float: Value of channel 1.
                - float: Value of channel 2.
                - float: Value of channel 3.
        """
        return self._get_data(self._eng1, self._eng2, self._eng3)

    def get_data_3axis_sensor2(self):
        """Get engineering data for sensor 2 (ch4-6).

        For '3axis' mode.

        Returns:
            Tuple[float, float, float, float]:
                - float: Time of reading data from the serial port.
                - float: Value of channel 4.
                - float: Value of channel 5.
                - float: Value of channel 6.
        """
        return self._get_data(self._eng4, self._eng5, self._eng6)

    def get_data(self):
        """Get engineering data for all 6 channels.

        For '6axis' mode.

        Returns:
            Tuple[float, float, float, float, float, float, float]:
                - float: Time of reading data from the serial port.
                - float: Value of channel 1.
                - float: Value of channel 2.
                - float: Value of channel 3.
                - float: Value of channel 4.
                - float: Value of channel 5.
                - float: Value of channel 6.
        """
        return self._get_data(
            self._eng1, self._eng2, self._eng3,
            self._eng4, self._eng5, self._eng6)

    def _get_data(self, *eng_values):
        """Get engineering data snapshot with assigning guard.

        Args:
            *eng_values (float): Engineering values to snapshot.

        Returns:
            Tuple[float, ...]: Time followed by the engineering values.
        """
        convert_ = self._convert_data
        self._convert_data = False

        # Wait for assigning
        i = 0
        while self._assigning and i < 5:
            time.sleep(0.1 / self._frequency)
            i += 1

        time_ = self._data_time
        values_ = tuple(eng_values)

        self._convert_data = convert_
        return (time_,) + values_


if __name__ == '__main__':

    # --- 3axis mode example ---
    initialize_ = False
    driver = DPA06BDriverForRobot(debug=True, init_zero=initialize_, sensor_mode='3axis')

    if driver.is_connected():
        fs_list = [1000, 1000, 2000, 1000, 1000, 2000]
        itf_3axis_sensor1_list = [1.44023,  0.09527,  0.00613,
                                  -0.08354,  1.42638,  0.04338,
                                  0.01594,  0.04522, -1.28155]
        itf_3axis_sensor2_list = [1.44023,  0.09527,  0.00613,
                                  -0.08354,  1.42638,  0.04338,
                                  0.01594,  0.04522, -1.28155]
        if initialize_:
            driver.set_fs(val_list=fs_list)
            driver.set_itf_3axis_sensor1(val_list=itf_3axis_sensor1_list)
            driver.set_itf_3axis_sensor2(val_list=itf_3axis_sensor2_list)

        driver.start()
        time.sleep(1)
        driver.stop()
        time.sleep(1)
        driver.close()

    # --- 6axis mode example ---
    # driver = DPA06BDriverForRobot(debug=True, init_zero=False, sensor_mode='6axis')
    # if driver.is_connected():
    #     fs_list = [1000, 1000, 2000, 1000, 1000, 2000]
    #     itf_list = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    #                 0.0, 1.0, 0.0, 0.0, 0.0, 0.0,
    #                 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
    #                 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
    #                 0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
    #                 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    #     if initialize_:
    #         driver.set_fs(val_list=fs_list)
    #         driver.set_itf_6axis(val_list=itf_list)
    #     driver.start()
    #     time.sleep(1)
    #     driver.stop()
    #     driver.close()
