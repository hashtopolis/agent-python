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
