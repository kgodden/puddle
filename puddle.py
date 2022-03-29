#!/usr/bin/python

#   Copyright 2018 Kevin Godden
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from lark import Lark,  Transformer, v_args
import re

from shutil import copyfile

def tool_name():
    """
    Returns the tools name for display in the dropdown box.
    :return: The tool's name
    """
    return "the tool name"

def tool_description():
    """
    Returns a long textual description of te tool for display in App tooltip or
    similar.
    :return: The tool's description
    """

    return "This text describes what the tool does"

def display_settings():
    """
    Somehow display some setting UI controls on the main app
    so that user can set tool specific settings, like start time / end
    time or brightness thresholds etc...

    Not sure how to do this!

    """
    pass

def tool_process(input_image_path, output_image_path):
    """
    Process an image and (maybe) copies an output image to the output path
    :param input_image_path: path to the input image file
    :param output_image_path: path to output image file to be written to.
    :return: success / failure code of some sort
    """

    # just copy the image over
    # need to check output directory exists first
    copyfile(input_image_path, output_image_path)


def get_attribute(name, attributes):

    attr = None

    for c in attributes.children:
        if c.data == name:
            attr = str(c.children[0])
            break

    return attr

def get_statement_parts(statement):
    return str(statement.children[0]), statement.children[1]

def load_outputs(out_statements):
    ops = {}

    for statement in out_statements:
        name, attributes = get_statement_parts(statement)
        target = get_attribute('target', attributes)
        initial_state = get_attribute('initial_state', attributes)

        ops[name] = { "name" : name, "target": target, "initial_state": initial_state}

    return ops

def load_pulses(pulse_statements):
    pulses = {}

    for statement in pulse_statements:
        name, attributes = get_statement_parts(statement)
        output = get_attribute('target_output', attributes)
        active = load_number(get_attribute('active', attributes), int)
        sense = get_attribute('sense', attributes)

        pulses[name] = { "name": name, "target_output": output, "active": active, "sense": sense}

    return pulses

'''
# We trigger the lights at 40Hz
pulse_train lights:
    pulse: light_pulse
    frequency: 40Hz
    offset: 0us
    '''

def load_profiles(profile_statements):
    profiles = {}

    for statement in profile_statements:
        name, attributes = get_statement_parts(statement)
        pulse_train = get_attribute('target_pulse_train', attributes)
        enabled = get_attribute('enabled', attributes) == "true"
        profiles[name] = { "name": name, "pulse_train": pulse_train, "enabled": enabled}

    return profiles

def load_number(snum, target_type):
    exp = re.search(r'^\s*(\d*[.,]?\d*)\D*$', snum)

    val = target_type(exp.group(1))

    return val

def load_pulse_trains(pulse__train_statements):
    pulse_trains = {}

    for statement in pulse__train_statements:
        name, attributes = get_statement_parts(statement)
        pulse = get_attribute('target_pulse', attributes)
        frequency = load_number(get_attribute('frequency', attributes), float)
        offset = load_number(get_attribute('offset', attributes), float)
        pulse_count = load_number(get_attribute('pulse_count', attributes), int)

        pulse_trains[name] = { "name": name, "pulse": pulse, "frequency": frequency, "offset": offset, "pulse_count": pulse_count}

    return pulse_trains

def compile_pulse_train(pulse_train, cycle_time, pulses, outputs):
    print("Compiling pulse_train: %s" % pulse_train['name'])

    frequency = pulse_train['frequency']
    period = 1E6 / frequency
    pulse_count = int(cycle_time / period)

    events = []

    for p in range(pulse_count + 1):
        start = 0
        end = 0

        start = p * period
        end = start + pulses[pulse_train['pulse']]['active']
        outputs = [ pulses[pulse_train['pulse']]['target_output']]

        event = { "pulse": pulse_train['name'],
                    "start": start,
                    "end": end,
                    "outputs": outputs}

        events.append(event)

    return events


def calculate_cycle_time(pulse_trains):
    for name, pulse_train in pulse_trains.items():
        if pulse_train['pulse_count'] != -1:
            break

    pulse_count = pulse_train['pulse_count']
    frequency = pulse_train['frequency']

    period = 1E6 / frequency

    cycle_time = int(pulse_count * period)

    return cycle_time




def compile_pulse_trains(profiles, pulse_trains, pulses, outputs):
    # want to create an event time line
    # for each profile we want to get the corresponding pulse trains
    # then for each pulse train we generate a list of state changes with times
    # then we associate the outputs with each
    # so have a list of events, each event has:
    # a us time
    # an action -> this output goes HIGH or LOW etc...
    # we also calculate a cycle time after which the pulses will be repeated..

    cycle_time = calculate_cycle_time(pulse_trains)
    print("Cycle time is %d us" % cycle_time)

    pulse_events = []

    for name, profile in profiles.items():
        print("Compiling profile: %s" % name)
        pulse_train = pulse_trains[profile['pulse_train']]
        pulse_events += compile_pulse_train(pulse_train, cycle_time, pulses, outputs)

    # now have list of pulse events with times
    sorted(pulse_events, key=lambda e : e['start'])

    #output_events = generate_output_events(pulse_events, pulses, outputs)

