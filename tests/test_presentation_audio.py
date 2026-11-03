"""Original audio order and explicit built-in PSG ownership contracts."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PresentationAudioTests(unittest.TestCase):
    def test_events_keep_same_values_silent_intervals_and_both_logical_steps(self):
        api=importlib.import_module('presentation_audio')
        records=[{'index':0,'cycles':100,'visible_cycles':60,'audio':[(70,21,12),(75,25,3),(80,25,3)]},
                 {'index':1,'cycles':101,'visible_cycles':61,'audio':[]},
                 {'index':2,'cycles':100,'visible_cycles':60,'audio':[(65,25,0)]}]
        intervals=api.events(records)
        self.assertEqual([r['logical_step'] for r in intervals],[0,1,2])
        self.assertEqual(intervals[0]['writes'],((70,21,12),(75,25,3),(80,25,3)))
        self.assertEqual(intervals[1]['writes'],())
        self.assertEqual(intervals[2]['writes'],((65,25,0),))
        for bad in ([{**records[0],'index':1}],[{**records[0],'audio':[(101,25,1)]}],
                    [{**records[0],'audio':[(80,25,1),(70,25,1)]}],[{**records[0],'audio':[(70,20,1)]}],[{**records[0],'audio':[(-1,25,1)]}]):
            with self.assertRaises(ValueError):api.events(bad)

    def test_source_tone_pitch_is_rounded_from_hardware_clock_ratio(self):
        api=importlib.import_module('presentation_audio')
        self.assertEqual([api.tone_period(12,f) for f in (0,1,31)],[21,43,684])
        self.assertEqual([api.tone_period(1,f) for f in (0,1,31)],[53,107,1710])
        self.assertEqual(api.tone_period(4,0),7)
        self.assertEqual(api.tone_period(2,31),4095)
        for control in (0,8,11):self.assertIsNone(api.tone_period(control,17))
        self.assertEqual(api.noise_period(2),11);self.assertEqual(api.noise_period(31),31)

    def test_psg_gpio_and_unowned_registers_survive_all_control_frequency_values(self):
        api=importlib.import_module('presentation_audio')
        for ports in (0,64,128,192):
            initial=bytearray(range(16));initial[7]=ports|63
            previous={'psg':bytes(initial)}
            for control in range(16):
                for frequency in range(32):
                    registers=bytes((control,12,frequency,31,15,9))
                    state=api.psg_step(registers,previous)
                    self.assertEqual(state['psg'][7]&192,ports)
                    self.assertEqual(state['psg'][7]&36,36)
                    self.assertEqual(state['psg'][10],0)
                    for index in (4,5,11,12,13,14,15):self.assertEqual(state['psg'][index],initial[index])
                    self.assertTrue(all(index in (0,1,2,3,6,7,8,9,10) for index,value in state['writes']))
                    self.assertEqual(previous,{'psg':bytes(initial)})
                    self.assertEqual(api.psg_step(registers,state)['writes'],())

    def test_noise_ownership_follows_active_channels_without_losing_their_latches(self):
        api=importlib.import_module('presentation_audio')
        first=api.psg_step(bytes((8,8,2,5,3,4)),{'psg':bytes(16)})
        self.assertEqual(first['noise_owner'],0);self.assertEqual(first['psg'][6],11)
        second=api.psg_step(bytes((8,8,2,5,0,4)),first)
        self.assertEqual(second['noise_owner'],1);self.assertEqual(second['psg'][6],21)
        self.assertEqual(second['source_registers'],bytes((8,8,2,5,0,4)))
        quiet=api.psg_step(bytes((8,8,2,5,0,0)),second)
        self.assertIsNone(quiet['noise_owner']);self.assertEqual(quiet['psg'][6],21)
        self.assertEqual(quiet['psg'][8:10],bytes(2))

    def test_bus_value_masks_are_hardware_masks_and_inputs_stay_immutable(self):
        api=importlib.import_module('presentation_audio')
        raw=bytes((252,241,255,254,255,254));previous={'psg':bytes(range(16))}
        result=api.psg_step(raw,previous)
        self.assertEqual(result['source_registers'],bytes((12,1,31,30,15,14)))
        self.assertEqual(raw,bytes((252,241,255,254,255,254)))
        self.assertEqual(previous,{'psg':bytes(range(16))})
        for data in (raw[:-1],raw+bytes(1),bytearray(raw)):
            with self.assertRaises(ValueError):api.psg_step(data,previous)

    def test_independent_capsule_latches_seed_the_audio_projection(self):
        api=importlib.import_module('presentation_audio_source_check')
        capsule={'tia':{'audio':{'channels':[{'control':1,'frequency':17,'volume':4},{'control':12,'frequency':3,'volume':0}]}}}
        initial=api.registers(capsule)
        self.assertEqual(initial,bytes((1,12,17,3,4,0)))
        previous={'psg':bytes(16)}
        final,projected,history=api.replay(initial,((70,25,0),(75,26,3),(80,26,3)),previous)
        self.assertEqual(final,bytes((1,12,17,3,0,3)))
        self.assertEqual(len(history),3)
        self.assertEqual(history[-1]['psg_writes'],())
        self.assertEqual(projected['psg'][8:10],bytes((0,3)))
        self.assertEqual(initial,bytes((1,12,17,3,4,0)))
        capsule['tia']['audio']['channels'][0]['control']=16
        with self.assertRaises(ValueError):api.registers(capsule)

    def test_every_raw_volume_byte_retains_its_bus_value_and_hardware_nibble(self):
        api=importlib.import_module('presentation_audio')
        for channel in (0,1):
            for value in range(256):
                raw=bytearray((12,12,0,0,0,0));raw[4+channel]=value;raw=bytes(raw)
                record={'index':0,'cycles':100,'visible_cycles':60,'audio':[(70,25+channel,value)]}
                self.assertEqual(api.events([record])[0]['writes'][0][2],value)
                state=api.psg_step(raw,{'psg':bytes(16)})
                self.assertEqual(state['psg'][8+channel],value&15)
                self.assertEqual(raw[4+channel],value)

    def test_native_table_rows_match_each_control_and_both_frequency_boundaries(self):
        api=importlib.import_module('presentation_audio');tables=api.tables()
        self.assertEqual(len(tables['data']),443)
        self.assertEqual(tables['offsets'],{'tone':0,'noise':384,'mixer':416,'defaults':432})
        for control in range(16):
            row=tables['tone_rows'][control]
            for frequency in (0,1,31):
                wanted=api.tone_period(control,frequency)
                if wanted is None:self.assertIsNone(row)
                else:
                    at=row*64+frequency*2
                    self.assertEqual(int.from_bytes(tables['data'][at:at+2],'little'),wanted)
        self.assertEqual(tables['data'][384:416],bytes(api.noise_period(f) for f in range(32)))
