This project contains some script utilities:
- `ozwillo_auth.py`: to generate OAuth2 tokens
- `senml_generator.py`: to generate SenML messages to send to an MQTT broker
- `thingsboard_generator.py`: similar to the previous one but adapted to communicate with the Thingsboard integrated MQTT broker

In order to use the `ozwillo_auth.py` script, you just have to edit the file and fill the contextual values at the beginning of the file:
- Kernel address
- user credentials
- client app credentials and configured redirect URI
