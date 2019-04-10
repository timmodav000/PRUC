import socket
import os
import time

class HubClient:
	def __init__(self):
		self.socket = None
		self.remote_address = None
		self.chunk = 1024
		self.image_length_size = 4
		self.total_images = 0
		self.park_open = 0

	def connect(self, addr, port):
		"""Connects to a remote sensor socket."""
		try:
			self.remote_address = (addr, port)
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.connect(self.remote_address)
			print("Connecting to {} port {}".format(*self.remote_address))
			return True
		except:
			print("UNABLE TO CONNECT TO HUB!!!!")
			return False

	def disconnect(self):
		"""Closes the socket connection"""
		self.socket.close()

	def execute_command(self, command):
		"""Sends a command to a sensor and receives the sensor's response

		:param command: The command string to be sent to the sensor.
		:return: The data response from the sensor
		"""
		data = bytes('', "utf-8")

		command_bin = bytes(command, "utf-8")
		try:
			self.socket.settimeout(0.25)
			self.socket.sendall(command_bin)
		except:
			print("Unable to send command %s" % command)
			return False
		print("Sent command: " + command)

		while True:
			try:
				response = self.socket.recv(self.chunk)
			except:
				response = bytes('',"utf-8")
			data += response
			if len(response) == 0:
				break
		return data

	def execute_command_images(self, number_of_images):
		"""Requests a number of images from the sensor and save those images.

		This function is made specifically for receiving and decoding multiple images.
		:param command: The command string to be sent to the sensor.
		:param number_of_images: This is the number of images we want save
		:return: Bool of whether or not the function succeeded.
		"""
		try:
			command = "getImages "+str(number_of_images)
			command_bin = bytes(command, "utf-8")
			self.socket.settimeout(1)
			self.socket.sendall(command_bin)
			print("Sent command: " + command)
		except Exception as e:
			print("Unable to send execute_command_images command.")
			print(e)
			return False
		while number_of_images > 0:
			try:
				response = self.socket.recv(self.image_length_size)
			except:
				print("Unable to get image length.")
				return False
			image_len = int.from_bytes(response,'big')
			print(" image len = "+str(response)+" -> "+str(image_len))
			image_data = bytes('',"utf-8")
			while True:
				try:
					data = self.socket.recv(image_len)
				except:
					data = bytes('',"utf-8")
				image_data += data
				if len(data)==0:
					print("Done reading "+str(len(data)))
					break
				image_len -= len(data)
				print(" read "+str(len(data)))

			if not image_len == 0:
				print("Error reading in image.")
				return False

			print(" received image len = "+ str(len(image_data)))
			image_name = "image" + str(self.total_images + 1) + ".jpg"

			try:
				image = open(image_name, "wb")
				image.write(image_data)
			except:
				print("Error saving image data")
				return False

			print("Saved an image named: [" + image_name + "] to the hub.")

			self.total_images += 1
			number_of_images -= 1

		return True

	def get_image_amount(self):
		"""Gets the number of images that the sensor needs to send to the hub.

		:return: Integer representing the amount of pictures the sensor has to send.
		"""
		amountb = self.execute_command(command="totalImages")
		amountstr = amountb.decode('utf-8')
		print(str(amountb)+ " -> "+str(amountstr))
		try:
			amount = int(amountstr)
			print(str(amountstr) + " -> "+str(amount))
		except Exception as e:
			print("Cant convert response. "+str(e))
			amount=0
		return amount

	def get_n_images(self, number_of_images):
		"""Gets and saves N images from a sensor.

		:return: Bool of whether or not we got 5 images from the sensor.
		"""
		retries = 3
		success = False
		while retries > 0 and not success:
			success = self.execute_command_images(number_of_images)
		return success

	def transfer_n_images(self, number_of_images):
		if not self.get_n_images(number_of_images): return False
		self.send_okay_signal(number_images_to_delete=number_of_images)
		return True


	def send_okay_signal(self, number_images_to_delete):
		"""This sends an okay to the sensor with the number of images to delete.

		:param number_images_to_delete: Number of images that the sensor will then delete.
		"""
		self.execute_command(command=("Okay " + str(number_images_to_delete)))

	def get_sensor_images(self):
		"""Gets and saves all images currently stored on the sensor.

		:return: Bool of whether or not we got all sensor images.
		"""
		# update this
		total_images = self.get_image_amount()
		print("total images =  "+str(total_images))
		if total_images==0:
			print("No images available or error")
			return False

		number_of_ten_loops = int(total_images / 10)
		images_remaining = total_images - (number_of_ten_loops * 10)

		number_of_five_loops = int(images_remaining / 5)
		images_remaining = images_remaining - (number_of_five_loops * 5)

		number_of_one_loops = images_remaining

		for number in range(0, number_of_ten_loops):
			if not self.transfer_n_images(10): return False

		for number in range(0, number_of_five_loops):
			if not self.transfer_n_images(5): return False

		for number in range(0, number_of_one_loops):
			if not self.transfer_n_images(1): return False

		print("All images saved successfully.")
		return True

	def delete_all_images(self):
		"""Deletes all saved images on the hub."""
		while self.total_images > 0:
			image_name = "image" + str(self.total_images + 1) + ".jpg"
			os.remove(image_name)
			self.total_images -= 1
		print("All images deleted.")

	# TODO: What other commands do we want to send
	# TODO: Implement function that calls detection algorithm


	def hub_main_cycle(self):
		""" The is the main sequence that the hub will repeatedly loop through."""
		# TODO: Look into how sensor IP's are set; we want them to be static
		# TODO: Implement multiple sensor capabilities
		# TODO: Check time on loop to know when to request images.
		# TODO: Implement a stored variable with all sensor's network information
		# TODO: Handle exceptions for loss of signal



#--------------------------------------------------------------------------------------------------

class DummyResponseHandler:
	def response_callback(self, conn, client_addr, data):
		print(str(data))


class ImageResponseHandler:
	def response_callback(self, conn, addr, data):
		file = open("image.jpg", "wb")
		file.write(data)
		print("wrote response data to file")

client = HubClient()
#client.connect("10.3.141.54", 1234)
client.connect("127.0.0.1", 1234)
client.get_sensor_images()
client.disconnect()



"""
resp_handler = DummyResponseHandler()
client = HubClient()
client.connect("10.3.141.54", 1234)
client.execute_command("ping xyz", resp_handler)
client.disconnect()

resp_handler = ImageResponseHandler()
client.connect("10.3.141.54", 1234)
client.execute_command("getimage", resp_handler)
client.disconnect()
"""
