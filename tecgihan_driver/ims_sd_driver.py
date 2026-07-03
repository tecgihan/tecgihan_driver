from threading import Thread

import time

import serial
import serial.tools.list_ports


class IMSSDDriver:
    r"""Serial port I/O class for IMS-SD.

    IMS-SD communicates via a virtual COM port.

    Protocol:
        - Baud rate  : 921600
        - Flow ctrl  : RTS/CTS (Handshake.RequestToSend)
        - Command terminator : LF (\n)
        - Data packet: 11 channels × 4 hex chars + LF  (45 bytes total)
    """

    BAUD_RATE = 921600
    PACKET_CHANNELS = 11
    PACKET_LEN = PACKET_CHANNELS * 4  # 44 hex chars

    # Accelerometer range code -> [G] value mapping
    ACC_RANGE_MAP = {1: 4, 2: 8, 3: 16, 4: 30}
    # [G] -> internal FS value (30G uses 32 for calculation)
    ACC_FS_MAP = {4: 4, 8: 8, 16: 16, 30: 32}

    def _open(self, port, timeout=1.0):
        """Open the serial port.

        Args:
            port (str): The device port path.
            timeout (float, optional): Serial read timeout [sec]. Defaults to 1.0.
        """
        try:
            self._ser = serial.Serial(
                port=port,
                baudrate=self.BAUD_RATE,
                parity=serial.PARITY_NONE,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
                write_timeout=timeout * 2.0,
                xonxoff=False,
                rtscts=True)
        except serial.SerialException as e:
            print('IMS-SD: Port open error: {}'.format(e))
            self._ser = None
            return

        if self._is_connected():
            print('Port Opened: {}'.format(self._ser.name))
        else:
            print('Port Open Error: {}'.format(port))

    def _close(self):
        """Close the serial port."""
        self._reset_input_buffer()
        try:
            self._ser.close()
            if not self._is_connected():
                print('Port Disconnected: {}'.format(self._ser.name))
        except serial.SerialException:
            pass

    def _print_info(self):
        """Print serial port settings."""
        print(' port: {}'.format(self._ser.name))
        for k, v in self._ser.get_settings().items():
            print(' {}: {}'.format(k, v))

    def _is_connected(self):
        """Return whether the serial port is open.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._ser is not None and self._ser.is_open

    def _send_command(self, command_string):
        """Write a command string to the serial port.

        Args:
            command_string (str): Command text including terminating LF.

        Returns:
            int: Number of bytes written, or 0 on error.
        """
        try:
            command_bytes = command_string.encode('utf-8')
            print('Command Bytes: {}'.format(command_bytes))
            result = self._ser.write(command_bytes)
            print('Write Data Result (Command Length): {}'.format(result))
            return result
        except (serial.SerialException, serial.SerialTimeoutException) as e:
            print('IMS-SD: Send error: {}'.format(e))
            return 0

    def _recv_command(self, terminator=b'\n'):
        r"""Read from serial until the terminator, strip the trailing terminator.

        Args:
            terminator (bytes, optional):
                The terminator to end reading. Defaults to b'\n'.

        Returns:
            str: Received line decoded as UTF-8 (without trailing terminator).
        """
        result = b''
        try:
            result = self._ser.read_until(terminator)
            if len(result) >= len(terminator) and result.endswith(terminator):
                result = result[:-len(terminator)]
        except serial.SerialException as e:
            print('IMS-SD: Receive error: {}'.format(e))
        except serial.SerialTimeoutException:
            print('IMS-SD: Receive timeout')
        except Exception:
            print('IMS-SD: Can Not Receive Command')
        return result.decode('utf-8', errors='replace')

    def _reset_input_buffer(self):
        """Discard any data in the serial receive buffer."""
        try:
            self._ser.reset_input_buffer()
        except serial.SerialException:
            pass

    def _find_port_by_name(self, search_product_name, serial_number=None, location=None):
        """Find the IMS-SD virtual COM port by name, serial number, or location.

        Discovery strategy:
          1. If serial_number is given, match port.serial_number.
          2. If location is given, match port.location.
          3. Otherwise, return the first port whose description
             contains search_product_name.
          4. Fallback: return the first /dev/ttyUSB* port found.

        Args:
            search_product_name (str): The product name to search for
                (e.g. 'FT230X Basic UART').
            serial_number (str, optional): Device serial number string.
                Defaults to None.
            location (str, optional): Device USB location string (e.g. '1-2').
                Defaults to None.

        Returns:
            dict or None:
                - dict: {'port': str, 'product': str} on success.
                - None: if not found.
        """
        ports = serial.tools.list_ports.comports()

        # Strategy 1: match by serial number
        if serial_number:
            for p in ports:
                if p.serial_number and serial_number in p.serial_number:
                    print('Device Serial No. Specified: {} -> {}'.format(
                        p.serial_number, p.device))
                    return {'port': p.device, 'product': p.product or search_product_name}
            print('IMS-SD: serial number {} not found.'.format(serial_number))
            return None

        # Strategy 2: match by USB location
        if location:
            for p in ports:
                if p.location and location in p.location:
                    print('Device Location Specified: {} -> {}'.format(
                        p.location, p.device))
                    return {'port': p.device, 'product': p.product or search_product_name}
            print('IMS-SD: location {} not found.'.format(location))
            return None

        # Strategy 3: description string match (also match FTDI product name)
        search_name_alt = search_product_name.replace('-', '_')
        for p in ports:
            desc = (p.description or '') + (p.product or '')
            if (search_product_name in desc or search_name_alt in desc
                    or 'FT230X Basic UART' in desc):
                print('Device Location or Serial No. - NOT Specified'
                      ' and 1st Device Chosen')
                return {'port': p.device, 'product': p.product or search_product_name}

        # Strategy 4: fallback to first /dev/ttyUSB* (Linux FTDI)
        usb_ports = [p for p in ports if 'ttyUSB' in (p.device or '')]
        if usb_ports:
            print('IMS-SD: Device Location or Serial No. NOT Specified, '
                  '1st ttyUSB device chosen: {}'.format(usb_ports[0].device))
            return {
                'port': usb_ports[0].device,
                'product': usb_ports[0].product or search_product_name
            }

        print('IMS-SD: No virtual COM port (ttyUSB) found.')
        return None


class IMSSDDriverForRobot(IMSSDDriver):
    """Command I/O class for IMS-SD IMU amplifier.

    Data channels (in order):
        Acc  X/Y/Z   [G]      positions  0-11
        Gyro X/Y/Z   [deg/s]  positions 12-23
        Mag  X/Y/Z   [uT]     positions 24-35
        Temperature  [degC]   positions 36-39
        Battery SoC  [%]      positions 40-43

    Engineering conversion:
        Acc  [G]     = AD * accFS  / 32000   (accFS: 4/8/16/32)
        Gyro [deg/s] = AD * 4000   / 32000
        Mag  [uT]    = AD * 300    / 32000
        Temp [degC]  = AD / 333.87 + 21
        SoC  [%]     = AD (raw integer)
    """

    def __init__(self,
                 debug=False,
                 frequency=100,
                 acc_range=30,
                 timeout=1.0,
                 port=None,
                 serial_number=None,
                 location=None):
        """Construct IMSSDDriverForRobot class instance.

        Args:
            debug (bool, optional): True enables verbose console output.
                Defaults to False.
            frequency (int, optional): Sensing frequency [Hz] (100/500/1000).
                Defaults to 100.
            acc_range (int, optional): Accelerometer full-scale range [G]
                (4/8/16/30). Defaults to 30.
            timeout (float, optional): Serial read timeout [sec].
                Defaults to 1.0.
            port (str, optional): Explicit port path (e.g. '/dev/ttyUSB0').
                When specified, serial_number and location are ignored.
                Defaults to None (auto-detect).
            serial_number (str, optional): Device serial number string to
                distinguish between multiple IMS-SD units. Defaults to None.
            location (str, optional): Device USB location string (e.g. '1-2')
                to distinguish between multiple IMS-SD units. Defaults to None.
        """
        print('Tec Gihan IMS-SD for Robot Driver: Starting ...')
        self._ser = None
        self._debug = debug

        # Validate and store accelerometer range
        if acc_range not in self.ACC_RANGE_MAP.values():
            print('Warning: acc_range {}G is not valid (4/8/16/30), '
                  'using 30G'.format(acc_range))
            acc_range = 30
        self._acc_range_g = acc_range
        self._acc_fs = self.ACC_FS_MAP[acc_range]

        # Determine serial port
        search_name = 'FT230X Basic UART'  # LINBLE-Z1 dongle product name
        product_name = 'IMS-SD'
        if port is not None:
            target_port = port
            print('Port Specified: {}'.format(target_port))
        else:
            info = self._find_port_by_name(
                search_product_name=search_name,
                serial_number=serial_number,
                location=location)
            if info is None:
                print('IMS-SD: No device found.')
                return
            target_port = info['port']
            product_name = info['product']

        self._open(target_port, timeout=timeout)
        if not self._is_connected():
            print('Not Connected: {}'.format(product_name))
            return

        self._print_info()

        # Wait for device ready
        time.sleep(2.0)
        print('Connected: {}'.format(product_name))

        self._convert_data = False

        # Initialize device
        self.stop()

        # Ensure robot mode is enabled
        for_robot_reply, for_robot_success = self.get_for_robot()
        if for_robot_reply == 'FOR_ROBOT_0':
            self.set_for_robot(True)

        # frequency
        current_frequency = self.get_frequency()
        if current_frequency != frequency:
            if self.set_frequency(frequency):
                self._frequency = frequency
            else:
                self._frequency = (
                    current_frequency if current_frequency is not None else frequency)
                print('IMS-SD: set_frequency failed, keeping frequency: {}'.format(
                    self._frequency))
        else:
            self._frequency = frequency
            print('IMS-SD: Frequency already set to {}Hz, skipping'.format(frequency))

        # acc_range
        # ACC_RANGE_MAP: {code: G} -> reverse to {G: code}
        acc_range_code_map = {v: k for k, v in self.ACC_RANGE_MAP.items()}
        current_acc_range_code = self.get_acc_range()
        current_acc_range_g = self.ACC_RANGE_MAP.get(current_acc_range_code)
        if current_acc_range_g != acc_range:
            target_code = acc_range_code_map[acc_range]
            if self.set_acc_range(target_code):
                self._acc_range_g = acc_range
                self._acc_fs = self.ACC_FS_MAP[acc_range]
            else:
                if current_acc_range_g is not None:
                    self._acc_range_g = current_acc_range_g
                    self._acc_fs = self.ACC_FS_MAP[current_acc_range_g]
                print('IMS-SD: set_acc_range failed, keeping acc_range: {}G'.format(
                    self._acc_range_g))
        else:
            print('IMS-SD: acc_range already set to {}G, skipping'.format(acc_range))

        # Engineering data buffers
        self._acc = [0.0, 0.0, 0.0]   # [G]
        self._gyro = [0.0, 0.0, 0.0]  # [deg/s]
        self._mag = [0.0, 0.0, 0.0]   # [uT]
        self._temp = 0.0              # [degC]
        self._soc = 0.0               # [%]
        self._data_time = time.time()
        self._assigning = False

        # Start background data conversion thread
        self._thr = Thread(target=self._data_conversion, daemon=True)
        self._thr.start()

    def __del__(self):
        """Destructor."""
        self.close()

    def _get_reply(self, command_string):
        """Send a command and return the reply.

        Pauses the data conversion thread, flushes the input buffer,
        sends the command, and reads reply lines until a non-data line
        is received (skipping any streaming data packets that arrive
        before the command reply).

        Args:
            command_string (str): Command including LF terminator.

        Returns:
            str: Reply line (without LF), or '' on error.
        """
        self._convert_data = False
        time.sleep(0.05)
        self._reset_input_buffer()
        time.sleep(0.2)
        self._send_command(command_string)
        reply = '0' * self.PACKET_LEN
        while len(reply) == self.PACKET_LEN:  # skip data
            reply = self._recv_command()
        print('Get reply: {}'.format(reply))
        return reply

    def _data_conversion(self):
        """Continuously receive and parse data packets (background thread)."""
        while self._is_connected():
            if not self._convert_data:
                if self._debug:
                    print('IMS-SD: Convert waiting...')
                time.sleep(0.1)
                continue

            line = self._recv_command()
            last_time = self._data_time
            self._data_time = time.time()
            diff_time = self._data_time - last_time

            if len(line) == self.PACKET_LEN:
                try:
                    self._assigning = True
                    self._parse_packet(line)
                    self._assigning = False
                    if self._debug:
                        print('Time: {} (Diff: {})'.format(
                            self._data_time, diff_time))
                        print('Buffer: {}'.format(line))
                        print('Acc  [G]:     {}'.format(self._acc))
                        print('Gyro [deg/s]: {}'.format(self._gyro))
                        print('Mag  [uT]:    {}'.format(self._mag))
                        print('Temp [degC]:  {}  SoC [%]: {}'.format(
                            self._temp, self._soc))
                    self._ros_publish()
                except (ValueError, IndexError) as ex:
                    self._assigning = False
                    if self._debug:
                        print('IMS-SD: Parse error: {}'.format(ex))
            else:
                if self._debug:
                    print('IMS-SD: NOT DATA [{}]'.format(line))

            time.sleep(0.6 / self._frequency)

    def _parse_packet(self, line):
        """Parse a 44-character hex data packet into engineering values.

        Args:
            line (str): 44-character uppercase hex string (no LF).

        Raises:
            ValueError: If hex conversion fails.
            IndexError: If the string is too short.
        """
        def to_s16(hex4):
            v = int(hex4, 16)
            return v - 0x10000 if v >= 0x8000 else v

        for i in range(3):
            ad = to_s16(line[i * 4:(i + 1) * 4])
            self._acc[i] = ad * self._acc_fs / 32000.0

        for i in range(3):
            ad = to_s16(line[(3 + i) * 4:(4 + i) * 4])
            self._gyro[i] = ad * 4000.0 / 32000.0

        for i in range(3):
            ad = to_s16(line[(6 + i) * 4:(7 + i) * 4])
            self._mag[i] = ad * 300.0 / 32000.0

        ad_temp = to_s16(line[36:40])
        self._temp = ad_temp / 333.87 + 21.0

        ad_soc = to_s16(line[40:44])
        self._soc = float(ad_soc)

    def _ros_publish(self):
        """Provide a placeholder overridden by a ROS node after data conversion.

        Returns:
            bool: False (no-op in base class).
        """
        return False

    def start(self):
        """Send START command and begin data conversion.

        Returns:
            str: Reply from the amplifier.
        """
        reply = self._get_reply('START\n')
        self._convert_data = True
        return reply

    def stop(self):
        """Send STOP command and halt data conversion.

        Returns:
            str: Reply from the amplifier.
        """
        self._convert_data = False
        self._send_command('STOP\n')

        # STOP_OK / STOP_NG が来るまでループで待つ（最大2秒）
        deadline = time.time() + 2.0
        buf = ''
        while time.time() < deadline:
            line = self._recv_command()
            buf += line
            if 'STOP_OK' in buf or 'STOP_NG' in buf:
                print('Get reply: STOP_OK' if 'STOP_OK' in buf else 'Get reply: STOP_NG')
                break
        else:
            print('Get reply: STOP timeout (no STOP_OK/STOP_NG received)')

        # 両バッファをクリア
        self._reset_input_buffer()
        return buf

    def close(self):
        """Stop data conversion, close the serial port, and join the thread."""
        self._convert_data = False
        if self._is_connected():
            self.stop()
            self._close()
        if hasattr(self, '_thr') and isinstance(self._thr, Thread):
            self._thr.join(timeout=2.0)

    def is_connected(self):
        """Return whether the serial port is open.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._is_connected()

    def set_frequency(self, frequency):
        """Set sensing frequency.

        Args:
            frequency (int): Frequency [Hz]: 100, 500, or 1000.

        Returns:
            bool: True on success, False on failure.
        """
        if frequency <= 100:
            command = 'SET_FREQUENCY_100\n'
            self._frequency = 100
        elif frequency <= 500:
            command = 'SET_FREQUENCY_500\n'
            self._frequency = 500
        else:
            command = 'SET_FREQUENCY_1000\n'
            self._frequency = 1000

        reply = self._get_reply(command)
        return reply == 'SET_FREQUENCY_OK'

    def get_frequency(self):
        """Get current sensing frequency from the amplifier.

        Returns:
            int or None: Frequency [Hz] on success, None on failure.
        """
        reply = self._get_reply('GET_FREQUENCY\n')
        if reply.startswith('FREQUENCY_'):
            try:
                return int(reply.replace('FREQUENCY_', ''))
            except ValueError:
                pass
        return None

    def set_acc_range(self, range_code):
        """Set accelerometer full-scale range.

        Args:
            range_code (int): 1=4G, 2=8G, 3=16G, 4=30G.

        Returns:
            bool: True on success, False on failure.
        """
        if range_code not in self.ACC_RANGE_MAP:
            print('IMS-SD: Invalid acc_range code: {} '
                  '(1=4G / 2=8G / 3=16G / 4=30G)'.format(range_code))
            return False

        reply = self._get_reply('SET_ACC_RANGE_{}\n'.format(range_code))
        success = (reply == 'SET_ACC_RANGE_OK')
        if success:
            self._acc_range_g = self.ACC_RANGE_MAP[range_code]
            self._acc_fs = self.ACC_FS_MAP[self._acc_range_g]
        return success

    def get_acc_range(self):
        """Get accelerometer range code from the amplifier.

        Returns:
            int or None: Range code (1/2/3/4) on success, None on failure.
        """
        reply = self._get_reply('GET_ACC_RANGE\n')
        if reply.startswith('ACC_RANGE_'):
            try:
                return int(reply.replace('ACC_RANGE_', ''))
            except ValueError:
                pass
        return None

    def get_serial(self):
        """Get device serial number string.

        Returns:
            str or None: Serial number on success, None on failure.
        """
        reply = self._get_reply('GET_SERIAL\n')
        if reply.startswith('SERIAL_'):
            return reply.replace('SERIAL_', '')
        return None

    def get_for_robot(self):
        """Get whether the amplifier is in robot mode.

        Returns:
            Tuple[str, bool]:
                - str: Raw reply string.
                - bool: True if robot mode is enabled.
        """
        reply = self._get_reply('GET_FOR_ROBOT\n')
        success = reply in ('FOR_ROBOT_0', 'FOR_ROBOT_1')
        return reply, success

    def set_for_robot(self, enable):
        """Enable or disable robot mode.

        Args:
            enable (bool): True to enable robot mode.

        Returns:
            str: Reply from the amplifier.
        """
        command = 'SET_FOR_ROBOT_{}\n'.format(1 if enable else 0)
        return self._get_reply(command)

    def get_data(self):
        """Return the latest engineering data snapshot.

        Returns:
            Tuple[float, list, list, list, float, float]:
                - float: Timestamp (time.time()) of the last received packet.
                - list[float]: Acceleration [X, Y, Z] in [G].
                - list[float]: Angular velocity [X, Y, Z] in [deg/s].
                - list[float]: Magnetic field [X, Y, Z] in [uT].
                - float: Temperature [degC].
                - float: Battery state of charge [%].
        """
        was_converting = self._convert_data
        self._convert_data = False

        # Wait briefly if a packet is being written
        i = 0
        while self._assigning and i < 5:
            time.sleep(0.1 / self._frequency)
            i += 1

        snapshot = (
            self._data_time,
            list(self._acc),
            list(self._gyro),
            list(self._mag),
            self._temp,
            self._soc,
        )

        self._convert_data = was_converting
        return snapshot


if __name__ == '__main__':
    # Standalone demo: connect, acquire data for 1 second, then stop.
    driver = IMSSDDriverForRobot(debug=True, frequency=100, acc_range=30)

    if driver.is_connected():
        driver.start()
        time.sleep(1)
        driver.stop()
        time.sleep(1)
        driver.close()
