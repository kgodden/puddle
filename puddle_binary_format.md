# Puddle Binary Format

Format of the binary data that defines pulse trains.  This data is generated ou the puddle 
Python script and send to the device that generates the pulse trains.

## Types:

Note: All multi-byte data is in Network Byte Order (Bug Endian)

- U1 Unsigned 8bit integer
- U2 Unsigned 16bit integer
- U4 Unsigned 32bit integer

## Outputs

Multiple outputs are defined along with their desired default state.
Each output is identified by its index, these are powers of two so that multiple indicies
can be specified as a bitfield.  The outputs map to physical pins on a pre-device type basis.
            
output_count: U2

Next we have output_count outputs:

output:
- id: U2 (i.e. 0, 1, 2, 4, ..., 16)
- initial_state: U1, 0 or 1

## Pulses
            
Multiple pulses will be defined, these result in a state transition of one or more outputs.

pulse_count: U2, the number of pulses that are defined in the following data.
    
Next we have pulse_count pulses:

pulse:
- start_time: U4, The start time of this pulse in microsconds
- end_time: U4, The end time of this pulse in microsconds
- sense - U1: The pulse's sense
    - 1 - Active High,
    - 0 - Active Low
- outputs: U2, specifies the outouts that get affected as a bitfield.

## Profiles
    
Profiles

profile_count - U2, The number of profiles defined here.

multiple profiles -
    pulses - U2, Bit mask that identifies the pulses that are defined in the following data.
    

## Boot    
boot - 
    boot_profile - U1
    