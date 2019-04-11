settings = {
  'default_interval': 5,
  'default_prefix': 'LZR.E98',
  'default_objects_collection': ['default_objects'],
  'additional_metric_attributes': ['room', 'rack', 'unit']
  'snmp_object_collections': {
      'default_objects': {
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.1': {  # power pro Phase
            'suffix': 'B83.W1',
            'unit': 'W',
            'short_description': 'Power Phase 1',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.2': {
            'suffix': 'B83.W2',
            'unit': 'W',
            'short_description': 'Power Phase 2',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.63.1.1.3': {
            'suffix': 'B83.W3',
            'unit': 'W',
            'short_description': 'Power Phase 3',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.1': {  # current pro Phase
            'suffix': 'B81.L1',
            'unit': 'A',
            'short_description': 'Current Phase 1',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.2': {
            'suffix': 'B81.L2',
            'unit': 'A',
            'short_description': 'Current Phase 2',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.22.1.1.3': {
            'suffix': 'B81.L3',
            'unit': 'A',
            'short_description': 'Current Phase 3',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.1': {  # voltage pro Phase
            'suffix': 'B82.L1',
            'unit': 'V',
            'short_description': 'Voltage Phase 1',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.2': {
            'suffix': 'B82.L2',
            'unit': 'V',
            'short_description': 'Voltage Phase 2',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.19.1.1.3': {
            'suffix': 'B82.L3',
            'unit': 'V',
            'short_description': 'Voltage Phase 3',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.1': {  # powerfactor pro Phase
            'suffix': 'B84.L1',
            'unit': '',
            'short_description': 'Power Factor Phase 1',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.2': {
            'suffix': 'B84.L2',
            'unit': '',
            'short_description': 'Power Factor Phase 2',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.30.40.1.67.1.1.3': {
            'suffix': 'B84.L3',
            'unit': '',
            'short_description': 'Power Factor Phase 3',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.1': {  # power pro Stromkreis
            'suffix': 'B83.WA',
            'unit': 'W',
            'short_description': 'Power Circuit A',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.2': {
            'suffix': 'B83.WB',
            'unit': 'W',
            'short_description': 'Power Circuit B',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.3': {
            'suffix': 'B83.WC',
            'unit': 'W',
            'short_description': 'Power Circuit C',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.4': {
            'suffix': 'B83.WD',
            'unit': 'W',
            'short_description': 'Power Circuit D',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.5': {
            'suffix': 'B83.WE',
            'unit': 'W',
            'short_description': 'Power Circuit E',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.115.1.6': {
            'suffix': 'B83.WF',
            'unit': 'W',
            'short_description': 'Power Circuit F',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.1': {  # current pro Stromkreis
            'suffix': 'B81.LA',
            'unit': 'A',
            'short_description': 'Current Circuit A',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.2': {
            'suffix': 'B81.LB',
            'unit': 'A',
            'short_description': 'Current Circuit B',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.3': {
            'suffix': 'B81.LC',
            'unit': 'A',
            'short_description': 'Current Circuit C',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.4': {
            'suffix': 'B81.LD',
            'unit': 'A',
            'short_description': 'Current Circuit D',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.5': {
            'suffix': 'B81.LE',
            'unit': 'A',
            'short_description': 'Current Circuit E',
         },
         '.1.3.6.1.4.1.476.1.42.3.8.40.20.1.130.1.6': {
            'suffix': 'B81.LF',
            'unit': 'A',
            'short_description': 'Current Circuit F',
         }
      },
      'temperature_sensor':
         '.1.3.6.1.4.1.476.1.42.3.8.60.15.1.70.1.1.1': {
            'suffix': 'B30',
            'unit': 'degC',
            'description': 'Temperature',
            'interval': 60,
         }
      }
   },
   'hosts': {
      '172.30.144.11': {
         'name': 'LZR-P70-S21-S1-L',
         'room': 'S21',
         'rack': 'S1',
         'infix': '2101A',
         'description': 'Room S21 Rack S1 PDU A',
         'objects': ['default_objects', 'temperature_sensor'],
      }
   }
}

def parse_config(cfg):
   pass
