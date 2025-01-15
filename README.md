# Albert Wrapper
A socket wrapper to run [Albert](https://sites.google.com/site/diplomacyai/QuickStart) on [Diplomacy: DATC-Compliant Game Engine](https://github.com/aLLAN-DIP/diplomacy).

## Why and How
Because Albert only runs on Windows and requires DAIDE server, it is difficult to visualize the game and have a better understanding of how well Albert performs. We want to connect Albert to a more user-friendly interface to
- streamlining the process of running human games involving Albert
- collecting data for analysis

To run Albert in our interface, [the server imitator](./server_imitator.py) opens a socket and listens for communications from albert. It then translates any communication between Albert and the server using the DAIDE and dipnet syntax converter.

## Requirements
- Windows
- Python 3.11+ (for the TOML parser)
- [Diplomacy: DATC-Compliant Game Engine](https://github.com/aLLAN-DIP/diplomacy)
- [Chiron Utils](https://github.com/ALLAN-DIP/chiron-utils) (for running Albert as advisor)

## Usage
- start the Diplomacy server (see [here](https://github.com/aLLAN-DIP/diplomacy?tab=readme-ov-file#web-interface))
- `python server_imitator.py`
- `start_albert.bat <num_instances>`

You may need to change path to Albert in `start_albert.bat`.