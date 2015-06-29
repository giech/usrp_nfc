# Eavesdropping on and Emulating MIFARE Ultralight and Classic Cards Using Software Defined Radio

By **Ilias Giechaskiel** https://ilias.giechaskiel.com

This project contains a Software Defined Radio (SDR) implementation for ISO 14443 Type A NFC/RFID communications. Specifically, it can eavesdrop and decrypt MIFARE Ultralight and Classic 1K communications and partially emulate them. It can also work with a USRP N210, with the BasicRX/TX and LFRX/TX daughterboards. For more details, please read the [detailed PDF write-up](report/report.pdf).


The usage is as follows:
```
Usage: usrp_nfc.py [options]

Options:
  -h, --help            show this help message and exit
  -t TYPE, --type=TYPE  action type [tag, reader, all]
  -a ACTION, --action=ACTION
                        action [eavesdrop, emulate]
  -i SRC, --input=SRC   input wav file or uhd
  -s IN_RATE, --sample_in_rate=IN_RATE
                        input sample rate
  -S OUT_RATE, --sample_out_rate=OUT_RATE
                        output sample rate
  -o DST, --output=DST  output
  -e EXTRA, --extra_file=EXTRA
                        helper file for emulation
```               
						
The defaults are as follows:
```
action = eavesdrop
type = all
input = uhd
sample_in_rate = 2M samples/sec
sample_out_rate = sample_in_rate
output = None
extra_file = None
```

The output and input parameters can either be a WAV file or uhd for the USRP (see the [recordings](recordings) folder for examples that can be used).

Note that the project is somewhat sensitive to the antenna -- any errors can usually be fixed by changing the `hi_val` parameter passed into the [transition_sink](code/transition_sink.py) module (called from the [decoder](code/decoder.py) module). In my tests, values from 1.05 to 1.1 work, depending on the antenna/PCD/PICC setup.

For the emulate action, a `.json` file (with examples in the [data](data) folder) needs to be passed in through the extra_file parameter. See the [create_json](code/create_json.py) module for an example of how to create it. Note that the rands parameter is only needed for MIFARE Classic 1K cards, and is used to ensure that when emulating against a recording (with the input switch) the parameters match. 

Example outputs of the program are found under the [outputs](outputs) folder.
