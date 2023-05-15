import cv2
import random
from argparse import *
import hashlib
import base64
from Crypto.Cipher import AES
import uuid
import os
from pydub import AudioSegment
from pydub.silence import detect_silence
from pydub.generators import WhiteNoise
import traceback
from pathlib import Path

# generate a unique name for the folder
FOLDER_NAME = str(uuid.uuid4())

# ----------------------- IMAGE -----------------------
def addPositions(image, pixel_num, number_to_add):
	new_pixel_num = pixel_num + number_to_add
	
	# calculamos el width y height
	new_width = new_pixel_num % image.shape[1]
	new_height = new_pixel_num // image.shape[1]

	# hacemos algunas comprobaciones (para ver que sigue dentro de la imagen)
	if(new_width >= image.shape[1] or new_height >= image.shape[0]):
		print('\033[1;31;40m[!] Error. The calculated positions are outside the image.\033[0;37;40m')
		remove_folder()
		exit(1)

	return new_pixel_num, new_width, new_height

def encode_image(filename, plaintext_password):
	while(is_correct_extension(filename, 'image') == False):
		filename = input("Introduce the filename of the image (must be .png): ")
	image = cv2.imread(filename)
	
	# we save the original image like BGR to use later
	try:
		aux_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	except:
		print("\033[1;31;40m[!] The image cannot be black and white.\033[0;37;40m")
		remove_folder()
		exit(1)
	cv2.imwrite("./" + FOLDER_NAME + "/" + Path(filename).stem + "_bgr.png", aux_image)

	# hacemos que el pixel en el que iniciar esté en el 
	# primer cuarto de imagen (para dejar espacio para el mensaje)
	initial_pixel_num = random.randrange(1, image.shape[0] * image.shape[1] // 10, 1)
	print('\033[1;33;40m[*] The initial pixel number is: ' + str(initial_pixel_num) + '\033[0;37;40m')
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
		print('\033[1;31;40m[!] The message entered is too large to store in this image!\033[0;37;40m')
		remove_folder()
		exit(1)

	index = 0
	current_pixel = initial_pixel_num
	while(index < len(message)):
		pixel = image[current_height][current_width]
		pixel[2] = ord(message[index])
		jump = pixel[0] if pixel[0] != 0 else 100
		current_pixel, current_width, current_height = addPositions(image, current_pixel, jump)
		index += 1

	# converting the image from BGR to RGB
	new_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

	out_filename = "./" + FOLDER_NAME + "/" + Path(filename).stem + "_stego.png"
	cv2.imwrite(out_filename, new_image)

	return initial_pixel_num, out_filename


def decode_image(filename, initial_pixel_num, plaintext_password):
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
		print('\033[1;31;40m[!] The password is NOT correct!\033[0;37;40m')
		remove_folder()
		exit(1)

	print('\033[1;32;40m[+] The message is: ' + plaintext + '\033[0;37;40m')

# -----------------------------------------------------



# ----------------------- AUDIO - MODE 1 -----------------------
def add_noise(file:AudioSegment, duration, start):
	noise = WhiteNoise().to_audio_segment(duration=duration)
	silence = AudioSegment.silent(duration=start)
	change_in_dBFS = -80 - noise.dBFS
	final = noise.apply_gain(change_in_dBFS)
	return file.overlay(silence + final)


def analyze_silences(audio_filename, min_silence_len):
    file = AudioSegment.from_wav(audio_filename)
    file_edited = file

    output_file = "./" + FOLDER_NAME + "/" + Path(audio_filename).stem + "_edited.wav"

    # First check that our audio file does not have any absolute silence
    silence_range = detect_silence(file, 3, silence_thresh=-100000000)
    if len(silence_range) > 0:
        # As the audio has absolute silence, we can't use it
        # we are going to add some inaudible noise to the audio
        # so we can use it
        print('\033[1;31;40m[!] Absolute silence found in audio file\033[0;37;40m')
        print('\033[1;33;40m[*] Adding inaudible noise to the audio file\033[0;37;40m')
        for value in silence_range:
            start = value[0]
            end = value[1]
            duration = end - start
            print('\033[1;33;40m[*] Silence duration: ' + str(duration) + '\033[0;37;40m')
            file_edited = add_noise(file, duration, start)
        file_edited.export(output_file, format="wav")
        print("\033[1;32;40m[+] Audio changed with white noise\033[0;37;40m")
    else:
        print('\033[1;33;40m[*] No absolute silence found in audio file\033[0;37;40m')
        file_edited.export(output_file, format="wav")
        print("\033[1;32;40m[+] Audio hasn't been changed\033[0;37;40m")
    
    # Now we can check the ranges where the silence threshold is under -60 dBFS
    neccessary_silence = min_silence_len*5+40
    ranges = detect_silence(file, neccessary_silence, -60.0)
    print('\033[1;33;40m[*] Found the following ranges: ' + str(ranges) + '\033[0;37;40m')
    if(len(ranges) == 0):
        print('\033[1;31;40m[!] Error. No silence found in audio file, use the mode 2 instead (with -m 2).\033[0;37;40m')
        remove_folder()
        exit(1)
    return ranges, output_file


def encode_audio_mode1(audio_filename, number):
	while(is_correct_extension(audio_filename, 'audio') == False):
		audio_filename = input("Introduce the filename of the audio (must be .wav): ")

	print('\033[1;33;40m[*] Decimal number to hide:',  number, '\033[0;37;40m')
	# convertir el mensaje en una lista de cadenas binarias
	number = decimalToBinary(int(number))
	print('\033[1;33;40m[*] Binary number to hide:', number, '\033[0;37;40m')

	ranges, audio_filename = analyze_silences(audio_filename, len(number))

	file = AudioSegment.from_wav(audio_filename)

	# Randomize the range that we will use
	#print("\033[1;33;40m[*] Found: " + str(len(ranges)) + " ranges\033[0;37;40m")
	random_range = random.randint(0, len(ranges)-1)
	if(random_range == len(ranges)-1 and random_range != 0):
		random_range -= 1
	if(ranges[random_range][0] == 0):
		random_range += 1
	length = len(str(number))
	final_audio = AudioSegment.silent(duration=length*5)
	#print('\033[1;33;40m[*] Using range: ' + str(ranges[random_range]) + '\033[0;37;40m')
	consequent = 1
	k = 0
	# Iterate over the binary number
	for i in range(length):
		if k >= length:
			break
		# Select each bit and depending on the value
		# we will add a silence or a noise
		# 0 -> silence
		# 1 -> noise
		# Also check if the next value is the same
		# if it is, we will add the value
		if number[k] == '0':
			k += 1
		else:
		   # Check if the next values are the same
			for j in range(k+1, length):
				if number[j] == '1':
					consequent += 1
				else:
					break
			# Add noise
			# The k value, it's the position (k*5) where we will add the noise
			# The consequent value is the duration of the noise			 
			start = k*5
			noise = WhiteNoise().to_audio_segment(duration=consequent*5)
			# Change the volume of the noise
			change_in_dBFS = - 60 - noise.dBFS
			final = noise.apply_gain(change_in_dBFS)
			final_audio = final_audio.overlay(final, position=start)
			k += consequent
			consequent = 1

	# Export the audio file
	aux_filename = audio_filename.replace("_edited", "_aux")
	final_audio.export(aux_filename, format="wav")

	start = ranges[random_range][0]
	ranges = detect_silence(final_audio, 5, -69.0)	
	

	# We need to import the audio again, due to some errors
	audio_edited = AudioSegment.from_wav(audio_filename)
	
	# Split the audio file in 2 parts, adding the secret in the middle
	audio_start:AudioSegment = audio_edited[:start]
	audio_end:AudioSegment = audio_edited[(start+40+final_audio.duration_seconds*1000):]
	audio_final = audio_start + AudioSegment.silent(duration=20) + final_audio + AudioSegment.silent(duration=20) + audio_end
	print("\033[1;33;40m[*] Secret starting at milisecond: "+ str(start+20)+'\033[0;37;40m')
	print("\033[1;33;40m[*] Audio edited, secret length: " + str(final_audio.duration_seconds*1000)+'\033[0;37;40m')
	print("\033[1;33;40m[*] Secret finishing in audio at : " + str((start + 20 + final_audio.duration_seconds*1000)) + " miliseconds\033[0;37;40m")
	out_filename = audio_filename.replace("_edited", "_stego")
	audio_final.export(out_filename, format="wav")
	print("\033[1;32;40m[+] Audio saved succesfully!\033[0;37;40m")
	
	return out_filename


def decode_audio_mode1(audio_filename):
    audio_filename = audio_filename.replace("_mode2", "_mode1")
    audio = AudioSegment.from_wav(audio_filename)

    # Find the audio chunk, with the 2 ms seconds of silence at the start and end
    find_silence_range = detect_silence(audio, 18, silence_thresh=-1000000)
    if(find_silence_range[0][0] == 0):
        find_silence_range.pop(0)

    length = find_silence_range[-1][0] - find_silence_range[0][1] 
    if(find_silence_range[-1][1] - find_silence_range[-1][0] > 20):
        length += (find_silence_range[-1][1] - find_silence_range[-1][0] - 20)
    
    # Once when we have the audio chunk with the secret, we need to retrieve it
    # We will use the same method as before, but in reverse
    # We will check the silence and the noise

    start_point = find_silence_range[0][1]
    
    
    absolute_silence_range = detect_silence(audio[start_point:start_point+length], 3, silence_thresh=-70)
    final_number = ''

    for i in range(0, len(absolute_silence_range)):
        i_range = absolute_silence_range[i]
        if(i==0 and absolute_silence_range[i][0] >> 0):
            n = i_range[0] / 5
            final_number += int(round(n))*'1'

        if(i >> 0):
            sum = (i_range[0] -  absolute_silence_range[i-1][1])  / 5
            final_number += int(round(sum))*'1'

        n = (i_range[1] - i_range[0]) / 5
        final_number += int(round(n))*'0'

        if(i == len(absolute_silence_range)-1):
            n = (length - i_range[1]) / 5
            final_number += int(round(n))*'1'
    
    #print('\033[1;33;40m[*] The final number is:', final_number, '\033[0;37;40m')
    initial_pixel = int(final_number, 2)
    if(initial_pixel > 1000000000000):
        raise Exception
    print('\033[1;33;40m[*] The initial pixel is:', initial_pixel, '\033[0;37;40m')
    return initial_pixel
# --------------------------------------------------------------


# ----------------------- AUDIO - MODE 2 -----------------------
# función para convertir un número entero en una cadena binaria de 8 bits
def decimalToBinary(decimal_number):
	return bin(decimal_number).replace("0b", "")

def create_array_of_spaces(audio_duration, number_length):
	result = []
	accum = 0
	for i in range(number_length):
		average_space = (audio_duration - 50 - accum) // (number_length - i)
		number_to_add = random.randint(average_space // 5, average_space)
		accum += number_to_add
		result.append(accum)
	return result

# función para ocultar un mensaje en el audio
def encode_audio_mode2(audio_file, message):
	while(is_correct_extension(audio_file, 'audio') == False):
		audio_file = input("Introduce the filename of the audio (must be .wav): ")

	print('\033[1;32;40m[+] Decimal number to hide:',  message, '\033[0;37;40m')
	# convertir el mensaje en una lista de cadenas binarias
	binary_message = decimalToBinary(int(message))
	print('\033[1;33;40m[*] Binary number to hide:', binary_message, '\033[0;37;40m')

	# cargar el archivo de audio
	audio = AudioSegment.from_file(audio_file, format="wav")

	# obtener el vector aleatorio de segundos donde introducir el silencio
	times = create_array_of_spaces(len(audio), len(binary_message)+1)

	# ocultar cada bit del mensaje en las frecuencias no audibles
	for i in range(len(binary_message)):
		if binary_message[i] == "1":
			audio = audio[:times[i]].append(AudioSegment.silent(duration=10), crossfade=2).append(audio[times[i] + 10:], crossfade=2)
		elif binary_message[i] == "0":
			audio = audio[:times[i]].append(AudioSegment.silent(duration=7), crossfade=2).append(audio[times[i] + 7:], crossfade=2)
	# añadimos uno más al final para asegurarnos
	audio = audio[:times[len(binary_message)]].append(AudioSegment.silent(duration=13), crossfade=2).append(audio[times[len(binary_message)] + 13:], crossfade=2)

	# guardar el archivo con el mensaje oculto
	output_file = "./" + FOLDER_NAME + "/" + Path(audio_file).stem + "_stego.wav"
	audio.export(output_file, format="wav")
	print("\033[1;32;40m[+] Audio saved succesfully!\033[0;37;40m")

	return output_file

def decode_audio_mode2(audio_file):
	audio = AudioSegment.from_file(audio_file)
	silent_ranges = detect_silence(audio, min_silence_len=1, silence_thresh=-100000000)

	diferencias = [i[1] - i[0] for i in silent_ranges]

	new_silent_ranges = []
	for i in range(len(diferencias)):
		if diferencias[i] <= 6:
			new_silent_ranges.append(silent_ranges[i])
		elif diferencias[i] in [7,8,9]:
			new_silent_ranges.append(silent_ranges[i])

	new_diferencias = [i[1] - i[0] for i in new_silent_ranges]
	
	binary_number = ''
	for i in new_diferencias:
		if i in [1,2,3]:
			binary_number += '0'
		elif i in [4,5,6]:
			binary_number += '1'
		elif i in [7,8,9]:
			break

	#binary_number = ''.join(['1' if i in [4, 5, 6] else '0' if i in [1, 2, 3] else '-' for i in new_diferencias])
	
	result = int(binary_number, 2)
	print('\033[1;33;40m[*] The initial pixel is:', result, '\033[0;37;40m')
	return result
# --------------------------------------------------------------



# ----------------------- VIDEO -----------------------
def create_video(image_filename, audio_filename, video_filename, mode):
	from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
	
	while(is_correct_extension(video_filename, 'video') == False):
		print("\033[1;31;40m[!] The filename is not correct. The video must be .avi!\033[0;37;40m")
		video_filename = input("Introduce the filename of the output video: ")

	original_image = image_filename.replace("_stego", "_bgr")

	# create the audio clip object
	audio_clip = AudioFileClip(audio_filename)
	# create the image clip object
	clip1 =  ImageClip(original_image).set_duration((audio_clip.duration + 1) // 10)
	clip2 =  ImageClip(image_filename).set_duration(1)
	clip3 =  ImageClip(original_image).set_duration(audio_clip.duration - ((audio_clip.duration + 1) // 10) - 1)
	clips = [clip1, clip2, clip3]
	video_clip = concatenate_videoclips(clips, method='compose')
	# use set_audio method from image clip to combine the audio with the image
	video_clip = video_clip.set_audio(audio_clip)
	# specify the duration of the new clip to be the duration of the audio clip
	video_clip.duration = audio_clip.duration
	# set the FPS to 1
	video_clip.fps = 1
	# export the video (in rawvideo format)
	if mode == 1:
		video_clip.write_videofile(video_filename, codec="rawvideo", audio_codec="pcm_s16le", audio_fps=48000, audio_bitrate="768k", ffmpeg_params=["-ac", "1"])
	else:
		video_clip.write_videofile(video_filename, codec="rawvideo", audio_codec="pcm_s16le")

	print("\033[1;32;40m[+] The video with the hidden message has been created: " + video_filename + '\033[0;37;40m')


def get_frame(video_filename, audio_duration):
	# read the video from specified path
	try:
		while(is_correct_extension(video_filename, 'video') == False):
			video_filename = input("Introduce the filename of the output video (must be .avi): ")
		cam = cv2.VideoCapture(video_filename)
	except:
		print("\033[1;31;40m[!] Error: File not found (" + video_filename + ")!\033[0;37;40m")
		remove_folder()
		exit(1)
	
	frame_to_read = int((audio_duration + 1) // 10 + 1)

	# reading from frame (skip some frames)
	for i in range(frame_to_read):
		ret,frame = cam.read()

	if ret:
		frame_filename = "./" + FOLDER_NAME + "/frame.png"

		# writing the extracted images
		cv2.imwrite(frame_filename, frame)
	  
	# release all space and windows once done
	cam.release()
	cv2.destroyAllWindows()

	return frame_filename


def get_audio(video_filename):
	from moviepy.editor import VideoFileClip

	try:
		while(is_correct_extension(video_filename, 'video') == False):
			video_filename = input("Introduce the filename of the output video (must be .avi): ")
		video = VideoFileClip(video_filename)
	except:
		print("\033[1;31;40m[!] Error: File not found (" + video_filename + ")!\033[0;37;40m")
		remove_folder()
		exit(1)
	audio = video.audio
	
	# guardamos el audio con unas características u otras dependiendo del modo
	audio_filename = './' + FOLDER_NAME + '/audio_mode1.wav'
	audio.write_audiofile(audio_filename, codec="pcm_s16le", fps=48000, bitrate="768k", ffmpeg_params=["-ac", "1"])

	audio_filename = './' + FOLDER_NAME + '/audio_mode2.wav'
	audio.write_audiofile(audio_filename, codec="pcm_s16le", fps=11025, bitrate="352k")

	return audio_filename, audio.duration
# -----------------------------------------------------



# ----------------------- OTHER -----------------------
def is_correct_extension(filename, type_of_file):
	if(filename == ''):
		return False
	extension = os.path.splitext(filename)[1][1:]
	if(type_of_file == 'image' and extension in ['png']):
		return True
	if(type_of_file == 'video' and extension in ['avi']):
		return True
	if(type_of_file == 'audio' and extension in ['wav']):
		return True
	return False

def create_folder():
	try:
		# creating a temporal folder
		if not os.path.exists(FOLDER_NAME):
			os.makedirs(FOLDER_NAME)
	# if not created then raise error
	except OSError:
		print ('\033[1;31;40m[!] Error: Creating the temporal directory\033[0;37;40m')
		exit(1)

def remove_folder():
	import shutil
	shutil.rmtree(FOLDER_NAME)


def main():
	# add arguments
	parser = ArgumentParser(description="Tool to hide a message into a video, using stego methods on images and audios", formatter_class=RawTextHelpFormatter)
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-e", "--encode", help="Encode a message on a video", action='store_true')
	group.add_argument("-d", "--decode", help="Decode a message from a video", action='store_true')
	parser.add_argument("-v", "--video", help="Video to encode (filename of the output) or decode (filename of the input). Must be .avi", type=str)
	parser.add_argument("-i", "--image", help="Image to use when encoding (must be .png)", type=str)
	parser.add_argument("-a", "--audio", help="Audio to use on encoding (must be .wav)", type=str)
	parser.add_argument("-p", "--password", help="Password to encode or decode", type=str)
	parser.add_argument("-m", "--mode", nargs='?', const=1, type=int, default=1, choices=[1, 2], help="Change the way of hiding the secret in the audio (mode 1 by default):\n(1) Use the silences already present in the audio (if they exist). Beta version.\n(2) Add new silences to the audio.")
	args = parser.parse_args()

	try:
		if(args.encode):
			# we create the folder to save data
			create_folder()
			# set the password
			password = args.password if args.password else ''
			# hide the message into the image
			input_image = args.image if args.image else ''
			initial_pixel, encoded_image_filename = encode_image(input_image, password)
			
			input_audio = args.audio if args.audio else ''
			if(args.mode == 1):
				# hide the initial pixel into the audio using their silences
				encoded_audio_filename = encode_audio_mode1(input_audio, initial_pixel)
			else:
				# hide the initial pixel into the audio adding new silences
				encoded_audio_filename = encode_audio_mode2(input_audio, initial_pixel)
			# create the video
			video_filename = args.video if args.video else ''
			create_video(encoded_image_filename, encoded_audio_filename, video_filename, args.mode)
			remove_folder()

		elif(args.decode):
			# we create the folder to save data
			create_folder()
			# set the password
			password = args.password if args.password else ''
			# split the video to get an audio and an image
			video_filename = args.video if args.video else ''
			audio_filename, audio_duration = get_audio(video_filename)
			frame_filename = get_frame(args.video, audio_duration)
			# get the initial pixel from the audio
			try:
				print("\033[1;33;40m[*] Getting the initial pixel from audio using mode 1...\033[0;37;40m")
				initial_pixel = decode_audio_mode1(audio_filename)
			except:
				print("\033[1;31;40m[!] Something went wrong using mode 1\033[0;37;40m")
				print("\033[1;33;40m[*] Getting the initial pixel from audio using mode 2...\033[0;37;40m")
				initial_pixel = decode_audio_mode2(audio_filename)
			# get the message from the image
			decode_image(frame_filename, initial_pixel, password)
			remove_folder()
	except Exception as e:
		print("\033[1;31;40m[!] Something went wrong!\033[0;37;40m")
		traceback.print_exc()
		remove_folder()

if __name__ == "__main__":
	main()
# -----------------------------------------------------