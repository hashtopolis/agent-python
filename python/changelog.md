
## 0.1.8 -> 0.x.x

### Features

* Added support for UDP multicast downloads on linux computers in local environments

## 0.1.7 -> 0.1.8

### Features

* The agent can request a to-delete filename list from the server and then cleanup them locally
* Piping can be enforced from the server for specific tasks.

## 0.1.6 -> 0.1.7

### Features

* Agent sends GPU utilization and temperature (if available)
* Added support for downloading files via rsync

### Bugfixes

* Catching the correct exception on downloads
* Avoiding endless loop on hashlist download error

## 0.1.5 -> 0.1.6

### Features

* The agent binary can update itself automatically and restart afterwards

### Bugfixes

* Fixed reading of allow-piping config variable

## 0.1.4 -> 0.1.5

### Features

* When a chunk can not ideally fully use the GPU it tries to use piping to increase the speed to the most possible.
* Agents can now run PRINCE tasks
* Device detection for CPUs now is independent from localization on Linux computers

### Bugfixes

* Fixed zap handling (including also unsalted hashes)
* Added delay to avoid very fast looping on agent errors

## 0.1.3 -> 0.1.4

### Bugfixes

* Fixed endless loop on error from server when sending chunk progress
* Fixed a critical bug in parsing the hashcat status when TEMP values are included

## 0.1.2 -> 0.1.3

* Fixed detection of 32/64 bit operating systems
* Changed timestamp format on logging
* Catching connection problems on downloads
* Added switch to 7z extraction to force overwrite of conflicting files

## 0.1.1 -> 0.1.2

* Added support for reading the 32/64bit settings from the client itself and use the appropriate hashcat binary
* On the logfile output timestamp and log level are now reported
* Fixed sending error function
* Fixed bug with killing hashcat process in case the server sends 'stop' or an error occurs
* Changed running directory for hashcat cracker, changed all paths
* Extracting is overwriting existing files if present to make sure files are up-to-date
