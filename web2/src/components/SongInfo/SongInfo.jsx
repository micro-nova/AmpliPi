import './SongInfo.scss'

const SongInfo = ({ 
  info, 
  artistClassName, 
  albumClassName, 
  trackClassName 
}) => {
  artistClassName = "artist-name " + artistClassName
  albumClassName = "album-name " + albumClassName
  trackClassName = "track-name " + trackClassName

  return (
    <div className="song-info">
      <div className={artistClassName}>{info.artist}</div>
      <div className={albumClassName}>{info.album}</div>
      <div className={trackClassName}>{info.track}</div>
    </div>
  );
}

export default SongInfo;
