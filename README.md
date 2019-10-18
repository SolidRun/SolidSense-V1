# SolidSense-V1
Version V1 of the gateway based on CIP

That repo is progressively augmented

# RPMB

Here are the fields and length to be used in the RPMB memory and set in factory.
The RPMB is only written in factory in the current version

## Fields
1. Serial Number: offset= X, length=Y
2. Partnumber: offset= , length=
3. Sink configuration (see below)

C like definition

	Typedef struct {
                char [6] sink_type; // fixed length no trailing NULL “NINAB1” or “NINAB3”
                char [2] stack_type; 
                // fixed length one of 
                //“EM” (Empty), 
                // “UB” Ublox connectivity SW,   
                // “HC” HCI stack,
                // "WP" Wirepas stack
                char[12] sw_version;  // can variable length NULL terminated “4.0.50”
	} sink_conf;

	Struct {
                Unsigned char number_of_sinks;
                Sink_conf[number_of_sinks] sinks;
} sink_rpmb;







# Kura

Include all Kura spefic add-ons and configuration files

## Kura configuration

All the files that are needed to configure Kura and by consequence the many aspects of the gateway. See dedicated file in the Kura directory

## LTE modem management

Kura (Java) module needed to configure the ppp interface
