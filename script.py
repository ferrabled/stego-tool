import cv2
import random
import argparse
import hashlib
import base64
from Crypto.Cipher import AES

def addPositions(image, pixel_num, number_to_add):
	new_pixel_num = pixel_num + number_to_add
	
	# calculamos el width y height
	new_width = new_pixel_num % image.shape[1]
	new_height = new_pixel_num // image.shape[1]

	# hacemos algunas comprobaciones (para ver que sigue dentro de la imagen)
	if(new_width >= image.shape[1] or new_height >= image.shape[0]):
		print('Error. The calculated positions are outside the image.')
		exit(1)

	return new_pixel_num, new_width, new_height



def encode(filename, out_filename, plaintext_password):
	image = cv2.imread(filename)

	# hacemos que el pixel en el que iniciar esté en el 
	# primer cuarto de imagen (para dejar espacio para el mensaje)
	initial_pixel_num = random.randrange(0, image.shape[0] * image.shape[1] // 4, 1)
	print('The initial pixel number is: ' + str(initial_pixel_num))
	_, current_width, current_height = addPositions(image, initial_pixel_num, 0)

	# introducir la password
	while(plaintext_password == ''):
		plaintext_password = input('Introduce the password to encode: ')
	# obtenemos el hash de la password con sha256
	password = hashlib.sha256(plaintext_password.encode("utf-8")).digest()

	# introducir el mensaje
	message = ''
	while(message == ''):
		message = input('Introduce the message to be encoded: ')

	# encriptamos el mensaje
	cipher = AES.new(password, AES.MODE_EAX)
	nonce = cipher.nonce
	ciphertext, tag = cipher.encrypt_and_digest(message.encode("utf-8"))
	# create the final message with all fields
	message = base64.b64encode(nonce).decode("utf-8")
	message += base64.b64encode(tag).decode("utf-8")
	message += base64.b64encode(ciphertext).decode("utf-8")
	message += chr(145) * 3 # we add the final string

	# calcular si se puede meter todo el mensaje (vemos el peor de los casos)
	if((initial_pixel_num + len(message) * 256) >= (image.shape[0] * image.shape[1])):
		print('The message entered is too large to store in this image!')
		exit(1)

	index = 0
	current_pixel = initial_pixel_num
	while(index < len(message)):
		pixel = image[current_height][current_width]
		pixel[2] = ord(message[index])
		jump = pixel[0] if pixel[0] != 0 else 100
		current_pixel, current_width, current_height = addPositions(image, current_pixel, jump)
		index += 1

	while(out_filename == ''):
		out_filename = input('Introduce the name of the output image (with extension): ')
	cv2.imwrite(out_filename, image)


def decode(filename, initial_pixel_num, plaintext_password):
	image = cv2.imread(filename)

	while(initial_pixel_num == -1):
		initial_pixel_num = int(input('Introduce the number of the initial pixel: '))
	_, current_width, current_height = addPositions(image, initial_pixel_num, 0)

	message = ''
	final_string = chr(145) * 3

	# introducir la password
	while(plaintext_password == ''):
		plaintext_password = input('Introduce the password to decode: ')
	# obtenemos el hash de la password con sha256
	password = hashlib.sha256(plaintext_password.encode("utf-8")).digest()

	index = 0
	current_pixel = initial_pixel_num
	while(message[-3:] != final_string):
		pixel = image[current_height][current_width]
		message += chr(pixel[2])
		jump = pixel[0] if pixel[0] != 0 else 100
		current_pixel, current_width, current_height = addPositions(image, current_pixel, jump)
		#todo: comprobar si se ha llegado al final de la imagen

	message = message[:-3]
	
	# desencriptamos el mensaje
	block_size_b64 = 24
	nonce = base64.b64decode(message[:block_size_b64])
	tag = base64.b64decode(message[block_size_b64:block_size_b64 * 2])
	ciphertext = base64.b64decode(message[block_size_b64 * 2:])
    # ---
	cipher = AES.new(password, AES.MODE_EAX, nonce=nonce)
	try:
		plaintext = cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")
	except:
		print('The password is NOT correct!')
		exit(1)

	print('The message is: ' + plaintext)


def main():
	# add arguments
	parser = argparse.ArgumentParser()
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-e", "--encode", help="Encode a message on a image", action='store_true')
	group.add_argument("-d", "--decode", help="Decode a message from a image", action='store_true')
	parser.add_argument("image", help="Image to encode or decode", type=str)
	parser.add_argument("-o", "--output", help="Name of the output image (on encoding)", type=str)
	parser.add_argument("-n", "--pixel_number", help="Number of the initial pixel (on decoding)", type=int)
	parser.add_argument("-p", "--password", help="Password to encode or decode", type=str)
	args = parser.parse_args()

	if(args.encode):
		out_filename = args.output if args.output else ''
		password = args.password if args.password else ''
		encode(args.image, out_filename, password)
	elif(args.decode):
		initial_pixel = args.pixel_number if args.pixel_number else -1
		password = args.password if args.password else ''
		decode(args.image, initial_pixel, password)

if __name__ == "__main__":
	main()