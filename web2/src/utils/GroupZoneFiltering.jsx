
// for the given group, returns how many zones in zones it contains
export const groupZoneMatchCount = (zones, group) => zones.reduce((sum, zone) => sum + (group.zones.includes(zone.id) ? 1 : 0), 0)

// returns the group with the most matches, and updated zones and groups with the used things subtracted
export const getFittestGroup = (zones, groups) => {
  let bestFitness = 0
  let best = null
  for (const group of groups) {

    let fitness = groupZoneMatchCount(zones, group)
    console.log(`${group.name}, ${group.zones}, ${fitness}`)
    if (fitness > bestFitness) {
      bestFitness = fitness
      best = group
    }
  }

  let newZones = zones
  let newGroups = groups

  if (best !== null) {
    newZones = zones.filter(zone => !best.zones.includes(zone.id))
    newGroups = groups.filter(group => group !== best)
  }

  return {
    'best': best,
    'zones': newZones,
    'groups': newGroups,
  }
}

// given the zones and groups for a source, find an optimal-ish representation
// with minimal zones by maximizing groups
export const getFittestRep = (zones, groups) => {
  let zonesLeft = [...zones]
  let groupsLeft = [...groups]
  let usedGroups = []
  let res = getFittestGroup(zonesLeft, groupsLeft)
  while (res.best !== null) {
    usedGroups.push(res.best)
    zonesLeft = res.zones
    groupsLeft = res.groups
    res = getFittestGroup(zonesLeft, groupsLeft)
  }

  return {
    'zones': zonesLeft,
    'groups': usedGroups,
  }
}
