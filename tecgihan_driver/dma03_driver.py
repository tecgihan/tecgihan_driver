from threading import Thread

import time

import serial
import serial.tools.list_ports


class DMA03Driver:
    """Serial port I/O class for DMA-03 for Robot amplifier."""

    def _open(self, port='/dev/ttyUSB0', product_name='DMA-03B', timeout=1.0):
        """Open a serial port.

        Args:
            port (str, optional): The device port. Defaults to '/dev/ttyUSB0'.
            product_name (str, optional): Amplifier product name. Defaults to 'DMA-03B'.
            timeout (float, optional): Set a read timeout value in seconds. Defaults to 1.0.
        """
        if product_name == 'DMA-03':
            baudrate = 6000000
        elif product_name == 'DMA-03B':
            baudrate = 3000000
        else:
            baudrate = 3000000
            print(f"Warning: Unknown product_name '{product_name}', using 3000000 baud")

        self._ser = serial.Serial(port=port,
                                  baudrate=baudrate,
                                  parity=serial.PARITY_NONE,
                                  bytesize=serial.EIGHTBITS,
                                  stopbits=serial.STOPBITS_ONE,
                                  timeout=timeout,
                                  write_timeout=timeout*2.0,
                                  xonxoff=False,
                                  rtscts=True)
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
        print('Command Bytes: {}'.format(command_bytes))
        result = self._ser.write(command_bytes)
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
            vendor_id (str): The device vendor ID
            product_id (str): The device product ID

        Returns:
            Union[str, None]:
                - str: The port device string like '/dev/ttyUSB0'.
                - None: VID or PID did not match the actual devoce connected.
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
            Union[str, None]:
                - str: The port device string like '/dev/ttyUSB0'.
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
                        'Device Location or Serial No. - NOT Specified' +
                        'and 1st Device Chosen')
                    return {
                        'port': port.device,
                        'product': port.product
                    }
        return None


