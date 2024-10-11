# main.py

import network
import utime
import uasyncio as asyncio
import sys
import json

from epd4in2_V2 import EPD_4in2

# ===========================
# Configuration
# ===========================

SSID = "TheWifi"
PASSWORD = "lakelife6234"
HOSTNAME = "FermentationMonitor"
TCP_PORT = 55000
EPD_WIDTH = 400
EPD_HEIGHT = 300

epd = EPD_4in2()

def connect_wifi(ssid, password, hostname='FermentationMonitor', timeout=10):
    """
    Connects to the specified Wi-Fi network with a custom hostname.

    :param ssid: Wi-Fi SSID
    :param password: Wi-Fi Password
    :param hostname: Desired hostname for the ESP32
    :param timeout: Time to wait for connection (in seconds)
    :return: True if connected successfully, False otherwise
    """
    station = network.WLAN(network.STA_IF)
    station.active(True)

    # Set the custom hostname before connecting
    station.config(dhcp_hostname=hostname)

    station.connect(ssid, password)

    print(f"Connecting to Wi-Fi SSID: {ssid} with hostname: {hostname}...")
    start_time = utime.time()
    while not station.isconnected():
        if utime.time() - start_time > timeout:
            print("\nFailed to connect to Wi-Fi.")
            return False
        print(".", end="")
        utime.sleep(1)
    print("\nConnected to Wi-Fi.")
    print("Network Config:", station.ifconfig())
    return True

async def handle_client(reader, writer):
    """
    Asynchronously handles a connected TCP client.
    Receives data terminated by newline and processes each message.
    """
    addr = writer.get_extra_info('peername')
    print(f"Accepted connection from {addr}")

    buffer = ""
    try:
        while True:
            data = await reader.read(1024)  # Read up to 1024 bytes
            if not data:
                print(f"Connection closed by {addr}")
                break  # Client disconnected
            buffer += data.decode('utf-8')  # Append received data to buffer

            while '\n' in buffer:
                message, buffer = buffer.split('\n', 1)  # Split at first newline
                message = message.strip()
                if message:
                    print(f"Processing message from {addr}: {message}")
                    await process_received_data(message, writer)
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Connection with {addr} closed.")

async def process_received_data(message, writer):
    """
    Processes the received message by parsing JSON and printing it.
    Sends an acknowledgment back to the client.
    """
    try:
        data = json.loads(message)
        update_e_paper_display(data["name"], data["temperature"], data["battery"], data["gravity"])
        print(f"Received JSON data: {data}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e} | Message: {message}")

    # Echo back acknowledgment
    response = f"Echo: {message}\n"
    writer.write(response.encode('utf-8'))
    await writer.drain()

async def start_tcp_server(host='0.0.0.0', port=TCP_PORT):
    """
    Starts the asynchronous TCP server.
    """
    try:
        server = await asyncio.start_server(handle_client, host, port)
    except Exception as e:
        print(f"Failed to start server on {host}:{port}: {e}")
        sys.exit(1)

    print(f"TCP server listening on {host}:{port}")

    # Keep the server running with an infinite loop
    try:
        while True:
            await asyncio.sleep(10)  # Sleep to prevent the loop from blocking
    except asyncio.CancelledError:
        pass
    
def calculate_battery_voltage(battery_voltage):
    min_voltage = 3.0
    max_voltage = 4.2
    
    if battery_voltage <= min_voltage:
        return 0
    elif battery_voltage >= max_voltage:
        return 100
    else:
        percentage = ((battery_voltage - min_voltage) / (max_voltage - min_voltage)) * 100
        return int(round(percentage))
    
def update_e_paper_display(devicename, temperature, battery, gravity):
    epd.image1Gray.fill(0xff)
    epd.image4Gray.fill(0xff)
    
    battery_percentage = calculate_battery_voltage(battery)
    temperature = int(round(temperature))
    gravity = round(gravity, 3)

    print("Full brush")
    epd.EPD_4IN2_V2_Init()
    epd.image1Gray.text(f"Device Name: {devicename}", 5, 10, epd.black)
    epd.image1Gray.text(f"Gravity: {gravity:.3f}", 5, 20, epd.black)
    epd.image1Gray.text(f"Temperature: {temperature}F", 5, 30, epd.black)
    epd.image1Gray.text(f"Battery: {battery_percentage}%", 5, 40, epd.black)
    #epd.image1Gray.text("Pico_ePaper-4.2", 5, 40, epd.black)
    #epd.image1Gray.text("Raspberry Pico", 5, 70, epd.black)
    epd.EPD_4IN2_V2_Display(epd.buffer_1Gray)
    #epd.delay_ms(2000)
    
    #epd.image1Gray.vline(10, 90, 60, epd.black)
    #epd.image1Gray.vline(90, 90, 60, epd.black)
    #epd.image1Gray.hline(10, 90, 80, epd.black)
    #epd.image1Gray.hline(10, 150, 80, epd.black)
    #epd.image1Gray.line(10, 90, 90, 150, epd.black)
    #epd.image1Gray.line(90, 90, 10, 150, epd.black)
    #epd.EPD_4IN2_V2_Display(epd.buffer_1Gray)
    #epd.delay_ms(2000)
    
    #print("Quick refresh")
    #epd.EPD_4IN2_V2_Init_Fast(epd.Seconds_1_5S)
    #epd.image1Gray.rect(10, 180, 50, 80, epd.black)
    #epd.image1Gray.fill_rect(70, 180, 50, 80, epd.black)
    #epd.EPD_4IN2_V2_Display_Fast(epd.buffer_1Gray)
    #epd.delay_ms(2000)

    #print("partial refresh")
    #for i in range(0, 10):
    #    print(str(i))
    #    epd.image1Gray.fill_rect(60, 270, 10, 10, epd.white)
    #    epd.image1Gray.text(str(i), 62, 272, epd.black)
    #    epd.EPD_4IN2_V2_PartialDisplay(epd.buffer_1Gray)
    #    epd.delay_ms(500)
    
    #print("Four grayscale refresh")
    #epd.EPD_4IN2_V2_Init_4Gray()
    #epd.image4Gray.fill_rect(150, 10, 250, 30, epd.black)
    #epd.image4Gray.text('GRAY1 with black background',155, 21, epd.white)
    #epd.image4Gray.text('GRAY2 with white background',155, 51, epd.grayish)
    #epd.image4Gray.text('GRAY3 with white background',155, 81, epd.darkgray)
    #epd.image4Gray.text('GRAY4 with white background',155, 111, epd.black)
    #epd.EPD_4IN2_V2_4GrayDisplay(epd.buffer_4Gray)
    #epd.delay_ms(5000)

    #print("Clear")
    #epd.EPD_4IN2_V2_Init()
    #epd.EPD_4IN2_V2_Clear()
    
    #print("Enter sleep mode ")
    epd.Sleep()

def main():
    """
    Main function to connect to Wi-Fi and start the TCP server.
    """
    # Connect to Wi-Fi with custom hostname
    if not connect_wifi(SSID, PASSWORD, hostname=HOSTNAME):
        print("Exiting due to Wi-Fi connection failure.")
        sys.exit(1)

    # Start the TCP server
    try:
        asyncio.run(start_tcp_server(host='0.0.0.0', port=TCP_PORT))
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Server encountered an error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