#print( l.parse(data).pretty())

def load_declarations():
    grammer = '''

        start: statement+

        statement: output | pulse | pulse_train | profile

        // Output
        // e.g.
        //
        // output light_trigger_op:
        // target: PORTB.0

        output: "output" NAME ":" output_attr+
        output_attr: output_target output_initial_state
        output_target: "target" ":" NAME -> target
        output_initial_state: "initial_state" ":" OP_LEVEL -> initial_state

        // Pulse
        pulse: "pulse" NAME ":" pulse_attr+    -> pulse
        pulse_attr: pulse_output pulse_active pulse_sense
        pulse_output: "output" ":" NAME             -> target_output
        pulse_active: "active" ":" TIME_VAL      -> active
        pulse_sense: "sense" ":" ACTIVE_HL             -> sense

        // Pulse Train
        pulse_train: "pulse_train" NAME ":" pulse_train_attr+    -> pulse_train

        pulse_train_attr: pulse_train_pulse pulse_train_frequency pulse_train_offset pulse_train_count?
        pulse_train_pulse: "pulse" ":" NAME             -> target_pulse
        pulse_train_frequency: "frequency" ":" FREQ_VAL             -> frequency
        pulse_train_offset: "offset" ":" TIME_VAL             -> offset
        pulse_train_count: "pulse_count" ":" NUMBER             -> pulse_count

        profile: "profile" NAME ":" profile_attr+    -> profile
        profile_attr: target_pulse_train profile_enabled
        target_pulse_train: "pulse_train" ":" NAME             -> target_pulse_train
        profile_enabled: "enabled" ":" BOOL_VAL             -> enabled

        COMMENT:  "#" /(.)+/ NEWLINE
        %ignore COMMENT

        NAME : LETTER (LETTER | "_" | DIGIT | ".")*
        OP_LEVEL : "low" | "high"
        ACTIVE_HL : "active_high" | "active_low"
        TIME_VAL : NUMBER "us"?
        FREQ_VAL : NUMBER "Hz"?
        BOOL_VAL : "true" | "false"
        %import common.LETTER
        %import common.DIGIT
        %import common.INT -> NUMBER
        %import common.WS
        %ignore WS
        %import common.NEWLINE

    '''

    l = Lark(grammer)

    data = '''
    output light_trigger_op:
        target: PORTB.0
        initial_state: high

    output left_camera_trigger_op:
        target: PORTB.1
        initial_state: high

    output right_camera_trigger_op:
        target: PORTB.1
        initial_state: high

    pulse light_pulse:
        output : light_trigger_op
        active : 2000us
        sense  : active_low

    # We trigger the lights at 40Hz
    pulse_train lights:
        pulse: light_pulse
        frequency: 40Hz
        offset: 0us
        pulse_count: 8

    profile main:
        pulse_train: lights
        enabled: true

    '''

    statements = l.parse(data)

    out_statements = statements.find_pred(lambda s: s.data == 'output')
    outputs = load_outputs(out_statements)

    pulse_statements = statements.find_pred(lambda s: s.data == 'pulse')
    pulses = load_pulses(pulse_statements)

    pulse_train_statements = statements.find_pred(lambda s: s.data == 'pulse_train')
    pulse_trains = load_pulse_trains(pulse_train_statements)

    profile_statements = statements.find_pred(lambda s: s.data == 'profile')
    profiles = load_profiles(profile_statements)

    print("Loaded %d outputs:" % len(outputs))

    for name, output in outputs.items():
        print("name: %s | target: %s | initial_state: %s" % (name, output['target'], output['initial_state']))

    print("Loaded %d pulses:" % len(pulses))

    for name, pulse in pulses.items():
        print("name: %s | target_output: %s | active: %s | sense: %s" % (name, pulse['target_output'], pulse['active'],  pulse['sense']))

    print("Loaded %d pulse trains:" % len(pulse_trains))

    for name, pulse_train in pulse_trains.items():
        print("name: %s | pulse: %s | frequency: %s | offset: %s | pulse_count: %s" % (name, pulse_train['pulse'], pulse_train['frequency'],  pulse_train['offset'], pulse_train['pulse_count']))

    print("Loaded %d profiles:" % len(profiles))

    for name, profile in profiles.items():
        print("name: %s | pulse_train: %s, enabled: %s" % (name, profile['pulse_train'], profile['enabled']))

    bin = compile_pulse_trains(profiles, pulse_trains, pulses, outputs)

if __name__ == "__main__":
    load_declarations()