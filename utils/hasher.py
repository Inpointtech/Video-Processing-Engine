"""Utility for generating the raw hashes."""

import string
import itertools

# Dictionary for characters from range 0 - 25.
hash_26 = {k: v for k, v in enumerate(string.ascii_uppercase, start=1)}
# Dictionary for characters from range 0 - 51.
hash_52 = {k: v for k, v in enumerate(string.ascii_letters, start=1)}
# Dictionary for characters from range 0 - 2703
temp = itertools.product(string.ascii_letters, string.ascii_letters)
hash_2704 = {k: v for k, v in enumerate(list(map(''.join, temp)), start=1)}
# Dictionary for hashing area.
hash_area = {'P': 'Parking lot',
             'G': 'Garage',
             'C': 'Counter',
             'K': 'Kitchen',
             'L': 'Lobby',
             'A': 'Aisle',
             'B': 'Basement',
             'F': 'Cafeteria',
             'O': 'Outdoor area',
             'W': 'Workdesk',
             'M': 'Meeting/conference room',
             'R': 'Reception desk',
             'X': 'Exit',
             'N': 'Entrance',
             'E': 'Extras'}
# Dictionary for hashing codecs and extensions.
hash_extension = {'libx264': 'mp4',
                  'mpeg4': 'mp4',
                  'rawvideo': 'avi',
                  'png': 'avi',
                  'libvorbis': 'ogv',
                  'libvpx': 'webm'}
# List of all 248 country codes.
country_codes_2_letter = ['AF', 'AL', 'DZ', 'AS', 'AD', 'AO', 'AI', 'AQ', 'AG',
                          'AR', 'AM', 'AW', 'AU', 'AT', 'AZ', 'BS', 'BH', 'BD',
                          'BB', 'BY', 'BE', 'BZ', 'BJ', 'BM', 'BT', 'BO', 'BQ', 
                          'BA', 'BW', 'BV', 'BR', 'IO', 'BN', 'BG', 'BF', 'BI', 
                          'KH', 'CM', 'CA', 'CV', 'KY', 'CF', 'TD', 'CL', 'CN', 
                          'CX', 'CC', 'CO', 'KM', 'CG', 'CD', 'CK', 'CR', 'HR', 
                          'CU', 'CW', 'CY', 'CZ', 'CI', 'DK', 'DJ', 'DM', 'DO', 
                          'EC', 'EG', 'SV', 'GQ', 'ER', 'EE', 'ET', 'FK', 'FO', 
                          'FJ', 'FI', 'FR', 'GF', 'PF', 'TF', 'GA', 'GM', 'GE', 
                          'DE', 'GH', 'GI', 'GR', 'GL', 'GD', 'GP', 'GU', 'GT', 
                          'GG', 'GN', 'GW', 'GY', 'HT', 'HM', 'VA', 'HN', 'HK', 
                          'HU', 'IS', 'IN', 'ID', 'IR', 'IQ', 'IE', 'IM', 'IL', 
                          'IT', 'JM', 'JP', 'JE', 'JO', 'KZ', 'KE', 'KI', 'KP', 
                          'KR', 'KW', 'KG', 'LA', 'LV', 'LB', 'LS', 'LR', 'LY', 
                          'LI', 'LT', 'LU', 'MO', 'MK', 'MG', 'MW', 'MY', 'MV', 
                          'ML', 'MT', 'MH', 'MQ', 'MR', 'MU', 'YT', 'MX', 'FM', 
                          'MD', 'MC', 'MN', 'ME', 'MS', 'MA', 'MZ', 'MM', 'NA', 
                          'NR', 'NP', 'NL', 'NC', 'NZ', 'NI', 'NE', 'NG', 'NU', 
                          'NF', 'MP', 'NO', 'OM', 'PK', 'PW', 'PS', 'PA', 'PG', 
                          'PY', 'PE', 'PH', 'PN', 'PL', 'PT', 'PR', 'QA', 'RO', 
                          'RU', 'RW', 'RE', 'BL', 'SH', 'KN', 'LC', 'MF', 'PM', 
                          'VC', 'WS', 'SM', 'ST', 'SA', 'SN', 'RS', 'SC', 'SL', 
                          'SG', 'SX', 'SK', 'SI', 'SB', 'SO', 'ZA', 'GS', 'SS', 
                          'ES', 'LK', 'SD', 'SR', 'SJ', 'SZ', 'SE', 'CH', 'SY', 
                          'TW', 'TJ', 'TZ', 'TH', 'TL', 'TG', 'TK', 'TO', 'TT', 
                          'TN', 'TR', 'TM', 'TC', 'TV', 'UG', 'UA', 'AE', 'GB', 
                          'US', 'UM', 'UY', 'UZ', 'VU', 'VE', 'VN', 'VG', 'VI', 
                          'WF', 'EH', 'YE', 'ZM', 'ZW']
# Dictionary of hashed country codes.
hash_248 = list(hash_2704.values())[:248]
hash_country = {k: v for k, v in zip(country_codes_2_letter, hash_248)}
