import { getSourceInputType } from "./getSourceInputType"


export const zoneIdToZone = (id, zones) => zones.filter(it => it.id === id)[0]

// returns promise so that you can chain together more fetches
export const moveSourceContents = (status, fromId, toId) => {
  const zones = status.zones
  const sources = status.sources

  const zoneIds = zones.filter(z => z.source_id === fromId).map(z => z.id)
  const fromSource = sources[fromId]
  const fromStreamInput = fromSource.input
  const streamType = getSourceInputType(fromSource)

  // move zones
  
  // return fetch('/api/zones', {
  //   method: 'PATCH',
  //   headers: {'Content-type': 'application/json'},
  //   body: JSON.stringify({
  //     'zones': zoneIds,
  //     'update': {
  //       'source_id': toId
  //     }
  //   })
  // }).then(() => {
  //   // move stream
  //   if (streamType === 'digital') {
  //     fetch(`/api/sources/${toId}`, {
  //       method: 'PATCH',
  //       headers: {'Content-type': 'application/json'},
  //       body: JSON.stringify({
  //         'input': fromStreamInput
  //       })
  //     })
  //   }
  // })
  console.log(`moving zones: ${zoneIds} to source: ${toId}`)

  if (streamType === 'digital') {
    return fetch(`/api/sources/${toId}`, {
      method: 'PATCH',
      headers: {'Content-type': 'application/json'},
      body: JSON.stringify({
        'input': fromStreamInput
      })
    }).then(
      fetch('/api/zones', {
        method: 'PATCH',
        headers: {'Content-type': 'application/json'},
        body: JSON.stringify({
          'zones': zoneIds,
          'update': {
            'source_id': toId
          }
        })
      })
    )
  } else {
    return fetch('/api/zones', {
      method: 'PATCH',
      headers: {'Content-type': 'application/json'},
      body: JSON.stringify({
        'zones': zoneIds,
        'update': {
          'source_id': toId
        }
      })
    })
  }
}

export const setSourceStream = (sourceId, streamId) => {
  return fetch(`/api/sources/${sourceId}`, {
    method: 'PATCH',
    headers: {'Content-type': 'application/json'},
    body: JSON.stringify({ input: `stream=${streamId}` }),
  })
}