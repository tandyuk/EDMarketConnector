#!/usr/bin/python
#
# Script for collating lists of seen commodities, modules and ships from dumps of the Companion API output
#

import csv
import json
import os
from os.path import exists, isfile
import sys

from eddn import ship_map	# use EDDN ship names
from companion import category_map, commodity_map
import outfitting


# keep a summary of commodities found using in-game names
def addcommodities(data):

    if not data['lastStarport'].get('commodities'): return

    commodityfile = 'commodity.csv'
    commodities = {}

    # slurp existing
    if isfile(commodityfile):
        with open(commodityfile) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = row.pop('name')
                commodities[key] = row
    size_pre = len(commodities)

    for commodity in data['lastStarport'].get('commodities'):
        key = commodity_map.get(commodity['name']) or commodity['name']
        new = {
            'id'       : commodity['id'],
            'category' : category_map.get(commodity['categoryname']) or commodity['categoryname'],
            'average'  : commodity['cost_mean'].split('.')[0]
        }
        old = commodities.get(key)
        if old:
            if new != old:
                raise AssertionError('%s: "%s"!="%s"' % (key, new, old))
        else:
            commodities[key] = new

    if len(commodities) > size_pre:

        if isfile(commodityfile):
            if isfile(commodityfile+'.bak'):
                os.unlink(commodityfile+'.bak')
            os.rename(commodityfile, commodityfile+'.bak')

        with open(commodityfile, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, ['id','category', 'name', 'average'])
            writer.writeheader()
            for key in commodities:
                commodities[key]['name'] = key
            for row in sorted(commodities.values(), key = lambda x: (x['category'], x['name'])):
                writer.writerow(row)

        print 'Added %d new commodities' % (len(commodities) - size_pre)

# keep a summary of modules found
def addmodules(data):

    if not data['lastStarport'].get('modules'): return

    outfile = 'outfitting.csv'
    modules = {}

    # slurp existing
    if isfile(outfile):
        with open(outfile) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = int(row.pop('id'))	# index by int for easier lookup and sorting
                modules[key] = row
    size_pre = len(modules)

    for key,module in data['lastStarport'].get('modules').iteritems():
        # sanity check
        if int(key) != module.get('id'): raise AssertionError('id: %s!=%s' % (key, module['id']))
        new = outfitting.lookup(module, ship_map)
        if new:
            old = modules.get(int(key))
            if old:
                # check consistency with existing data
                for thing in ['category', 'name', 'mount', 'guidance', 'ship', 'class', 'rating']:
                    if new.get(thing,'') != old.get(thing): raise AssertionError('%s: %s "%s"!="%s"' % (key, thing, new.get(thing), old.get(thing)))
            else:
                modules[int(key)] = new

    if len(modules) > size_pre:

        if isfile(outfile):
            if isfile(outfile+'.bak'):
                os.unlink(outfile+'.bak')
            os.rename(outfile, outfile+'.bak')

        with open(outfile, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, ['id', 'category', 'name', 'mount', 'guidance', 'ship', 'class', 'rating'])
            writer.writeheader()
            for key in sorted(modules):
                row = modules[key]
                row['id'] = key
                writer.writerow(row)

        print 'Added %d new modules' % (len(modules) - size_pre)

# keep a summary of ships found
def addships(data):

    if not data['lastStarport'].get('ships'): return

    shipfile = 'shipyard.csv'
    ships = {}

    # slurp existing
    if isfile(shipfile):
        with open(shipfile) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ships[int(row['id'])] = row['name']	# index by int for easier lookup and sorting
    size_pre = len(ships)

    for ship in (data['lastStarport']['ships'].get('shipyard_list') or {}).values() + data['lastStarport']['ships'].get('unavailable_list'):
        # sanity check
        key = ship['id']
        new = ship_map.get(ship['name'].lower())
        if new:
            old = ships.get(int(key))
            if old:
                # check consistency with existing data
                if new != old: raise AssertionError('%s: "%s"!="%s"' % (key, new, old))
            else:
                ships[int(key)] = new

    if len(ships) > size_pre:

        if isfile(shipfile):
            if isfile(shipfile+'.bak'):
                os.unlink(shipfile+'.bak')
            os.rename(shipfile, shipfile+'.bak')

        with open(shipfile, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, ['id', 'name'])
            writer.writeheader()
            for key in sorted(ships):
                row = { 'id': key, 'name': ships[key] }
                writer.writerow(row)

        print 'Added %d new ships' % (len(ships) - size_pre)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print 'Usage: collate.py [dump.json]'
    else:
        # read from dumped json file(s)
        for f in sys.argv[1:]:
            with open(f) as h:
                print f
                data = json.load(h)
                if not data['commander'].get('docked'):
                    print 'Not docked!'
                elif not data.get('lastStarport'):
                    print 'No starport!'
                else:
                    if data['lastStarport'].get('commodities'):
                        addcommodities(data)
                    else:
                        print 'No market'
                    if data['lastStarport'].get('modules'):
                        addmodules(data)
                    else:
                        print 'No outfitting'
                    if data['lastStarport'].get('ships'):
                        addships(data)
                    else:
                        print 'No shipyard'
