# 1. Main usage

The crucial features of the high-performance server used in scientific research is stability on its job. The unstable
job of the server can result to sudden abortion of high-loaded scientific tasks, data loss and damage in highly
expensive hardware components such as CPU, hard disks etc. Among the factors causing the instability of the server job
are hardware and software troubles.

Examples of hardware troubles:
1. CPU overheating;
2. I/O errors within the operating memory;
3. Troubles with hard disk (I/O errors, bad blocks, logical errors etc.);
4. Unstable job of the network card.
And so on....

Examples of software troubles that can result to unstable job:
1. Outdated version of the Linux kernel that contains several security bugs;
2. Damage in the database due to hardware troubles, hacking attacks etc.;
And so on...

In order to deal with some of these factors this is important to provide regular testing of the servers. This short
program is used to perform such a test.

## 1.1. This is a continuation of the corefacility project

This utility interacts with the corefacility (e.g., it shuts down the corefacility Web server before the test and
turns it on after the test).

However, this is a stand-alone application that can work without the corefacility.

## 1.2. This is not substitution of the standard test utilities like fsck, memtester, smartmontools etc.

The main purpose of the utility is to call fsck, memtester, smartmontools at regular intervals. Hence, it doesn't work
without them.

## 1.3. This is not substitution of the systemd timers

Because the corefacility-check implements its own internal tests that can be run in conjunction with external testers
like memtester, fsck etc. It can process the standard output from these utilities, has an extensive logging system
(e.g., the corefacility-checker will e-mail you in case of troubles), provide pre-test and post-test routines
(e.g., the fsck requires a given disk to be unmounted, this is important for the SQL dump and POSIX synchronization
that the corefacility server is shut down).

## 1.4. The corefacility-checker is an intermediate

between the standard testing utilities like fsck, smartmontools etc. on one side and the systemd timer on the other
side.


# 2. Developers

(c) Sergei Kozhukhov, 2024. Scientist in the Institute of Higher Nervous Activity and Neurophysiology, RAS, Moscow,
Russia.

E-mail: sergei.kozhukhov@ihna.ru

Website: https://www.ihna.ru/en/employees/sergei.kozhukhov

(c) the Institute of Higher Nervous Activity and Neurophysiology, Russian Academy of Sciences, Moscow, Russia

Address: 5A Butlerova str., Moscow, Russia

E-mail: admin@ihna.ru

Phone number: +7 (495) 334-70-00

Website: https://www.ihna.ru

# 3. License notes

Please, see LICENSE.txt for details

# 4. Installation instructions

First, open the following URL: https://github.com/serik1987/corefacility-monthly-checker/releases

Click on the latest stable release of the corefacility-checker. You will see the "Assets" section on the bottom.
Expand this section, right-click on the .whl file and select the "Copy link URL" option.

Then, you have to open the terminal of your high-performance server (e.g., by means of SSH). Type `wget` on the
terminal, press space and paste the information from the clipboard here. In the long run you have to see something
like this:

```commandline
wget https://github.com/serik1987/corefacility-monthly-checker/releases/download/1.0.1/corefacility_monthly_checker-1.0.1-py3-none-any.whl
```

Press Enter to launch this command. It will download the latest release of the corefacility-checker on your
high-performance server.

The next stage is to ensure that the Python version 3.10 or later has been installed. To ensure that the Python
has been installed, run the following command

```commandline
python --version
```

The negative result mean that the latest version of the Python has not been installed. To install this you can run
the following command in the Linux Ubuntu Server:

```commandline
sudo apt install python3 python3-pip
```

To install python on another distributions refer to corresponding manuals.

Once the python is installed you have to add the `corefacility-checker` distribution to the python system. This can
be added by the following command:

```commandline
sudo pip install $(ls *.whl)
```

The last step is to set default configuration settings of the corefacility-checker. This can be done by the following
command:

```commandline
sudo corefacility-checker --copy-config /etc/corefacility/checker.json
```

The only thing that is remained is to change the contents of the `checker.json` file according to your hardware features
and how deeply you wish to provide the regular testing. Refer to the following sections on how to do this.

# 5. Corefacility configuration file

To create standard settings of the corefacility-checker run the command above. However, you are also allowed to create
local corefacility settings. When running the tests you will have a choice to use the standard settings or the local
settings. To create default local settings you may run the following command:

