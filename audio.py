from pydub import AudioSegment
from pydub.silence import detect_silence
from pydub.generators import WhiteNoise
import random

def convert(decimal):
    binary = bin(decimal)
    binary = binary.replace("0b", "")
    return binary


def add_noise(file:AudioSegment, duration, start):
    noise = WhiteNoise().to_audio_segment(duration=duration)
    silence = AudioSegment.silent(duration=start)
    change_in_dBFS = -30 - noise.dBFS
    final = noise.apply_gain(change_in_dBFS)
    return file.overlay(silence + final)


def analyze_silences(file, min_silence_len):
    file_edited = file
    # First check that our audio file does not have any absolute silence
    silence_range = detect_silence(file, 3, silence_thresh=-100000000)
    print(silence_range)
    if len(silence_range) > 0:
        # As the audio has absolute silence, we can't use it
        # we are going to add some inaudible noise to the audio
        # so we can use it
        print('Absolute silence found in audio file')
        print('Adding inaudible noise to the audio file')
        for value in silence_range:
            start = value[0]
            end = value[1]
            duration = end - start
            print('Silence duration: ' + str(duration))
            file_edited = add_noise(file, duration, start)
        file_edited.export("./temp/audio_edited.mp3", format="mp3")
        print("Audio changed with white noise")
        #raise ValueError('Absolute silence found in audio file')
    else:
        print('No absolute silence found in audio file')
        file_edited.export("./temp/audio_edited.mp3", format="mp3")
        print("Audio not changed")
    
    # Now we can check the ranges where the silence threshold is under -16 dBFS
    ranges = detect_silence(file, min_silence_len, -60.0)
    print(ranges)
    print(len(ranges))
    if(len(ranges) == 0):
        raise ValueError('No silence found in audio file')
    return ranges, file_edited


def add_secret(file:AudioSegment, number, ranges):
    # Randomize the range that we will use
    print("Found: " + str(len(ranges)) + " ranges")
    random_range = random.randint(0, len(ranges)-1)
    length = len(str(number))

    final_audio = AudioSegment.silent(duration=length*4)
    print('Using range: ' + str(ranges[random_range]))

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
            print("0; empty")
            k += 1
        else:
           # Check if the next values are the same
            for j in range(k+1, length):
                if number[j] == '1':
                    consequent += 1
                else:
                    break
            print("1 *: " + str(consequent))
            # Add noise
            # The k value, it's the position (k*4) where we will add the noise
            # The consequent value is the duration of the noise             
            start = k*4
            noise = WhiteNoise().to_audio_segment(duration=consequent*4)
            # Change the volume of the noise
            change_in_dBFS = -30 - noise.dBFS
            final = noise.apply_gain(change_in_dBFS)
            final_audio = final_audio.overlay(final, position=start)

            k += consequent
            consequent = 1

    # Export the audio file
    final_audio.export("./temp/secret.mp3", format="mp3")

    start = ranges[random_range][0]
    end = ranges[random_range][1]
    duration = end - start  

    # We need to import the audio again, due to some errors
    audio_edited = AudioSegment.from_mp3("./audio.mp3")
    
    # Split the audio file in 2 parts, adding the secret in the middle
    audio_start:AudioSegment = audio_edited[:start]
    audio_end:AudioSegment = audio_edited[(start+final_audio.duration_seconds*1000):]

    audio_final = audio_start + AudioSegment.silent(duration=2) + final_audio + AudioSegment.silent(duration=2) + audio_end
    print("Secret starting at milisecond: "+ str(audio_start.duration_seconds*1000))

    print("Audio edited, secret length: " + str(final_audio.duration_seconds))
    print("Secret finishing in audio at : " + str((2 + start + final_audio.duration_seconds*1000) + 2) + " miliseconds")
    audio_final.export("./audioWithSecret.mp3", format="mp3")
    return audio_start.duration_seconds*1000


#TODO delete variable start_point, as it won't be known
def retrieve_secret(audio:AudioSegment, start_point):

    # TODO first chunk retrieval not working
    # Find the audio chunk, with the 2 ms seconds of silence at the start and end
    find_silence_range = detect_silence(audio, 2, silence_thresh=-80)
    print(find_silence_range)
    
    # Once when we have the audio chunk with the secret, we need to retrieve it
    # We will use the same method as before, but in reverse
    # We will check the silence and the noise

    #TODO once when we have the chunk, only get the length of it -(2 ms of the start)
    length = 80
    print("length: " + str(length))

    #TODO use chunk found, not the already know range
    print(str(start_point)+' - '+str(start_point+80))

    absolute_silence_range = detect_silence(audio[start_point:start_point+80], 3, silence_thresh=-40)
    print(absolute_silence_range)
    final_number = ''
    for i in range(0, len(absolute_silence_range)):
        i_range = absolute_silence_range[i]
        if(i==0 and absolute_silence_range[i][0] >> 0):
            n = i_range[0] / 4
            final_number += int(n)*'1'

        if(i >> 0):
            sum = (i_range[0] -  absolute_silence_range[i-1][1])  / 4
            final_number += int(n)*'1'

        n = (i_range[1] - i_range[0]) / 4
        final_number += int(n)*'0'

        if(i == len(absolute_silence_range)-1):
            n = (length - i_range[1]) / 4
            final_number += int(n)*'1'
               
    return final_number
        




if __name__ == '__main__':
    '''
        CREATION OF THE AUDIO FILE
    '''
    # Cast our secret number into binary
    secret_number = 1001295
    print('Secret number: ' +  str(secret_number))
    number = convert(secret_number)
    print('Binary representation: ' + str(number))
    length = len(number)
    print('Total number bits ' + str(length))
    print('Needed ' + str(length*4) + ' ms of "silence"')
    print('Checking audio file ...')
    
    # Analyze the audio, see the silenced parts (not full silence) 
    # and check if it's bigger than our needed threshold (length*4)
    try:
        #file = AudioSegment.from_mp3("./tests/chunk0.mp3")
        file = AudioSegment.from_mp3("./audio.mp3")
        ranges, file_edited = analyze_silences(file, length)
        file_edited:AudioSegment

        #ranges= [[0, 742], [1176, 1889], [2761, 3887], [5906, 7238], [7582, 8438]]
        #TODO delete *** all values *** start point
        start_point = add_secret(file_edited, number, ranges)    

    except ValueError:
        print("Not enough silence found, please use another audio file")
    except Exception as e:
        print("Something went wrong")
        print(e)    

    '''
        RETRIEVE THE SECRET
    '''
    print("start point: " + str(start_point))
    secret_number = 1001295
    print('Secret number: ' +  str(secret_number))
    number = convert(secret_number)
    print('Binary representation: ' + str(number))
    secret = AudioSegment.from_mp3("./audioWithSecret.mp3")
    secret_number = retrieve_secret(secret, start_point+2)
    print('Secret number retrieved: ' +  str(secret_number))






#pasar a binario, ver los datos, y dependiendo de si es menos de 3 ms el silencio, es un 0, sino un 1.




#our original audio should have a 'silence' of more than 20*4 ms long ()
# each bit is represented in 4ms, depending on if it's a full silence or not, it will be a 0 or a 1

