import PageHeader from "@/components/PageHeader/PageHeader"
import { useStatusStore } from "@/App"
import "./About.scss"

const About = ({onClose}) => {

  const info = useStatusStore.getState().status.info

  console.log(info)

  return(
    <>
      <PageHeader title="About" onClose={onClose}/>
      <div className="about-body">
        <a href="http://www.amplipi.com">Amplipi ™</a>
        <br/>
        by <a href="http://www.micro-nova.com">MicroNova</a> © {(new Date(Date.now())).getFullYear()}
        <br/>
        Version: {info.version}
        <br/>
        Latest: {info.latest_release}
        <br/>
        <ul>
        Links:
          <li><a href="/doc">Browsable API</a></li>
          <li><a href="https://github.com/micro-nova/AmpliPi">Github</a></li>
          <li><a href="https://amplipi.discourse.group/">Community</a></li>
          <li><a href="https://github.com/micro-nova/AmpliPi/blob/main/COPYING">License</a></li>
          <li><a href={window.location.href} onClick={()=>{window.location.href="http://"+window.location.hostname+':19531/entries'}}>Logs</a></li>
        </ul>



      </div>

    </>
  )

}

export default About