```commandline
sudo corefacility-checker --copy-config $(pwd)/my-settings.json
```

The configuration file has JSON format with the following sections.

`posix_log` Location of default logging file for your Linux distribution. The default value is valid for the Linux
Ubuntu. Change the default value if you have another distribution.

`logging` Defines how the corefacility-checker will tell you about whether the tests are succeed or failed.
This is no necessity to modify this section but if you want to do this, refer to this link on how to do this:
https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema

`mailing` Defines how the corefacility-checker will e-mail you. This section will tell the corefacility-checker
how to interact with the SMTP server required for the mail delivery.  You can e-mail the check status either by the
internal SMTP server installed on your high-performance server or by external SMTP server like gmail.com, mail.ru etc.
The  second one is the only option when the server is accessible only via the Intranet or VPN. Contact the system
administrator of your SMTP server on how to adjust such properties

`set_up` POSIX commands to be run before all test. Value of this property is list of all command. Each command in the
list will be interpreted by the bash interpreter.

`set_up` POSIX commands to be run after all test. Value of this property is list of all command. Each command in the
list will be interpreted by the bash interpreter.

`tests` list of tests to perform. The value of this property is dictionary like test name => test properties.
The test name doesn't influence on how the corefacility-check will work, so you can put any arbitrary string here.
The test value is a set of test properties. The test properties define how the test will check your server. All test
properties are described in the next section.


## 5.1. Test classes

All tests must contain the `class` property that defines the test class. Test class is what the corefacility-checker
will do during the test. Here are list of all test classes.

### 5.2. `posix_command`

Allows to call the external test routine like fsck, ping etc. When you choose the `posix_command` as the test class you
need to specify the `command` property that contains the command itself. Such a command must exit with the code 0 at
success and with the non-zero code at failure. The command will be interpreted by the bash interpreter.

### 5.3. `cpu_test`

Engages all CPU kernels by a sample job (particularly, Fast Fourier Transform of the noise) and measures the temperature
of each CPU kernel. If the temperature is above 71C the test has failed. Test properties:

`duration` how long does the CPU kernels will be engaged. Increasing this value will give you more accurate results but
during longer period of time. We are sure that 10 minutes is an optimal value.

### 5.4. `memory_test`

Checks operating memory with I/O bus errors using the `memtester` utility. Point out total amount of memory to test
in the `memory_size` property.

### 5.5. `disk_physical_reading`

Reads each block of the disk, then looks for operating system logs for the ATA bus I/O errors.

`device` is the device file

`count` number of blocks to read. Remove/omit this property to read all blocks.

### 5.6. `smart`

Tests list of drives with the `smartmontools` utility. Use the following properties:

`devices` list of all devices to test. All devices will be tested in parallel.

`test_type` `short` for short test, `long` for long and more accurate test.

### 5.7. `sql_dump`

Dumps the SQL database to some external storage, compresses the SQL dump and stores the compressed dumps on another
drive.

`command` POSIX command responsible for the SQL dump. Please, refer to the reference manual for your Database Management
System for more certain information. The command will be executed in the bash interpreter. When writing the command
you have to use the `$output` variable that contains name of the file where the SQL dump will be written.

`temporary_dump_folder` A temporary folder that contains uncompressed files. The corefacility-checker will create
uncompressed dumps, put them into this folder, then compress them and remove uncompressed dumps.

`permanent_dump_folder` A folder that contains compressed dumps. Such dumps will be remained after finishing the dump.

`max_backup_size` if the SQL dump doesn't exceed this size, the dump will send you by the e-mail and its copy
will be stored on the `permanent_dump_folder`. If the SQL dump exceeds this size the dump will be stored in the
`permanent_dump_folder` only, no e-mail will be sent in this case.

# 6. Running the tests

To run the tests using the standard test configuration just do the following command:

```commandline
sudo corefacility-checker
```

To run the tests using the `my-tests.json` local configuration file do the following command:

```commandline
sudo corefacility-checker --config $(pwd)/my-tests.json
```

By default, all tests mentioned in the `tests` section of the configuration file will be launched. To launch just one
test or several tests append the list of name of the tests (they relate to keys of the `tests` dictionary) to run after
the end of this command. It should look like:

```commandline
sudo corefacility-checker network cpu memory os_update
```

# 7. And don't forget to setup regular test running

You can do this using the `cron` daemon or with the aid of the systemd timers - that's absolutely your choice!
