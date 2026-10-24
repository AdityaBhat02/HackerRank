import sys
import os
import csv
import json

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')

# Test hash resolution
p = resolver.resolve_user_by_hash('44a65154bfd8e408852578fbd76813d094d1944f255ac1769ee81ba90492f10e')
print('Resolved hash:', p.user_id if p else None, p.email if p else None)

# Test noah old email
p2 = resolver.resolve_user_by_email('noah.f438085@outlook.com')
print('Resolved noah old email:', p2.user_id if p2 else None, p2.email if p2 else None)