class DMA03DriverForRobot(DMA03Driver):
    """Command I/O class for DMA-03 for Robot amplifier."""

    def __init__(self,
                 debug=False,
                 frequency=1000,
                 init_zero=False,
                 timeout=1.0,
                 serial_number=None,
                 location=None):
        """Construct DMA03DriverForRobot class instance.

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
        """
        print('Tec Gihan DMA-03 for Robot Driver: Starting ...')
        search_name = 'DMA-03'
        port = '/dev/ttyUSB0'
        product_name = 'DMA-03B'
        info = self._find_port_by_name(
            product_name=search_name, serial_number=serial_number, location=location)
        port = info['port']
        product_name = info['product']
        self._open(port, product_name, timeout=timeout)
        time.sleep(1)

        if self._is_connected():
            print('Connected: {}'.format(product_name))
            self._print_info()
        else:
            print('Not Connected: {}'.format(product_name))
            return

        self._debug = debug

        self.stop()
        self.set_for_robot()

        if init_zero:
            self.set_zero()

        if self.set_frequency(frequency):
            self._frequency = frequency
        else:
            self._frequency = 1000

        fs_list = self.get_fs()
        if fs_list:
            self._fs_ch1, self._fs_ch2, self._fs_ch3 = fs_list
        else:
            self._fs_ch1, self._fs_ch2, self._fs_ch3 = 1000, 1000, 1000
            print('FS read failed, using default values (1000,1000,1000)')
        self.get_itf()

        self._assigning = False
        self._eng1 = 0.0
        self._eng2 = 0.0
        self._eng3 = 0.0
        self._data_time = time.time()

        self._convert_data = False
        self._thr = Thread(target=self._data_conversion)
        self._thr.start()

    def __del__(self):
        """Destructor of this class instance."""
        self.close()

    def _data_conversion(self):
        """Aquire and convert sensing data with thread."""
        while self._is_connected():
            # Skip if self.convert_data is False
            if not self._convert_data:
                if self._debug:
                    print('Convert waiting...')
                time.sleep(0.1)
                continue
            buffer = self._recv_command()
            last_time = self._data_time
            self._data_time = time.time()
            diff_time = self._data_time - last_time
            if len(buffer) == 3 * 4:
                data = int('0x'+buffer, 0)
                ch1 = (data & 0xffff00000000) >> 32
                ch2 = (data & 0x0000ffff0000) >> 16
                ch3 = data & 0x00000000ffff
                ad1 = self._to_signedint(ch1)
                ad2 = self._to_signedint(ch2)
                ad3 = self._to_signedint(ch3)
                self._assigning = True
                self._eng1, self._eng2, self._eng3 = self._calculate_eng_data(
                    ad1, ad2, ad3)
                self._assigning = False
                if self._debug:
                    print('Time: {} (Diff: {} )'.format(
                        self._data_time, diff_time))
                    print('Buffer: {}'.format(buffer))  # print without newline
                    print('Hex: (     0x{:04x},     0x{:04x},     0x{:04x} )'.format(
                        ch1, ch2, ch3))
                    print('Int: ( {:10d}, {:10d}, {:10d} )'.format(
                        ad1, ad2, ad3))
                    print('Eng: ( {:10.5f}, {:10.5f}, {:10.5f} )'.format(
                        self._eng1, self._eng2, self._eng3))
                self._ros_publish()
            else:
                if self._debug:
                    print('NOT DATA [{}]'.format(buffer))
            time.sleep(0.6/self._frequency)

    def _ros_publish(self):
        """Be overrided in a ROS node.

        An empty function to override in a ROS node
        to publish a ROS topic after the data conversion.

        Returns:
            bool: False
        """
        return False

    def _calculate_eng_data(self, ad1, ad2, ad3):
        """Calculate the engineering data from signed int data with FS values.

        Args:
            ad1 (int): Channel 1 integer value
            ad2 (int): Channel 2 integer value
            ad3 (int): Channel 3 integer value

        Returns:
            Tuple[float, float, float]:
                - float: Channel 1 engineering data.
                - float: Channel 2 engineering data.
                - float: Channel 3 engineering data.
        """
        eng1 = ad1 * self._fs_ch1 / 32000
        eng2 = ad2 * self._fs_ch2 / 32000
        eng3 = ad3 * self._fs_ch3 / 32000
        return eng1, eng2, eng3

    def _to_signedint(self, value: int, bits=16):
        """Convert an unsigned int to a signed int.

        Converts an unsigned integer to its signed integer representation
        using two's complement.

        Args:
            value (int): The unsigned integer to convert
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
        self._convert_data = False
        time.sleep(0.2)
        self._send_command(command_string)
        time.sleep(0.5)
        reply = '000011112222'
        while len(reply) == 3 * 4:  # skip data
            reply = self._recv_command()
        print('Get reply: {}'.format(reply))
        return reply

    def start(self):
        """Send START command to the amplifire and start the data conversion.

        Returns:
            str: Reply for the command.
        """
        reply = self._get_reply('START\n')
        self._convert_data = True
        return reply

    def stop(self):
        """Send STOP command to the amplifier and stop the data conversion.

        Returns:
            str: Reply for the command.
        """
        reply = self._get_reply('STOP\n')
        self._convert_data = False
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
            str:  Reply for the command.

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
            self.stop()  # for DMA-03B
            if restart:
                reply += ' and Restart: '
                reply += self.start()
        else:
            reply += ' and ZERO command: Not Sent'
        print(reply)
        return reply

    def get_fs(self):
        """Get a list of 3 int data of FS (Full Scale) from the amplifier.

        Returns:
            List[int]: List of 3 int FS [X,Y,Z] data.
        """
        reply = self._get_reply('GET_FS\n')

        if reply.startswith('FS_'):
            reply = reply.replace('FS_', '')
        else:
            return None
        reply = reply.split(',')

        if len(reply) != 3:
            print('FS Dimension Error')
            return None
        else:
            reply_fs_ch1 = int(reply[0])
            reply_fs_ch2 = int(reply[1])
            reply_fs_ch3 = int(reply[2])
            print('FS ({},{},{})'.format(reply_fs_ch1, reply_fs_ch2, reply_fs_ch3))
            return [reply_fs_ch1, reply_fs_ch2, reply_fs_ch3]

    def set_fs(self, val_list: list[int]):
        """Set 3 int data of FS (Full Scale) to the amplifier.

        Args:
            val_list (list[int]): List of 3 float FS [X,Y,Z] data.

        Returns:
            bool: True on success, False on failure.

        Note:
            The set data are stored in non-volatile memory in the amplifier.
        """
        dim = 3
        if len(val_list) == dim:
            for i in range(dim):
                command_string = 'SET_FS_' + \
                    str(i) + '_' + str(val_list[i]) + '\n'
                self._get_reply(command_string)
        else:
            print('Get FS Dimension Error: {}/{}'.format(len(val_list), dim))
            return False

        # Check for each
        overall_result = True
        get_list = self.get_fs()
        for i in range(dim):
            result = True
            if val_list[i] != get_list[i]:
                overall_result = result = False
            print('Check Value: No.{} Set:{:5} Get:{:5} Check: {}'.format(
                i, val_list[i], get_list[i], result))
        if overall_result:
            self._fs_ch1, self._fs_ch2, self._fs_ch3 = get_list
        return overall_result

    def get_itf(self):
        """Get a list of 3x3 float data of ITF from the amplifier.

        ITF means Interference coefficients.

        Returns:
            list float: List of 3x3 float ITF data
        """
        reply = self._get_reply('GET_ITF\n')

        if reply.startswith('ITF_'):
            reply = reply.replace('ITF_', '')
        else:
            return None
        reply = reply.split(',')

        dim = 9
        itf_list = []
        if len(reply) != dim:
            print('Get ITF Dimension Error {}/{}'.format(len(reply), dim))
            return None
        else:
            for s in reply:
                try:
                    f = float(s)
                    itf_list.append(f)
                except ValueError:
                    print('Get ITF ValueError')
                    return None
            print('ITF {}'.format(itf_list))
            return list(itf_list)

    def set_itf(self, val_list: list[float]):
        """Set 3x3 float data for ITF in the amplifier.

        ITF means Interference coefficients.

        Args:
            val_list (list[float]): list of 3x3 float for ITF to set in the amplifier.

        Returns:
            bool: True on success, False on failure.

        Note:
            The set data are stored in non-volatile memory in the amplifier.
        """
        dim = 9
        if len(val_list) == dim:
            for i in range(dim):
                command_string = 'SET_ITF_' + \
                    str(i) + '_' + str(val_list[i]) + '\n'
                self._get_reply(command_string)
        else:
            print('Set ITF Dimension Error: {}/{}'.format(len(val_list), dim))
            return False

        # Check for each
        overall_result = True
        get_list = self.get_itf()
        for i in range(dim):
            result = True
            if val_list[i] != get_list[i]:
                overall_result = result = False
            print('Check Value: No.{} Set:{:9.5f} Get:{:9.5f} Check: {}'.format(
                i, val_list[i], get_list[i], result))
        return overall_result

    def set_frequency(self, frequency: int):
        """Set sensing frequency to the amplifier.

        Args:
            frequency (int): Freqency [Hz] of the amplifier sensing.

        Returns:
            bool: True on success, False on failure.

        Note:
            The set data are Stored in non-volatile memory in the amplifier.
        """
        success = False

        if frequency <= 100:
            command = 'SET_FREQUENCY_100\n'
        elif 100 < frequency and frequency < 1000:
            command = 'SET_FREQUENCY_500\n'
        elif 1000 <= frequency:
            command = 'SET_FREQUENCY_1000\n'
        else:
            return success

        reply = self._get_reply(command)
        if reply == 'SET_FREQUENCY_OK':
            success = True
        return success

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
        self._convert_data = False
        time.sleep(0.1)
        set_reply = 'Set for Robot: Error'
        if success and reply == 'FOR_ROBOT_0':
            set_reply = self._get_reply('SET_FOR_ROBOT_1\n')
        return set_reply

    def get_data(self):
        """Get engineering data.

        Returns:
            Tuple[float, float, float, float]:
                - float: Time of reading data from the serial port.
                - float: Value of X-axis force.
                - float: Value of Y-axis force.
                - float: Value of Z-axis force.
        """
        convert_ = self._convert_data
        self._convert_data = False

        # Wait for assigning
        i = 0
        while self._assigning and i < 5:
            time.sleep(0.1/self._frequency)
            i += 1

        time_ = self._data_time
        eng1_ = self._eng1
        eng2_ = self._eng2
        eng3_ = self._eng3

        self._convert_data = convert_
        return time_, eng1_, eng2_, eng3_


if __name__ == '__main__':

    initialize_ = False
    driver = DMA03DriverForRobot(debug=True, init_zero=initialize_)

    if driver.is_connected():
        fs_list = [1000, 1000, 2000]
        itf_list = [1.44023, 0.09527, 0.00613,
                    -0.08354, 1.42638, 0.04338,
                    -0.01594, -0.04522, 1.28155]
        if initialize_:
            reply = driver.set_fs(val_list=fs_list)
            reply = driver.set_itf(val_list=itf_list)

        reply = driver.start()
        time.sleep(1)

        reply = driver.stop()
        time.sleep(1)

        driver.close()
