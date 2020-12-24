## v0.6.1 -> v0.x.x

## v0.6.0 -> v0.6.1

### Features

* Added monitoring of cpu utilization and sending to server.
* Allow setting a certs bundle using for the connections.

### Bugfixes
* Fixed missing space with certain attack commands.
* Fixed crashing agent when hashcat benchmark output contained warnings.
* Fixed version detection on Hashcat release versions.
* Fixed parsing of hashcat status with no temp values.

## v0.5.0 -> v0.6.0

### Features

* Generic integration of preprocessors.
* Added compatibility for newer Hashcat versions with different outfile format specification.

### Bugfixes

* Fixed crash handling on generic cracker for invalid binary names.

## v0.4.0 -> v0.5.0

### Enhancements

* Adapt to path change of Hashcat which dropped pre-builds for 32-bit.

### Bugfixes

* Increased waiting time after full hashlist crack as hashcat quits too fast.

## v0.3.0 -> v0.4.0

### Features

* Agents can de-register from server automatically on quitting.

### Bugfixes

* Fixed benchmark commands for hashes with have salts separated from hash.

### Enhancements

* Agent checks if there is already an agent running in the same directory.
* Agent cleans up old hashcat PID files on startup.
* Outfile names can be unique if configured.

## v0.2.0 -> v0.3.0

### Features

* Agents can run health checks requested from the server.

### Bugfixes

* Fixed benchmark results when having many GPUs in one agent.
* Fixed sleep after finishing of task to avoid cracks not being caught.

### Enhancements

* Added check for chunk length 0 sent from the server to avoid full agent crash on running.
* Using requests session
* Added option for using proxies
* Added HTTP Basic Auth support

## v0.1.8 -> v0.2.0

### Features

* Added support for UDP multicast downloads on linux computers in local environments

### Bugfixes

* Fixed when a agent starts the first time there was no logging output

## v0.1.7 -> v0.1.8

### Features

* The agent can request a to-delete filename list from the server and then cleanup them locally
* Piping can be enforced from the server for specific tasks.

## v0.1.6 -> v0.1.7

### Features

* Agent sends GPU utilization and temperature (if available)
* Added support for downloading files via rsync

### Bugfixes

* Catching the correct exception on downloads
* Avoiding endless loop on hashlist download error

## v0.1.5 -> v0.1.6

### Features

* The agent binary can update itself automatically and restart afterwards

### Bugfixes

* Fixed reading of allow-piping config variable

## v0.1.4 -> v0.1.5

### Features

* When a chunk can not ideally fully use the GPU it tries to use piping to increase the speed to the most possible.
* Agents can now run PRINCE tasks
* Device detection for CPUs now is independent from localization on Linux computers

### Bugfixes

* Fixed zap handling (including also unsalted hashes)
* Added delay to avoid very fast looping on agent errors

## v0.1.3 -> v0.1.4

### Bugfixes

* Fixed endless loop on error from server when sending chunk progress
* Fixed a critical bug in parsing the hashcat status when TEMP values are included

## v0.1.2 -> v0.1.3

* Fixed detection of 32/64 bit operating systems
* Changed timestamp format on logging
* Catching connection problems on downloads
* Added switch to 7z extraction to force overwrite of conflicting files

## v0.1.1 -> v0.1.2

* Added support for reading the 32/64bit settings from the client itself and use the appropriate hashcat binary
* On the logfile output timestamp and log level are now reported
* Fixed sending error function
* Fixed bug with killing hashcat process in case the server sends 'stop' or an error occurs
* Changed running directory for hashcat cracker, changed all paths
* Extracting is overwriting existing files if present to make sure files are up-to-date
