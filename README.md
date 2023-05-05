# stego-tool

## Installation

1. Clone this repository:
```bash
$> git clone https://github.com/davidmohedanovazquez/stego-tool.git
```

2. Install all the Python requirements:
```bash
$> pip3 install -r requirements.txt
```

3. Install `ffmpeg`:

- On Linux:
```bash
$> sudo apt get install ffmpeg
```

- On Windows: You can follow [this](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/) manual


## Usage

- Hide the message:
```bash
$> python3 stego-tool.py -e [-i <input_image_filename>.png] [-a <input_audio_filename>.wav] [-v <output_video_filename>.avi] [-p <password>] [-m {1,2}]
```

- Obtain the message:
```bash
$> python3 stego-tool.py -d [-v <input_video_filename>.avi] [-p <password>]
```


## Accepted formats

- Image format: PNG
- Audio format: WAV
- Video format: AVI


## Examples

- Hide a message using image1.png and audio1.wav, saving the result on video1.avi with the password "hello"
```bash
$> python3 stego-tool.py -e -i image1.png -a audio1.wav -v video1.avi -p "hello"
```

- Obtain a message from video1.avi using the password "hello"
```bash
$> python3 stego-tool.py -d -v video1.avi -p "hello"
```

- If you do not provide any of the parameters, you will be prompted to enter them later.
```bash
$> python3 stego-tool.py -e -i image1.png
$> python3 stego-tool.py -d
```
